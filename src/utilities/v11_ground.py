"""V11 ground-partition repairs (owner screenshots 03/05/12/15). Geometry-level, reproducible.

1. extend_footways   Footway ribbons that stop in open sand are extended to the nearest hard
                     surface (road/paving) within 12 m, with a 2.5 m paved connector
                     ("randomly terminated sidewalk ribbons", owner 05).
2. close_slivers     Morphological closing of the hard-surface set (paving, curbs, roads and
                     building footprints): bare-terrain slivers narrower than 2*CLOSE_R that
                     are enclosed by hard surfaces become paving ("exposed strips of sand
                     cutting through paved walkways", sand wedges between curbs, sand between
                     an entrance and the pavement; owner 03/12/15). Lawns, planted soil, beds
                     and footprints are never overwritten; the partition stays disjoint.
3. relocate_trees    Trees/palms whose trunk stands on a walk, road or curb are moved to the
                     nearest point >= 1.2 m outside the hard surface (<= 4 m move), otherwise
                     removed ("trees intersecting sidewalks", owner 05).
All results are logged to output/validation/v11/ground_repairs_v11.json.
"""
import json
import math
from pathlib import Path
import bpy
from shapely import union_all
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import nearest_points
from shapely.validation import make_valid

ROOT = Path(__file__).resolve().parents[2]
CLOSE_R = 1.75
LOG = {'footway_connectors': [], 'slivers': {}, 'trees': {'moved': [], 'removed': []}}


def extend_footways(regions, M, hard_names):
    from . import survey as SV
    from shapely.geometry import box
    from shapely.strtree import STRtree
    hard = union_all([g for m, g in regions.items() if m in hard_names])
    parts = [g for g in getattr(hard, 'geoms', [hard]) if not g.is_empty]
    tree = STRtree(parts)
    add = []
    for w in SV.campus_footways():
        pts = w['pts']
        if len(pts) < 2:
            continue
        for end, prev in ((pts[0], pts[1]), (pts[-1], pts[-2])):
            p = Point(end)
            # Local window only (the campus-wide union is far too large to clip per end).
            win = box(p.x - 13., p.y - 13., p.x + 13., p.y + 13.)
            local = union_all([parts[i].intersection(win) for i in tree.query(win)])
            # Already connected: the ribbon end overlaps another hard surface.
            others = local.difference(LineString(pts).buffer(1.3))
            if others.is_empty or others.distance(p) < .6:
                continue
            d = others.distance(p)
            if d > 12.:
                continue
            q = nearest_points(p, others)[1]
            add.append(LineString([p, q]).buffer(1.25, cap_style='round'))
            LOG['footway_connectors'].append({'from': [round(p.x, 2), round(p.y, 2)], 'to': [round(q.x, 2), round(q.y, 2)], 'length_m': round(d, 2)})
    if add:
        name = M['paving'].name
        regions[name] = regions.get(name, Polygon()).union(union_all(add))
    return len(add)


def g1_structures():
    """Plan footprints of the G1 complex masses (portal legs, gatehouse, V11 return walls,
    pedestrian-gate piers, gate buildings, lattice screens) for the sliver closing."""
    from shapely.geometry import box
    from . import survey as SV
    GY = SV.GATE_Y; D = SV.PORTAL['depth']; ga, gb = SV.GATEHOUSE['y0'], SV.GATEHOUSE['y1']
    xo = SV.PORTAL['outer_w'] / 2; xi = xo - SV.PORTAL['leg_w']; l1 = SV.LANE_HALF[1]
    parts = [box(-7., ga, 7., gb)]
    for sx in (-1, 1):
        def B(a, b, y0, y1):
            lo, hi = sorted((sx * a, sx * b)); return box(lo, y0, hi, y1)
        parts += [B(xi, xo, GY - D / 2, GY + D / 2), B(l1 - .05, l1 + .55, GY + D / 2 - .3, SV.GATEHOUSE['y0'] + 2.33),
                  B(16.7, 21.5, GY - .35, GY + .35), B(21.5, 36., GY - 6., GY + 2.), B(36., 53., GY - 6., GY + 8.),
                  B(53., 62., GY + 2., GY + 2.8)]
    return union_all(parts)


def g1_lane_paving(regions, M):
    """QA defect 6: bare ground inside the G1 lanes. Both vehicle lanes are paved from the
    inner apron through the portal to the lane-gate plane (|x| 7.0..11.9)."""
    from shapely.geometry import box
    from . import survey as SV
    GY = SV.GATE_Y; l0, l1 = SV.LANE_HALF
    lanes = union_all([box(-l1, GY - 6., -l0, SV.GATEHOUSE['y0'] + 3.2), box(l0, GY - 6., l1, SV.GATEHOUSE['y0'] + 3.2)])
    name = M['paver_road'].name
    regions[name] = regions.get(name, Polygon()).union(lanes)
    LOG['g1_lane_paving_m2'] = round(lanes.area, 2)


def close_slivers(partition, occupied, bed, footprints, M, hard_names):
    """Return (partition, occupied) with enclosed terrain slivers turned into paving."""
    footprints = footprints.union(g1_structures())
    hard = union_all([g for m, g in partition if m in hard_names] + [footprints])
    closed = hard.buffer(CLOSE_R, join_style='round').buffer(-CLOSE_R, join_style='round')
    fill = make_valid(closed.difference(occupied).difference(bed).difference(footprints))
    pieces = [g for g in getattr(fill, 'geoms', [fill]) if g.geom_type == 'Polygon' and g.area > .05]
    if not pieces:
        return partition, occupied
    fill = union_all(pieces)
    name = M['paving'].name
    for i, (m, g) in enumerate(partition):
        if m == name:
            partition[i] = (m, make_valid(g.union(fill)))
            break
    else:
        partition.append((name, fill))
    LOG['slivers'] = {'closing_radius_m': CLOSE_R, 'pieces': len(pieces), 'area_m2': round(fill.area, 2),
                      'largest': sorted([{'area_m2': round(p.area, 2), 'centroid': [round(p.centroid.x, 1), round(p.centroid.y, 1)]}
                                         for p in pieces], key=lambda d: -d['area_m2'])[:40]}
    return partition, occupied.union(fill)


def g1_shoulders(partition, occupied, bed, footprints, M):
    """Paved shoulders of the existing flared G1 lanes, never a new road.

    The lane mesh narrows at the portal while the approach/forecourt stays
    wider. Complete that apron through the widening and exterior bend; keep
    every existing carriageway, curb, building and raised planting bed.
    """
    from shapely.geometry import box
    from .site import roads
    soft = {M[k].name for k in ('groundcover','grass','planted_soil','soil')}
    fixed = union_all([g for m,g in partition if m not in soft] + [bed, footprints])
    apron = union_all([LineString([(p.x,p.y) for p in roads()[n]['pts']]).buffer(3.4, cap_style='flat')
                       for n in ('Approach_Inbound','Approach_Outbound')])
    fill = make_valid(apron.intersection(box(-20,280,20,345)).difference(fixed))
    name = M['paving'].name
    result = []
    for m,g in partition:
        if m in soft:
            g = make_valid(g.difference(fill))
        if m == name:
            g = make_valid(g.union(fill))
        result.append((m,g))
    if not any(m == name for m,_ in result):
        result.append((name,fill))
    LOG['g1_paved_shoulders_m2'] = round(fill.area,3)
    return result, occupied.union(fill)


def round_curb_tips(curb, road):
    """Round sharp source tips and close their hairline offset cracks.

    Separate top/skirt sampling formerly hid these corners behind T junctions.
    Conforming skirts expose the actual outline, so repair the polygon instead
    of changing sampling to hide it. Keep only complete repair pieces touching
    a sharp vertex; smoothing the entire network creates tiny curved triangles
    and moves otherwise sound boundaries. No carriageway is ever overwritten.
    """
    from .ground_system import polygons
    tips = []
    for poly in polygons(curb):
        for ring in [poly.exterior, *poly.interiors]:
            co = list(ring.coords)[:-1]
            for i, (x, y) in enumerate(co):
                a, b = co[i-1], co[(i+1) % len(co)]
                u, v = (a[0]-x, a[1]-y), (b[0]-x, b[1]-y)
                lu, lv = math.hypot(*u), math.hypot(*v)
                if min(lu, lv) <= .4:
                    continue
                cosine = (u[0]*v[0]+u[1]*v[1])/(lu*lv)
                turn = 180.-math.degrees(math.acos(max(-1., min(1., cosine))))
                if turn > 25.:
                    tips.append(Point(x, y).buffer(.02))
    if not tips:
        return curb
    tip_zone = union_all(tips)
    # 30 mm closing joins offset cracks; 80 mm opening gives real rounded
    # noses without erasing the standard 250-300 mm curb runs. The 2 mm
    # simplification removes near-coincident buffer vertices before meshing.
    # Two chords per quadrant avoid sub-centimetre cap facets and detached
    # native-precision offcuts while staying within 7 mm of the round nose.
    smooth = curb.buffer(.03, quad_segs=2).buffer(-.03, quad_segs=2)
    smooth = smooth.difference(road).buffer(-.08, quad_segs=2).buffer(.08, quad_segs=2)
    smooth = smooth.simplify(.002).difference(road)
    removed = union_all([p for p in polygons(curb.difference(smooth)) if p.intersects(tip_zone)])
    added = union_all([p for p in polygons(smooth.difference(curb)) if p.intersects(tip_zone)])
    LOG['curb_outline_repairs'] = {'sharp_vertices': len(tips),
        'removed_m2': round(removed.area, 6), 'added_m2': round(added.area, 6)}
    return make_valid(curb.difference(removed).union(added))


def repair_curb_runs(partition, M):
    """Close the G1 median noses and remove isolated clipping fragments.

    Work on the disjoint partition so returns can never cover a carriageway.
    Removed curb tips become flush paving, preserving complete coverage.
    """
    from shapely.geometry import box
    from .ground_system import polygons
    cn, gn, pn = (M[k].name for k in ('curb','groundcover','paving'))
    regions = dict(partition)
    original = regions.get(cn,Polygon())
    # The north median terminates at the gatehouse; retain that threshold.
    # Rebuild the free nose on the south side of the perimeter-loop crossing.
    window = box(-7,280,7,301.2)
    body = make_valid(union_all([original,regions.get(gn,Polygon())]).intersection(window))
    # An inward ring makes an actual closed nose at the loop cut, rather than
    # two independently clipped side ribbons. Leave the south clipping seam
    # open so it joins the unchanged median below y=280.
    noses = []
    for p in polygons(body):
        if p.area < 3:
            continue
        # A 20 mm inset avoids near-coincident intersections with the old
        # ribbon outline. Intersecting a rounded copy back into that outline
        # generated hundreds of sub-millimetre curb and paving needles.
        rounded = p.buffer(-.37,quad_segs=6).buffer(.35,quad_segs=6)
        noses.append(rounded.difference(rounded.buffer(-.3,quad_segs=6)))
    ring = make_valid(union_all(noses).simplify(.005).difference(box(-7,279,7,281)))
    tie_in = original.intersection(box(-7,280,7,282))
    curb = make_valid(union_all([original.difference(window),ring,tie_in]))
    # Pointed offcuts at the two gate-loop returns and academic junction.
    zones = union_all([box(-14,293,-10,311),box(10,293,14,311),box(18,-121,44,-110)])
    local = curb.intersection(zones)
    rounded = local.buffer(-.14,quad_segs=6).buffer(.12,quad_segs=6).simplify(.003)
    # Do not introduce a cut at the boundary of a repair window.
    inner = zones.buffer(-.35)
    curb = make_valid(curb.difference(inner).union(rounded.intersection(inner)))
    road = union_all([regions.get(M[k].name, Polygon()) for k in ('asphalt', 'paver_road')])
    curb = round_curb_tips(curb, road)
    stubs = [p for p in polygons(curb) if p.area < 1.]
    curb = make_valid(curb.difference(union_all(stubs)))
    removed = make_valid(original.difference(curb))
    added = make_valid(curb.difference(original))
    result = []
    for m,g in partition:
        if m == cn:
            g = curb
        elif m == pn:
            g = make_valid(g.union(removed).difference(added))
        else:
            g = make_valid(g.difference(added))
        result.append((m,g))
    if not any(m == pn for m,_ in result):
        result.append((pn,removed))
    LOG['curb_repairs'] = {'stubs_removed':len(stubs),'stub_area_m2':round(sum(p.area for p in stubs),3),
                           'nose_area_m2':round(ring.area,3),'curb_to_paving_m2':round(removed.area,3)}
    return result


def relocate_trees(walk_hard):
    """walk_hard: union of walks, plazas, roads and curbs (Polygon/MultiPolygon)."""
    from shapely.prepared import prep
    # make_valid may return a GeometryCollection (lines/points mixed in): keep polygons only.
    polys = []
    for g in getattr(walk_hard, 'geoms', [walk_hard]):
        if g.geom_type == 'Polygon':
            polys.append(g)
        elif g.geom_type == 'MultiPolygon':
            polys.extend(g.geoms)
    walk_hard = union_all(polys)
    ph = prep(walk_hard)
    boundary = None
    for o in list(bpy.data.objects):
        if o.type != 'MESH' or not o.name.startswith(('Tree_', 'Palm_', 'Fan_')):
            continue
        p = Point(o.location.x, o.location.y)
        if not ph.contains(p):
            continue
        if boundary is None:
            boundary = walk_hard.boundary
        q = nearest_points(p, boundary)[1]
        dx, dy = q.x - p.x, q.y - p.y
        L = math.hypot(dx, dy) or 1.
        tgt = Point(q.x + dx / L * 1.2, q.y + dy / L * 1.2)
        if p.distance(tgt) <= 4.0 and not ph.contains(tgt):
            LOG['trees']['moved'].append({'name': o.name, 'from': [round(p.x, 2), round(p.y, 2)], 'to': [round(tgt.x, 2), round(tgt.y, 2)]})
            o.location.x, o.location.y = tgt.x, tgt.y
        else:
            LOG['trees']['removed'].append({'name': o.name, 'at': [round(p.x, 2), round(p.y, 2)]})
            bpy.data.objects.remove(o, do_unlink=True)


def write_log():
    out = ROOT / 'output/validation/v11'
    out.mkdir(parents=True, exist_ok=True)
    LOG['summary'] = {'footway_connectors': len(LOG['footway_connectors']), 'sliver_area_m2': LOG['slivers'].get('area_m2', 0),
                      'trees_moved': len(LOG['trees']['moved']), 'trees_removed': len(LOG['trees']['removed'])}
    (out / 'ground_repairs_v11.json').write_text(json.dumps(LOG, indent=2))
    print('[ground-v11]', json.dumps(LOG['summary']), flush=True)
