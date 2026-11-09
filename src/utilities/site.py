"""Site works for the as-built reconstruction (V4): ground, road network, plazas,
planting and street furniture.

V4 rebuilds the site from the survey in survey.py instead of the 2014 brochure plan:
  * Roads: OSM centrelines (campus service roads mapped 2021, ring road, approach,
    slip roads, the drop-off loop in front of the admin, and the streets around the
    plot). The brochure's octagonal road, its four diagonals and the east-west /
    south axes do not exist on the ground and were removed.
  * Approach and gate: the OSM approach centrelines plus the C02 cross-section and the
    C01/C02 gate lanes.
  * Ground cover and tree density: Sentinel-2 NDVI of 2026-09-16 (10 m pixels). Only the
    gate-side half of the ring and the two approach parcels are irrigated; the south half
    of the ring is bare graded ground. V3's four green grove quadrants are gone.
  * Set pieces seen in photographs: approach median palms and lamps (A04, C02), planted
    strips with young trees and cycads (C02), the wedge lawn and circular bed (A01, A02,
    C02), the admin parterre (A01-A03), cactus/agave beds at the gate (C01).
Widths not measurable from the evidence are labelled ESTIMATED in SOURCE_EVIDENCE.md.
"""
import math
import random

from mathutils import Vector

from . import survey as SV
from .geometry import (MeshBuilder, circle_poly, dist_to_polyline, in_zones, instance, rect_poly, resample,
                       runs_outside, sample_along, seg_intersections, smooth_polyline)

GY = SV.GATE_Y
RING_C, RING_R = SV.RING_C, SV.RING_R
Z_RING, Z_APPROACH = 0.056, 0.060          # road surface heights (other roads sit lower)
PAVE = 0.21                                  # sidewalks / plazas: ~0.15 m above the carriageways
LANE_C = sum(SV.LANE_HALF) / 2.0                    # 9.45: lane centre at the gate
APP_C = SV.APPROACH_MEDIAN_HALF + SV.APPROACH_CW / 2.0   # 5.8: approach carriageway centre
WEDGE_BED = (0.0, 82.0, 7.0)                         # circular flower bed (A01, A02, C02)
# red-mulch beds edged with white pebbles on the island outside the gate (C01); positions ESTIMATED
GATE_BEDS = ((0.0, GY + 25.5, 4.0), (-8.0, GY + 36.0, 4.5), (9.0, GY + 35.5, 5.0))
PERGOLA_ADMIN = (90.0, 26.0)                         # brown pergola beside the admin (A03)


def _bed_prism(mb, mat, geom, z0, z1):
    """Triangulated bed solid, including holes; never a self-crossing n-gon."""
    from shapely import constrained_delaunay_triangles, make_valid
    from shapely.geometry.polygon import orient
    from .ground_system import polygons
    for poly in polygons(make_valid(geom)):
        poly = orient(poly, sign=1.)
        verts, faces, ids = [], [], {}
        def vertex(x,y,z):
            key = (x,y,z)
            if key not in ids:
                ids[key] = len(verts)
                verts.append(key)
            return ids[key]
        for tri in constrained_delaunay_triangles(poly).geoms:
            co = list(orient(tri, sign=1.).exterior.coords)[:3]
            faces.append(tuple(vertex(x,y,z1) for x,y in co))
            faces.append(tuple(vertex(x,y,z0) for x,y in reversed(co)))
        for ring in [poly.exterior, *poly.interiors]:
            co = list(ring.coords)
            for (x,y),(u,v) in zip(co[:-1],co[1:]):
                faces.append((vertex(x,y,z0),vertex(u,v,z0),vertex(u,v,z1),vertex(x,y,z1)))
        mb.raw(mat,verts,faces)


# ------------------------------------------------------------------ paths
def ring_pts(step=3.0):
    n = int(2 * math.pi * RING_R / step)
    pts = [(RING_C[0] + RING_R * math.cos(2 * math.pi * i / n), RING_C[1] + RING_R * math.sin(2 * math.pi * i / n))
           for i in range(n)]
    return pts + [pts[0]]


def _smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def approach_x(y):
    """|x| of an approach carriageway centreline at y (straight 5.8 m, flaring to the 9.45 m gate lanes)."""
    return APP_C + (LANE_C - APP_C) * _smoothstep((y - (GY - 38.0)) / 30.0)


def approach_half_w(y):
    """Carriageway half width: 3.5 m on the approach, 2.45 m in the gate lanes."""
    return 3.5 + (2.45 - 3.5) * _smoothstep((y - (GY - 38.0)) / 30.0)


def _osm_curve(way_index, sx):
    """OSM approach way below y = 110 (the curve into the slip road), blended onto x = sx * 5.8."""
    pts = [tuple(p) for p in SV.slip_roads()[way_index]['pts'] if 72.0 < p[1] < 110.5]
    out = []
    for x, y in pts:
        w = _smoothstep((y - 80.0) / 25.0)
        out.append((x + (sx * APP_C - x) * w, y))
    return sorted(out, key=lambda p: -p[1])           # from the approach toward the slip end


def carriageway(sx):
    """Full centreline of one approach carriageway, from the slip-road end to Side Zewail Street.
    sx = -1: inbound (west, OSM 685373372), +1: outbound (east, OSM 912696914)."""
    curve = _osm_curve(0 if sx < 0 else 1, sx)
    straight = [(sx * approach_x(y), y) for y in [110.0 + 2.0 * k for k in range(int((GY + 15.0 - 110.0) / 2.0) + 1)]]
    # outside the gate: curve out to Side Zewail Street (OSM: (-57.2, 361.3) in, (69.2, 361.4) out)
    end = (-57.2, 361.3) if sx < 0 else (69.2, 361.4)
    p0 = (sx * LANE_C, GY + 15.0)
    ext = []
    for k in range(1, 21):
        t = k / 20.0
        # quadratic Bezier with the control point straight ahead of the gate lane
        c = (sx * LANE_C, end[1] - 4.0)
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * end[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * end[1]
        ext.append((x, y))
    path = list(reversed(curve)) + straight + ext
    return resample(path, 2.0)


def _clean(pts):
    out = []
    for p in pts:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > 0.2:
            out.append(p)
    return out


# road table: name -> dict(pts, half, mat, kind)
def road_table():
    roads = {}
    roads['Campus_Ring'] = dict(pts=resample(ring_pts(), 3.0), half=SV.RING_W / 2, mat='paver_road', kind='campus',
                                sidewalk=2.5)
    roads['Approach_Inbound'] = dict(pts=carriageway(-1), half=None, mat='paver_road', kind='approach')
    roads['Approach_Outbound'] = dict(pts=carriageway(1), half=None, mat='paver_road', kind='approach')
    for s in SV.slip_roads():
        pts = [tuple(p) for p in s['pts'] if p[1] < 76.0]
        if len(pts) > 2:
            nm = 'Slip_West' if pts[0][0] < 0 or pts[-1][0] < 0 else 'Slip_East'
            roads[nm] = dict(pts=resample(_clean(smooth_polyline(pts, 2)), 2.5), half=3.5, mat='paver_road',
                             kind='campus', sidewalk=0.0)
    roads['Admin_Drop_Off_Loop'] = dict(pts=resample(_clean(smooth_polyline(SV.drop_off_loop(), 2)), 2.0), half=3.2,
                                        mat='paver_road', kind='campus', sidewalk=0.0)
    for w in SV.campus_roads():
        t = w['tags']
        hw = 3.0 if t.get('service') == 'parking_aisle' else (2.75 if t.get('oneway') == 'yes' else 3.25)
        if t.get('highway') in ('unclassified', 'residential'):
            hw = 3.6
        pts = _clean(smooth_polyline(w['pts'], 2))
        if len(pts) < 2:
            continue
        roads[f"Campus_OSM_{w['id']}"] = dict(pts=resample(pts, 2.5), half=hw, mat='paver_road', kind='campus',
                                              sidewalk=0.0, parking=t.get('service') == 'parking_aisle')
    for w in SV.external_roads():
        t = w['tags']
        hw = {'secondary': 5.5, 'secondary_link': 3.2}.get(t.get('highway'), 3.75)
        pts = _clean(smooth_polyline(w['pts'], 2))
        if len(pts) < 2:
            continue
        roads[f"External_OSM_{w['id']}"] = dict(pts=resample(pts, 4.0), half=hw, mat='asphalt', kind='external',
                                                sidewalk=0.0, lanes=3 if t.get('highway') == 'secondary' else 2)
    return roads


ROADS = None
_JUNCTION_CACHE = None


def roads():
    global ROADS
    if ROADS is None:
        ROADS = road_table()
    return ROADS


def junction_zones(R):
    """Circles where centrelines cross or end on another road: no curbs or markings there."""
    global _JUNCTION_CACHE
    if _JUNCTION_CACHE is not None and _JUNCTION_CACHE[0] is R:
        return _JUNCTION_CACHE[1]
    names = list(R)
    zones = []
    approx = {n: [(p.x, p.y) for p in resample(R[n]['pts'], 6.0)] for n in names}
    hw = {n: (R[n]['half'] if R[n]['half'] else 3.5) for n in names}
    bbox = {n: (min(p[0] for p in approx[n]) - 10, max(p[0] for p in approx[n]) + 10,
                min(p[1] for p in approx[n]) - 10, max(p[1] for p in approx[n]) + 10) for n in names}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if {a, b} == {'Approach_Inbound', 'Approach_Outbound'}:
                continue
            A_, B_ = bbox[a], bbox[b]
            if A_[1] < B_[0] or B_[1] < A_[0] or A_[3] < B_[2] or B_[3] < A_[2]:
                continue
            for p in seg_intersections(approx[a], approx[b]):
                zones.append((p[0], p[1], max(hw[a], hw[b]) + 4.0))
        for end in (approx[a][0], approx[a][-1]):
            for b in names:
                if b == a:
                    continue
                if dist_to_polyline(end, approx[b]) < hw[b] + 2.0:
                    zones.append((end[0], end[1], max(hw[a], hw[b]) + 4.0))
                    break
    # perimeter loop meets the approach just inside the gate
    for sx in (-1, 1):
        zones.append((sx * 9.0, SV.PERIMETER_LOOP_Y, 9.0))
    _JUNCTION_CACHE=(R,zones)
    return zones


# ------------------------------------------------------------------- roads
def _road(M, name, coll, pts, half, z, zones, mat, sidewalk=0.0, lanes=0, median=0.0):
    mb = MeshBuilder()
    mb.ribbon(M[mat], pts, -half, half, z)
    # V11 (owner 15, QA defect 7): sidewalks run THROUGH junction zones. The ground
    # partition gives carriageways and curb returns priority, so each sidewalk is cut
    # exactly at the crossing road's edge instead of stopping ~16 m early in sand.
    if sidewalk > 0:
        for sgn in (-1, 1):
            a, b = sorted((sgn * (half + 0.25), sgn * (half + 0.25 + sidewalk)))
            mb.ribbon(M['paving'], pts, a, b, PAVE, depth=0.22)
    for run in runs_outside(pts, zones):
        for sgn in (-1, 1):
            a, b = sorted((sgn * (half - 0.05), sgn * (half + 0.25)))
            mb.ribbon(M['curb'], run, a, b, PAVE + 0.02, depth=0.25)
            if lanes:
                a, b = sorted((sgn * (half - 0.45), sgn * (half - 0.3)))
                mb.ribbon(M['marking'], run, a, b, z + 0.012)
    if lanes and lanes > 1:      # lane dashes on the public streets only (campus roads are unmarked pavers)
        lw = 2 * half / lanes
        for k in range(1, lanes):
            mb.dashes(M['marking'], pts, -half + k * lw, 0.15, 3.0, 6.0, z + 0.012, zones)
    return mb.to_object(name, coll)


def _approach(M, coll, zones):
    """Both approach carriageways (variable width), the palm median, planted strips, walkways."""
    objs = []
    for sx, nm in ((-1, 'Approach_Inbound'), (1, 'Approach_Outbound')):
        pts = roads()[nm]['pts']
        ab = []
        for p in pts:
            if p.y >= GY + 16.0:
                hw = 2.45 + (3.5 - 2.45) * _smoothstep((p.y - (GY + 16.0)) / 15.0)
            else:
                hw = approach_half_w(p.y) if p.y > 100.0 else 3.5
            ab.append((-hw, hw))
        mb = MeshBuilder()
        mb.ribbon_var(M['paver_road'], pts, ab, Z_APPROACH)
        # curbs on both edges outside junctions, except across the gate threshold
        keep = [i for i, p in enumerate(pts) if not in_zones(p, zones) and not (GY - 3.0 < p.y < GY + 3.0)]
        runs, cur = [], []
        for i in range(len(pts)):
            if i in keep:
                cur.append(i)
            elif cur:
                runs.append(cur)
                cur = []
        if cur:
            runs.append(cur)
        for run in runs:
            if len(run) < 2:
                continue
            rp = [pts[i] for i in run]
            for sgn in (-1, 1):
                mb.ribbon_var(M['curb'], rp, [tuple(sorted((sgn * (ab[i][1] - 0.05), sgn * (ab[i][1] + 0.25))))
                                              for i in run], PAVE + 0.02, depth=0.25)
        objs.append(mb.to_object("Road_" + nm, coll))
    return objs


def build_roads(M, C):
    R = C['roads']
    T = roads()
    zones = junction_zones(T)
    objs = _approach(M, R, zones)
    k_campus = k_ext = 0
    for name, r in T.items():
        if r['kind'] == 'approach':
            continue
        # every road surface gets its own height so crossing surfaces never coincide
        # (coplanar overlaps shadow each other in Cycles and z-fight in Godot)
        if name == 'Campus_Ring':
            z = Z_RING
        elif name.startswith(('Slip_', 'Admin_')):
            z = Z_RING - 0.003
        elif r['kind'] == 'campus':
            z = 0.040 + 0.0006 * (k_campus % 20)
            k_campus += 1
        else:
            z = 0.030 + 0.0006 * (k_ext % 12)
            k_ext += 1
        objs.append(_road(M, "Road_" + name, R, r['pts'], r['half'], z, zones, r['mat'],
                          sidewalk=r.get('sidewalk', 0.0), lanes=r.get('lanes', 0)))
    # parking pads along OSM parking aisles (stalls 5.5 m deep each side, lines every 2.6 m)
    mb = MeshBuilder()
    for name, r in T.items():
        if not r.get('parking'):
            continue
        pts = r['pts']
        mb.ribbon(M['paver_road'], pts, -8.5, 8.5, 0.036)
        for sgn in (-1, 1):
            a, b = sorted((sgn * 8.5, sgn * 8.8))
            mb.ribbon(M['curb'], pts, a, b, PAVE + 0.02, depth=0.25)
            for p, t in sample_along(pts, 2.6, start=1.3):
                c = p + Vector((-t.y, t.x)) * sgn * 5.75
                mb.obox(M['marking'], (c.x, c.y, 0.055), (0.1, 5.5, 0.02), math.atan2(t.y, t.x))
    if not mb.empty():
        objs.append(mb.to_object("Parking_Lots", R))
    return objs


# ------------------------------------------------------------------ ground
def _hard_mask(T, extra=1.5, step=2.0):
    """Set of grid cells (step m) covered by roads, sidewalks and building footprints."""
    cells = set()

    def mark(x, y, r):
        i0, i1 = int((x - r) // step), int((x + r) // step)
        j0, j1 = int((y - r) // step), int((y + r) // step)
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                cx, cy = (i + 0.5) * step, (j + 0.5) * step
                if (cx - x) ** 2 + (cy - y) ** 2 <= r * r:
                    cells.add((i, j))

    for r in T.values():
        hw = (r['half'] or 3.5) + r.get('sidewalk', 0.0) + extra
        if r.get('parking'):
            hw = 9.0 + extra
        for p in resample(r['pts'], 1.5):
            mark(p.x, p.y, hw)
    return cells


def build_ground(M, C):
    mb = MeshBuilder()
    mb.box(M['sand'], -25000, -25000, -0.5, 25000, 25000, 0.0)
    sand = mb.to_object("Ground_Desert_Sand", C['ground'])
    mb = MeshBuilder()
    mb.prism(M['soil_light'], SV.PLOT, -0.1, 0.012)              # graded campus land (A01, S2: bare in the south)
    plot = mb.to_object("Ground_Campus_Plot", C['ground'])
    return [sand, plot]


def _ext_mask():
    """Cells (8 m) within 25 m of an external road centreline: planted medians and verges."""
    cells = set()
    for w in SV.external_roads():
        for p in resample([tuple(q) for q in w['pts']], 4.0):
            for di in range(-3, 4):
                for dj in range(-3, 4):
                    cells.add((int(p.x // 8.0) + di, int(p.y // 8.0) + dj))
    return cells


def build_landscape(M, C):
    objs = []
    T = roads()
    g = SV.NDVI_GRID
    v = g['ndvi_x1000']
    nx = g['nx']
    ext = _ext_mask()

    def field(i, j):
        return v[j * nx + i] / 1000.0

    step, x0, y0 = g['step'], g['x0'], g['y0']
    cellmask = {}
    for j in range(g['ny'] - 1):
        for i in range(nx - 1):
            cx, cy = x0 + (i + 0.5) * step, y0 + (j + 0.5) * step
            cellmask[(i, j)] = SV.inside_plot(cx, cy) or (int(cx // 8.0), int(cy // 8.0)) in ext

    def mask(x, y):
        return cellmask.get((int((x - x0) // step), int((y - y0) // step)), False)

    # NDVI ground cover (Sentinel-2, 2026-09-16): irrigated lawn >= 0.36; 0.20-0.36 is sparse planting
    # on soil (tree canopy over bare ground gives these values; the true-colour image shows the
    # approach parcels brown, not green)
    mb = MeshBuilder()
    n_l = mb.isoband(M['grass'], field, g['x0'], g['y0'], g['step'], g['nx'], g['ny'], 0.36, 9.0, 0.032, mask)
    n_g = mb.isoband(M['planted_soil'], field, g['x0'], g['y0'], g['step'], g['nx'], g['ny'], 0.20, 0.36, 0.026, mask)
    # wedge lawn between the approach curves (A01, C02: lawn around the circular bed)
    wedge = [(-17.0, 70.0), (17.0, 70.0), (3.5, 104.0), (-3.5, 104.0)]
    mb.prism(M['grass'], wedge, -0.1, 0.05)
    lawns = mb.to_object("Lawns", C['veg_lawns'])
    lawns["zc_ndvi_faces"] = [n_l, n_g]
    objs.append(lawns)

    # plazas, walkways, aprons --------------------------------------------------------
    mb = MeshBuilder()
    pav, pal = M['paving'], M['paving_light']
    # approach: planted strips (C02), walkways, outer beds, both sides; gate plaza inside the frame
    for sx in (-1, 1):
        ys = [100.0 + 2.0 * k for k in range(int((GY - 32.0 - 100.0) / 2.0) + 1)]
        line = resample([(0.0, y) for y in ys], 2.0)
        ab_strip, ab_walk, ab_bed = [], [], []
        for p in line:
            xc = approach_x(p.y) + approach_half_w(p.y) + 0.25
            ab_strip.append(tuple(sorted((sx * xc, sx * 14.3))))
            ab_walk.append(tuple(sorted((sx * 14.3, sx * 18.3))))
            ab_bed.append(tuple(sorted((sx * 18.3, sx * 22.0))))
        mb.ribbon_var(M['groundcover'], line, ab_strip, 0.16, depth=0.2)
        mb.ribbon_var(pav, line, ab_walk, PAVE, depth=0.25)
        mb.ribbon_var(M['groundcover'], line, ab_bed, 0.08, depth=0.1)
        # inner gate plaza between the perimeter loop and the frame (D02 pavers), reaching the
        # pedestrian gates at |x| 17.4-20.6
        y_a, y_b = SV.PERIMETER_LOOP_Y + 3.6, GY + 0.4
        pts = [(sx * (approach_x(y) + approach_half_w(y) + 0.25), y) for y in (y_a, (y_a + y_b) / 2, y_b)]
        poly = pts + [(sx * 23.0, y_b), (sx * 23.0, y_a)]
        mb.prism(pal, poly, -0.1, PAVE)
        # walkway segment between the loop and the approach walkway (crossing point)
        lo, hi = sorted((sx * 14.3, sx * 18.3))
        mb.prism(pav, rect_poly(lo, GY - 32.0, hi, SV.PERIMETER_LOOP_Y - 3.6), -0.1, PAVE)
        # exterior apron in front of the gate buildings (C01 pavers and curbs)
        lo, hi = sorted((sx * 12.3, sx * 62.0))
        mb.prism(pal, rect_poly(lo, GY + 0.4, hi, GY + 14.0), -0.1, PAVE)
    # median: raised palm bed, widening to the gatehouse; U-turn gap at the OSM median link
    # V11 (owner 03): 0.5 m resampling (V4-V10: 2 m) so the widening median curb is smooth.
    line = resample([(0.0, y) for y in (104.0, GY + 5.6)], 0.5)
    for run in runs_outside(line, [(0.0, SV.APPROACH_U_TURN_Y, 6.0)]):
        ab = [(-(approach_x(p.y) - approach_half_w(p.y) - 0.25), approach_x(p.y) - approach_half_w(p.y) - 0.25)
              for p in run]
        # V11 (QA defect 3): the median is a curb RING around a planting bed. V4-V10 drew a
        # full-width curb ribbon that won the partition, so the palms stood on a concrete slab.
        mb.ribbon_var(M['curb'], run, [(a, a + 0.3) for a, b in ab], PAVE + 0.02, depth=0.25)
        mb.ribbon_var(M['curb'], run, [(b - 0.3, b) for a, b in ab], PAVE + 0.02, depth=0.25)
        mb.ribbon_var(M['groundcover'], run, [(a + 0.3, b - 0.3) for a, b in ab], PAVE + 0.03)
    # admin forecourt: paving from the facade to the drop-off loop (A01), parterre band to the ring
    loop = SV.drop_off_loop()
    front = [(x, y - 3.4) for x, y in smooth_polyline(loop, 2) if abs(x) < 46]
    mb.prism(pal, [(-46.0, 18.0)] + front + [(46.0, 18.0)], -0.1, PAVE)
    mb.prism(pal, rect_poly(-82, -16, 82, 18), -0.1, PAVE)
    # institute and residential aprons (paved 6 m round the footprint)
    for spec in (SV.HELMY, SV.EAST_INSTITUTE):
        a = math.radians(spec['angle_deg'])
        hl, hw = spec['length'] / 2 + 6, spec['width'] / 2 + 6
        cx, cy = spec['center']
        pts = [(cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a))
               for x, y in ((-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw))]
        mb.prism(pal, pts, -0.1, PAVE)
    # academic: courtyard between the prongs (D05: paved court with beds) and the forecourt apron
    A = SV.ACADEMIC
    mb.prism(pal, rect_poly(-A['prong_x'][0], A['core_front_y'] - 1, A['prong_x'][0], A['prong_front_y']), -0.1, PAVE)
    mb.prism(pal, rect_poly(-A['prong_x'][1] - 6, A['prong_front_y'], A['prong_x'][1] + 6, A['prong_front_y'] + 14),
             -0.1, PAVE)
    # campus footways (OSM 2021), 2.5 m light pavers
    for w in SV.campus_footways():
        pts = resample(smooth_polyline(w['pts'], 1), 2.0)
        if len(pts) > 1:
            mb.ribbon(pav, pts, -1.25, 1.25, PAVE + 0.004, depth=0.25)   # never coplanar with plazas
    objs.append(mb.to_object("Plaza_Paving", C['roads']))

    # planting beds ------------------------------------------------------------------
    mb = MeshBuilder()
    # V10: the D05 planted beds along the Gate (A) forecourt are removed; owner photo
    # P09 shows this forecourt as continuous open paving with nested dark inlays.
    # V11 (owner 00): the V4-V10 striped red/orange/hedge ribbons on the drop-off islands
    # are removed (no photo shows striped bars there). A02 shows LOW red and orange
    # flower rows edged in white pebbles right at the building line: the arm beds follow
    # that (0.35 m, pebble edge), replacing the raised orange bars.
    for sx in (-1, 1):
        lo, hi = sorted((sx * 50.0, sx * 61.0))
        mb.box(M['pebbles'], lo - 0.45, 36.0, 0.0, hi + 0.45, 38.2, 0.16)
        mb.box(M['mulch'], lo - 0.05, 36.4, 0.0, hi + 0.05, 37.8, 0.2)
        n = int((hi - lo) / 0.9)
        for k in range(n):
            x = lo + 0.45 + k * (hi - lo - 0.9) / max(1, n - 1)
            mat = M['shrub_red'] if k % 2 == 0 else M['shrub_orange']
            mb.cylinder(mat, (x, 36.8), 0.2, 0.52, 0.34, 0.24, segs=8)
            mb.cylinder(M['shrub_orange'] if k % 2 == 0 else M['shrub_red'], (x + 0.2, 37.45), 0.2, 0.48, 0.3, 0.2, segs=8)
    # V11 (owner 00 + C02, PHOTO VERIFIED): the approach circle is kept but restyled to C02 -
    # white pebble ring, dark red mulch, tall red euphorbia clumps (no bullseye rings).
    cx, cy, r = WEDGE_BED
    from shapely.geometry import Polygon
    outer = Polygon(circle_poly(cx, cy, r, 64))
    inner = Polygon(circle_poly(cx, cy, r - .7, 64))
    _bed_prism(mb, M['pebbles'], outer.difference(inner), 0., .16)
    _bed_prism(mb, M['mulch'], inner, 0., .19)
    for k in range(9):
        a = 2 * math.pi * k / 9
        rr = r * (0.45 if k % 2 else 0.62)
        mb.cylinder(M['shrub_red'], (cx + rr * math.cos(a), cy + rr * math.sin(a)), 0.19, 1.25, 0.45, 0.18, segs=7)
    # gate island outside the frame (C01): red mulch beds edged with white pebbles on soil
    isl = _gate_island_poly(to_gatehouse=True)
    _bed_prism(mb, M['soil'], Polygon(isl), -.1, .1)
    for bx, by, rr in GATE_BEDS:
        outer = Polygon(circle_poly(bx, by, rr + .45, 40))
        inner = Polygon(circle_poly(bx, by, rr, 40))
        _bed_prism(mb, M['pebbles'], outer.difference(inner), 0., .16)
        _bed_prism(mb, M['mulch'], inner, 0., .18)
    objs.append(mb.to_object("Flower_Beds", C['veg_lawns']))

    # pergola beside the admin (A03 shows a brown timber/steel pergola)
    mb = MeshBuilder()
    px, py = PERGOLA_ADMIN
    w = M['wood']
    for x in (-6, -2, 2, 6):
        for y in (-2.5, 2.5):
            mb.box(w, px + x - 0.25, py + y - 0.25, 0.15, px + x + 0.25, py + y + 0.25, 3.6)
    for y in (-2.5, 2.5):
        mb.box(w, px - 6.6, py + y - 0.2, 3.6, px + 6.6, py + y + 0.2, 4.1)
    for k in range(27):
        x = -6.5 + k * 0.5
        mb.box(w, px + x - 0.07, py - 3.2, 4.1, px + x + 0.07, py + 3.2, 4.35)
    objs.append(mb.to_object("Pergola_Admin_Side", C['furniture']))
    return objs


def _gate_island_poly(to_gatehouse=False):
    """Island between the exterior in/out roads, behind the gatehouse (C01 camera position)."""
    inn, out = roads()['Approach_Inbound']['pts'], roads()['Approach_Outbound']['pts']
    left = [(p.x + 4.0, p.y) for p in inn if p.y > GY + 16.0 and p.y < 356.0]
    right = [(p.x - 4.0, p.y) for p in out if p.y > GY + 16.0 and p.y < 356.0]
    if not to_gatehouse:
        # Vegetation placement keeps the V4-V14 island so its random stream (and every later
        # plant on the campus) is unchanged.
        return [(-6.0, GY + 16.0)] + left + list(reversed(right)) + [(6.0, GY + 16.0)]
    # V15 bed surface (C01, V14 unresolved sand strip x -5.5..6.5, y 326.5..330.5): the island bed
    # starts at the gatehouse back wall (GATEHOUSE y1 = GY + 14.6), not 1.4 m behind it.
    y1 = SV.GATEHOUSE["y1"] + 0.05
    return [(-6.5, y1)] + left + list(reversed(right)) + [(6.5, y1)]


# ------------------------------------------------------------- vegetation
def build_vegetation(M, C, A, seed=3):
    rng = random.Random(seed)
    cnt = {'palm': 0, 'fan': 0, 'tree': 0, 'shrub': 0, 'xero': 0}
    T = roads()
    hard = _hard_mask(T)

    def put(kind, mesh_list, coll, x, y, s=None, z=0.0):
        cnt[kind] += 1
        instance(rng.choice(mesh_list), f"{kind.title()}_{cnt[kind]:04d}", coll, (x, y, z),
                 rng.uniform(0, 6.283), s or rng.uniform(0.85, 1.15))

    def free(x, y):
        if abs(x) < 24.0 and 60.0 < y < GY + 60.0:      # approach corridor: planted explicitly below
            return False
        return (int(x // 2.0), int(y // 2.0)) not in hard and not _in_buildings(x, y)

    # approach median (C02 2017): low planting along its length, date palms only over the last
    # ~60 m before the gate; one fan palm where the median ends at the wedge (A01)
    for y in [GY - 62.0 + 9.0 * k for k in range(7)]:
        put('palm', A['palms'], C['veg_palms'], 0.0, y, s=rng.uniform(0.8, 1.0), z=0.2)
    for y in [110.0 + 4.0 * k for k in range(int((GY - 66.0 - 110.0) / 4.0) + 1)]:
        if abs(y - SV.APPROACH_U_TURN_Y) > 7.0:
            put('shrub', A['shrubs'], C['veg_shrubs'], rng.uniform(-0.6, 0.6), y, s=rng.uniform(0.45, 0.6), z=0.2)
    # planted strip beside the carriageway: low clipped shrubs (C02); young broadleaf trees and
    # cycads on the outer side of the walkway (C02 left foreground)
    for sx in (-1, 1):
        for y in [104.0 + 4.0 * k for k in range(int((GY - 36.0 - 104.0) / 4.0) + 1)]:
            put('shrub', A['shrubs'], C['veg_shrubs'], sx * 11.9 + rng.uniform(-0.8, 0.8), y, s=rng.uniform(0.45, 0.6), z=0.12)
        for y in [104.0 + 8.0 * k for k in range(int((GY - 36.0 - 104.0) / 8.0) + 1)]:
            # V11 (owner 05, QA defect 13): trunks ~3 m outside the walk edge (V4-V10 1.0-1.6 m;
            # canopies overhung the footpath). C02 shows the trees outside the walk.
            put('tree', A['trees'], C['veg_trees'], sx * 21.4 + rng.uniform(-0.3, 0.3), y + rng.uniform(-1, 1),
                s=rng.uniform(0.7, 0.95), z=0.08)
            put('shrub', A['cycad'], C['veg_shrubs'], sx * 22.8 + rng.uniform(-0.4, 0.4), y + 4.0, s=rng.uniform(0.8, 1.2), z=0.08)
    # palms in front of the perimeter wall either side of the gate (C02 left / right)
    for sx in (-1, 1):
        for k in range(26):
            x = sx * (66.0 + k * 7.0)
            y = GY - 7.0 - max(0.0, (abs(x) - 140.0)) * 0.35
            if not SV.inside_plot(x, y) or not free(x, y):
                continue
            put('fan' if k % 2 else 'palm', A['fan_palms'] if k % 2 else A['palms'], C['veg_palms'], x, y)
    # gate island (C01): agaves, golden barrel cacti, red euphorbia clumps, young date palms
    isl = _gate_island_poly()
    xs = [p[0] for p in isl]
    ys = [p[1] for p in isl]
    for _ in range(420):
        x, y = rng.uniform(min(xs), max(xs)), rng.uniform(min(ys), max(ys))
        if not _pip(x, y, isl):
            continue
        r = rng.random()
        if r < 0.32:
            put('xero', A['barrel'], C['veg_shrubs'], x, y, s=rng.uniform(0.8, 1.2), z=0.1)
        elif r < 0.62:
            put('xero', A['agave'], C['veg_shrubs'], x, y, s=rng.uniform(0.8, 1.3), z=0.1)
        elif r < 0.84:
            put('xero', A['euphorbia'], C['veg_shrubs'], x, y, s=rng.uniform(0.8, 1.2), z=0.1)
        else:
            put('shrub', A['shrubs'], C['veg_shrubs'], x, y, s=rng.uniform(0.25, 0.4), z=0.1)
    for x, y, _r in GATE_BEDS:
        put('palm', A['palms'], C['veg_palms'], x, y, s=0.45, z=0.18)
    # V10: the six D05 'Gate (A) courtyard trees' are removed. Owner photo P09 shows
    # the whole forecourt between the prongs as open paving (D05 is a possibly
    # enhanced image). The random stream is consumed identically so every other
    # NDVI-driven plant keeps its V9 position.
    for _ in range(6):
        rng.choice(A['trees'])
        rng.uniform(0, 6.283)
    # wedge bed: a large fan palm in the centre (A02, C02) and small fan palms on the lawn (C02)
    put('fan', A['fan_palms'], C['veg_palms'], WEDGE_BED[0], WEDGE_BED[1], s=0.42, z=0.58)
    for x, y in ((-9.0, 74.0), (9.0, 74.0)):
        put('fan', A['fan_palms'], C['veg_palms'], x, y, s=0.5, z=0.05)
    # date palms + fan palms around the admin precinct (A01, A02, A03)
    for x, y in ((-96, 0), (96, 0), (-96, -32), (96, -32), (-100, -70), (100, -70)):
        put('palm', A['palms'], C['veg_palms'], x + rng.uniform(-1, 1), y + rng.uniform(-1, 1))
    # ring road: trees along both sidewalks where the 2026 NDVI shows planting
    for p, t in sample_along(T['Campus_Ring']['pts'], 18.0, start=4.0):
        nrm = Vector((-t.y, t.x))
        for side in (-1, 1):
            q = p + nrm * side * (SV.RING_W / 2 + 4.6)
            if SV.ndvi(q.x, q.y) > 0.17 and free(q.x, q.y):
                put('tree', A['trees'], C['veg_trees'], q.x, q.y, s=rng.uniform(0.7, 1.0))
    # NDVI-driven planting on the irrigated land (parcels, west sector, gardens): jittered 9 m grid,
    # probability rises with NDVI; bare ground (south half of the ring) stays bare.
    for gx in range(-480, 481, 9):
        for gy in range(-640, 360, 9):
            x, y = gx + rng.uniform(-3.0, 3.0), gy + rng.uniform(-3.0, 3.0)
            if not SV.inside_plot(x, y):
                continue
            nd = SV.ndvi(x, y)
            p_tree = max(0.0, min(0.8, (nd - 0.19) / 0.22))
            if p_tree <= 0 or rng.random() > p_tree or not free(x, y):
                continue
            if rng.random() < 0.12:
                put('tree', A['cypress'], C['veg_trees'], x, y, s=rng.uniform(0.7, 1.0))
            else:
                put('tree', A['trees'], C['veg_trees'], x, y, s=rng.uniform(0.65, 1.1))
    # shrubs on planted soil (NDVI 0.2-0.3) and a few desert shrubs on bare land
    for _ in range(9000):
        if cnt['shrub'] > 900:
            break
        x, y = rng.uniform(-470, 480), rng.uniform(-680, 340)
        if not SV.inside_plot(x, y) or not free(x, y):
            continue
        nd = SV.ndvi(x, y)
        if nd > 0.2 and rng.random() < 0.35:
            put('shrub', A['shrubs'], C['veg_shrubs'], x, y, s=rng.uniform(0.5, 0.9))
        elif nd < 0.14 and rng.random() < 0.02:
            put('shrub', A['shrubs'], C['veg_shrubs'], x, y, s=rng.uniform(0.3, 0.5))
    return cnt


def _pip(x, y, poly):
    c = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def _footprints():
    out = [rect_poly(-90, -100, 90, 40),                                 # admin precinct
           [(x, y) for x, y in circle_poly(0.0, SV.ACADEMIC['curve_c'][1], SV.ACADEMIC['r_out'] + 8, 32)],
           rect_poly(-62, -250, 62, -160),                               # academic prongs + court
           rect_poly(-30, GY - 8, 30, GY + 16),                          # gatehouse / frame
           rect_poly(-64, GY - 8, 64, GY + 10)]                          # gate buildings
    for spec in (SV.HELMY, SV.EAST_INSTITUTE):
        a = math.radians(spec['angle_deg'])
        hl, hw = spec['length'] / 2 + 8, spec['width'] / 2 + 8
        cx, cy = spec['center']
        out.append([(cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a))
                    for x, y in ((-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw))])
    out += [list(map(tuple, b)) for b in SV.EAST_PAIR]
    return out


_FP = None


def _in_buildings(x, y):
    global _FP
    if _FP is None:
        _FP = [(fp, min(p[0] for p in fp), max(p[0] for p in fp), min(p[1] for p in fp), max(p[1] for p in fp))
               for fp in _footprints()]
    for fp, x0, x1, y0, y1 in _FP:
        if x0 <= x <= x1 and y0 <= y <= y1 and _pip(x, y, fp):
            return True
    return False


# --------------------------------------------------------------- furniture
def build_furniture(M, C, A, seed=5):
    rng = random.Random(seed)
    furn, n = C['furniture'], {'lamp': 0, 'car': 0}
    T = roads()

    def lamp(mesh, x, y, rot):
        n['lamp'] += 1
        instance(mesh, f"Lamp_{n['lamp']:03d}", furn, (x, y, 0.0), rot)

    # (V4: no lamps in the approach median: C02 shows none; the double-arm lamps of A04 stand
    #  on the ring road, below)
    zones = junction_zones(T)
    for p, t in sample_along(T['Campus_Ring']['pts'], 40.0, start=14.0):            # ring lamps, inner sidewalk
        if not in_zones(p, zones):
            q = p - Vector((-t.y, t.x)) * (SV.RING_W / 2 + 1.2)
            lamp(A['lamp2'] if q.y > -60 else A['lamp'], q.x, q.y, math.atan2(t.y, t.x) + math.pi / 2)
    for sx in (-1, 1):                                                                # walkway lamps (C02)
        for y in [120.0 + 30.0 * k for k in range(int((GY - 40.0 - 120.0) / 30.0) + 1)]:
            lamp(A['lamp'], sx * 18.6, y, 0.0 if sx > 0 else math.pi)
    paints = [M['car_' + k] for k in ('white', 'white', 'silver', 'silver', 'black', 'red', 'blue')]

    # V10 (owner brief + evidence audit): no photograph shows parked or moving cars
    # (owner photos show an empty campus; A01 only a few on the ring). Vehicles are
    # kept for future gameplay in Optional_Vehicles_Disabled, excluded from the view
    # layer, renders and the game export.
    veh = C.get('vehicles', furn)

    def car(x, y, ang, z=0.05):
        n['car'] += 1
        o = instance(A['car'], f"Car_{n['car']:03d}", veh, (x, y, z), ang)
        o.material_slots[0].link = 'OBJECT'
        o.material_slots[0].material = rng.choice(paints)

    # traffic: a few cars on the ring (A01) and the approach; parked cars along the OSM aisles
    for name, count in (('Campus_Ring', 16), ('Approach_Inbound', 3), ('Approach_Outbound', 3)):
        pts = T[name]['pts']
        samples = [s for s in sample_along(pts, 9.0, start=10.0) if not in_zones(s[0], zones)
                   and s[0].y < GY - 40.0]
        for p, t in rng.sample(samples, min(count, len(samples))):
            q = p + Vector((-t.y, t.x)) * rng.choice((-1.8, 1.8))
            car(q.x, q.y, math.atan2(t.y, t.x))
    for name, r in T.items():
        if not r.get('parking'):
            continue
        for p, t in sample_along(r['pts'], 2.6, start=2.6):
            for sgn in (-1, 1):
                if rng.random() < 0.55:
                    q = p + Vector((-t.y, t.x)) * sgn * 5.75
                    car(q.x, q.y, math.atan2(t.y, t.x) + math.pi / 2 + (math.pi if rng.random() < 0.5 else 0.0))
    return n
