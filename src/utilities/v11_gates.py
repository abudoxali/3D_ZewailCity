"""V11 perimeter gate family (owner screenshots 02/04/06) and interactive gate leaves.

G1 (PHOTO VERIFIED form, C01/C02/D02): the lane leaves stand in the gatehouse plane, ~5.7 m
outside the portal frame. V4-V10 left the strip between each lane's outer post and the
portal leg open, so a closed leaf could be walked around (owner 02). V11 adds stone return
walls from each lane post back to the portal leg (ESTIMATED; C01/C02 do not show that strip
clearly) and makes both lane leaves separate sliding objects that move parallel to the
gatehouse plane (C02: right lane closed, left lane open).

G2-G6 (owner 06): no photograph exists. They now share G1's architectural language - stone
pylons with the dark ledgestone inverted-U inlay, a lintel carrying the gate number, black
lattice sliding leaves and a framed pedestrian bay - scaled to each mapped opening. This is a
CONCEPTUALLY STANDARDISED design (ESTIMATED), not an as-built record.

Interactive leaves are exported as separate meshes whose names encode the slide:
  GATELEAF_<gate>_<leaf>_dx<cm>_dy<cm>_s<1 closed | 0 open at start>
(Blender metres; the Godot gate controller converts to (dx, 0, -dy)).
"""
import json
import math
from pathlib import Path
import bpy
from .geometry import MeshBuilder, get_collection
from . import survey as SV

ROOT = Path(__file__).resolve().parents[2]
LEAF_COLL = 'V11_Gate_Leaves'
LEAF_PLANE = -1.20  # overlaps the 2.4 m pylon depth; no leaf-to-pylon seam
REGISTRY = []


def leaf_name(gid, leaf, dx, dy, closed):
    return 'GATELEAF_%s_%s_dx%d_dy%d_s%d' % (gid, leaf, round(dx * 100), round(dy * 100), 1 if closed else 0)


def emit_leaf(mb, gid, leaf, dx, dy, closed, evidence, ang=0.0):
    coll = get_collection(LEAF_COLL)
    o = mb.to_object(leaf_name(gid, leaf, dx, dy, closed), coll)
    # Codex review (V11): the leaf mesh is axis-aligned in its own frame and the object carries
    # the rotation, so Godot's box collider (fitted to the local AABB) follows an angled leaf.
    if abs(ang) > 1e-6:
        from mathutils import Matrix
        o.data.transform(Matrix.Rotation(-ang, 4, 'Z'))
        o.rotation_euler = (0.0, 0.0, ang)
    o['zc_gate_id'] = gid
    o['zc_leaf'] = leaf
    o['zc_slide_m'] = [dx, dy]
    o['zc_start_closed'] = bool(closed)
    o['zc_evidence'] = evidence
    return o


def lattice_leaf(mb, M, p0, p1, z0, h=3.9, t=0.16):
    """C01/C02 black lattice leaf between plan points p0..p1 (any orientation): frame,
    vertical bars below 2.45 m, square lattice above."""
    st = M['steel_dark']
    L = math.dist(p0, p1)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    ux, uy = math.cos(ang), math.sin(ang)

    def bar(s0, s1, za, zb, th=t):
        c = ((s0 + s1) / 2)
        mb.obox(st, (p0[0] + ux * c, p0[1] + uy * c, z0 + (za + zb) / 2), (s1 - s0, th, zb - za), ang)
    bar(0, L, .08, .2); bar(0, L, h - .12, h); bar(0, L, 2.45, 2.55)
    for s in (0, L):
        bar(s - .07, s + .07, .08, h)
    n = max(2, int(L / .17))
    for k in range(1, n):
        s = L * k / n
        bar(s - .02, s + .02, .2, 2.45, .04)
    m = max(2, int(round(L / .32)))
    for k in range(1, m):
        s = L * k / m
        bar(s - .025, s + .025, 2.55, h - .12, .06)
    for z in (2.85, 3.15, 3.45):
        bar(0, L, z - .025, z + .025, .06)


# ----------------------------------------------------------------------------- G1
def g1_lane_system(P, M):
    """Return walls + interactive leaves for G1 (replaces the static V4-V10 leaves)."""
    GY = SV.GATE_Y
    D = SV.PORTAL['depth']
    y1 = GY + D / 2.0                 # outer face of the portal legs
    yg = SV.GATEHOUSE['y0'] + 2.5     # lane-gate plane (V4 C01/C02 interpretation)
    l0, l1 = SV.LANE_HALF             # 7.0 .. 11.9
    gs = M['gate_stone']
    for sx in (-1, 1):
        lo, hi = sorted((sx * (l1 - .05), sx * (l1 + .55)))
        # Stone return wall: lane post -> portal leg (closes the owner-02 bypass).
        P.shell.box(gs, lo, y1 - .3, -.45, hi, yg - .17, 4.1)
        P.det.box(M['ledgestone'], lo - .01, y1, .0, hi + .01, yg - .17, .45)
        P.det.box(M['band'], lo - .02, y1, 3.55, hi + .02, yg - .17, 3.75)
        # Lane post at the meeting edge (gatehouse side) and at the outer edge.
        for x in (sx * (l0 + .06), sx * (l1 + .12)):
            P.det.box(M['steel_dark'], x - .12, yg - .15, 0.0, x + .12, yg + .15, 4.1)
    for sx, leaf, closed in ((1, 'E', True), (-1, 'W', False)):
        mb = MeshBuilder()
        a, b = sx * (l0 + .18), sx * (l1 + .02)
        lattice_leaf(mb, M, (a, yg), (b, yg), 0.0)
        span = abs(b - a) + .1
        dx = sx * span
        if not closed:   # built in the closed position, then parked open (slid outward)
            for v in mb.bm.verts:
                v.co.x += dx
        o = emit_leaf(mb, 'G1', leaf, dx, 0.0, closed, 'C02: right lane closed, left lane open; sliding leaf in the gatehouse plane. Slide travel ESTIMATED.')
        o['zc_closed_offset'] = [0.0, 0.0] if closed else [-dx, 0.0]
    REGISTRY.append({'id': 'G1', 'leaves': ['E', 'W', 'PedE', 'PedW'], 'start': {'E': 'closed', 'W': 'open', 'PedE': 'open', 'PedW': 'open'},
                     'return_walls': 'stone, lane post -> portal leg, both sides (V11 ESTIMATED)',
                     'evidence': 'PHOTO_AND_MAP (C01/C02/D02/D03); return walls and slide travel ESTIMATED'})


def g1_pedestrian_leaf(M, sx):
    """Keep the photographed pedestrian bays usable initially, close them with G1.

    Sliding operation is estimated. Previously the static parked doors were never
    controlled, so 'close G1' left two walk-through perimeter openings.
    """
    mb = MeshBuilder()
    travel = sx * 2.6
    lattice_leaf(mb, M, (sx * 17.76, SV.GATE_Y), (sx * 20.24, SV.GATE_Y), 0.0, h=3.8)
    for vert in mb.bm.verts:
        vert.co.x += travel
    emit_leaf(mb, 'G1', 'PedE' if sx > 0 else 'PedW', travel, 0.0, False,
              'C01/C02 pedestrian bay; sliding travel and shared operation ESTIMATED.')


# ----------------------------------------------------------------------------- G2-G6
def wing_half(c):
    """Half-length of a V11 secondary gate assembly along the wall (perimeter cut radius)."""
    w = c['opening_width'] / 2
    return 2 * w + .9 + 1.2 + c['pedestrian_width'] + 2.6


def v11_parameters(c):
    """V11 gate-family parameters (single source for the scene build and gate_inventory)."""
    c = dict(c)
    c.update(v11_leg_width=2.4, v11_portal_height=9.6, v11_lintel=2.2, wall_connection_half=wing_half(c),
             v11_family='G1 portal language (stone pylons, ledgestone inlay, lintel number, lattice leaves)')
    return c


def secondary(M, C):
    """Monumental G1-family gates for G2-G6 (owner 06). Replaces v8_gates.build geometry."""
    from .architecture import Parts
    from .gate_inventory import RECORDS, write
    from .ground_system import datum
    from .v8_gates import configuration, axes, xy, graded_prism
    from .gate import FONT_LAT, _text_mesh
    from mathutils import Matrix
    for r in RECORDS[1:]:
        c = configuration(r)
        u, v = axes(r, c)
        w = c['opening_width'] / 2
        leg, depth, H, lintel = 2.4, 2.4, 9.6, 2.2          # ESTIMATED G1 proportions scaled
        ped = c['pedestrian_width']
        # Parked-open leaves rest in front of solid wing wall; the pedestrian bay starts
        # beyond the parked leaf so an open leaf never blocks it.
        p0 = 2 * w + .9
        whalf = wing_half(c)                                # wing ends (ped bay + pier)
        c = v11_parameters(c)
        P = Parts(r['object'], M)
        base = datum(*r['model_position_blender_m']) + c['threshold_offset']
        ang = c['orientation']

        def block(mb, mat, s, t, z, width, dep, height):
            x, y = xy(r, u, v, s, t)
            mb.obox(mat, (x, y, base + z + height / 2), (width, dep, height), ang)
        # Pylons with footings, ledgestone inverted-U inlay on both faces (G1 C01/C02).
        for sgn in (-1, 1):
            sc = sgn * (w + leg / 2)
            x, y = xy(r, u, v, sc, 0)
            bottom = datum(x, y) - .45
            block(P.shell, M['curb'], sc, 0, bottom - base, leg + .3, depth + .3, base + .1 - bottom)
            block(P.shell, M['gate_stone'], sc, 0, -.1, leg, depth, H + .1)
            for tf in (-1, 1):
                block(P.det, M['ledgestone'], sc + sgn * .35, tf * (depth / 2 + .012), 0., .32, .03, H - 1.05)
        block(P.shell, M['gate_stone'], 0, 0, H - lintel, 2 * w + .2, depth, lintel)
        for tf in (-1, 1):
            block(P.det, M['ledgestone'], 0, tf * (depth / 2 + .012), H - 1.05 - .32, 2 * w + 2 * leg - 1.4, .03, .32)
        block(P.det, M['roof'], 0, 0, H, 2 * (w + leg) - .2, depth - .2, .03)
        # Gate number on the lintel, both faces ("G2".."G6"; owner: visible gate numbering).
        for tf in (1, -1):
            me = _text_mesh(r['id'], FONT_LAT, 1.1)
            if me:
                x, y = xy(r, u, v, 0, tf * (depth / 2 + .03))
                # Text runs along t with its outward normal = right of t = tf * v.
                tx, ty = (-v[1], v[0]) if tf > 0 else (v[1], -v[0])
                yaw = math.atan2(ty, tx)
                mat = Matrix.Translation((x, y, base + H - lintel / 2 - .45)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(math.pi / 2, 4, 'X')
                P.det.add_mesh(M['stone_plain'], me, mat)
        # Pedestrian bay on the +s side: animated door shares this gate's closed state.
        for s0, s1 in ((p0, p0 + 1.2), (p0 + 1.2 + ped, p0 + 2.2 + ped)):
            block(P.shell, M['gate_stone'], (s0 + s1) / 2, 0, -.1, s1 - s0, .9, 4.4)
        block(P.shell, M['gate_stone'], p0 + 1.2 + ped / 2, 0, 3.6, ped + .2, .9, .8)
        ped_mb = MeshBuilder()
        pa, pb = xy(r, u, v, p0 + 1.16, -.45), xy(r, u, v, p0 + 1.24 + ped, -.45)
        lattice_leaf(ped_mb, M, pa, pb, base, h=3.5)
        pdx, pdy = (ped + .3) * u[0], (ped + .3) * u[1]
        for vert in ped_mb.bm.verts:
            vert.co.x += pdx
            vert.co.y += pdy
        emit_leaf(ped_mb, r['id'], 'Ped', pdx, pdy, False,
                  'V11 estimated pedestrian leaf; closes with the vehicle leaves.',
                  ang=math.atan2(u[1], u[0]))
        # Wing walls to the perimeter cut ends (perimeter() cuts at wall_connection_half).
        for a0, a1 in ((-whalf, -(w + leg)), (w + leg, p0), (p0 + 2.2 + ped, whalf)):
            pa, pb = xy(r, u, v, a0, 0), xy(r, u, v, a1, 0)
            graded_prism(P.shell, M['curb'], pa, pb, .9, -.45, .10)
            graded_prism(P.shell, M['stucco'], pa, pb, .42, -.12, c['wall_height'])
            graded_prism(P.det, M['gate_stone'], pa, pb, .58, c['wall_height'], c['wall_height'] + .16)
        # Flush steel track across the opening (walkable).
        block(P.det, M['steel_dark'], 0, LEAF_PLANE, .0, 2 * w, .07, .012)
        obj = P.finish(C, 'provisional_gates', bevel=.015)
        obj['zc_evidence'] = r['status']
        obj['zc_parameters_v8'] = json.dumps(c)
        obj['zc_note'] = 'V11 G1-family design, conceptually standardised (ESTIMATED); no secondary-gate photograph.'
        # Two sliding leaves inside the pylon line, meeting at the centre when closed.
        for leaf, sgn in (('A', -1), ('B', 1)):
            mb = MeshBuilder()
            sa, sb = (0.0, sgn * (w + .25))
            pa, pb = xy(r, u, v, sa, LEAF_PLANE), xy(r, u, v, sb, LEAF_PLANE)
            lattice_leaf(mb, M, pa, pb, base)
            travel = w + .35
            dx, dy = sgn * travel * u[0], sgn * travel * u[1]
            # G2-G6 start OPEN (keeps the V8-V10 explorer routes); closed state is real.
            for vv in mb.bm.verts:
                vv.co.x += dx; vv.co.y += dy
            o = emit_leaf(mb, r['id'], leaf, dx, dy, False, 'V11 G1-family leaf; dimensions and operation ESTIMATED (no photograph).', ang=math.atan2(u[1], u[0]))
            o['zc_closed_offset'] = [-dx, -dy]
        r.update(appearance='V11 G1-family monumental portal (stone pylons, ledgestone inlay, numbered lintel, lattice leaves); ESTIMATED',
                 pedestrian_route='Framed pedestrian bay with interactive sliding leaf (ESTIMATED)', parameters_v8=c,
                 external_access='UNRESOLVED_SAND_GAP_25M' if r['id'] == 'G2' else 'UNVERIFIED_NO_EXTERNAL_EXTENSION')
        REGISTRY.append({'id': r['id'], 'leaves': ['A', 'B', 'Ped'], 'start': {'A': 'open', 'B': 'open', 'Ped': 'open'},
                         'opening_width_m': round(2 * w, 2), 'portal_height_m': H, 'wall_connection_half_m': round(whalf, 2),
                         'evidence': 'PROVISIONAL_MAP_CLUSTER position; V11 design conceptually standardised from G1 (ESTIMATED)'})
    write()
    out = ROOT / 'output/validation/v11'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'gate_family_v11.json').write_text(json.dumps(REGISTRY, indent=2))
