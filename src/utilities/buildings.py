"""As-built campus buildings, reconstructed from photographs and the site plan.

Evidence IDs refer to references/REFERENCE_SOURCES.md / SOURCE_EVIDENCE.md.
All plan positions come from site_plan.py; heights come from photographs
(A02 elevation scaled by the three-storey parapet, A01 aerial proportions).
Names prefixed AB_ are descriptive labels for as-built structures, not
official building codes (the contractor itself labels the admin both B5 and B8).
"""
import math
import random

from mathutils import Vector

from . import site_plan as SP
from .architecture import GROUND, Parts
from .geometry import Edge, arc_band, arc_points, ccw, poly_edges, rect_poly

G = GROUND


def _xr(a, b):
    return (min(a, b), max(a, b))


def face_py(x0, x1, y):
    """Facade facing +Y between x0..x1; arc length s = x_hi - x."""
    lo, hi = _xr(x0, x1)
    return Edge((hi, y), (lo, y)), hi


def face_ny(x0, x1, y):
    """Facade facing -Y; s = x - x_lo."""
    lo, hi = _xr(x0, x1)
    return Edge((lo, y), (hi, y)), lo


def face_px(y0, y1, x):
    """Facade facing +X; s = y - y_lo."""
    lo, hi = _xr(y0, y1)
    return Edge((x, lo), (x, hi)), lo


def face_nx(y0, y1, x):
    """Facade facing -X; s = y_hi - y."""
    lo, hi = _xr(y0, y1)
    return Edge((x, hi), (x, lo)), hi


# =============================================================================
#  Administration & Cultural Building  (plan bldg 4)
# =============================================================================
def admin_cultural(M, C):
    """Symmetric rectilinear building with copper drum + dome (A01-A04, B01, B04).

    From the axis outward (A01 aerial, A02 elevation): flat-roofed entrance portico
    on slender columns; central block with tall stone piers and dark curtain wall;
    lower lateral sections with framed dark glass; side volumes with full-height
    dark glass slots; open stone portal frames; low arms projecting toward the
    gate; small end pavilions joined by bridges. Behind the dome a stepped
    (auditorium-like) roof rises to a rear block (A01, B01)."""
    P = Parts("AB_Administration_Cultural_Building", M)
    st, band, cu = M['stone'], M['band'], M['copper']
    yF = SP.ADMIN['front_y']            # 21.4
    yPo = SP.ADMIN['portico_front_y']   # 29.8
    yA = SP.ADMIN['arm_front_y']        # 33.9

    # ---- massing -----------------------------------------------------------
    # V10: the central block, front portico, entrance steps/ramp, central curtain
    # walls and tower piers live in v10_admin_entrance (single owner module).
    from . import v10_admin_entrance
    v10_admin_entrance.build(P, M)
    P.rblock(-24, -36, 24, -16, G, 18.0)
    P.parapet(rect_poly(-24, -36, 24, -16), 18.0)
    for sx in (-1, 1):
        lo, hi = _xr(sx * 18, sx * 29.8)
        P.rblock(lo, -16, hi, yF, G, 15.7)
        P.parapet(rect_poly(lo, -16, hi, yF), 15.7)
        lo, hi = _xr(sx * 29.8, sx * 38)
        P.rblock(lo, -16.7, hi, -1.8, G, 16.5)
        P.parapet(rect_poly(lo, -16.7, hi, -1.8), 16.5)

    # ---- lateral sections (A02: dark glass strip, framed ground floor, upper band)
    for sx in (-1, 1):
        e, hi = face_py(sx * 18, sx * 29.8, yF)
        s = lambda x: hi - x  # noqa: E731
        a, b = sorted((s(sx * 18.4), s(sx * 22.4)))
        P.curtain(e, a, b, 1.0, 15.0, mull=1.0, transom=3.0)
        a, b = sorted((s(sx * 23.4), s(sx * 28.9)))
        P.frame(e, a, b, G, 8.0, t=0.8, depth=1.6)
        P.curtain(e, a, b, G + 0.05, 8.0, mull=1.8, transom=4.0, off=0.6)
        P.curtain(e, a, b, 9.4, 12.6, mull=1.8, transom=3.2)
        P.det.fbox(M['metal_light'], e, (a + b) / 2, 0.0, 0.5, b - a, 10.4, 10.5)   # balcony rail
        P.band(e, 0.0, e.L, 13.6, 14.4)
        # side volume with the tall dark glass slot (A01: dark bays either side)
        # V3 (A03 mismatch): two adjacent full-height dark slots separated by a stone pier
        e2, hi2 = face_py(sx * 29.8, sx * 38, -1.8)
        P.frame(e2, 1.2, 7.0, 1.0, 14.8, t=0.7, depth=0.8)
        for a2, b2 in ((1.2, 3.7), (4.5, 7.0)):
            P.curtain(e2, a2, b2, 1.0, 14.8, mull=1.25, transom=3.0)
        P.det.fbox(st, e2, 4.1, 0.0, 0.8, 0.8, 1.0, 14.8)
        # outer side of lateral section: slit windows
        fe, _ = (face_px if sx > 0 else face_nx)(-1.8, yF, sx * 29.8)
        P.slits(fe, 1.0, 14.5, spacing=4.0, w=1.0, floors=3, margin=2.0)

    # ---- open portal frames linking to the arms (A01: tall white frames) -----
    for sx in (-1, 1):
        for a, b in ((38, 40.6), (46.2, 48.8)):
            lo, hi = _xr(sx * a, sx * b)
            P.shell.box(st, lo, -8.3, G, hi, -1.2, 15.7)
        lo, hi = _xr(sx * 38, sx * 48.8)
        P.shell.box(st, lo, -8.3, 13.0, hi, -1.2, 15.7)
        P.det.box(band, lo, -1.2, 13.4, hi, -1.14, 14.0)
        lo, hi = _xr(sx * 40.6, sx * 46.2)
        P.glass.box(M['glass'], lo, -7.6, G, hi, -1.9, 4.4)
        P.det.box(st, lo, -8.0, 4.4, hi, -1.5, 4.9)

    # ---- arms projecting toward the gate (plan 4: u 1470-1492 / 1659-1682) --
    for sx in (-1, 1):
        lo, hi = _xr(sx * 48.8, sx * 62.2)
        P.rblock(lo, -19.6, hi, yA, G, 10.5)   # A02: arms read ~0.6 of the 18 m centre
        P.parapet(rect_poly(lo, -19.6, hi, yA), 10.5)
        e, ehi = face_py(lo, hi, yA)
        P.curtain(e, 1.2, 12.2, G + 0.05, 5.0, mull=1.8, transom=5)
        P.det.fbox(st, e, 6.7, 0.0, 2.6, 13.4, 5.0, 5.7)                      # canopy
        for s_ in (1.0, 4.6, 8.8, 12.4):
            P.det.fbox(st, e, s_, 1.9, 0.5, 0.5, G, 5.0)                        # colonnade
        P.frame(e, 2.0, 11.4, 6.0, 9.0, t=0.6, depth=0.6)
        P.curtain(e, 2.0, 11.4, 6.0, 9.0, mull=1.6, transom=4.4)
        # outer side: horizontal glazing bands with vertical fins (A02 far left/right)
        fe, f0 = (face_px if sx > 0 else face_nx)(-19.6, yA, sx * 62.2)
        for z0, z1 in ((1.2, 4.6), (6.0, 9.0)):
            P.curtain(fe, 2.0, fe.L - 2.0, z0, z1, mull=1.8, transom=10)
        P.piers(fe, 2.0, fe.L - 2.0, G, 10.0, spacing=2.4, w=0.35, depth=0.7)
        ie, _ = (face_nx if sx > 0 else face_px)(-1.2, yA, sx * 48.8)
        P.slits(ie, 1.0, 9.5, spacing=4.2, w=0.9, floors=2, margin=2.0)
        P.roof_plant(lo + 2, -16, hi - 2, 20, 10.5, random.Random(4 + sx), n=2)

    # ---- end pavilions + bridges ------------------------------------------
    for sx in (-1, 1):
        lo, hi = _xr(sx * 69.6, sx * 81.5)
        P.rblock(lo, -0.9, hi, 11.0, G, 14.0)
        P.parapet(rect_poly(lo, -0.9, hi, 11.0), 14.0)
        e, _ = face_py(lo, hi, 11.0)
        P.slits(e, 8.0, 12.8, spacing=1.6, w=0.55, floors=1, margin=3.6)       # three slits (A02)
        P.frame(e, 1.5, 10.4, G, 5.0, t=0.6, depth=0.6)
        P.curtain(e, 1.5, 10.4, G + 0.05, 5.0, mull=1.5, transom=5)
        lo2, hi2 = _xr(sx * 62.2, sx * 69.6)
        P.shell.box(st, lo2, 3.6, 7.0, hi2, 7.0, 10.0)
        P.glass.box(M["glass"], lo2, 3.55, 7.6, hi2, 7.05, 9.4)

    # ---- rear: stepped auditorium roof + rear block + wings 4.a / 4.b --------
    ys = [-13.5 - i * 4.4 for i in range(7)]
    tops = [18.6 + i * 0.95 for i in range(6)]
    for i in range(6):
        P.shell.box(st, -14, ys[i + 1], G, 14, ys[i], tops[i])
        P.det.box(M['roof'], -13.8, ys[i + 1], tops[i], 13.8, ys[i], tops[i] + 0.04)
        if i:
            P.glass.box(M['glass'], -13.5, ys[i] - 0.05, tops[i - 1] + 0.15, 13.5, ys[i] + 0.02, tops[i] - 0.15)
    # V11 (owner 16 + P09, PHOTO VERIFIED sightline): from the Academic upper deck (eye
    # ~6.1 m, the P09 vantage) the copper drum and dome rise above the Academic-facing
    # admin block. V10's 25 m blocks hid the dome completely. The rear block is lowered to
    # 18.0 m (P09: ~1.2-1.4x the 15 m wings) and the link block to 20.4 m. ESTIMATED.
    ADMIN_REAR_H, ADMIN_LINK_H = 18.0, 20.4
    P.rblock(-16, -50, 16, ys[-1], G, ADMIN_LINK_H)
    P.parapet(rect_poly(-16, -50, 16, ys[-1]), ADMIN_LINK_H)
    # P09: the Academic-facing admin centre is a tall, three-bay glazed facade.
    P.rblock(-16, -94, 16, -50, G, ADMIN_REAR_H)
    P.parapet(rect_poly(-16, -94, 16, -50), ADMIN_REAR_H)
    for sx in (-1, 1):
        lo, hi = _xr(sx * 14, sx * 44)
        poly = rect_poly(lo, -88, hi, -45)
        edges = P.block(poly, G, 15.0)
        P.parapet(poly, 15.0)
        for e in edges:
            P.slits(e, 1.0, 14.0, spacing=4.5, w=1.0, floors=3, margin=3.0)
        P.roof_plant(lo + 2, -86, hi - 2, -47, 15.0, random.Random(9 + sx), n=3)
    e, _ = face_ny(-16, 16, -94)
    from .v6_academic import admin_rear
    admin_rear(P,M)

    # ---- drum + dome (A01: white base, copper collar, copper windowed drum,
    #      banded darker dome, flat top ring and thin mast; A02/A03 proportions)
    oct_r = 13.8 / math.cos(math.radians(22.5))
    octagon = [(oct_r * math.cos(math.radians(22.5 + 45 * i)), oct_r * math.sin(math.radians(22.5 + 45 * i))) for i in range(8)]
    P.shell.prism(st, octagon, 17.9, 19.2)
    P.det.cylinder(st, (0, 0), 19.2, 20.0, 11.6, segs=64)
    P.det.cylinder(cu, (0, 0), 20.0, 21.0, 12.4, 11.0, segs=8, smooth=False)       # octagonal copper collar
    # V3 (A02 mismatch "drum slightly taller relative to the dome"): window band
    # 3.2 -> 3.8 m, drum top 26.4 -> 26.8 m; drum:dome height ratio ~0.83 (A02 ~0.82).
    r_d = 10.6
    zw0, zw1 = 21.5, 25.3
    zc = (zw0 + zw1) / 2
    P.det.cylinder(cu, (0, 0), 21.0, zw0, r_d, segs=64)
    P.det.cylinder(cu, (0, 0), zw1, 26.4, r_d + 0.15, segs=64)
    P.det.cylinder(cu, (0, 0), 26.3, 26.8, r_d + 0.45, segs=64)
    P.det.cylinder(cu, (0, 0), 21.0, 21.25, r_d + 0.25, segs=64)                    # drum sill ring
    nwin = 20
    for i in range(nwin):
        a = 2 * math.pi * (i + 0.5) / nwin
        u = Vector((math.cos(a), math.sin(a)))
        p = u * (r_d - 0.25)
        P.glass.obox(M['glass'], (p.x, p.y, zc), (2.5, 0.12, zw1 - zw0), a - math.pi / 2)
        P.det.obox(M['metal'], (p.x, p.y, zc), (2.5, 0.16, 0.08), a - math.pi / 2)   # transom bar
        a2 = 2 * math.pi * i / nwin
        q = Vector((math.cos(a2), math.sin(a2))) * (r_d - 0.15)
        P.det.obox(cu, (q.x, q.y, zc), (0.85, 0.5, zw1 - zw0), a2 - math.pi / 2)
    P.det.cylinder(M['metal'], (0, 0), zw0, zw1, r_d - 0.6, segs=40)                 # drum interior
    # V4 (A02 full-resolution measurement, camera elevation ~15 deg): dome rise / base diameter
    # = 104 / 380 px = 0.27, so the rise is ~5.5 m (V3: 7.0 m, ratio 0.36). Cap ring 6.1 m wide,
    # mast ~6.1 m above the cap.
    _dome(P, M, base_r=9.7, z0=26.8, rise=5.5)
    P.det.cylinder(cu, (0, 0), 32.2, 32.5, 3.0, segs=32)
    P.det.cylinder(M["metal_light"], (0, 0), 32.5, 38.6, 0.16, 0.05, segs=8)
    # thin roof masts (A02: four slender masts above the central and outer blocks)
    for x, y, z0, z1 in ((-21.5, -20.0, 18.0, 26.5), (21.5, -20.0, 18.0, 26.5),
                         (-43.5, -4.8, 15.7, 22.5), (43.5, -4.8, 15.7, 22.5)):
        P.det.cylinder(M['metal_light'], (x, y), z0, z1, 0.09, 0.05, segs=8)
    # V11 (owner 00): the V4-V10 rooftop trellis frames beside the drum are removed. Their
    # only support was a weak A01 aerial reading; A02/A03/P08/P09 show nothing above the
    # parapet. The ground-level pergola (A03) is a separate, retained object.
    return P.finish(C, 'main')


def _dome(P, M, base_r, z0, rise, segs=72, rings=14):
    """Spherical cap with alternating copper bands (A03 shows banded panels)."""
    R = (base_r ** 2 + rise ** 2) / (2 * rise)
    zc = z0 + rise - R
    th_max = math.asin(base_r / R)
    pts = []
    for j in range(rings + 1):
        th = th_max * (1 - j / rings)
        pts.append((R * math.sin(th), zc + R * math.cos(th)))
    for j in range(rings):
        (r0, z_a), (r1, z_b) = pts[j], pts[j + 1]
        verts, faces = [], []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            verts.append((r0 * math.cos(a), r0 * math.sin(a), z_a))
        for i in range(segs):
            a = 2 * math.pi * i / segs
            verts.append((r1 * math.cos(a), r1 * math.sin(a), z_b))
        for i in range(segs):
            k = (i + 1) % segs
            faces.append((i, k, segs + k, segs + i))
        # V3 (A03): a broad darker band at the dome base, then thinner dark bands higher up
        dark = j in (1, 2) or j in (6, 10)
        mat = M['copper_dark'] if dark else M['copper_dome']
        P.det.raw(mat, verts, faces, smooth=True)
    r_top, z_top = pts[-1]
    P.det.cylinder(M['copper_dome'], (0, 0), z_top - 0.05, z_top + 0.02, r_top, segs=segs)
    # standing-seam meridian ribs (A02/A03 show a fine panel grid on the dome)
    n_rib, lift = 36, 0.035
    for i in range(n_rib):
        a = 2 * math.pi * i / n_rib
        ca, sa = math.cos(a), math.sin(a)
        ta, tb = -sa * 0.03, ca * 0.03            # half rib width along the tangent
        verts, faces = [], []
        for j, (r, z) in enumerate(pts[:-2]):
            nr = r / R
            nz = (z - zc) / R
            rr, zz = r + nr * lift, z + nz * lift
            verts += [(rr * ca - ta, rr * sa - tb, zz), (rr * ca + ta, rr * sa + tb, zz)]
            if j:
                k = 2 * j
                faces.append((k - 2, k - 1, k + 1, k))
        P.det.raw(M['copper_dark'], verts, faces)


# =============================================================================
#  Academic Building  (V4: OSM 540106547 outline, A01 front blocks, D05 Gate (A) view)
# =============================================================================
# The sign above Gate (A) in D05 ("Academic Building" in Arabic) in Arabic Presentation
# Forms-B, visual left-to-right order for Blender's unshaped text.
# V10 Academic forecourt arcade (P09). ESTIMATED: set-back depth, height, pier size/pitch.
ARC_D, ARC_H, ARC_PIER, ARC_PITCH, ARC_Y0 = 3.2, 8.2, 1.8, 5.6, -218.0

ACADEMIC_SIGN_AR = "ﻲﻤﻳﺩﺎﻛﻷﺍ ﻰﻨﺒﻤﻟﺍ"


def academic(M, C):
    """C-shaped building (V4 re-fit to the OSM outline): a semicircular rear ring around an
    inner court, straight side wings, two forward prongs framing the Gate (A) courtyard, and
    a core with the large glazed Gate (A) front (D05). V3 placed the prongs 11 m and the core
    front 22 m too far toward the admin."""
    from . import survey as SV
    from .gate import FONT_AR, FONT_LAT, _on_face, _text_mesh
    P = Parts("AB_Academic_Building", M)
    st = M['stone']
    A = SV.ACADEMIC
    cx, cy = A['curve_c']
    Ro = A['r_out']
    Ri = Ro - A['ring_depth']
    h_w, h_p = A['h_wing'], A['h_prong']
    px0, px1 = A['prong_x']
    y_pf, y_core, y_notch, y_side = A['prong_front_y'], A['core_front_y'], A['notch_y'], A['side_front_y']
    floors = [1.0 + 4.0 * f for f in range(5)]

    from .v6_academic import ring
    from . import v11_academic as V11
    V11.ENTRANCES.clear()
    ring(P,M,A)
    # V11: owner X marks (11) at both side-wing corners carry entrances; windows skip them.
    v11_skip = dict(zip((1, -1), V11.side_wing_entrances(P, M, A)))
    V11.ring_entrances(P, M, A)
    V11.rear_passage(P, M, A)
    for sx in (-1, 1):
        # side wings: ring ends rising to y_side, framed dark glass fronts (A01 outer blocks)
        lo, hi = _xr(sx * Ri, sx * Ro)
        P.rblock(lo, cy, hi, y_side, G, h_w)
        P.parapet(rect_poly(lo, cy, hi, y_side), h_w)
        e, _ = face_py(lo, hi, y_side)
        P.frame(e, 3.0, e.L - 3.0, 1.0, h_w - 2.0, t=1.2, depth=1.2)
        P.curtain(e, 3.0, e.L - 3.0, 1.0, h_w - 2.0, mull=1.8, transom=4.0)
        fe, _ = (face_px if sx > 0 else face_nx)(cy, y_side, sx * Ro)
        k0, k1 = v11_skip[sx]
        if k0 - 1.5 > 4.0:
            P.window_rows(fe, floors, w=1.5, h=2.4, spacing=0.9, margin=1.5, s1=k0)
        if fe.L - 1.5 - k1 > 4.0:
            P.window_rows(fe, floors, w=1.5, h=2.4, spacing=0.9, margin=1.5, s0=k1)
        # notch blocks between the wings and the prongs (outline recess at y_notch)
        lo, hi = _xr(sx * px1, sx * Ri)
        P.rblock(lo, cy, hi, y_notch, G, h_w)
        P.parapet(rect_poly(lo, cy, hi, y_notch), h_w)
        e, _ = face_py(lo, hi, y_notch)
        P.window_rows(e, floors, w=1.5, h=2.4, spacing=1.2, margin=1.5)
        # forward prongs (A01: tall blocks with a projecting glazed box; D05: colonnade)
        lo, hi = _xr(sx * px0, sx * px1)
        # V10 (P09, PHOTO VERIFIED form): the forecourt face is a double-height arcade.
        # Stout square stone piers stand on the facade line and the ground storey is
        # set back ARC_D under the upper floors, so the colonnade is a real covered
        # walkway (V9: thin piers glued to a solid glazed wall). It stops short of the
        # big stair (y > ARC_Y0) so no pier stands on the treads. Depth/height ESTIMATED.
        P.rblock(lo, cy, hi, y_pf, ARC_H, h_p)
        P.rblock(lo, cy, hi, ARC_Y0, G, ARC_H)
        rlo, rhi = _xr(sx * (px0 + ARC_D), sx * px1)
        P.rblock(rlo, ARC_Y0, rhi, y_pf, G, ARC_H)
        P.parapet(rect_poly(lo, cy, hi, y_pf), h_p)
        e, _ = face_py(lo, hi, y_pf)
        P.frame(e, 4.0, e.L - 4.0, 1.0, h_p - 3.5, t=1.4, depth=1.6)
        P.curtain(e, 4.0, e.L - 4.0, 1.0, h_p - 3.5, mull=1.6, transom=4.0)
        P.piers(e, 4.0, e.L - 4.0, 1.0, h_p - 3.5, spacing=6.25, w=0.6, depth=1.0)
        gb0, gb1, gz0, gz1, gd = e.L * 0.3, e.L * 0.7, 9.0, h_p - 4.5, 2.2
        P.det.fbox(st, e, (gb0 + gb1) / 2, 0.0, gd + 0.3, gb1 - gb0 + 1.2, gz0 - 0.6, gz0)
        P.det.fbox(st, e, (gb0 + gb1) / 2, 0.0, gd + 0.3, gb1 - gb0 + 1.2, gz1, gz1 + 0.6)
        for s_ in (gb0 - 0.3, gb1 + 0.3):
            P.det.fbox(st, e, s_, 0.0, gd + 0.3, 0.6, gz0, gz1)
        P.curtain(e, gb0, gb1, gz0, gz1, mull=1.5, transom=3.4, off=gd)
        # courtyard face of each prong (D05): stone colonnade with dark bands at the ground
        # floor, punched windows above, a glazed box on the top two floors
        ie, _ = (face_nx if sx > 0 else face_px)(y_core, y_pf, sx * px0)
        # Codex review (V10): ie runs from y_pf on the east prong (face_nx) but from
        # y_core on the west prong (face_px); map world y to arc length per side.
        S = (lambda y: y_pf - y) if sx > 0 else (lambda y: y - y_core)
        a0, a1 = sorted((S(y_pf), S(ARC_Y0)))       # arcade interval along ie
        n0, n1 = sorted((S(ARC_Y0), S(y_core)))     # unrecessed stretch behind the stair head
        # stout square piers on the facade line (P09: ~1.8 m, dark inlay bands)
        pier_y = [y_pf - 1.4 - ARC_PITCH * k for k in range(int((y_pf - ARC_Y0 - 2.6) / ARC_PITCH) + 1)]
        for py in pier_y:
            s_ = S(py)
            P.det.fbox(st, ie, s_, -ARC_PIER, ARC_PIER, ARC_PIER, G, ARC_H)
            for zb in (3.4, 6.1):
                P.det.fbox(M['band'], ie, s_, 0.0, 0.05, ARC_PIER + 0.02, zb, zb + 0.3)
        # fascia over the arcade and a light soffit lining (close-range read)
        am, al = (a0 + a1) / 2, a1 - a0
        P.det.fbox(st, ie, am, 0.0, 0.25, al, ARC_H - 0.05, ARC_H + 0.75)
        P.det.fbox(M['band'], ie, am, 0.25, 0.04, al, ARC_H + 0.2, ARC_H + 0.32)
        P.det.fbox(M['plaza_light'], ie, am, -ARC_D, ARC_D - 0.02, al, ARC_H - 0.06, ARC_H - 0.01)
        # recessed ground-storey glazing at the back of the arcade, and the
        # unrecessed stretch behind the stair head
        P.curtain(ie, a0 + 0.5, a1 - 0.3, G + 0.05, ARC_H - 0.1, mull=2.8, transom=3.6, off=-ARC_D + 0.02)
        m_arc, m_core = (0.3, 1.5) if sx > 0 else (1.5, 0.3)   # 1.5 m margin at the core end
        P.curtain(ie, n0 + m_arc, n1 - m_core, G + 0.05, 7.2, mull=2.8, transom=3.6)
        centre=abs(-219.-ie.p0.y)
        # V10 (P09): the upper glazed box is wide, in heavy frames (big panes, 2-3 rows);
        # V9 had a 12 m box with fine mullions. Width ESTIMATED (~20 m).
        b0, b1 = max(centre - 10.0, 0.6), min(centre + 10.0, ie.L - 0.6)
        # P09 supersedes the V5 repeated square rows / full upper glass ribbon:
        # slits only where the glazed box is not.
        if b0 - 1.2 > 3.0:
            P.slits(ie,9.,22.5,spacing=4.8,w=1.05,floors=1,margin=3.,s1=b0-1.2)
        if b1 + 1.2 < ie.L - 3.0:
            P.slits(ie,9.,22.5,spacing=4.8,w=1.05,floors=1,margin=3.,s0=b1+1.2)
        P.frame(ie,b0,b1,10.5,22.,t=.6,depth=1.35)
        P.curtain(ie,b0,b1,10.5,22.,mull=b1-b0,transom=12.,off=1.1)
        nb = 4
        for k in range(1, nb):
            P.det.fbox(M['band'], ie, b0 + (b1 - b0) * k / nb, 1.1, 0.45, 0.42, 10.5, 22.)
        for zt in (14.3, 18.1):
            P.det.fbox(M['band'], ie, (b0 + b1) / 2, 1.1, 0.45, b1 - b0, zt - 0.21, zt + 0.21)
        oe, _ = (face_px if sx > 0 else face_nx)(cy, y_pf, sx * px1)
        P.window_rows(oe, [1.0 + 4.0 * f for f in range(6)], w=1.6, h=2.5, spacing=1.0, group=2, margin=2.0)
        lo, hi = _xr(sx * (px0 + 3), sx * (px1 - 3))
        P.roof_plant(lo, y_core - 10, hi, y_pf - 4, h_p, random.Random(30 + sx), n=3)
    # core with the Gate (A) glazed front (D05)
    # P15: deep stone bridge/portal. Opening dimensions are still estimated.
    # V11 (owner 08/11/14 + P09/P15): the core is rebuilt as a real two-level system.
    # Ground: enclosed lobbies flank an open lower passage. Upper (4.41 m): a 10 m deep
    # open terrace in front of the glazed core, a covered hall under the upper block and a
    # bridge projecting ~21 m into the court, with two railed voids looking down into the
    # passage. V10's 3 m deck strip, open 7 m hall and passage ceiling are replaced.
    P.rblock(-px0,cy,px0,y_core-3.,7.4,h_p)
    plate = V11.core(P, M, A)
    P.parapet(rect_poly(-px0, cy, px0, y_core-3.), h_p)
    e, _ = face_py(-px0, px0, y_core-3.)
    P.curtain(e, 2.5, e.L - 2.5, 7.5, h_p - 4.6, mull=1.6, transom=2.6)
    P.det.fbox(st, e, e.L / 2, 0.0, 0.5, e.L, h_p - 4.6, h_p)             # top stone band with the sign
    # Upper-level main entry (Gate A hall): the terrace runs straight into the covered hall;
    # glazed entrance doors stand on the solid prong walls that bound the hall (glass on a
    # solid wall, so no walk-through glazing). Owner: main entry/hall relationship here.
    for sx in (-1, 1):
        he, _ = (face_nx if sx > 0 else face_px)(cy, y_core - 3., sx * px0)
        P.curtain(he, 3.0, he.L - 3.0, 4.41, 7.25, mull=1.7, transom=2.84, off=.02)
        P.det.fbox(M['metal'], he, he.L / 2, .02, .2, he.L - 5.8, 7.2, 7.34)
    # V11 (07, D05 proportions): Arabic sign ~27 % of the core width (was 1.1 m text).
    me = _text_mesh(ACADEMIC_SIGN_AR, FONT_AR, 1.75)
    if me:
        P.det.add_mesh(M['band'], me, _on_face(0.0, h_p - 3.7, y_core - 3. + 0.55))
    obj=P.finish(C, 'main')
    obj['zc_public_route_v5']=True
    V11.build_stairs(M, C, obj)
    V11.rails_and_planters(M, C, obj, plate)
    from .academic_public import organize
    organize(C,obj)
    V11.write_registry()
    return obj


def east_residential_pair(M, C):
    """Two curved 5-storey blocks east of the ring (OSM 540106540/541, building:levels=5,
    visible in Sentinel-2 2026). Identity not confirmed. ESTIMATED low-detail massing."""
    from . import dormitory
    return dormitory.build_pair(M,C)


# =============================================================================
#  Research institutes (plan bldgs 5 and 6), built in local coordinates
# =============================================================================
def helmy_institute(M, C):
    """Helmy Institute for Medical Sciences (SIAC; plan bldg 5; A05, A01 right).
    Local +X = long axis (NW->SE on site), local +Y faces the admin building.
    A01: alternating blank stone panels and dark glass bays, central glazed recess."""
    from . import survey as SV
    spec = SV.HELMY
    P = Parts("AB_Helmy_Institute_Medical_Sciences", M)
    L, W, h = spec["length"], spec["width"], spec.get("height", 20.0)
    x0, x1, y0, y1 = -L / 2, L / 2, -W / 2, W / 2
    P.rblock(x0, y0, x1, y1, G, h)
    P.parapet(rect_poly(x0, y0, x1, y1), h)
    P.glass.box(M['glass_blue'], x0 + 8, -4.5, h, x1 - 8, 4.5, h + 0.9)        # atrium roof light
    P.det.box(M['metal'], x0 + 7.8, -4.7, h + 0.9, x1 - 8 + 0.2, 4.7, h + 1.0)
    e, _ = face_py(x0, x1, y1)
    s = 2.0
    while s < L - 2.0:
        mid = abs(s + 3.5 - L / 2) < 13
        if mid:
            s = L / 2 + 13
            continue
        P.det.fbox(M['stone'], e, s + 3.25, 0.0, 0.35, 6.5, G, h - 0.2)          # blank stone panel
        P.curtain(e, s + 6.7, s + 10.0, 1.0, h - 1.0, mull=1.1, transom=4.4)     # dark glass bay
        s += 10.4
    P.recess(e, L / 2 - 12.5, L / 2 + 12.5, 1.0, 13.5, depth=2.0, mull=1.6, transom=4.2)
    P.det.fbox(M['stone'], e, L / 2, 0.0, 4.0, 27.0, 13.5, 14.3)                 # canopy
    e, _ = face_ny(x0, x1, y0)
    P.window_rows(e, [1.0 + 4.3 * f for f in range(4)], w=1.6, h=2.4, spacing=2.2, group=2, margin=3.0)
    for fe, _ in (face_px(y0, y1, x1), face_nx(y0, y1, x0)):
        P.slits(fe, 1.0, h - 1.0, spacing=4.0, w=1.0, floors=4, margin=3.0)
    P.roof_plant(x0 + 4, y0 + 2, x0 + 30, y1 - 2, h, random.Random(51), n=4)
    return P.finish(C, 'secondary', location=spec['center'], angle_deg=spec['angle_deg'])


def nano_institute(M, C):
    """Research institute east of the admin (plan bldg 6; A01 left side), presumed to be
    the NBE Nanosciences institute. A01: white, punched windows in threes, tall dark
    glass strips, a taller block at one end."""
    from . import survey as SV
    spec = SV.EAST_INSTITUTE
    P = Parts("AB_East_Research_Institute_Nano", M)
    L, W, h = spec["length"], spec["width"], spec.get("height", 20.0)
    x0, x1, y0, y1 = -L / 2, L / 2, -W / 2, W / 2
    P.rblock(x0, y0, x1 - 20, y1, G, h)
    P.parapet(rect_poly(x0, y0, x1 - 20, y1), h)
    P.rblock(x1 - 20, y0, x1, y1, G, 26.0)
    P.parapet(rect_poly(x1 - 20, y0, x1, y1), 26.0)
    for face in (face_py(x0, x1, y1)[0], face_ny(x0, x1, y0)[0]):
        main = (23.0, L - 3.0) if face.n.y > 0 else (3.0, L - 23.0)   # tall block sits at +X
        P.window_rows(face, [1.2 + 4.3 * f for f in range(4)], w=1.2, h=2.3, spacing=3.4, group=3, gap=0.45,
                      margin=3.0, s0=main[0], s1=main[1])
        for s_ in (24.0, 48.0):
            P.curtain(face, s_ - 1.6, s_ + 1.6, 1.0, h - 1.0, mull=1.0, transom=4.3)
        P.window_rows(face, [1.2 + 4.3 * f for f in range(5)], w=1.4, h=2.6, spacing=2.0, group=2, margin=1.0,
                      s0=1.0 if face.n.y > 0 else L - 19.0, s1=19.0 if face.n.y > 0 else L - 1.0)
    for fe, _ in (face_px(y0, y1, x1), face_nx(y0, y1, x0)):
        P.curtain(fe, W / 2 - 4, W / 2 + 4, 1.0, 16.0, mull=1.3, transom=4.3)
    P.roof_plant(x0 + 4, y0 + 2, x1 - 24, y1 - 2, h, random.Random(61), n=5)
    return P.finish(C, 'secondary', location=spec['center'], angle_deg=spec['angle_deg'])



def build_all(M, C):
    return [admin_cultural(M, C), academic(M, C), helmy_institute(M, C), nano_institute(M, C),
            east_residential_pair(M, C)]
