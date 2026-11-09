"""V4 site survey: evidence-derived layout of the as-built campus.

This module replaces the brochure-plan anchors of V2/V3 (site_plan.py, which is
now kept only for the hidden HISTORICAL DESIGN layer) as the source of the site
layout. Every coordinate is in the Blender frame used since V2:

    metres, origin = centre of the copper dome, +Y = toward the main gate along
    the campus axis, +X = right when facing the gate, Z up.

Sources (see references/SOURCE_EVIDENCE.md, section V4):
  * OpenStreetMap (ODbL), extracted 2026-11-06 with Overpass. Campus service
    roads mapped 2021-03-02, building outlines 2017-11-13, ring and gate nodes.
    Curated into data/osm_campus.json by tools/geo/export_osm_campus.js.
  * Copernicus Sentinel-2 L2A, 2026-09-16 (S2A_36RUU_20260916): true-colour
    image used as an independent dated orthophoto check, and NDVI (B08, B04)
    used for the distribution of irrigated planting (data/ndvi_s2_20260916.json).
  * Photographs: C01/C02 Wikimedia Commons 2017-11-18 (CC BY-SA 4.0), D02/D03
    official zewailcity.edu.eg (gate, 2021 and undated), A01-A05 (V2 register).

Coordinate transformation (documented in tools/geo/osm_to_axis.js):
  1. WGS84 -> local ENU metres about 29.9410 N, 31.0670 E (ellipsoidal metre/degree).
  2. Axis frame: origin = least-squares circle centre of the campus ring road
     (all ring-road vertices, n = 184, rms 5.7 m), +Y = unit vector to the
     midpoint of the two main-gate nodes (OSM 5225739523, 5225739528).
     Bearing of +Y: N 36.5 deg W. Gate distance 560.7 m.
  3. Blender = (x_axis, y_axis - 246.1). 246.1 m is the dome's axis-frame Y,
     from the admin outline (arm fronts 280 m, rear 148 m) and the V3 admin
     massing (arm fronts +33.9 m, rear -94 m from the dome); the two
     estimates agree to 4 m.
  The axis is an independent control: it is defined by the gate nodes and the
  ring, and the admin, academic and gate road centrelines all fall within 3 m
  of it.

Status labels used below: VERIFIED (photo + dated map/imagery agree),
ESTIMATED (position from map, size or height inferred), HISTORICAL (design
documents only, hidden), UNVERIFIED (not modelled).
"""
import json
import math
import os

_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _load(name):
    with open(os.path.join(_DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


OSM = _load("osm_campus.json")
_NDVI = _load("ndvi_s2_20260916.json")

# ---------------------------------------------------------------- control
DOME_AXIS_Y = OSM["frame"]["dome_axis_y"]      # 246.1
AXIS_BEARING_DEG = -36.54                       # +Y bearing from true north (N 36.5 W)

# Ring road: OSM ways 912696913 (north half) and 685373371 (south half) fitted separately:
# centres (2.0, 8.9) and (1.9, 8.1) axis frame, r = 301.5 / 300.9 m, rms 0.54 / 0.36 m.
# One one-way carriageway (OSM oneway=yes). Centre x 2.0 m off the gate axis is inside
# the tracing tolerance, so the ring is centred on the axis.          VERIFIED (position)
RING_C = (0.0, 8.5 - DOME_AXIS_Y)            # (0, -237.6)
RING_R = 301.2
RING_W = 8.0                                   # carriageway width: ESTIMATED (2 lanes, A01)

# Main gate: OSM gate nodes 10.4 m apart, axis-frame y 560.7.         VERIFIED (position)
GATE_Y = 560.7 - DOME_AXIS_Y                  # 314.6

# Approach (OSM 685373372 in, 912696914 out: centrelines x = -5.9 / +6.6 m).
# Cross-section from C02 (2017) at its 32 px/m gate scale: 7 m carriageways of grey
# pavers, a ~4.5 m palm median, planted strip, walkway.           ESTIMATED (widths)
APPROACH_MEDIAN_HALF = 2.3
APPROACH_CW = 7.0
APPROACH_STRIP = 5.0          # planted strip between carriageway and walkway
APPROACH_WALK = 4.0
APPROACH_U_TURN_Y = 506.5 - DOME_AXIS_Y      # OSM 912696893 median link
PERIMETER_LOOP_Y = 547.3 - DOME_AXIS_Y       # OSM 674883447, just inside the gate

# Portal frame and gatehouse, photogrammetry from C02 (person 1.7 m = 55 px -> 32 px/m at the
# frame) cross-checked against C01 (minibus 2.3 m) and D02.        ESTIMATED (+-8 %)
PORTAL = {
    'outer_w': 33.4, 'height': 18.7, 'leg_w': 4.8, 'lintel_h': 4.5, 'depth': 4.8,
    'inlay_w': 0.55, 'inlay_off': 1.9,
}
GATEHOUSE = {'w': 14.0, 'y0': GATE_Y + 5.6, 'y1': GATE_Y + 14.6, 'h': (9.4, 8.1, 6.5)}
LANE_HALF = (7.0, 11.9)          # |x| range of each gate lane (5.1 m wide)

# ---------------------------------------------------------------- buildings
def _bld(key):
    return [tuple(p) for p in OSM["buildings"][key]["pts"]]


def _rect_spec(pts):
    """Centre, long-axis angle, length, width of a 4-corner OSM outline."""
    p = pts[:4]
    e1 = (p[1][0] - p[0][0], p[1][1] - p[0][1])
    e2 = (p[2][0] - p[1][0], p[2][1] - p[1][1])
    l1, l2 = math.hypot(*e1), math.hypot(*e2)
    cx = sum(q[0] for q in p) / 4.0
    cy = sum(q[1] for q in p) / 4.0
    long_e = e1 if l1 >= l2 else e2
    ang = math.degrees(math.atan2(long_e[1], long_e[0]))
    if ang > 90:
        ang -= 180
    if ang < -90:
        ang += 180
    return {'center': (round(cx, 2), round(cy, 2)), 'angle_deg': round(ang, 2),
            'length': round(max(l1, l2), 2), 'width': round(min(l1, l2), 2)}


# Helmy Institute for Medical Sciences: OSM 540106545 (building=university, 2017).
# 103.5 x 29.8 m; SIAC gives 12,200 m2 total area (~4 floors).    VERIFIED (identity: SIAC + A05)
HELMY = _rect_spec(_bld("helmy_2017"))
HELMY['height'] = 20.0
# East institute: OSM 540106546 (building=university, 2017). 77.3 x 36.7 m.   ESTIMATED (identity unconfirmed)
EAST_INSTITUTE = _rect_spec(_bld("east_institute_2017"))
EAST_INSTITUTE['height'] = 20.0

# Academic Building: OSM 540106547 (2017 outline, C-shaped with two prongs and two side wings),
# A01 (front blocks), D05 (official Gate (A) courtyard view).
ACADEMIC = {
    'curve_c': (0.0, -249.0), 'r_out': 99.0, 'ring_depth': 25.0,
    'side_front_y': -212.0,              # side wings end   (axis y 34)
    'notch_y': -236.0,                   # recess between prong and side wing (axis y 10)
    'prong_x': (19.8, 55.3), 'prong_front_y': -169.0,   # prongs (axis y 77)
    'core_front_y': -229.0,              # Gate (A) facade between the prongs (axis y 17)
    'h_wing': 22.0, 'h_prong': 24.0,     # ~5 storeys (D05, A01)      ESTIMATED
}

# Residential pair east of the ring: OSM 540106540/541 (building=university, building:levels=5),
# visible in Sentinel-2 2026. Identity not confirmed (the official "Dorms" photo D01 shows
# 5-storey blocks, location not stated).                          ESTIMATED
EAST_PAIR = [_bld("east_pair_a"), _bld("east_pair_b")]
EAST_PAIR_H = 21.4   # V7: six storeys from P16 + official dorms image (OSM levels=5 conflict recorded)

# ---------------------------------------------------------------- site geometry
PLOT = [tuple(p) for p in OSM["plot_boundary"]]


def inside_plot(x, y, poly=PLOT):
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


def ndvi(x, y):
    """Sentinel-2 NDVI (2026-09-16) at Blender (x, y), bilinear, 4 m grid."""
    g = _NDVI
    fx = (x - g['x0']) / g['step']
    fy = (y - g['y0']) / g['step']
    nx, ny = g['nx'], g['ny']
    if fx < 0 or fy < 0 or fx > nx - 1 or fy > ny - 1:
        return 0.08
    i, j = int(fx), int(fy)
    i1, j1 = min(i + 1, nx - 1), min(j + 1, ny - 1)
    tx, ty = fx - i, fy - j
    v = g['ndvi_x1000']
    a = v[j * nx + i] * (1 - tx) + v[j * nx + i1] * tx
    b = v[j1 * nx + i] * (1 - tx) + v[j1 * nx + i1] * tx
    return (a * (1 - ty) + b * ty) / 1000.0


NDVI_GRID = _NDVI


def campus_roads():
    return OSM["campus_roads"]


def campus_footways():
    return OSM["campus_footways"]


def external_roads():
    return OSM["external_roads"]


def slip_roads():
    return OSM["slip_roads"]


def drop_off_loop():
    return [tuple(p) for p in OSM["drop_off_loop"]["pts"]]


# ---------------------------------------------------------------- control-point table
# (name, V3 value from the brochure plan, V4 value from survey, source). Written to
# output/validation/control_points.json by validate_architecture.py.
CONTROL_POINTS = [
    ("main gate y", 307.6, GATE_Y, "OSM gate nodes"),
    ("ring centre y", -245.0, RING_C[1], "OSM ring fit (two halves)"),
    ("ring radius", 300.0, RING_R, "OSM ring fit"),
    ("academic prong front y", -158.3, ACADEMIC['prong_front_y'], "OSM 540106547"),
    ("academic core front y", -207.0, ACADEMIC['core_front_y'], "OSM 540106547, D05"),
    ("academic rear y", -342.4, ACADEMIC['curve_c'][1] - ACADEMIC['r_out'], "OSM 540106547"),
    ("Helmy centre x", -129.7, HELMY['center'][0], "OSM 540106545"),
    ("Helmy centre y", -61.3, HELMY['center'][1], "OSM 540106545"),
    ("Helmy length", 108.0, HELMY['length'], "OSM 540106545"),
    ("east institute centre x", 143.4, EAST_INSTITUTE['center'][0], "OSM 540106546"),
    ("east institute centre y", -60.1, EAST_INSTITUTE['center'][1], "OSM 540106546"),
    ("east institute length", 96.0, EAST_INSTITUTE['length'], "OSM 540106546"),
]
