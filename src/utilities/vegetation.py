"""Low-poly vegetation and site-furniture asset meshes.

Assets are created once as mesh datablocks; the site module places them as
linked duplicates (objects sharing mesh data), which keeps memory and file size low.
"""
import math
import random

from mathutils import Matrix, Vector

from .geometry import MeshBuilder


def palm_mesh(M, name, height, seed):
    rng = random.Random(seed)
    mb = MeshBuilder()
    # slightly leaning, tapering trunk built from stacked frusta
    segs = 5
    lean = Vector((rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04)))
    for i in range(segs):
        z0, z1 = height * i / segs, height * (i + 1) / segs
        r0 = 0.42 - 0.17 * i / segs
        r1 = 0.42 - 0.17 * (i + 1) / segs
        off = lean * (z0 + z1) / 2
        mb.cylinder(M['palm_trunk'], (off.x, off.y), z0, z1 + 0.02, r0, r1, segs=9)
    top = Vector((lean.x * height, lean.y * height, height))
    mb.ico(M['palm_trunk'], tuple(top), 0.55, subdiv=1, scale=(1, 1, 1.3))
    # V7: pinnate date-palm fronds. Each frond is an arching rachis carrying paired,
    # drooping leaflets (V6: one flat ribbon per frond read as a plastic star).
    nf = 18
    for i in range(nf):
        ang = 2 * math.pi * i / nf + rng.uniform(-0.15, 0.15)
        up = rng.uniform(0.05, 0.75) if i % 2 else rng.uniform(0.35, 0.95)
        L = rng.uniform(3.4, 4.6)
        ca, sa = math.cos(ang), math.sin(ang)
        verts, faces = [], []
        N = 12
        spine = []
        for k in range(N + 1):
            s_ = k / N
            h = L * s_
            z = top.z + L * (up * s_ - 0.78 * s_ * s_)
            spine.append(Vector((top.x + ca * h, top.y + sa * h, z)))
        for k in range(N):
            p0, p1 = spine[k], spine[k + 1]
            d = (p1 - p0).normalized()
            side = Vector((-sa, ca, 0.0))
            # rachis
            verts += [tuple(p0 + side * 0.03), tuple(p1 + side * 0.03), tuple(p1 - side * 0.03), tuple(p0 - side * 0.03)]
            faces.append((len(verts) - 4, len(verts) - 3, len(verts) - 2, len(verts) - 1))
            if k < 1:
                continue
            s_ = k / N
            ll = 0.95 * math.sin(math.pi * min(1.0, 0.12 + s_ * 0.92)) + 0.12
            for sd in (-1, 1):
                tip = p0 + side * sd * ll + d * 0.18 + Vector((0, 0, -0.32 * ll))
                base_a, base_b = p0, p0 + d * 0.22
                verts += [tuple(base_a), tuple(base_b), tuple(tip + d * 0.05), tuple(tip - d * 0.04)]
                faces.append((len(verts) - 4, len(verts) - 3, len(verts) - 2, len(verts) - 1))
        mb.raw(M['palm_leaf'], verts, faces, smooth=False)
    return mb.to_mesh(name)


def fan_palm_mesh(M, name, height, seed):
    """Washingtonia: slender tall trunk, dead-leaf skirt, compact crown of round fans (A02, A04)."""
    rng = random.Random(seed)
    mb = MeshBuilder()
    mb.cylinder(M['palm_trunk'], (0, 0), 0, height, 0.32, 0.2, segs=8)
    mb.cylinder(M['palm_skirt'], (0, 0), height - 2.2, height - 0.2, 0.45, 0.75, segs=10)
    top = Vector((0, 0, height))
    for i in range(18):
        ang = 2 * math.pi * i / 18 + rng.uniform(-0.12, 0.12)
        tilt = rng.uniform(-0.2, 0.75)                    # elevation of the petiole
        stalk = 1.2
        d = Vector((math.cos(ang) * math.cos(tilt), math.sin(ang) * math.cos(tilt), math.sin(tilt)))
        base = top + d * stalk
        side = Vector((-math.sin(ang), math.cos(ang), 0))
        up = d.cross(side).normalized()
        r = rng.uniform(0.9, 1.25)
        verts = [tuple(base)]
        for k in range(11):                               # fan = 200-degree disc sector
            a = math.radians(-100 + 20 * k)
            p = base + (side * math.sin(a) + d * math.cos(a)) * r
            p.z -= 0.25 * r * (1 - math.cos(a))
            verts.append(tuple(p))
        faces = [(0, k, k + 1) for k in range(1, 11)]
        mb.raw(M['palm_fan'], verts, faces, smooth=False)
    return mb.to_mesh(name)


def tree_mesh(M, name, seed, height=5.0):
    """V7: visible trunk/limbs and a crown of many small clumps, lit and shaded
    foliage tones (V6: six large spheres on a pole). Generic shade tree; species
    is not claimed."""
    rng = random.Random(seed)
    mb = MeshBuilder()
    tz = height * 0.42
    mb.cylinder(M['bark'], (0, 0), 0, tz + 0.3, 0.2, 0.15, segs=8)
    crown_c = Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), height * 0.74))
    for k in range(4):
        a = 2 * math.pi * k / 4 + rng.uniform(-0.4, 0.4)
        end = Vector((math.cos(a) * 1.2, math.sin(a) * 1.2, tz + height * 0.28))
        base = Vector((0, 0, tz))
        d = end - base
        m = Matrix.Translation(base) @ d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        mb.cylinder_matrix(M['bark'], m @ Matrix.Translation((0, 0, d.length / 2)), 0.08, d.length, segs=6)
    rx, rz = 2.3 + 0.004 * seed, 1.55
    for k in range(13):
        u, v = rng.uniform(0, 2 * math.pi), rng.uniform(-0.55, 1.0)
        rr = math.sqrt(max(0.0, 1 - v * v))
        c = crown_c + Vector((math.cos(u) * rr * rx * 0.8, math.sin(u) * rr * rx * 0.8, v * rz * 0.8))
        mat = M['foliage_dark'] if c.z < crown_c.z - 0.3 else M['foliage']
        mb.ico(mat, tuple(c), rng.uniform(0.75, 1.15), subdiv=1, scale=(1, 1, 0.8), jitter=0.3, seed=seed * 3 + k)
    return mb.to_mesh(name)


def cypress_mesh(M, name, seed, height=7.0):
    mb = MeshBuilder()
    mb.cylinder(M['bark'], (0, 0), 0, 0.9, 0.18, 0.14, segs=6)
    mb.cylinder(M['cypress'], (0, 0), 0.6, height, 1.05, 0.08, segs=12)
    mb.ico(M['cypress'], (0, 0, 1.6), 1.05, subdiv=2, scale=(1, 1, 1.2), jitter=0.12, seed=seed)
    return mb.to_mesh(name)


def shrub_mesh(M, name, mat_key, seed):
    """V7: clump of three overlapping lobes (V6: one smooth blob)."""
    rng = random.Random(seed)
    mb = MeshBuilder()
    for k in range(3):
        a = 2 * math.pi * k / 3 + rng.uniform(-0.3, 0.3)
        mb.ico(M[mat_key], (math.cos(a) * 0.38, math.sin(a) * 0.38, 0.42 + 0.06 * k), rng.uniform(0.55, 0.7),
               subdiv=1, scale=(1.0, 1.0, 0.8), jitter=0.18, seed=seed + k)
    return mb.to_mesh(name)


def round_shrub_mesh(M, name, seed, r=0.42, mat_key='hedge'):
    """P04/P16 clipped round bed shrub (~0.6-0.8 m); official dorms image adds
    red-flowering and golden-green bed shrubs."""
    mb = MeshBuilder()
    mb.ico(M[mat_key], (0, 0, r * 0.82), r, subdiv=1, scale=(1.0, 1.0, 0.86), jitter=0.06, seed=seed)
    return mb.to_mesh(name)


def lamp_mesh(M, name, height=8.0, double=False):
    mb = MeshBuilder()
    mb.cylinder(M['pole'], (0, 0), 0, 0.5, 0.22, 0.18, segs=10)
    mb.cylinder(M['pole'], (0, 0), 0.5, height, 0.11, 0.08, segs=10)
    arms = (1, -1) if double else (1,)
    for d in arms:
        mb.box(M['pole'], 0, -0.06, height - 0.12, d * 1.6, 0.06, height)
        x0, x1 = sorted((d * 1.2, d * 2.2))
        mb.box(M['pole'], x0, -0.25, height - 0.25, x1, 0.25, height + 0.05)
        mb.box(M['lamp'], x0 + 0.05, -0.2, height - 0.3, x1 - 0.05, 0.2, height - 0.25)
    return mb.to_mesh(name)


def bollard_lamp_mesh(M, name):
    mb = MeshBuilder()
    mb.cylinder(M['pole'], (0, 0), 0, 3.6, 0.07, segs=8)
    mb.cylinder(M['lamp'], (0, 0), 3.6, 4.0, 0.2, segs=12)
    mb.cylinder(M['pole'], (0, 0), 4.0, 4.1, 0.26, segs=12)
    return mb.to_mesh(name)


def bench_mesh(M, name):
    mb = MeshBuilder()
    for x in (-0.8, 0.8):
        mb.box(M['stone'], x - 0.12, -0.25, 0, x + 0.12, 0.25, 0.42)
    for k in range(4):
        y = -0.24 + k * 0.16
        mb.box(M['wood'], -1.0, y, 0.42, 1.0, y + 0.12, 0.47)
    return mb.to_mesh(name)


def car_mesh(M, name):
    """Generic sedan, 4.5 m long along +X. Body slot uses an object-level material."""
    mb = MeshBuilder()
    body = M['car_white']
    mb.box(body, -2.25, -0.88, 0.32, 2.25, 0.88, 0.95)
    mb.obox(body, (-0.2, 0, 1.25), (2.3, 1.6, 0.6))
    mb.obox(M['car_glass'], (-0.2, 0, 1.25), (2.0, 1.64, 0.42))
    mb.obox(M['car_glass'], (0.92, 0, 1.2), (0.06, 1.5, 0.4), 0.0)
    for x in (-1.45, 1.4):
        for y in (-0.82, 0.82):
            m = Matrix.Translation((x, y, 0.33)) @ Matrix.Rotation(math.pi / 2, 4, 'X')
            mb.cylinder_matrix(M['tire'], m, 0.33, 0.24, segs=12)
    return mb.to_mesh(name)


def agave_mesh(M, name, seed, r=0.9):
    """Agave americana rosette: stiff tapering blades (C01 gate beds)."""
    rng = random.Random(seed)
    mb = MeshBuilder()
    for k in range(16):
        ang = 2 * math.pi * k / 16 + rng.uniform(-0.15, 0.15)
        tilt = math.radians(rng.uniform(25, 65))
        L = r * rng.uniform(0.75, 1.1)
        d = Vector((math.cos(ang) * math.cos(tilt), math.sin(ang) * math.cos(tilt), math.sin(tilt)))
        side = Vector((-math.sin(ang), math.cos(ang), 0.0)) * 0.09 * r
        base = Vector((0, 0, 0.05))
        verts = [tuple(base - side), tuple(base + side), tuple(base + d * L * 0.6 + side * 0.7),
                 tuple(base + d * L * 0.6 - side * 0.7), tuple(base + d * L)]
        mb.raw(M['agave'], verts, [(0, 1, 2, 3), (3, 2, 4)])
    return mb.to_mesh(name)


def barrel_cactus_mesh(M, name):
    """Golden barrel cactus (Echinocactus grusonii), ~0.5 m (C01)."""
    mb = MeshBuilder()
    mb.ico(M['cactus'], (0, 0, 0.22), 0.3, subdiv=2, scale=(1.0, 1.0, 0.85), jitter=0.04, seed=3.0)
    return mb.to_mesh(name)


def euphorbia_mesh(M, name, seed):
    """Clump of red-stemmed columnar euphorbia, ~1.6 m (C01 gate beds)."""
    rng = random.Random(seed)
    mb = MeshBuilder()
    for _ in range(6):
        x, y = rng.uniform(-0.35, 0.35), rng.uniform(-0.35, 0.35)
        h = rng.uniform(1.0, 1.8)
        mb.cylinder(M['euphorbia'], (x, y), 0.0, h, 0.09, 0.06, segs=5, smooth=False)
    return mb.to_mesh(name)


def cycad_mesh(M, name, seed):
    """Sago palm (Cycas revoluta): low rosette of arching dark fronds (C02 approach beds)."""
    rng = random.Random(seed)
    mb = MeshBuilder()
    mb.cylinder(M['palm_trunk'], (0, 0), 0.0, 0.35, 0.16, 0.14, segs=7)
    for k in range(14):
        ang = 2 * math.pi * k / 14 + rng.uniform(-0.1, 0.1)
        ca, sa = math.cos(ang), math.sin(ang)
        verts, faces = [], []
        N = 5
        for i in range(N + 1):
            s = i / N
            h = 1.1 * s
            z = 0.35 + 0.55 * s - 0.6 * s * s
            w = 0.16 * math.sin(math.pi * min(1.0, 0.1 + s))
            cx, cy = ca * h, sa * h
            verts += [(cx - sa * w, cy + ca * w, z), (cx + sa * w, cy - ca * w, z)]
        for i in range(N):
            faces.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
        mb.raw(M['cycad'], verts, faces)
    return mb.to_mesh(name)


def build_assets(M):
    A = {
        'palms': [palm_mesh(M, f"ASSET_Palm_{i}", h, 11 + i) for i, h in enumerate((7.5, 9.5, 11.5, 13.0))],
        'fan_palms': [fan_palm_mesh(M, f"ASSET_Fan_Palm_{i}", h, 71 + i) for i, h in enumerate((10.0, 12.5, 15.0))],
        'trees': [tree_mesh(M, f"ASSET_Tree_{i}", 21 + i, h) for i, h in enumerate((4.5, 5.5, 6.5))],
        'cypress': [cypress_mesh(M, "ASSET_Cypress_0", 31, 7.0)],
        'shrubs': [shrub_mesh(M, "ASSET_Shrub_Green_0", 'shrub', 41), shrub_mesh(M, "ASSET_Shrub_Green_1", 'hedge', 42)],
        'garden_shrub': [round_shrub_mesh(M, "ASSET_V7_Round_Shrub_0", 51, 0.40), round_shrub_mesh(M, "ASSET_V7_Round_Shrub_1", 52, 0.33),
                         round_shrub_mesh(M, "ASSET_V7_Round_Shrub_Red", 53, 0.36, 'shrub_red'),
                         round_shrub_mesh(M, "ASSET_V7_Round_Shrub_Golden", 54, 0.38, 'shrub_golden')],
        'flowers': [shrub_mesh(M, "ASSET_Shrub_Red", 'shrub_red', 43), shrub_mesh(M, "ASSET_Shrub_Orange", 'shrub_orange', 44)],
        'lamp': lamp_mesh(M, "ASSET_Street_Lamp", 9.0),
        'lamp2': lamp_mesh(M, "ASSET_Street_Lamp_Double", 10.0, double=True),
        'bollard': bollard_lamp_mesh(M, "ASSET_Plaza_Lamp"),
        'bench': bench_mesh(M, "ASSET_Bench"),
        'car': car_mesh(M, "ASSET_Car"),
        # V4: drought-tolerant planting photographed at the main gate (C01) and approach (C02)
        'agave': [agave_mesh(M, "ASSET_Agave_0", 81, 0.9), agave_mesh(M, "ASSET_Agave_1", 82, 0.7)],
        'barrel': [barrel_cactus_mesh(M, "ASSET_Barrel_Cactus")],
        'euphorbia': [euphorbia_mesh(M, "ASSET_Euphorbia_0", 91)],
        'cycad': [cycad_mesh(M, "ASSET_Cycad_0", 95)],
    }
    return A
