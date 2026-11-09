"""Main (external) campus gate on Ahmed Zewail Road. New in V4.

Evidence (references/SOURCE_EVIDENCE.md, V4):
  C01  Wikimedia Commons "Zewail City Gates.jpg", 2017-11-18 10:46 (EXIF), CC BY-SA 4.0,
       taken OUTSIDE the gate from the landscaped island: portal frame, gatehouse with the
       logo medallion, sliding steel gate, pedestrian gate, gate buildings, cactus beds.
  C02  Wikimedia Commons "Zewail City.jpg", 2017-11-18 14:55, CC BY-SA 4.0, taken from the
       admin forecourt looking back along the approach: frame proportions, inside faces,
       closed right-lane gate, flanking pedestrian portals, perimeter walls and palms.
  D03  Official zewailcity.edu.eg "Landscape" image: same scene as C01 (official source).
  D02  Official zewailcity.edu.eg "Transportation" image (file name dated 2021): the same
       portal legs and stepped gatehouse seen from inside, grey interlocking pavers.
  OSM  Gate nodes 5225739523 / 5225739528 (lanes 10.4 m apart, axis-frame y 560.7); the
       2017 site outline 540106539 steps back from the gate in staggered setbacks.

Dimensions are photogrammetric estimates (C02: a 1.7 m person beside the left leg spans
55 px, i.e. 32 px/m at the frame plane): frame 33.4 m wide x 18.7 m high, legs 4.8 m,
lintel 4.5 m, dark inlay 0.55 m set 1.9 m in from the outer edge on both faces. The
gatehouse appears smaller than the frame in C02 (inside) and larger in C01 (outside),
so it stands ~10 m OUTSIDE the frame, between the two lanes. Frame depth (4.8 m) and the
gatehouse depth are not visible in any photo and are estimates.

Public-facing text reproduced: the medallion "مدينة زويل" / "ZEWAIL CITY" with the three
pyramids (C01; the same mark is printed on the official campus bus in D02). Nothing else
(no guard booths, barriers, cameras or signage) is added beyond what the photos show.
Whether the 2017 medallion is still mounted today is not verified.
"""
import math
import os

import bmesh
import bpy
from mathutils import Matrix

from . import survey as SV
from .architecture import Parts
from .geometry import MeshBuilder, circle_poly

GY = SV.GATE_Y
PT = SV.PORTAL
GH = SV.GATEHOUSE

FONT_AR = r"C:\Windows\Fonts\tahomabd.ttf"
FONT_LAT = r"C:\Windows\Fonts\arialbd.ttf"
# "مدينة زويل" in Arabic Presentation Forms-B, visual (left-to-right) order, so that a
# renderer without complex-text shaping (Blender text objects) draws the joined letters.
# Logical: meem-ini, dal-fin, yeh-ini, noon-med, teh-marbuta-fin, space, zain, waw, yeh-ini, lam-fin.
AR_VISUAL = "\uFEDE\uFEF3\uFEED\uFEAF \uFE94\uFEE8\uFEF3\uFEAA\uFEE3"


def _text_mesh(body, font_path, size, extrude=0.03, align='CENTER'):
    """Mesh of a text string in the XY plane (baseline at y=0), or None if the font is missing."""
    if not os.path.exists(font_path):
        print(f"[gate] font missing, text skipped: {font_path}")
        return None
    font = bpy.data.fonts.load(font_path, check_existing=True)
    cu = bpy.data.curves.new("TMP_TEXT", type='FONT')
    cu.body = body
    cu.font = font
    cu.size = size
    cu.extrude = extrude
    cu.align_x = align
    cu.resolution_u = 3
    ob = bpy.data.objects.new("TMP_TEXT", cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.curves.remove(cu)
    return me


def _on_face(x, z, y_face, out=1.0):
    """Matrix mapping text-plane (X right, Y up, Z out) onto a facade facing +Y (out=1) at y_face."""
    # text X -> world -X when the face looks +Y (viewer looks -Y, so their right is -X)
    rot = Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1))) if out > 0 else \
        Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    return Matrix.Translation((x, y_face, z)) @ rot


def _logo(det, M, cx, y_face, z0):
    """Medallion from C01: arch outline, Arabic name, three pyramids on a horizon line,
    'ZEWAIL CITY' below. ~3.4 m wide x 2.7 m high, bottom at z0, mounted on a +Y facade."""
    mat = M['logo_metal']
    t = 0.07          # profile thickness
    proud = 0.05
    y = y_face + proud
    # arch: semicircle r 1.45 centred 1.25 m above the horizon line + straight legs
    zc = z0 + 1.25
    seg = 28
    for i in range(seg):
        a0, a1 = math.pi * i / seg, math.pi * (i + 1) / seg
        xa, za = cx - 1.45 * math.cos(a0), zc + 1.45 * math.sin(a0)
        xb, zb = cx - 1.45 * math.cos(a1), zc + 1.45 * math.sin(a1)
        mx, mz = (xa + xb) / 2, (za + zb) / 2
        L = math.hypot(xb - xa, zb - za)
        ang = math.atan2(zb - za, xb - xa)
        m = Matrix.Translation((mx, y, mz)) @ Matrix.Rotation(-ang, 4, 'Y') @ Matrix.Diagonal((L + 0.02, 0.06, t, 1))
        r = bmesh.ops.create_cube(det.bm, size=1.0, matrix=m)
        det._tag(r['verts'], mat)
    for sx in (-1, 1):
        det.box(mat, cx + sx * 1.45 - t / 2, y - 0.03, z0 + 0.55, cx + sx * 1.45 + t / 2, y + 0.03, zc)
    det.box(mat, cx - 1.45, y - 0.03, z0 + 0.55, cx + 1.45, y + 0.03, z0 + 0.55 + t)   # horizon line
    # pyramids (front faces only, slightly proud), largest in the middle
    for px, w, h in ((cx - 0.05, 1.25, 0.78), (cx + 0.62, 0.9, 0.55), (cx - 0.72, 0.62, 0.36)):
        b = z0 + 0.55 + t
        det.raw(mat, [(px - w / 2, y + 0.04, b), (px + w / 2, y + 0.04, b), (px, y + 0.04, b + h),
                      (px - w / 2, y - 0.02, b), (px + w / 2, y - 0.02, b), (px, y - 0.02, b + h)],
                [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)])
    me = _text_mesh(AR_VISUAL, FONT_AR, 0.42)
    if me:
        det.add_mesh(mat, me, _on_face(cx, z0 + 1.62, y))
        bpy.data.meshes.remove(me)
    me = _text_mesh("ZEWAIL CITY", FONT_LAT, 0.40)
    if me:
        det.add_mesh(mat, me, _on_face(cx, z0 + 0.06, y))
        bpy.data.meshes.remove(me)


def _steel_gate(det, M, x0, x1, y, h=3.9):
    """Sliding steel gate (C02 right lane, C01 left): dark frame, vertical bars below,
    square lattice panel above."""
    st = M['steel_dark']
    lo, hi = min(x0, x1), max(x0, x1)
    det.box(st, lo, y - 0.08, 0.08, hi, y + 0.08, 0.2)
    det.box(st, lo, y - 0.08, h - 0.12, hi, y + 0.08, h)
    det.box(st, lo, y - 0.08, 2.45, hi, y + 0.08, 2.55)
    for x in (lo, hi):
        det.box(st, x - 0.07, y - 0.08, 0.08, x + 0.07, y + 0.08, h)
    n = int((hi - lo) / 0.17)
    for k in range(1, n):
        x = lo + (hi - lo) * k / n
        det.box(st, x - 0.02, y - 0.02, 0.2, x + 0.02, y + 0.02, 2.45)
    m = max(2, int(round((hi - lo) / 0.32)))
    for k in range(1, m):
        x = lo + (hi - lo) * k / m
        det.box(st, x - 0.025, y - 0.03, 2.55, x + 0.025, y + 0.03, h - 0.12)
    for z in (2.85, 3.15, 3.45):
        det.box(st, lo, y - 0.03, z - 0.025, hi, y + 0.03, z + 0.025)
    # wheels / rail
    det.box(st, lo, y - 0.05, 0.0, hi, y + 0.05, 0.08)


def _grid_door(det, M, hinge_x, y, w, h, open_dir):
    """Pedestrian grid door, swung open 90 deg (open_dir = -1 swings toward the campus)."""
    st = M['steel_dark']
    y1 = y + open_dir * w
    lo, hi = min(y, y1), max(y, y1)
    det.box(st, hinge_x - 0.05, lo, 0.05, hinge_x + 0.05, hi, 0.15)
    det.box(st, hinge_x - 0.05, lo, h - 0.1, hinge_x + 0.05, hi, h)
    for yy in (lo, hi):
        det.box(st, hinge_x - 0.05, yy - 0.05, 0.05, hinge_x + 0.05, yy + 0.05, h)
    for k in range(1, 8):
        yy = lo + (hi - lo) * k / 8
        det.box(st, hinge_x - 0.02, yy - 0.02, 0.15, hinge_x + 0.02, yy + 0.02, h - 0.1)
    for k in range(1, 10):
        z = 0.15 + (h - 0.25) * k / 10
        det.box(st, hinge_x - 0.02, lo, z - 0.02, hinge_x + 0.02, hi, z + 0.02)


def build_gate(M, C):
    P = Parts("AB_Main_Gate_Complex", M)
    gs, led, stu = M['gate_stone'], M['ledgestone'], M['stucco']
    xo = PT['outer_w'] / 2.0              # 16.7
    xi = xo - PT['leg_w']                  # 11.9
    H, LH, D = PT['height'], PT['lintel_h'], PT['depth']
    y0, y1 = GY - D / 2.0, GY + D / 2.0

    # ---- portal frame --------------------------------------------------------
    for sx in (-1, 1):
        lo, hi = sorted((sx * xi, sx * xo))
        P.shell.box(gs, lo, y0, 0.0, hi, y1, H)
    P.shell.box(gs, -xi, y0, H - LH, xi, y1, H)
    # dark ledgestone inlay: inverted U on both faces (C01 outside, C02 inside)
    w, off = PT['inlay_w'], PT['inlay_off']
    xa, xb = xo - off - w, xo - off
    for yf, s in ((y1, 1), (y0, -1)):
        ya, yb = sorted((yf - s * 0.01, yf + s * 0.025))
        for sx in (-1, 1):
            lo, hi = sorted((sx * xa, sx * xb))
            P.det.box(led, lo, ya, 0.0, hi, yb, H - off)
        P.det.box(led, -xb, ya, H - off - w, xb, yb, H - off)
    P.det.box(M['roof'], -xo + 0.1, y0 + 0.1, H, xo - 0.1, y1 - 0.1, H + 0.03)

    # ---- gatehouse (outside the frame, between the lanes; C01 stepped blocks) --------
    gw = GH['w'] / 2.0                     # 7.0
    ga, gb = GH['y0'], GH['y1']
    hA, hB, hC = GH['h']
    P.shell.box(gs, -gw, ga, 0.0, gw, ga + 5.5, hA)
    P.shell.box(gs, -gw, ga + 5.5, 0.0, gw - 1.7, ga + 6.6, hB)
    P.shell.box(gs, -gw, ga + 6.6, 0.0, gw - 3.5, gb, hC)
    for (xa_, xb_, ya_, yb_, h_) in ((-gw, gw, ga, ga + 5.5, hA), (-gw, gw - 1.7, ga + 5.5, ga + 6.6, hB),
                                     (-gw, gw - 3.5, ga + 6.6, gb, hC)):
        P.det.box(M['roof'], xa_ + 0.1, ya_ + 0.05, h_, xb_ - 0.1, yb_ - 0.05, h_ + 0.03)
    # three dark vertical slots with stone fins on the logo block (C01: right of the medallion)
    for k in range(3):
        x = -5.25 + 0.35 / 2 + k * 0.8
        P.det.box(M['steel_dark'], x - 0.175, gb - 0.01, 0.3, x + 0.175, gb + 0.03, 5.9)
    _logo(P.det, M, -0.2, gb, 2.5)
    # inner (campus-side) face of the gatehouse: plain stone, one service door (D02 shows a door)
    P.det.box(M['steel_dark'], 2.0, ga - 0.04, 0.0, 3.2, ga + 0.01, 2.3)

    # ---- lane gates (C02: right lane closed; C01 / C02 left lane open) ---------------
    # V11 (owner 02): lane leaves are separate interactive sliding objects and stone return
    # walls close the strip between each lane post and the portal leg (v11_gates).
    from .v11_gates import g1_lane_system
    g1_lane_system(P, M)

    # ---- pedestrian gates beside the legs (C01 left close-up; C02 both sides) ------------
    for sx in (-1, 1):
        def X(a, b):
            return sorted((sx * a, sx * b))
        lo, hi = X(17.4, 17.8)
        P.shell.box(stu, lo, GY - 0.35, 0.0, hi, GY + 0.35, 4.6)
        lo, hi = X(20.2, 20.6)
        P.shell.box(stu, lo, GY - 0.35, 0.0, hi, GY + 0.35, 4.6)
        lo, hi = X(17.4, 20.6)
        P.shell.box(stu, lo, GY - 0.35, 3.9, hi, GY + 0.35, 4.6)
        for a, b in ((16.7, 17.4), (20.6, 21.5)):
            lo, hi = X(a, b)
            P.shell.box(led, lo, GY - 0.3, 0.0, hi, GY + 0.3, 3.4)
        from .v11_gates import g1_pedestrian_leaf
        g1_pedestrian_leaf(M, sx)

    # ---- single-storey gate buildings and stone pavilions (C01 right, C02 sides) ------
    for sx in (-1, 1):
        def X(a, b):
            return sorted((sx * a, sx * b))
        lo, hi = X(21.5, 36.0)
        P.shell.box(stu, lo, GY - 6.0, 0.0, hi, GY + 2.0, 5.4)
        P.det.box(stu, lo - 0.05, GY - 6.05, 5.4, hi + 0.05, GY + 2.05, 5.75)       # coping
        for k in range(3):                                                           # roof AC units (C01)
            ax = sx * (24.5 + k * 4.0)
            P.det.box(M['metal_light'], ax - 0.6, GY - 2.0, 5.75, ax + 0.6, GY - 1.2, 6.35)
        for k in range(4):                                                           # wall lights (C01)
            ax = sx * (23.0 + k * 3.6)
            P.det.box(M['steel_dark'], ax - 0.08, GY + 2.0, 3.25, ax + 0.08, GY + 2.12, 3.45)
        lo, hi = X(36.0, 53.0)
        P.shell.box(stu, lo, GY - 6.0, 0.0, hi, GY + 8.0, 6.5)
        P.det.box(stu, lo - 0.05, GY - 6.05, 6.5, hi + 0.05, GY + 8.05, 6.8)
        yf = GY + 8.0
        # stone-tile field inside a plaster border, two slots, big ledgestone panel
        lo, hi = X(36.8, 52.2)
        P.det.box(gs, lo, yf, 0.0, hi, yf + 0.12, 5.9)
        for a in (38.0, 39.0):
            lo, hi = X(a, a + 0.38)
            P.det.box(M['steel_dark'], lo, yf + 0.11, 0.3, hi, yf + 0.16, 4.9)
        lo, hi = X(40.6, 50.4)
        P.det.box(led, lo, yf + 0.11, 0.3, hi, yf + 0.2, 4.6)
        # lattice portal and screen (C01 right edge)
        lo, hi = X(53.0, 62.0)
        P.shell.box(led, lo, GY + 2.0, 0.0, hi, GY + 2.8, 2.6)
        for a, b in ((53.0, 53.6), (61.4, 62.0)):
            lo, hi = X(a, b)
            P.shell.box(stu, lo, GY + 2.0, 0.0, hi, GY + 2.8, 5.0)
        lo, hi = X(53.0, 62.0)
        P.shell.box(stu, lo, GY + 2.0, 4.4, hi, GY + 2.8, 5.0)
        for k in range(1, 26):
            x = sx * (53.6 + 7.8 * k / 26)
            P.det.box(M['steel_dark'], x - 0.025, GY + 2.37, 2.6, x + 0.025, GY + 2.43, 4.4)
        for z in (2.95, 3.3, 3.65, 4.0):
            lo, hi = X(53.6, 61.4)
            P.det.box(M['steel_dark'], lo, GY + 2.37, z - 0.025, hi, GY + 2.43, z + 0.025)
    # V8 C02 campus-side frontage: taller recessed pier/wall masses. C01's lower
    # exterior pavilion is retained. Heights are approximate photo interpretations.
    for sx in (-1,1):
        lo,hi=sorted((sx*36.,sx*53.))
        P.shell.box(stu,lo,GY-6.,0.,hi,GY-3.5,9.8)
        for x in (lo,hi):
            P.shell.box(stu,x-.28,GY-6.3,-.25,x+.28,GY-3.4,10.)
        P.det.box(gs,lo-.1,GY-6.1,9.8,hi+.1,GY-3.4,9.96)
    # Embedded foundations under solid masses, never across gate openings.
    for sx in (-1,1):
        for a,b,ya,yb in ((xi,xo,y0,y1),(21.5,36.,GY-6.,GY+2.),(36.,53.,GY-6.,GY+8.)):
            lo,hi=sorted((sx*a,sx*b))
            P.shell.box(M['curb'],lo-.12,ya-.12,-.45,hi+.12,yb+.12,.04)
    # V11 (QA defect 8): gatehouse footing top below the sand (was 0.040 vs sand 0.042: z-fight).
    P.shell.box(M['curb'],-gw-.12,ga-.12,-.45,gw+.12,gb+.12,-.03)
    obj=P.finish(C, 'gate', bevel=0.02)
    obj['zc_v8_frontage']='C02 recessed campus-side masses 9.8 m / piers 10 m ESTIMATED; C01 low exterior pavilions retained.'
    return obj


# --------------------------------------------------------------------------- perimeter wall
def build_perimeter_wall(M, C, gap_half=62.5):
    """V8 terrain-following boundary with embedded footings; dimensions estimated."""
    from .v8_gates import perimeter
    return perimeter(M,C,gap_half)
