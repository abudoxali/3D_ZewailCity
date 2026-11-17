"""V17 deterministic, complete internal transport surface generator.

The dated survey is evidence for alignment, not a current as-built survey.
Widths, 3 m junction returns, 2.5 m sidewalks and 0.30 m kerbs are engineering
ESTIMATES. External asphalt envelopes are immutable baseline geometry. Nothing
extends G2's exterior approach. Native POLY splines are the editable source;
curbs and sidewalks are cross sections of their union, never crossing ribbons.
"""
import hashlib
import json
import math
from pathlib import Path

import bpy
from shapely import make_valid, union_all
from shapely.geometry import LineString, Point, Polygon, box, mapping, shape
from shapely.ops import nearest_points

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/build_metadata/v17'
OVERRIDES = ROOT / 'src/utilities/data/v17_alignment_overrides.json'
COLLECTION = 'V17_Editable_Transport_Sources'
SCHEMA = 'zewail.transport-splines.v17.1'
DEFAULTS = {'curb_width_m': .30, 'sidewalk_width_m': 2.5,
            'junction_radius_m': 5.5, 'walk_merge_radius_m': 1.75,
            'walk_corner_radius_m': .65, 'footway_width_m': 2.5}
STATE = {}


def polys(g):
    if g.is_empty:
        return
    if g.geom_type == 'Polygon':
        yield g
    elif hasattr(g, 'geoms'):
        for p in g.geoms:
            yield from polys(p)


def clean(g):
    return union_all(list(polys(make_valid(g))))


def close(g, radius):
    return clean(g.buffer(radius, quad_segs=12).buffer(-radius, quad_segs=12))


def opening(g, radius):
    return clean(g.buffer(-radius, quad_segs=12).buffer(radius, quad_segs=12))


def _points(spec):
    return [[float(p.x), float(p.y)] for p in spec['pts']]


def _area_sources(name, role, material, geom):
    """Boundary loops, including holes, are real editable planar source splines."""
    result = []
    parts = sorted(polys(geom), key=lambda p: (round(p.centroid.x, 6), round(p.centroid.y, 6), p.area))
    for i, p in enumerate(parts):
        if p.area < .01:
            continue
        result.append({'id': f'{name}_{i:04d}', 'role': role, 'material': material,
                       'geometry': 'area', 'rings': [list(map(list, p.exterior.coords))] +
                       [list(map(list, h.coords)) for h in p.interiors],
                       'evidence': 'dated baseline boundary; editable source, dimensions estimated'})
    return result


def area(row):
    return clean(Polygon(row['rings'][0], row['rings'][1:]))


def _validate(document, roads):
    if document.get('schema') != SCHEMA:
        raise ValueError('Unsupported V17 transport source schema')
    ids = set()
    for row in document['sources']:
        if row['id'] in ids:
            raise ValueError('Duplicate V17 source: ' + row['id'])
        ids.add(row['id'])
        arrays = row.get('rings', [row.get('points', [])])
        for points in arrays:
            if len(points) < (3 if row['geometry'] == 'area' else 2):
                raise ValueError('Insufficient spline points: ' + row['id'])
            if not all(len(p) == 2 and all(math.isfinite(float(v)) for v in p) for p in points):
                raise ValueError('Nonfinite spline point: ' + row['id'])
        if row['geometry'] == 'area' and not Polygon(arrays[0], arrays[1:]).is_valid:
            raise ValueError('Self-intersecting source area: ' + row['id'])
        if row['geometry'] == 'line':
            width = float(row.get('width_m', 0))
            if not 1. <= width <= 30.:
                raise ValueError('Invalid estimated source width: ' + row['id'])
            if not 0.<=float(row.get('sidewalk_m',0.))<=10.:
                raise ValueError('Invalid estimated sidewalk width: '+row['id'])
    for name, spec in roads.items():
        matches = [r for r in document['sources'] if r['id'] == name and r['role'] == 'vehicle']
        if len(matches) != 1 or matches[0]['kind'] != spec['kind']:
            raise ValueError('Missing/reclassified dated road: ' + name)
        # No edit can silently move the immutable external reference network.
        if spec['kind'] == 'external' and matches[0]['points'] != _points(spec):
            raise ValueError('External alignment is immutable: ' + name)
        if spec['kind']=='external' and (matches[0]['material']!=spec['mat'] or
                abs(matches[0]['width_m']-2*spec['half'])>1e-8):
            raise ValueError('External cross section is immutable: '+name)
    for key, value in document['parameters'].items():
        if key not in DEFAULTS or not .05 <= float(value) <= 10.:
            raise ValueError('Invalid cross-section parameter: ' + key)


def source_document(regions, M, table):
    """Seed once from dated input; future rebuilds consume a full source snapshot."""
    from . import survey as SV
    from .v15_corridor import ZONE
    from .gate_inventory import RECORDS
    from .v8_gates import configuration, threshold_polygon
    source_hash = hashlib.sha256((ROOT/'src/utilities/data/osm_campus.json').read_bytes()).hexdigest()
    if OVERRIDES.exists():
        document = json.loads(OVERRIDES.read_text(encoding='utf-8'))
        if document['dated_osm_sha256'] != source_hash:
            raise ValueError('Source snapshot belongs to a different dated survey')
        _validate(document, table)
        preserved=clean(union_all([area(r) for r in document['sources'] if r['role']=='external_baseline']))
        expected=clean(regions.get(M['asphalt'].name,Polygon()))
        if preserved.symmetric_difference(expected).area>1e-4:
            raise ValueError('External baseline envelope changed or source boundary deleted')
        preserved_kerb=clean(union_all([area(r) for r in document['sources'] if r['role']=='external_curb']))
        expected_kerb=clean(regions.get(M['curb'].name,Polygon()).intersection(expected.buffer(.5)))
        if preserved_kerb.symmetric_difference(expected_kerb).area>1e-4:
            raise ValueError('External baseline kerb changed or source boundary deleted')
        return document
    rows = []
    for name, spec in table.items():
        rows.append({'id': name, 'role': 'vehicle', 'geometry': 'line',
                     'kind': spec['kind'], 'material': spec['mat'], 'points': _points(spec),
                     'width_m': 17. if spec.get('parking') else 2*(spec['half'] or 3.5),
                     'width_profile': 'v15_photo_flared_approach' if spec['half'] is None else 'constant',
                     'sidewalk_m': 0. if spec['kind'] in ('approach','external') else DEFAULTS['sidewalk_width_m'],
                     'evidence': 'dated OSM / site alignment; width ESTIMATED',
                     'immutable_external': spec['kind'] == 'external'})
    for way in SV.campus_footways():
        if len(way['pts']) < 2:
            continue
        rows.append({'id': 'Footway_'+str(way['id']), 'role': 'pedestrian', 'geometry': 'line',
                     'kind': 'mapped_footway', 'material': 'paving_light',
                     'points': way['pts'], 'width_m': DEFAULTS['footway_width_m'],
                     'evidence': 'dated OSM; 2.5 m width ESTIMATED'})
    for i, pts in enumerate([[(0.,-117.88),(0.,-155.)], [(-16.3,100.),(-31.,60.)],
                              [(16.3,100.),(36.,60.)]]):
        rows.append({'id': f'Pedestrian_Link_{i+1}', 'role': 'pedestrian', 'geometry': 'line',
                     'kind': 'estimated_connector', 'material': 'paving', 'points': pts,
                     'width_m': 3., 'evidence': 'functional internal link ESTIMATED, inherited baseline topology'})
    # Retain wide plazas/aprons as explicit boundary sources. Thin legacy strips
    # are retired: complete sidewalk/footway cross sections replace them.
    pilot = box(-26., 90., 26., SV.GATE_Y + 52.)
    for key in ('paving','paving_light','plaza_grey','plaza_light','plaza_inlay','garden_paver'):
        g = regions.get(M[key].name, Polygon())
        retained = g.intersection(pilot).union(opening(g.difference(pilot), 1.8)) if key in ('paving','paving_light') else g
        rows += _area_sources('Paved_Area_'+key, 'pedestrian_area', key, retained)
    # Photo-backed approach kerbs and median/bed cross sections are retained as
    # editable boundary sources. No other legacy road/kerb ribbon is reused.
    rows += _area_sources('Photo_Approach_Kerb', 'photo_kerb', 'curb', regions.get(M['curb'].name,Polygon()).intersection(pilot))
    for key in ('groundcover','grass','planted_soil','soil'):
        rows += _area_sources('Photo_Approach_Landscape_'+key, 'photo_landscape', key,
                              regions.get(M[key].name,Polygon()).intersection(pilot))
    rows += _area_sources('External_Asphalt', 'external_baseline', 'asphalt', regions.get(M['asphalt'].name,Polygon()))
    rows += _area_sources('External_Kerb', 'external_curb', 'curb',
                          regions.get(M['curb'].name,Polygon()).intersection(regions.get(M['asphalt'].name,Polygon()).buffer(.5)))
    from .site import roads
    internal = union_all([LineString(_points(s)) for s in table.values() if s['kind'] == 'campus'])
    plot = Polygon(SV.PLOT)
    for gate in RECORDS[1:]:
        p = Point(gate['model_position_blender_m'])
        inward=gate['inward']
        anchor=Point(p.x+inward[0]*6.,p.y+inward[1]*6.)
        q = nearest_points(anchor, internal.intersection(plot.buffer(-.3)))[1]
        rows.append({'id': 'Gate_Internal_'+gate['id'], 'role': 'vehicle', 'geometry': 'line',
                     'kind': 'gate_internal', 'material': 'paver_road',
                     'points': [list(p.coords)[0], list(anchor.coords)[0], list(q.coords)[0]], 'width_m': 5.2,
                     'sidewalk_m': 2.5, 'gate_id': gate['id'],
                     'evidence': 'owner six-gate topology; short INTERNAL connector ESTIMATED; no exterior extension'})
        rows += _area_sources('Gate_Threshold_'+gate['id'], 'vehicle_area', 'paver_road',
                              threshold_polygon(gate, configuration(gate)))
    # Explicit G1 lane planes retain the photo-backed flared carriageway through
    # the gate; their geometry is editable and no late repair appends polygons.
    lo, hi = SV.LANE_HALF
    rows += _area_sources('G1_Lane_Planes', 'vehicle_area', 'paver_road',
                          union_all([box(-hi,SV.GATE_Y-6.,-lo,SV.GATEHOUSE['y0']+3.2),
                                     box(lo,SV.GATE_Y-6.,hi,SV.GATEHOUSE['y0']+3.2)]))
    document = {'schema': SCHEMA, 'dated_osm_sha256': source_hash,
                'evidence_status': 'DATED MAP / historical photos; widths and corner radii ESTIMATED, no current imagery claim',
                'parameters': dict(DEFAULTS), 'sources': rows}
    _validate(document, table)
    return document


def half_width(row, y):
    if row.get('width_profile') != 'v15_photo_flared_approach':
        return row['width_m']/2
    from .site import approach_half_w, _smoothstep
    from . import survey as SV
    if y >= SV.GATE_Y+16.:
        width=2.45 + (3.5-2.45)*_smoothstep((y-(SV.GATE_Y+16.))/15.)
    else:width=approach_half_w(y) if y > 100. else 3.5
    return width*row['width_m']/7.


def envelope(row):
    line = LineString(row['points'])
    if row.get('width_profile') != 'v15_photo_flared_approach':
        return clean(line.buffer(row['width_m']/2, cap_style='round', join_style='round', quad_segs=12))
    # Explicit variable-width cross section using the same V15 photographic
    # width profile, with shared station normals and unioned segment quads.
    pts = row['points']; left=[]; right=[]
    for i,(x,y) in enumerate(pts):
        a,b=pts[max(0,i-1)],pts[min(len(pts)-1,i+1)]
        length=math.dist(a,b); nx,ny=(-(b[1]-a[1])/length,(b[0]-a[0])/length)
        h=half_width(row,y)
        left.append((x+nx*h,y+ny*h));right.append((x-nx*h,y-ny*h))
    return clean(union_all([Polygon([left[i],right[i],right[i+1],left[i+1]]) for i in range(len(pts)-1)]))


def native_sources(document):
    from .geometry import get_collection
    from .ground_system import datum
    coll=get_collection(COLLECTION)
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj,do_unlink=True)
    coll.hide_render=True
    coll['zc_schema']=SCHEMA
    coll['zc_document_metadata']=json.dumps({k:v for k,v in document.items() if k!='sources'})
    for key,value in document['parameters'].items():coll[key]=float(value)
    for source_order,row in enumerate(document['sources']):
        curve=bpy.data.curves.new('SOURCE_'+row['id'],'CURVE');curve.dimensions='3D'
        arrays=row.get('rings',[row.get('points',[])])
        for pts in arrays:
            cyclic=row['geometry']=='area'
            coords=pts[:-1] if cyclic and pts[0]==pts[-1] else pts
            spline=curve.splines.new('POLY');spline.points.add(len(coords)-1)
            for p,(x,y) in zip(spline.points,coords):
                p.co=(x,y,datum(x,y)+(.21 if row['role'].startswith('pedestrian') else .06),1.)
            spline.use_cyclic_u=cyclic
        obj=bpy.data.objects.new(curve.name,curve);coll.objects.link(obj)
        obj['zc_source_id']=row['id']
        obj['zc_source_order']=source_order
        obj['zc_source_metadata']=json.dumps({k:v for k,v in row.items() if k not in ('points','rings')})
        obj['zc_original_geometry']=json.dumps({k:row[k] for k in ('points','rings') if k in row})
        native=[]
        for spline in curve.splines:
            xy=[[float(p.co.x),float(p.co.y)] for p in spline.points]
            if row['geometry']=='area':xy.append(xy[0])
            native.append(xy)
        obj['zc_native_signature']=json.dumps(native,separators=(',',':'))
        if row.get('immutable_external') or row['role'].startswith('external_'):
            # Blender curve coordinates use float32. Preserve the exact dated
            # baseline through export while rejecting actual external edits.
            obj['zc_immutable_source']=json.dumps(row)
        obj['zc_width_m']=float(row.get('width_m',0.))
        obj['zc_sidewalk_m']=float(row.get('sidewalk_m',0.))
        obj['zc_evidence']=row.get('evidence','DATED SOURCE / estimated dimensions')
    for layer in bpy.context.scene.view_layers:
        child=layer.layer_collection.children.get(coll.name)
        if child:child.exclude=True


def sample_audit(document, vehicle, walk, curb):
    """Independent interpolated stations, not just original mapped vertices.

    Every segment gets centre and both edge checks at 20/50/80%; endpoints
    and junction approach start/end stations are separate rows. Edge probes
    are inset 8 cm to avoid classifying a shared mathematical boundary twice.
    """
    records=[]; failures=[]; junctions=[]
    sources=[r for r in document['sources'] if r['geometry']=='line']
    lines={r['id']:LineString(r['points']) for r in sources}
    target={'vehicle':vehicle,'pedestrian':walk.union(vehicle)}
    for row in sources:
        if row['role'] not in target or row.get('immutable_external'):
            continue
        surface=target[row['role']];points=row['points'];line=lines[row['id']]
        for i,(a,b) in enumerate(zip(points[:-1],points[1:])):
            length=math.dist(a,b)
            if length<1e-6:continue
            nx,ny=-(b[1]-a[1])/length,(b[0]-a[0])/length
            for t in (.2,.5,.8):
                x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
                h=max(.1,half_width(row,y)-.08)
                checks={label:surface.distance(Point(x+nx*d,y+ny*d))<=.10
                        for label,d in [('center',0.),('left_edge',h),('right_edge',-h)]}
                data={'source':row['id'],'segment':i,'t':t,'xy':[x,y],**checks}
                records.append(data)
                if not all(checks.values()):failures.append(data)
        for tag,s in [('start',0.),('end',line.length)]:
            p=line.interpolate(s)
            other=[n for n,l in lines.items() if n!=row['id'] and l.distance(p)<half_width(row,p.y)+3.]
            entry={'source':row['id'],'station':tag,'xy':[p.x,p.y],
                   'surface_distance_m':surface.distance(p),'near_sources':other}
            junctions.append(entry)
            if other:
                for delta in (-3.,3.):
                    q=line.interpolate(max(0.,min(line.length,s+delta)))
                    junctions.append({'source':row['id'],'station':tag+('_junction_before' if delta<0 else '_junction_after'),
                                      'xy':[q.x,q.y],'surface_distance_m':surface.distance(q)})
    def junction_points(g):
        if g.is_empty:return
        if g.geom_type=='Point':yield g
        elif g.geom_type=='LineString':
            yield Point(g.coords[0]);yield Point(g.coords[-1])
        elif hasattr(g,'geoms'):
            for part in g.geoms:yield from junction_points(part)
    # Interior intersections are independent of each alignment's end vertices.
    # Sample both sides of each crossing at the estimated junction-envelope
    # distance, including mapped pedestrian crossings of vehicle routes.
    seen=set()
    for i,a in enumerate(sources):
        for b in sources[i+1:]:
            if a['role']!='vehicle' and b['role']!='vehicle':continue
            cross=lines[a['id']].intersection(lines[b['id']])
            for point in junction_points(cross):
                for row,other in ((a,b),(b,a)):
                    if row.get('immutable_external') or row['role'] not in target:continue
                    line=lines[row['id']];station=line.project(point)
                    key=(row['id'],other['id'],round(station,2))
                    if key in seen:continue
                    seen.add(key)
                    distance=max(half_width(row,point.y),half_width(other,point.y))+3.
                    for direction,label in ((-1.,'junction_start'),(1.,'junction_end')):
                        q=line.interpolate(max(0.,min(line.length,station+direction*distance)))
                        junctions.append({'source':row['id'],'other_source':other['id'],'station':label,
                                          'intersection_xy':[point.x,point.y],'xy':[q.x,q.y],
                                          'surface_distance_m':target[row['role']].distance(q)})
    return {'method':'per-segment 20/50/80% interpolation; 8 cm inset side probes; 10 cm tolerance; roads valid crossing surfaces for footways',
            'samples':records,'failures':failures,'junction_start_end':junctions}


def reconstruct(regions,M,C):
    from .site import roads
    from . import survey as SV
    from .gate_inventory import RECORDS
    OUT.mkdir(parents=True,exist_ok=True)
    baseline=OUT/'rollback_old_envelopes.geojson'
    if not baseline.exists():
        baseline.write_text(json.dumps({'type':'FeatureCollection','features':[
            {'type':'Feature','properties':{'material':m,'status':'PRE-V17 SOURCE ENVELOPE / rollback only'},'geometry':mapping(g)}
            for m,g in sorted(regions.items())]},separators=(',',':')),encoding='utf-8')
        (OUT/'source_osm_original.json').write_bytes((ROOT/'src/utilities/data/osm_campus.json').read_bytes())
    table=roads();document=source_document(regions,M,table);p=document['parameters'];rows=document['sources']
    # V18 real G2 diagnosis: the inherited +9m floor target sits immediately
    # beside an internal curb return. Give each gate a bounded INNER walking
    # threshold corridor before deriving curb/paving partitions. This is a
    # source-level crossing, not an overlay, and never extends outside a gate.
    for gate in RECORDS[1:]:
        ident='Gate_Inner_Walk_'+gate['id']
        if any(r['id']==ident for r in rows):continue
        x,y=gate['model_position_blender_m'];dx,dy=gate['inward']
        rows.append({'id':ident,'role':'pedestrian','geometry':'line',
                     'kind':'estimated_connector','material':'paving',
                     'points':[[x+dx*3.,y+dy*3.],[x+dx*14.,y+dy*14.]],
                     'width_m':3.2,'evidence':'Functional gate access on campus side only; dimensions ESTIMATED; G2 external gap unchanged'})

    (OUT/'transport_sources.json').write_text(json.dumps(document,indent=1),encoding='utf-8')
    vehicle_rows=[r for r in rows if r['role']=='vehicle' and r['kind']!='external']
    ext=clean(union_all([area(r) for r in rows if r['role']=='external_baseline']))
    basic=clean(union_all([envelope(r) for r in vehicle_rows]+[area(r) for r in rows if r['role']=='vehicle_area']))
    # One union first, one return operation second: no independent overlapping
    # T-junction ribbons or triangular detached kerb islands survive.
    pilot=box(-26.,90.,26.,SV.GATE_Y+52.)
    plot=Polygon(SV.PLOT)
    rounded=close(basic,p['junction_radius_m'])
    # Blunt convex island tips using a bounded 1.2m road-side return, outside
    # the accepted pilot. No surface overlay and no new road connection.
    land=plot.difference(rounded)
    softened=opening(land,1.2)
    tip_fill=land.difference(softened).intersection(basic.buffer(2.0))
    rounded=clean(rounded.union(tip_fill))
    vehicle=clean(rounded.difference(pilot).union(basic.intersection(pilot)))
    # Morphological returns cannot creep outward from an internal endpoint into
    # unverified exterior land; only dated basic envelopes may exist there.
    vehicle=clean(vehicle.intersection(plot).union(basic.difference(plot)))
    all_road=clean(vehicle.union(ext))
    sidewalks=[];sidewalk_support=[]
    for row in vehicle_rows:
        width=float(row.get('sidewalk_m',0.))
        if width<=0:continue
        e=envelope(row)
        sidewalks.append(e.buffer(p['curb_width_m']+width,quad_segs=12).difference(e.buffer(p['curb_width_m'],quad_segs=12)))
        sidewalk_support.append(e.buffer(p['curb_width_m']+width,quad_segs=12))
    paths=[envelope(r) for r in rows if r['role']=='pedestrian' and r['geometry']=='line']
    areas=[area(r) for r in rows if r['role']=='pedestrian_area']
    # Join sidewalks at the *unioned* intersection outline, rather than terminate
    # strips early. Full crossing paths remain flush carriageway passages.
    sidewalk_union=vehicle.buffer(p['curb_width_m']+p['sidewalk_width_m'],quad_segs=12).difference(vehicle.buffer(p['curb_width_m'],quad_segs=12)).intersection(union_all(sidewalk_support)).difference(pilot).intersection(plot)
    walk_raw=clean(union_all(sidewalks+paths+areas+[sidewalk_union]))
    connections=[]
    for row in [r for r in rows if r['role']=='pedestrian' and r['geometry']=='line']:
        own=envelope(row).buffer(.05)
        others=clean(walk_raw.difference(own).union(all_road))
        for end in (row['points'][0],row['points'][-1]):
            pt=Point(end);d=pt.distance(others)
            if .2<d<=8.:
                q=nearest_points(pt,others)[1]
                link=LineString([pt,q]).buffer(row['width_m']/2,quad_segs=12)
                connections.append(link)
    joined=close(union_all([walk_raw]+connections),p['walk_merge_radius_m'])
    # Opening rounds convex pedestrian noses. Retain source path envelopes so
    # narrow functional links do not disappear during corner treatment.
    walk=clean(opening(joined,p['walk_corner_radius_m']).union(union_all(paths)))
    buildings=clean(union_all([Polygon(v['pts']) for v in SV.OSM['buildings'].values()]))
    # Preserve academic public route/apron; final building clipping remains in
    # ground_system, which knows the fully generated architectural footprint.
    walk=clean(walk.difference(all_road))
    crossing=clean(union_all(paths+[area(r) for r in rows if r['id'].startswith('Gate_Threshold_')]))
    photo_curb=clean(union_all([area(r) for r in rows if r['role']=='photo_kerb']))
    external_curb=clean(union_all([area(r) for r in rows if r['role']=='external_curb']))
    curb=clean(vehicle.buffer(p['curb_width_m'],quad_segs=12).difference(vehicle).difference(pilot).intersection(plot))
    curb=clean(curb.union(photo_curb).difference(all_road).difference(crossing).union(external_curb.difference(all_road)))
    walk=clean(walk.difference(curb))
    # All paving classes now come from the source model. Region class assignment
    # happens after the complete connected shape is made and is disjoint.
    paving_keys=('paving','paving_light','plaza_grey','plaza_light','plaza_inlay','garden_paver')
    old_areas={m:g.area for m,g in regions.items()}
    for key in paving_keys:regions[M[key].name]=Polygon()
    assigned=Polygon()
    for key in ('plaza_inlay','plaza_grey','plaza_light','garden_paver'):
        g=clean(union_all([area(r) for r in rows if r['role']=='pedestrian_area' and r['material']==key]).intersection(walk).difference(assigned))
        regions[M[key].name]=g;assigned=assigned.union(g)
    regions[M['paving'].name]=clean(walk.difference(assigned))
    regions[M['paver_road'].name]=clean(vehicle.difference(ext))
    regions[M['asphalt'].name]=ext
    regions[M['curb'].name]=curb
    for key in ('groundcover','grass','planted_soil','soil'):
        original=regions.get(M[key].name,Polygon())
        photo=clean(union_all([area(r) for r in rows if r['role']=='photo_landscape' and r['material']==key]))
        regions[M[key].name]=clean(original.difference(pilot).union(photo))
    # Retire obsolete flush restraints: the new shared boundary provides them.
    regions[M['edge'].name]=Polygon()
    native_sources(document)
    audit=sample_audit(document,all_road,walk,curb)
    (OUT/'alignment_segment_audit.json').write_text(json.dumps(audit,separators=(',',':')),encoding='utf-8')
    gates=[]
    for gate in RECORDS:
        pt=Point(gate['model_position_blender_m']);inward=gate['inward']
        q=Point(pt.x+inward[0]*4.,pt.y+inward[1]*4.)
        if gate['id']=='G1':
            # G1's central gatehouse is intentionally not a road. Both source
            # carriageway centres, rather than the gatehouse, are the probes.
            from .site import LANE_C
            threshold_points=[Point(-LANE_C,pt.y),Point(LANE_C,pt.y)]
            inside_points=[Point(-LANE_C,pt.y-4.),Point(LANE_C,pt.y-4.)]
        else:threshold_points=[pt];inside_points=[q]
        gates.append({'id':gate['id'],'threshold_surface_distance_m':max(all_road.distance(q) for q in threshold_points),
                      'internal_4m_surface_distance_m':max(all_road.distance(q) for q in inside_points),
                      'external':'UNRESOLVED ~25m G2 exterior gap retained' if gate['id']=='G2' else 'no exterior extension',
                      'confidence':'photo/map G1; owner topology + dated map association and estimated dimensions G2-G6'})
    report={'schema':SCHEMA,'source_count':len(rows),'dated_road_count':len(table),
            'evidence':document['evidence_status'],'parameters':p,
            'implementation':'entire internal vehicle/sidewalk/footway/curb network regenerated from editable sources; no V16 collars',
            'areas_m2':{'internal_vehicle':vehicle.difference(ext).area,'external_baseline':ext.area,'pedestrian':walk.area,'curb':curb.area},
            'validity':{n:g.is_valid for n,g in [('vehicle',vehicle),('pedestrian',walk),('curb',curb),('external',ext)]},
            'overlap_m2':{'vehicle_walk':all_road.intersection(walk).area,'vehicle_curb':all_road.intersection(curb).area,'curb_walk':curb.intersection(walk).area},
            'external_baseline_change_m2':ext.symmetric_difference(union_all([area(r) for r in rows if r['role']=='external_baseline'])).area,
            'walk_endpoint_connections':len(connections),'gates':gates,
            'audit_samples':len(audit['samples']),'audit_failures':len(audit['failures']),
            'junction_endpoint_samples':len(audit['junction_start_end']),
            'material_changes':{m:{'before_m2':old_areas.get(m,0.),'after_m2':g.area} for m,g in regions.items() if m in {M[k].name for k in (*paving_keys,'curb','edge','paver_road','asphalt')}},
            'status':'SOURCE AUDIT ONLY; build, mesh audit, engine traversal and visual acceptance are separate'}
    (OUT/'network.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (OUT/'generated_network.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[
        {'type':'Feature','properties':{'surface':n},'geometry':mapping(g)} for n,g in [('vehicle',vehicle.difference(ext)),('pedestrian',walk),('curb',curb),('external',ext)]]},separators=(',',':')),encoding='utf-8')
    STATE.update(document=document,vehicle=all_road,walk=walk,curb=curb,report=report)
    if not all(report['validity'].values()) or max(report['overlap_m2'].values())>1e-5:
        raise RuntimeError('V17 network validity/overlap failed')
    print('[v17 network]',len(table),'dated roads;',len(rows),'editable sources;',len(audit['samples']),'independent segment probes;',len(audit['failures']),'probe failures',flush=True)
    return report


def finalize_partition(partition,M):
    """Audit actual final regions after building/bed clipping and V15 material split."""
    from shapely import union_all
    roads={M[k].name for k in ('asphalt','paver_road','v15_band')}
    paving={M[k].name for k in ('paving','paving_light','plaza_grey','plaza_light','plaza_inlay','garden_paver','edge')}
    road=clean(union_all([g for m,g in partition if m in roads]))
    walk=clean(union_all([g for m,g in partition if m in paving]))
    curb=clean(union_all([g for m,g in partition if m==M['curb'].name]))
    audit=sample_audit(STATE['document'],road,walk,curb)
    (OUT/'final_partition_segment_audit.json').write_text(json.dumps(audit,separators=(',',':')),encoding='utf-8')
    report=STATE['report'];report['final_partition_audit']={'samples':len(audit['samples']),'failures':len(audit['failures']),
        'endpoint_failures':sum(s['surface_distance_m']>.1 for s in audit['junction_start_end']),
        'areas_m2':{'vehicle':road.area,'pedestrian':walk.area,'curb':curb.area}}
    (OUT/'network.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    summary=report['final_partition_audit']
    if summary['failures'] or summary['endpoint_failures']:
        print('[v17 FINAL PARTITION AUDIT] FAIL:',summary['failures'],'segment stations;',
              summary['endpoint_failures'],'junction/end stations; see final_partition_segment_audit.json',flush=True)
    else:
        print('[v17 FINAL PARTITION AUDIT] PASS:',len(audit['samples']),'independent segment probes',flush=True)
