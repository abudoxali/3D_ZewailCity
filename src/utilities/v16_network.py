"""Rebuild source road envelopes and junction boundaries before final meshing.

All alignments come from site.road_table / dated OSM. Widths remain estimates.
No external road is extended. Existing curb area is protected from road fill.
Native source curves are kept in an excluded collection for future editing.
"""
import json
from pathlib import Path
import bpy
from shapely import make_valid, union_all
from shapely.geometry import Point, LineString, Polygon, box

ROOT = Path(__file__).resolve().parents[2]


def reconstruct(regions, M, C):
    from .site import roads, junction_zones
    from .geometry import get_collection
    table = roads()
    coll = get_collection('V16_Editable_Road_Alignments')
    coll.hide_render = True
    coll['zc_source'] = 'Dated OSM + validated site alignment; widths ESTIMATED; no new external connection'
    from .gate_inventory import RECORDS
    gates=union_all([Point(*g['model_position_blender_m']).buffer(18) for g in RECORDS])
    from .v15_corridor import ZONE
    protected_road=ZONE.buffer(12.).union(gates)
    raw_curb = regions.get(M['curb'].name, Polygon())
    report = {'alignments':[], 'road_changes':{}, 'g2_external_gap':'UNRESOLVED / no extension'}
    envelopes = {}
    for name, spec in table.items():
        pts = [(p.x,p.y) for p in spec['pts']]
        line = LineString(pts)
        # Retain explicit editable centreline data, including approach variable width.
        curve = bpy.data.curves.new('ALIGN_'+name,'CURVE')
        curve.dimensions='3D'
        spline=curve.splines.new('POLY');spline.points.add(len(pts)-1)
        for p,(x,y) in zip(spline.points,pts):p.co=(x,y,.065,1.)
        obj=bpy.data.objects.new('ALIGN_'+name,curve);coll.objects.link(obj)
        obj['zc_classification']=spec['kind'];obj['zc_material']=spec['mat']
        obj['zc_width_m']=2*spec['half'] if spec['half'] else -1.
        obj['zc_width_evidence']='ESTIMATED; approach variable width in site.approach_half_w'
        report['alignments'].append({'name':name,'kind':spec['kind'],'length_m':line.length,
                                     'width_m':obj['zc_width_m'],'points':pts})
        if spec['half'] is None:
            continue  # photo-supported flared lane polygon is retained exactly
        half = 8.5 if spec.get('parking') else spec['half']
        geom=line.buffer(half,cap_style='flat',join_style='round',quad_segs=6)
        envelopes.setdefault(M[spec['mat']].name,[]).append(geom)
    # True unioned road boundaries replace the ribbon mitres. The dated envelopes
    # only influence a 0.60 m collar of the captured road, and never eat a curb.
    for mat, polys in envelopes.items():
        old=regions.get(mat,Polygon())
        desired=make_valid(union_all(polys))
        influence=desired.buffer(.6)
        replacement=old.difference(influence).union(desired.intersection(old.buffer(.6)))
        replacement=make_valid(replacement.difference(raw_curb.difference(old)))
        # Reconstruct outside the photo-validated G1 corridor. Freeze its full
        # source envelope (including V15 median collars) plus a 12 m join guard;
        # otherwise mapped duplicate ways can consume the later median kerb.
        replacement=make_valid(replacement.difference(protected_road).union(old.intersection(protected_road)))
        regions[mat]=replacement
        report['road_changes'][mat]={'before_m2':old.area,'after_m2':replacement.area,
                                    'removed_m2':old.difference(replacement).area,
                                    'curb_to_road_m2':replacement.difference(old).intersection(raw_curb).area}
    report['internal_blind_caps']=round_internal_caps(regions,M,table,gates)
    report['junction_island_rounding']=round_islands(regions,M,table,gates)
    # Cap returns explicitly replace their old straight kerb ends. The moved
    # curb is a protected source for the subsequent shared-boundary operation.
    raw_curb=regions.get(M['curb'].name,Polygon())
    road=union_all([regions.get(M[k].name,Polygon()) for k in ('asphalt','paver_road')])
    # A coherent return around the complete union, rather than each crossing
    # ribbon. Keep measured G1 pilot beds/kerbs and all gate thresholds untouched.
    from .v15_corridor import ZONE
    from .gate_inventory import RECORDS
    gates=union_all([Point(*g['model_position_blender_m']).buffer(18) for g in RECORDS])
    safe=ZONE.union(gates)
    junctions=union_all([Point(x,y).buffer(r+3.) for x,y,r in junction_zones(table)])
    edit=junctions.difference(safe)
    ideal=road.buffer(.30,quad_segs=6,join_style='round').difference(road)
    # Rebuild only where a source kerb exists within 1.0 m: do not invent road-edge
    # obstructions across a mapped pedestrian route or an unkerbed threshold.
    new=ideal.intersection(raw_curb.buffer(1.)).intersection(edit)
    outside=raw_curb.difference(edit)
    regions[M['curb'].name]=make_valid(outside.union(new))
    retired=raw_curb.intersection(edit).difference(new).difference(road)
    # Former arbitrary interior kerb fragments become walkable paving at the
    # graded sidewalk datum. Surface classes remain disjoint at partition time.
    pave=M['paving'].name
    regions[pave]=make_valid(regions.get(pave,Polygon()).union(retired))
    report['junction_reconstruction']={'zone_m2':edit.area,'retired_interior_kerb_m2':retired.area,
                                      'continuous_returns_m2':new.area}
    # Rebuild the complete pedestrian union, including the light apron/footway
    # class. Editing only M_Paving_Limestone left the separate light strips and
    # their pointed junction noses untouched in the first visual comparison.
    report['ring_sidewalk_replacement']=rebuild_pedestrians(
        regions,M,table,road,raw_curb,safe)
    for way in report['ring_sidewalk_replacement']['source_footways']:
        curve=bpy.data.curves.new('ALIGN_Footway_'+str(way['id']),'CURVE')
        curve.dimensions='3D'
        spline=curve.splines.new('POLY');spline.points.add(len(way['points'])-1)
        for p,(x,y) in zip(spline.points,way['points']):p.co=(x,y,.21,1.)
        obj=bpy.data.objects.new(curve.name,curve);coll.objects.link(obj)
        obj['zc_classification']='mapped pedestrian / dated OSM'
        obj['zc_width_m']=way['width_m']
    # Close hairline cracks in the existing pedestrian network without moving
    # surveyed road boundaries or using shader coverage to hide mesh gaps.
    walk=regions.get(pave,Polygon())
    healed=walk.buffer(.12,join_style='round').buffer(-.12,join_style='round')
    fill=healed.difference(walk).difference(road.union(regions[M['curb'].name])).difference(safe)
    regions[pave]=make_valid(walk.union(fill))
    report['pedestrian_seam_fill_m2']=fill.area
    # Native alignment curves are source only, excluded from render and export.
    for layer in bpy.context.scene.view_layers:
        node=layer.layer_collection.children.get(coll.name)
        if node:node.exclude=True
    dest=ROOT/'output/build_metadata/v16/network.json';dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=1))
    assert all(v['curb_to_road_m2']<1e-5 for v in report['road_changes'].values())
    print('[v16 network]',len(table),'editable alignments;',round(retired.area,2),'m2 interior kerbs retired',flush=True)


def round_internal_caps(regions,M,table,gates):
    """Inset semicircular caps for isolated mapped internal blind road ends.

    Never extends an endpoint or touches an external road, parking aisle, a
    connected road end, a building apron, G1 pilot or a gate approach. The ring
    corridor bounds this change to the owner-reported junction context. Kerb
    moves are recorded rather than presented as unchanged classifications.
    """
    from . import survey as SV
    from .v15_corridor import ZONE
    lines={n:LineString([(p.x,p.y) for p in s['pts']]) for n,s in table.items()}
    ring=lines['Campus_Ring']
    buildings=union_all([Polygon(v['pts']).buffer(8.) for v in SV.OSM['buildings'].values()])
    protected=ZONE.union(gates.buffer(12.)).union(buildings)
    curb_name=M['curb'].name
    result=[]
    for name,spec in table.items():
        line=lines[name]
        if spec['kind']!='campus' or spec.get('parking') or spec['half'] is None or line.is_ring:
            continue
        half=spec['half']
        for end in (0,-1):
            point=Point(line.coords[end])
            if ring.distance(point)>16. or protected.intersects(point):
                continue
            # A centreline ending inside another road's width is connected even
            # when the dated map did not share an exact vertex there.
            connected=any(other.distance(point)<=half+(table[n]['half'] or 3.5)+1.
                          for n,other in lines.items() if n!=name)
            if connected:
                continue
            inward=line.interpolate(1. if end==0 else max(0.,line.length-1.))
            dx,dy=inward.x-point.x,inward.y-point.y
            length=(dx*dx+dy*dy)**.5
            if length<1e-6:
                continue
            dx,dy=dx/length,dy/length
            # Keep the mapped endpoint inside the vehicle surface (8 cm guard
            # exceeds the 2 cm ray-grid offsets). The rounded return remains
            # clipped strictly to the original road+kerb footprint.
            depth=half-.08
            cx,cy=point.x+dx*depth,point.y+dy*depth
            nx,ny=-dy*(half+.35),dx*(half+.35)
            window=Polygon([(point.x+nx,point.y+ny),(point.x-nx,point.y-ny),
                            (cx-nx,cy-ny),(cx+nx,cy+ny)])
            if protected.intersects(window):
                continue
            mat=M[spec['mat']].name
            old=regions.get(mat,Polygon())
            curb=regions.get(curb_name,Polygon())
            hard=old.union(curb)
            cap=Point(cx,cy).buffer(half,quad_segs=16)
            new_curb=Point(cx,cy).buffer(half+.30,quad_segs=16).difference(cap).intersection(window).intersection(hard)
            removed=old.intersection(window).difference(cap)
            regions[mat]=make_valid(old.difference(removed))
            retired=curb.intersection(window)
            regions[curb_name]=make_valid(curb.difference(window).union(new_curb))
            assert new_curb.difference(hard).area<1e-5
            result.append({'road':name,'endpoint_index':end,'endpoint':list(point.coords)[0],
                           'status':'ESTIMATED inset cap; original mapped endpoint retained as limit',
                           'radius_m':half,'road_removed_m2':removed.area,
                           'old_curb_retired_m2':retired.area,'new_curb_return_m2':new_curb.area,
                           'outside_original_hard_m2':new_curb.difference(hard).area})
    return result


def round_islands(regions,M,table,gates):
    """Bounded, estimated real kerb relocation at acute junction-island noses.

    This is an intentional geometry correction, not a blanket relabelling of
    kerbs as carriageway. The exact old/new masks are retained for independent
    classification and player checks. No vehicle centreline moves.
    """
    from . import survey as SV
    from .v15_corridor import ZONE
    from .ground_system import polygons
    ring=LineString([(p.x,p.y) for p in table['Campus_Ring']['pts']])
    protected=ZONE.buffer(12).union(gates.buffer(12)).union(union_all([
        Polygon(v['pts']).buffer(6) for v in SV.OSM['buildings'].values()]))
    road_names={M[k].name for k in ('paver_road','asphalt')}
    road=union_all([regions.get(n,Polygon()) for n in road_names])
    mapped=union_all([LineString(w['pts']).buffer(1.25,cap_style='flat')
                      for w in SV.campus_footways()])
    rows=[]
    for poly in polygons(road):
        for ring_coords in poly.interiors:
            old=Polygon(ring_coords)
            if not 10 < old.area < 1800 or old.distance(ring)>16 or old.intersects(protected):
                continue
            new=make_valid(old.buffer(-2.5,quad_segs=12).buffer(2.5,quad_segs=12).intersection(old))
            if new.is_empty or new.geom_type!='Polygon':continue
            removed=make_valid(old.difference(new))
            if not .1 < removed.area <= min(25.,old.area*.10):continue
            # Retain the full mapped 2.5 m corridor through the usable interior.
            # The 3 m old-edge collar is an expected crossing/entry termination.
            core_walk=mapped.intersection(old.buffer(-3.))
            if core_walk.difference(new.buffer(-.3)).area>1e-5:continue
            if any(o.type=='MESH' and o.data.name.startswith('ASSET_') and
                   removed.buffer(.4).covers(Point(o.location.x,o.location.y))
                   for o in bpy.data.objects):continue
            old_curb=regions.get(M['curb'].name,Polygon()).intersection(old)
            new_curb=new.difference(new.buffer(-.30,quad_segs=12))
            # Classify the replaced nose from its adjacent original vehicle
            # surface; preserve asphalt vs campus pavers.
            name=max(road_names,key=lambda n:regions.get(n,Polygon()).intersection(old.buffer(.5)).area)
            regions[name]=make_valid(regions.get(name,Polygon()).union(removed))
            regions[M['curb'].name]=make_valid(regions.get(M['curb'].name,Polygon()).difference(old).union(new_curb))
            rows.append({'reason':'owner junction nose correction / ESTIMATED 2.5 m radius',
                         'center':list(old.centroid.coords)[0],'before_m2':old.area,'after_m2':new.area,
                         'nose_to_road_m2':removed.area,'old_curb_m2':old_curb.area,'new_curb_m2':new_curb.area,
                         'intentional_road_fill_wkt':removed.wkt,'new_island_wkt':new.wkt,
                         'mapped_corridor_loss_m2':core_walk.difference(new.buffer(-.3)).area})
    return rows


def rebuild_pedestrians(regions,M,table,road,raw_curb,safe):
    """Replace ring-side ribbons by one bounded, source-derived pedestrian area.

    Existing vehicle surfaces, curb footprints, gate thresholds, the accepted G1
    pilot and building aprons are exclusions. Mapped footway axes and the ring's
    original 2.5 m sidewalks supply the geometry; closing nearby parallel strips
    produces a single wider walk instead of a thin soil slot between two walks.
    Rounding radii and the resulting local width are engineering ESTIMATES.
    """
    from . import survey as SV
    from .geometry import smooth_polyline
    spec=table['Campus_Ring']
    axis=LineString([(p.x,p.y) for p in spec['pts']])
    keys=('paving','paving_light','plaza_grey','plaza_light','plaza_inlay','garden_paver')
    names={M[k].name for k in keys if k in M}
    old={name:regions.get(name,Polygon()) for name in names}
    old_union=make_valid(union_all(list(old.values())))
    # The 16 m corridor captures both the road-edge walk and the mapped parallel
    # footway seen in owner 07/08. Retain a 3 m foundation/entrance apron;
    # the first 6 m guard wrongly retained broken offset strip ends. Both
    # margins are functional estimates; doors and their actual mesh stay intact.
    footprints=union_all([Polygon(v['pts']).buffer(3.,quad_segs=8)
                         for v in SV.OSM['buildings'].values()])
    protected=safe.union(footprints)
    work=axis.buffer(16.,quad_segs=12).difference(
        axis.buffer(spec['half']-.05,quad_segs=12)).difference(protected)
    curb=raw_curb.union(regions.get(M['curb'].name,Polygon()))
    obstacles=road.union(curb)
    half=spec['half']+.30
    ring_walk=axis.buffer(half+spec['sidewalk'],quad_segs=12).difference(
        axis.buffer(half,quad_segs=12))
    paths=[]
    source_axes=[]
    for way in SV.campus_footways():
        pts=smooth_polyline(way['pts'],1)
        if len(pts)<2:
            continue
        line=LineString(pts)
        paths.append(line.buffer(1.25,quad_segs=12,cap_style='round',join_style='round'))
        if line.intersects(work):
            source_axes.append({'id':way['id'],'width_m':2.5,'points':pts})
    mapped=union_all(paths)
    source=make_valid(ring_walk.union(mapped).intersection(work).difference(obstacles))
    # Nearby source walks merge into one coherent paved area. This deliberately
    # retires disconnected, sharp fragments instead of laying a second ribbon
    # over them. Never bridge vehicle roads or consume existing curbs.
    merge_radius=2.0
    joined=source.buffer(merge_radius,quad_segs=12,join_style='round').buffer(
        -merge_radius,quad_segs=12,join_style='round')
    # A 1 m planar corner radius removes triangular noses and short thin strips
    # while retaining the 2.5 m supported walking width and its route alignment.
    rounded=joined.buffer(-1.,quad_segs=12,join_style='round').buffer(
        1.,quad_segs=12,join_style='round')
    seam=old_union.intersection(work.boundary.buffer(.40))
    replacement=make_valid(rounded.union(seam).intersection(work).difference(obstacles))
    per_class={}
    for name,geom in old.items():
        regions[name]=make_valid(geom.difference(work))
        per_class[name]={'retired_m2':geom.intersection(work).area}
    destination=M['paving'].name
    regions[destination]=make_valid(regions.get(destination,Polygon()).union(replacement))
    before=old_union.intersection(work).difference(obstacles)
    removed=before.difference(replacement)
    added=replacement.difference(old_union)
    # Source class safeguards apply to the whole union, not just one material.
    assert replacement.intersection(road).area < 1e-5
    assert replacement.intersection(curb).area < 1e-5
    assert replacement.intersection(protected).area < 1e-5
    return {'source_width_m':spec['sidewalk'],'edit_corridor_m':16.,
            'parallel_walk_merge_radius_m':merge_radius,'corner_radius_m':1.,
            'source_footways':source_axes,'material_classes':per_class,
            'replaced_m2':before.area,'new_m2':replacement.area,
            'old_dead_end_m2':removed.area,'new_connection_m2':added.area,
            'road_to_paving_m2':replacement.intersection(road).area,
            'curb_to_paving_m2':replacement.intersection(curb).area,
            'protected_change_m2':replacement.intersection(protected).area,
            'geometry_valid':replacement.is_valid,
            'status':'SOURCE GEOMETRY ONLY; final engine images and traversal required'}
