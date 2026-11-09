"""V11 Academic Building structural reconstruction (owner screenshots 07/08/11/13/14/16).

Evidence classes (see references/SOURCE_EVIDENCE.md, V11 section):
  OWNER CONFIRMED  two large stairs reach an upper walking level; that level is an open
                   terrace with a void overlooking the ground floor, guarded by railings;
                   the ground floor is an open passage to the inner court; the rear of the
                   court connects to the rear open area; ~6 Academic entrances (A, C, +~4).
  PHOTO VERIFIED   P09 (camera on the central deck: rails + planters at both deck corners,
                   stairs descending left/right), P15 (deep stone bridge/portal into the
                   court), P12 (Gate (C) tall glazed bay on a curved stone face),
                   P14 (UST panel + "Gate (F)", flush in stone beside a glass box, 8-10 steps).
  OWNER MARK (interpretation, ESTIMATED)
                   11: red line ~10 m in front of the core = terrace front edge; red bracket on
                   the court side = missing upper hall projecting ~21 m into the court, ~34 m
                   wide; five X marks on the outer ring = entrance positions (two side-wing
                   corners, two rear diagonals, rear centre).
                   14: stair foot far out in the forecourt, terrace along the glazed core,
                   two rectangles on the terrace = two openings (voids) in the deck.
Every metric dimension below is an ENGINEERING ESTIMATE; nothing here is surveyed.

Entrance names: only names read from photos are written on the model (Gate (A) D05/P09,
Gate (C) P12, UST / Gate (F) P14). The assignment of C and F to particular X marks assumes
sequential lettering counter-clockwise from Gate (A) (A north, F at the +X corner, which is
consistent with P14's dome-on-the-right sightline). Unnamed entrances carry no letter.
"""
import math, json
from pathlib import Path
import bpy
from shapely.geometry import box
from shapely import union_all
from .geometry import MeshBuilder, Edge, get_collection, parent_keep, arc_points

DECK_Z0, DECK_Z1 = 4.20, 4.41          # upper walking level (unchanged V10 level)
TER_FRONT = -219.0                      # owner 11 red line: terrace front edge (ESTIMATED)
PASS_HALF = 7.0                         # lower passage half-width
STAIR_IN, STAIR_OUT = 7.0, 19.5         # each flight spans |x| 7.0..19.5 (12.5 m; V10 10.5 m)
RISERS, RISE, TREAD = 28, .15, .36      # 4.2 m rise; 10.08 m run
VOID_A = (-5.8, -229.5, 5.8, -221.5)    # open-air void in the front terrace
VOID_B = (-5.8, -266.0, 5.8, -235.0)    # covered void in the hall / bridge
BRIDGE_HALF, BRIDGE_END = 16.4, -270.0  # owner 11 bracket: upper hall into the court
BRIDGE_TOP = 15.8                       # two storeys above the deck soffit (ESTIMATED)
RAIL_H = 1.10

ENTRANCES = []   # filled by the builders; exported as references/academic_entrances_v11.json


def _register(**kw):
    ENTRANCES.append(kw)


# ----------------------------------------------------------------------------- rails
def balustrade(mb, M, p0, p1, z, glass=True):
    """Metal posts + handrail + laminated glass infill (collidable as one object)."""
    e = Edge(p0, p1)
    n = max(1, int(math.ceil(e.L / 1.6)))
    for i in range(n + 1):
        p = e.at(e.L * i / n)
        mb.box(M['metal_light'], p.x - .035, p.y - .035, z, p.x + .035, p.y + .035, z + RAIL_H)
    mb.fbox(M['metal_light'], e, e.L / 2, -.04, .08, e.L, z + RAIL_H - .05, z + RAIL_H + .02)
    # Light open rails (V11 review: dark glass infill read as solid black walls). Gaps of
    # <= 0.3 m still stop the player capsule; the whole object is collidable.
    for zz in (.12, .42, .72):
        mb.fbox(M['metal_light'], e, e.L / 2, -.02, .04, e.L, z + zz, z + zz + .035)


def rect_rail(mb, M, r, z, skip=()):
    x0, y0, x1, y1 = r
    sides = {'s': ((x0, y0), (x1, y0)), 'e': ((x1, y0), (x1, y1)), 'n': ((x1, y1), (x0, y1)), 'w': ((x0, y1), (x0, y0))}
    for k, (a, b) in sides.items():
        if k not in skip:
            balustrade(mb, M, a, b, z)


# ----------------------------------------------------------------------------- core
def core(P, M, A):
    """Core between the prongs: lower passage, upper terrace, covered hall, court bridge."""
    from .v6_academic import polygon_prism
    px0 = A['prong_x'][0]
    cy = A['curve_c'][1]
    st = M['stone']
    G = .21
    # Ground floor: enclosed side lobbies flank the open lower passage (|x| < PASS_HALF).
    for sx in (-1, 1):
        lo, hi = sorted((sx * PASS_HALF, sx * px0))
        P.rblock(lo, cy, hi, TER_FRONT, G, DECK_Z0)
        # Lobby glazing on the passage faces and the court face (behind the bridge piers).
        fx = sx * PASS_HALF
        e = Edge((fx, TER_FRONT - 1.0), (fx, cy + 1.0)) if sx > 0 else Edge((fx, cy + 1.0), (fx, TER_FRONT - 1.0))
        # Edge normal must face the passage (towards x = 0).
        if e.n.x * sx > 0:
            e = Edge(e.p1, e.p0)
        P.curtain(e, .4, e.L - .4, G + .05, DECK_Z0 - .15, mull=2.4, transom=3.9, off=.03)
        for k in range(3):   # glazed lobby doors (dark frames) along the passage
            s = e.L * (k + 1) / 4
            P.det.fbox(M['metal'], e, s, .03, .12, 2.6, G, 3.0)
    # Upper floor plate: front terrace + covered hall + bridge, minus the two voids.
    plate = union_all([box(-px0, cy, px0, TER_FRONT), box(-BRIDGE_HALF, BRIDGE_END, BRIDGE_HALF, cy)])
    plate = plate.difference(box(*VOID_A)).difference(box(*VOID_B))
    polygon_prism(P.shell, st, plate, DECK_Z0, DECK_Z1)
    # Finished deck surface in honed light granite (walkable top), dark granite void copings.
    polygon_prism(P.det, M['plaza_light'], plate.buffer(-.01), DECK_Z1 - .005, DECK_Z1 + .005)
    for v in (VOID_A, VOID_B):
        ring_ = box(*v).buffer(.35, join_style=2).difference(box(*v))
        polygon_prism(P.det, M['granite'], ring_, DECK_Z1, DECK_Z1 + .06)
    # Bridge piers (P15 deep portal) and the upper hall volume over the court.
    for x in (-15.8, -7.6, 7.6, 15.8):
        for y in (BRIDGE_END + .7, -259.5):
            P.shell.box(st, x - .7, y - .7, 0.0, x + .7, y + .7, DECK_Z0)
    P.rblock(-BRIDGE_HALF, BRIDGE_END, BRIDGE_HALF, cy, 7.4, BRIDGE_TOP)
    P.parapet([(-BRIDGE_HALF, BRIDGE_END), (BRIDGE_HALF, BRIDGE_END), (BRIDGE_HALF, cy), (-BRIDGE_HALF, cy)], BRIDGE_TOP)
    ce = Edge((BRIDGE_HALF, BRIDGE_END), (-BRIDGE_HALF, BRIDGE_END))   # court face (normal -Y)
    # P15 shows a blank stone bridge face with two thin horizontal course joints,
    # not the large glazed curtain wall used by the interrupted V11 draft.
    for zz in (10.3, 12.9):
        P.det.fbox(M['band'], ce, ce.L / 2, .006, .014, ce.L, zz, zz + .025)
    for sx in (-1, 1):
        se = Edge((sx * BRIDGE_HALF, cy), (sx * BRIDGE_HALF, BRIDGE_END)) if sx > 0 else Edge((sx * BRIDGE_HALF, BRIDGE_END), (sx * BRIDGE_HALF, cy))
        P.window_rows(se, [8.6, 12.4], w=1.4, h=2.4, spacing=2.2, margin=1.5)
    # Light stone soffit under the hall and bridge (deep P15 soffit read).
    P.det.box(M['plaza_light'], -BRIDGE_HALF, BRIDGE_END, 7.34, BRIDGE_HALF, cy, 7.4)
    P.det.box(M['plaza_light'], -px0, cy, 7.34, px0, -232., 7.4)
    # Downlights in the soffits (emissive squares; real lights come from v7_lighting).
    for x in (-11., -3., 3., 11.):
        for y in (-236., -243., -252., -262.):
            if abs(x) < BRIDGE_HALF:
                P.det.box(M['lamp'], x - .25, y - .25, 7.3, x + .25, y + .25, 7.34)
    _register(id='A', name='Gate (A)', name_ar='البوابة (أ)', level='ground + upper terrace',
              position_blender=[0.0, TER_FRONT, DECK_Z1], orientation_deg=90.0,
              connected_walkway='forecourt → two great stairs → terrace; lower passage → inner court',
              evidence='PHOTO VERIFIED name/form (D05, P09); geometry ESTIMATED', traversal='walk-through (passage) + both stairs',
              label=True)
    _register(id='HALL', name='Upper hall / court bridge', name_ar='القاعة العلوية', level='upper (4.41 m)',
              position_blender=[0.0, -258.0, DECK_Z1], orientation_deg=270.0,
              connected_walkway='terrace → covered hall → bridge overlook', evidence='OWNER MARK 11 + P15 bridge; dimensions ESTIMATED',
              traversal='walkable deck with railed voids', label=False)
    return plate


def rails_and_planters(M, C, root, plate):
    """Collidable balustrades (voids, terrace front, bridge edges) and P09 deck planters."""
    mb = MeshBuilder()
    z = DECK_Z1
    rect_rail(mb, M, VOID_A, z)
    rect_rail(mb, M, VOID_B, z)
    # Terrace front between the two stair heads (P09: rail + planter at the deck corners).
    balustrade(mb, M, (STAIR_IN, TER_FRONT + .12), (-STAIR_IN, TER_FRONT + .12), z)
    # Bridge edges over the court and the hall's exposed back edge beside the bridge.
    balustrade(mb, M, (-BRIDGE_HALF + .12, BRIDGE_END + .12), (BRIDGE_HALF - .12, BRIDGE_END + .12), z)
    for sx in (-1, 1):
        x = sx * (BRIDGE_HALF - .12)
        balustrade(mb, M, (x, BRIDGE_END + .12), (x, -249.12), z)
        balustrade(mb, M, (sx * BRIDGE_HALF, -249.12), (sx * 19.7, -249.12), z)
    for sx in (-1, 1):   # concrete planters at the deck corners beside each stair head (P09)
        x0, x1 = sorted((sx * 4.2, sx * 6.85))
        mb.box(M['plaza_light'], x0, TER_FRONT + .25, z, x1, TER_FRONT + 1.55, z + .78)
        mb.box(M['soil'] if 'soil' in M else M['granite'], x0 + .12, TER_FRONT + .37, z + .78, x1 - .12, TER_FRONT + 1.43, z + .8)
        for k in range(4):
            cx = x0 + .45 + k * (x1 - x0 - .9) / 3
            mb.cylinder(M['hedge'] if 'hedge' in M else M['lawn'], (cx, TER_FRONT + .9), z + .8, z + 1.25, .32, .2, segs=8)
    o = mb.to_object('Academic_V11_Balustrades', C['academic_stairs'])
    parent_keep(o, root)
    o['zc_collision'] = True
    o['zc_evidence'] = 'Owner: railings around real drop-offs (terrace, voids, bridge). P09: rail + planter at the deck corners. Heights 1.1 m; layout ESTIMATED.'
    # Front fascia between the stairs carries the D05 "Gate (A)" lettering.
    fas = MeshBuilder()
    fas.box(M['stone'], -STAIR_IN, TER_FRONT - .1, 3.25, STAIR_IN, TER_FRONT + .5, DECK_Z1)
    fas.box(M['band'], -STAIR_IN, TER_FRONT + .5, 3.25, STAIR_IN, TER_FRONT + .53, 3.37)
    from .gate import FONT_LAT, _on_face, _text_mesh
    me = _text_mesh("Gate (A)", FONT_LAT, .5)
    if me:
        fas.add_mesh(M['band'], me, _on_face(0.0, 3.55, TER_FRONT + .54))
    o = fas.to_object('Academic_V11_GateA_Fascia', C['academic_entry'])
    parent_keep(o, root)
    o['zc_collision'] = True
    o['zc_evidence'] = 'D05 "Gate (A)" lettering on the lower fascia above the passage between the stairs; size ESTIMATED from D05 proportions.'


def build_stairs(M, C, root):
    """Two great stairs from the forecourt to the terrace front edge (owner: larger, and
    reaching the upper level; P09: rails, flights descending left/right of the deck)."""
    from .v6_academic import rail_stairs
    back = TER_FRONT
    front = back + RISERS * TREAD
    top = .21 + RISERS * RISE
    for side in (-1, 1):
        mb = MeshBuilder()
        lo, hi = sorted((side * STAIR_IN, side * STAIR_OUT))
        for k in range(RISERS):
            mb.box(M['stone'], lo, front - (k + 1) * TREAD, -.15, hi, front - k * TREAD, .21 + (k + 1) * RISE)
        # Dark granite nosing strip on every tread (contrast; reads as real stone stair).
        for k in range(RISERS):
            y = front - k * TREAD
            mb.box(M['granite'], lo + .05, y - .05, .21 + (k + 1) * RISE - .01, hi - .05, y, .21 + (k + 1) * RISE + .004)
        rail_stairs(mb, M, lo, hi, front, back, top)
        # Mid-flight handrail every ~6 m of width (wide public stair).
        mid = (lo + hi) / 2
        for k in range(11):
            t = k / 10; y = front + (back - front) * t; zz = .21 + (top - .21) * t
            mb.cylinder(M['metal_light'], (mid, y), zz, zz + .95, .027, segs=8)
        mb.box(M['stone'], lo, back - 3., DECK_Z0, hi, back, DECK_Z1)
        obj = mb.to_object('Academic_Stair_' + ('Left' if side < 0 else 'Right'), C['academic_stairs'])
        parent_keep(obj, root)
        obj['zc_collision'] = True
        obj['zc_risers'] = RISERS
        obj['zc_riser_height_m'] = RISE
        obj['zc_tread_m'] = TREAD
        obj['zc_width_m'] = hi - lo
        obj['zc_evidence'] = ('V11: owner (stairs too small/misplaced; must reach the upper terrace) + P09 rails. '
                              'Foot y %.2f, head y %.2f, width %.1f m, 28 x 0.15 m: ESTIMATED.' % (front, back, hi - lo))


# ----------------------------------------------------------------------------- ring entrances
RING_ENTRANCES = {   # angle on the outer ring (deg) -> spec; owner 11 X marks
    225.: dict(id='C', name='Gate (C)', name_ar='البوابة (ج)', label=True,
               evidence='P12 PHOTO VERIFIED form/name; position = owner X mark + sequential-lettering hypothesis (ESTIMATED)'),
    315.: dict(id='E?', name='Academic entrance (name unverified)', name_ar='مدخل', label=False,
               evidence='Owner X mark; form copied from P12 (ESTIMATED); name UNVERIFIED'),
}
RING_SPAN_DEG = 4.2


def ring_window_skip(angle_deg):
    """True where V11 entrance bays replace the punched windows of the outer ring."""
    for a in RING_ENTRANCES:
        if abs(angle_deg - a) < RING_SPAN_DEG + .6:
            return True
    return False


def ring_entrances(P, M, A):
    cx, cy = A['curve_c']; ro = A['r_out']
    from .gate import FONT_LAT, _text_mesh
    from mathutils import Matrix
    for a, spec in RING_ENTRANCES.items():
        p0 = (cx + (ro + .05) * math.cos(math.radians(a - RING_SPAN_DEG)), cy + (ro + .05) * math.sin(math.radians(a - RING_SPAN_DEG)))
        p1 = (cx + (ro + .05) * math.cos(math.radians(a + RING_SPAN_DEG)), cy + (ro + .05) * math.sin(math.radians(a + RING_SPAN_DEG)))
        e = Edge(p0, p1)
        L = e.L
        # P12: tall dark-framed glazed bay, ~4 storeys, 3 bays, stone frame.
        P.frame(e, .9, L - .9, .66, 16.4, t=.9, depth=1.3)
        P.curtain(e, .9, L - .9, 4.6, 16.4, mull=(L - 1.8) / 3, transom=3.95, off=.3, mat=M['court_glass'])
        for k in (1, 2):
            P.det.fbox(M['band'], e, .9 + (L - 1.8) * k / 3, .3, .55, .5, .66, 16.4)
        # Two door pairs at the base (P12), dark metal transom bar under the sign.
        for s in (L * .33, L * .67):
            P.curtain(e, s - 1.6, s + 1.6, .66, 3.6, mull=1.6, transom=2.94, off=.32)
            P.det.fbox(M['metal'], e, s, .32, .2, 3.4, 3.6, 3.75)
        P.curtain(e, .9, L * .33 - 1.7, .66, 4.6, mull=1.5, transom=3.94, off=.3, mat=M['court_glass'])
        P.curtain(e, L * .33 + 1.7, L * .67 - 1.7, .66, 4.6, mull=1.5, transom=3.94, off=.3, mat=M['court_glass'])
        P.curtain(e, L * .67 + 1.7, L - .9, .66, 4.6, mull=1.5, transom=3.94, off=.3, mat=M['court_glass'])
        P.det.fbox(M['metal'], e, L / 2, .3, .3, L - 1.8, 4.5, 4.75)
        if spec['label']:
            me = _text_mesh(spec['name'], FONT_LAT, .55)
            if me:
                p = e.at(L / 2, .42)
                P.det.add_mesh(M['stone_plain'], me, Matrix.Translation((p.x, p.y, 5.6)) @ Matrix.Rotation(e.angle, 4, 'Z') @ Matrix.Rotation(math.pi / 2, 4, 'X'))
        # Landing + three steps (step k: 0.42*(k+1) deep, top 0.66-0.15*(k+1); the outermost is the
        # lowest - Codex review fixed the V11 draft that buried the lower steps) + flank rails (P12).
        P.shell.fbox(M['stone'], e, L / 2, 0., 2.6, L - 2.4, .0, .66)
        for k in range(3):
            P.shell.fbox(M['stone'], e, L / 2, 2.6, .42 * (k + 1), L - 2.4 + (3 - k) * .3, -.1, .66 - (k + 1) * .15)
        # P12: slender metal flank rails beside the steps (V11 Wave 5 review).
        for s in (1.0, L - 1.0):
            for k in range(6):
                t = k / 5; off = .2 + 3.66 * t; z0 = .66 - .45 * max(0., (off - 2.6) / 1.26)
                p = e.at(s, off)
                P.det.cylinder(M['metal_light'], (p.x, p.y), z0, 1.66, .028, segs=8)
            P.det.fbox(M['metal_light'], e, s, .2, 3.66, .06, 1.62, 1.68)
        _register(id=spec['id'], name=spec['name'], name_ar=spec['name_ar'], level='ground (+0.66 landing)',
                  position_blender=[round(e.at(L / 2, 1.).x, 2), round(e.at(L / 2, 1.).y, 2), .66], orientation_deg=round(math.degrees(e.angle) - 90, 1),
                  connected_walkway='rear campus walk', evidence=spec['evidence'], traversal='reach the doors (no interior modelled)',
                  label=spec['label'])


def side_wing_entrances(P, M, A):
    """Owner X marks at both side-wing corners. +X corner = UST / Gate (F) (P14, owner 13:
    corner position); -X corner = unnamed side entrance."""
    from .gate import FONT_LAT, _text_mesh
    from .buildings import face_px, face_nx
    from mathutils import Matrix
    cx, cy = A['curve_c']; ro = A['r_out']; ys = A['side_front_y']
    # ---- +X: UST panel (flush black, ~6 x 23 m) beside a projecting glass box toward the corner.
    e, lo = face_px(cy, ys, ro)              # s = y - cy
    s_p = (-223.0) - cy                      # panel centre at y -223 (ESTIMATED)
    P.frame(e, s_p - 3.0, s_p + 3.0, .21, 22.4, t=.6, depth=.35)
    P.det.fbox(M['band'], e, s_p, 0., .1, 6.0, 1.7, 22.4)
    P.curtain(e, s_p - 2.6, s_p + 2.6, 1.7, 4.6, mull=1.3, transom=2.9, off=.11)
    for words, z, size in (('UST', 12.0, 2.25), ('Gate (F)', 4.95, .45)):
        me = _text_mesh(words, FONT_LAT, size)
        if me:
            p = e.at(s_p, .23)
            P.det.add_mesh(M['stone_plain'], me, Matrix.Translation((p.x, p.y, z)) @ Matrix.Rotation(e.angle, 4, 'Z') @ Matrix.Rotation(math.pi / 2, 4, 'X'))
    # Glass box toward the front corner (P14).
    s_g0, s_g1 = s_p + 4.4, e.L - 1.4
    P.det.fbox(M['stone'], e, (s_g0 + s_g1) / 2, 0., 2.2, s_g1 - s_g0 + .6, 5.0, 5.6)
    P.det.fbox(M['stone'], e, (s_g0 + s_g1) / 2, 0., 2.2, s_g1 - s_g0 + .6, 19.0, 19.5)
    P.curtain(e, s_g0, s_g1, 5.6, 19.0, mull=1.9, transom=3.35, off=2.0)
    # Nine steps (P14: 8-10) up to a 1.56 m landing, with side rails.
    n = 9; land = .21 + n * .15
    P.shell.fbox(M['stone'], e, s_p, 0., 2.2, 6.0, .21, land)
    for k in range(n):
        P.shell.fbox(M['stone'], e, s_p, 2.2, .38 * (n - k), 6.0, -.1, .21 + (k + 1) * .15)
    for d in (-3.1, 3.1):
        for k in range(8):
            t = k / 7; off = 2.2 + .38 * n * t; z0 = land - (land - .21) * t
            p = e.at(s_p + d, off)
            P.det.cylinder(M['metal_light'], (p.x, p.y), z0, z0 + 1.0, .027, segs=8)
    _register(id='F', name='UST / Gate (F)', name_ar='UST / البوابة (و)', level='ground (+1.56 landing)',
              position_blender=[round(ro + 4.0, 2), -223.0, land], orientation_deg=0.0,
              connected_walkway='east walk to the dormitory approach', evidence='P14 PHOTO VERIFIED form + names; owner 13 corner position; exact face ESTIMATED',
              traversal='nine steps to the doors (no interior modelled)', label=True)
    # ---- -X corner: unnamed side entrance (owner X mark).
    e2, hi = face_nx(cy, ys, -ro)            # s = y_hi - y
    s_b = ys - (-226.0)
    P.frame(e2, s_b - 3.2, s_b + 3.2, .66, 8.6, t=.7, depth=1.0)
    P.curtain(e2, s_b - 3.2, s_b + 3.2, 4.6, 8.6, mull=1.6, transom=4., off=.05)
    P.curtain(e2, s_b - 3.2, s_b + 3.2, .66, 4.4, mull=1.6, transom=2.9, off=.05)
    P.det.fbox(M['metal'], e2, s_b, .05, .25, 6.4, 4.4, 4.6)
    P.shell.fbox(M['stone'], e2, s_b, 0., 2.4, 7.0, .0, .66)
    for k in range(3):
        P.shell.fbox(M['stone'], e2, s_b, 2.4, .42 * (k + 1), 7.0, -.1, .66 - (k + 1) * .15)
    _register(id='B?', name='Academic side entrance (name unverified)', name_ar='مدخل جانبي', level='ground (+0.66 landing)',
              position_blender=[-ro - 3.5, -226.0, .66], orientation_deg=180.0, connected_walkway='west walk',
              evidence='Owner X mark (11); form ESTIMATED; name UNVERIFIED', traversal='reach the doors', label=False)
    return (s_p - 3.6, s_g1 + .4), (s_b - 4.0, s_b + 4.0)


def rear_passage(P, M, A):
    """Owner 09: the court must connect to the rear open area. The V5-V10 aperture
    (arc 266-274 deg) stays open; V11 replaces the blank tunnel walls by glazed lobby
    returns and adds a light soffit with downlights."""
    cx, cy = A['curve_c']; ro = A['r_out']; ri = ro - A['ring_depth']
    for a, sgn in ((266., 1), (274., -1)):
        r0, r1 = ri + .6, ro - .4
        u = (cx + r0 * math.cos(math.radians(a)), cy + r0 * math.sin(math.radians(a)))
        v = (cx + r1 * math.cos(math.radians(a)), cy + r1 * math.sin(math.radians(a)))
        # Normal must face into the passage (266 deg face looks +X, 274 deg face looks -X).
        e = Edge(v, u) if sgn > 0 else Edge(u, v)
        P.curtain(e, .3, e.L - .3, .26, 7.0, mull=2.3, transom=3.4, off=.05)
    pts = arc_points(cx, cy, (ri + ro) / 2, 266.5, 273.5, 4)
    for p in pts:
        P.det.box(M['lamp'], p[0] - .25, p[1] - .25, 7.35, p[0] + .25, p[1] + .25, 7.4)
    _register(id='D?', name='Rear passage (name unverified)', name_ar='الممر الخلفي', level='ground',
              position_blender=[0.0, cy - ro - 2.0, .21], orientation_deg=270.0,
              connected_walkway='inner court ↔ rear campus (owner 09)', evidence='OWNER CONFIRMED connection; opening width/height ESTIMATED',
              traversal='walk-through', label=False)


def write_registry():
    out = Path(__file__).resolve().parents[2] / 'references' / 'academic_entrances_v11.json'
    out.write_text(json.dumps({'classification': 'ACADEMIC BUILDING ENTRANCES (independent of perimeter gates G1-G6)',
                               'lettering_hypothesis': 'Sequential lettering counter-clockwise from Gate (A); only A, C, F names are photo-read.',
                               'entrances': ENTRANCES}, indent=2, ensure_ascii=False), encoding='utf-8')
    return out
