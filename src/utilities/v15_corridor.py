"""V15 pilot: G1 -> main approach -> Administration corridor reconstruction.

Evidence (references/source_images/v4/C02_commons_zewail_city_approach_2017.jpg, C01, D02, A04):
  * Kerbs are modular precast concrete units (~1 m, visible joints, ~0.15-0.17 m upstand,
    rounded road arris). V4-V14 drew one continuous extruded strip.
  * The planted verges between each carriageway and its walkway are RAISED, KERBED beds of
    brown soil with groundcover in rows and young trees, not mown lawn.
  * Two darker transverse paver bands cross each carriageway at the median crossover.
  * The palm median is a raised, worn lawn (sand patches), kerbed with rounded noses.
  * Natural ground grades softly between sandy soil and planted soil (no hard-edged patches).

This module changes only surfaces inside ZONE. Road centrelines, carriageway outlines,
gate geometry and the collision kerb (Kerb_Box_Collision_Proxy) logic are unchanged:
kerb units are VISUAL; the player still collides with the box kerb that V13/V14 used.
Widths/heights not measurable from the photos are ESTIMATED (stated per item below).
"""
import json
import math
import random
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector, Matrix

from . import survey as SV

ROOT = Path(__file__).resolve().parents[2]
GY = SV.GATE_Y
from shapely import make_valid, union_all, contains_xy
from shapely.ops import linemerge
from shapely.geometry import Polygon, LineString, MultiLineString, Point, box
from shapely.prepared import prep
from shapely.strtree import STRtree

# Pilot zone: G1 exterior (to the public street bend) through the approach to the ring junction,
# the drop-off loop and the Administration forecourt.
ZONE = box(-62., 8., 62., GY + 52.)
# Terrain feathering is applied in a wider corridor and faded out over FEATHER_FADE m.
FEATHER_ZONE = box(-150., 40., 150., GY + 70.)
FEATHER_FADE = 25.
FEATHER_W = 3.5

LOG = {}
STATE = {}


# ----------------------------------------------------------------------------- materials
def _img(path, colorspace):
    im = bpy.data.images.load(str(path), check_existing=True)
    im.colorspace_settings.name = colorspace
    return im


def _image_material(name, asset, tile, res='2k', tint=(1., 1., 1.), rough=0.95):
    """Blender source material from a CC0 provider map at its physical tile (world projection)."""
    old = bpy.data.materials.get(name)
    if old:
        bpy.data.materials.remove(old)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sc = nt.nodes.new('ShaderNodeVectorMath'); sc.operation = 'SCALE'; sc.inputs[3].default_value = 1.0 / tile
    nt.links.new(geo.outputs['Position'], sc.inputs[0])
    base = ROOT / 'game/godot/assets/pbr' / asset
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = _img(base / f'{asset}_diff_{res}.jpg', 'sRGB')
    t.extension = 'REPEAT'
    nt.links.new(sc.outputs[0], t.inputs['Vector'])
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
    mul.inputs['Factor'].default_value = 1.0
    nt.links.new(t.outputs['Color'], mul.inputs[6]); mul.inputs[7].default_value = (*tint, 1.)
    nt.links.new(mul.outputs[2], b.inputs['Base Color'])
    r = nt.nodes.new('ShaderNodeTexImage'); r.image = _img(base / f'{asset}_rough_{res}.jpg', 'Non-Color')
    nt.links.new(sc.outputs[0], r.inputs['Vector']); nt.links.new(r.outputs['Color'], b.inputs['Roughness'])
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = _img(base / f'{asset}_nor_gl_{res}.jpg', 'Non-Color')
    nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 0.6
    nt.links.new(sc.outputs[0], n.inputs['Vector']); nt.links.new(n.outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = (0.30 * tint[0], 0.21 * tint[1], 0.13 * tint[2], 1.)
    m.roughness = rough
    m['gltf_base_color'] = [1., 1., 1.]
    m['zc_tile_m'] = tile
    m['zc_bake_res'] = 1024
    m['zc_v15_asset'] = asset
    m['zc_periodic'] = True     # one provider tile per bake tile: already seamless
    return m


def create_materials(M):
    from .materials import paving, noisy
    # Brown planting-bed soil (C02 verges): Poly Haven `dirt` (CC0), physical 2.0 m tile.
    M['v15_bed'] = _image_material('M_V15_Planted_Bed_Soil', 'dirt', 2.0, tint=(1.0, 0.97, 0.93))
    # Darker transverse paver bands at the crossover (C02). Same 0.22 x 0.11 m running bond.
    M['v15_band'] = paving('M_Paver_Road_Grey_V15_Band', (0.075, 0.074, 0.072), (0.060, 0.060, 0.058),
                           (0.04, 0.04, 0.039), brick_w=0.22, row_h=0.11, rough=0.86)
    M['v15_band']['zc_tile_m'] = 2.2
    M['v15_band']['zc_periodic'] = True   # 10 x 20 units per 2.2 m tile
    # Worn median lawn (C02: green with sandy patches and kerb-side sand).
    M['v15_median'] = noisy('M_Grass_Lawn_V15_Median', (0.26, 0.21, 0.13), (0.065, 0.15, 0.035), scale=0.45,
                            rough=0.95, bump=0.3, bump_scale=70.0)
    # Mostly green; sandy patches only where the noise is low (C02 median).
    for n in M['v15_median'].node_tree.nodes:
        if n.type == 'VALTORGB':
            n.color_ramp.elements[0].position = 0.30
            n.color_ramp.elements[1].position = 0.43
            break
    M['v15_median']['zc_tile_m'] = 8.0
    return M


# ----------------------------------------------------------------------------- partition
def _geoms(g):
    if g.is_empty:
        return []
    if g.geom_type == 'Polygon':
        return [g]
    out = []
    for p in getattr(g, 'geoms', []):
        out.extend(_geoms(p))
    return out


def _poly(g):
    """Polygonal part of a (possibly mixed) geometry, as one valid geometry."""
    ps = [q for q in _geoms(make_valid(g)) if q.area > 1e-7]
    return union_all(ps) if ps else Polygon()


def _lines(g):
    if g.is_empty:
        return []
    if g.geom_type == 'LineString':
        return [g]
    if g.geom_type == 'LinearRing':
        return [LineString(g.coords)]
    out = []
    for p in getattr(g, 'geoms', []):
        out.extend(_lines(p))
    return out


def verge_masks():
    """Approach verge beds between carriageway and walkway, and the outer beds (site.py layout)."""
    inner, outer = [], []
    for sx in (-1, 1):
        lo, hi = sorted((sx * 8.6, sx * 14.45))
        inner.append(box(lo, 98.0, hi, GY - 29.0))
        lo, hi = sorted((sx * 18.15, sx * 22.2))
        outer.append(box(lo, 98.0, hi, GY - 29.0))
    return union_all(inner), union_all(outer)


def adjust_partition(partition, M):
    """Reassign surfaces inside ZONE (no area leaves the partition, nothing overlaps)."""
    name = {k: M[k].name for k in ('groundcover', 'grass', 'planted_soil', 'soil', 'paver_road', 'curb', 'edge')}
    soft = {name['groundcover'], name['grass'], name['planted_soil'], name['soil']}
    inner, outer = verge_masks()
    median = box(-8.5, 98.0, 8.5, GY + 7.0)
    take = {'bed': [], 'median': [], 'band': [], 'curb': []}
    out = []
    for mat, g in partition:
        if mat in soft:
            b = make_valid(g.intersection(inner.union(outer)))
            md = make_valid(g.intersection(median)) if mat == name['groundcover'] else Polygon()
            rest = make_valid(g.difference(inner.union(outer)).difference(md))
            take['bed'].append(b); take['median'].append(md)
            out.append((mat, rest))
        else:
            out.append((mat, g))
    bed = make_valid(union_all(take['bed']))
    # Transverse bands: 1.6 m wide, centred 7.8 m either side of the OSM crossover (just beyond the
    # median noses), across each carriageway. ESTIMATED from C02.
    U = SV.APPROACH_U_TURN_Y
    bands = union_all([box(-10.5, y - 0.8, -2.2, y + 0.8) for y in (U - 7.8, U + 7.8)] +
                      [box(2.2, y - 0.8, 10.5, y + 0.8) for y in (U - 7.8, U + 7.8)])
    res = []
    for mat, g in out:
        if mat == name['paver_road']:
            bnd = make_valid(g.intersection(bands))
            take['band'].append(bnd)
            g = make_valid(g.difference(bnd))
        if mat == name['edge']:
            # Bed/walkway edge (C02: a precast kerb, not a flush strip) -> kerb.
            k = make_valid(g.intersection(inner.buffer(0.3)).intersection(bed.buffer(0.08)))
            k = union_all([p for p in _geoms(k) if p.area > 0.05])
            take['curb'].append(k)
            g = make_valid(g.difference(k))
        res.append((mat, g))
    curb_add = make_valid(union_all(take['curb']))
    res = [(m, make_valid(g.union(curb_add)) if m == name['curb'] else g) for m, g in res]
    res = [(m, g) for m, g in res if not g.is_empty]
    med = make_valid(union_all(take['median']))
    band = make_valid(union_all(take['band']))
    for key, g in (('v15_bed', bed), ('v15_median', med), ('v15_band', band)):
        if not g.is_empty:
            res.append((M[key].name, g))
    STATE['bed'] = bed
    STATE['bed_inner'] = make_valid(bed.intersection(inner))
    # The verge masks mirror site.build_landscape (strips |x| 9.55..14.3, outer beds 18.3..22.0,
    # y 100..GY-32). If that layout moves, fail loudly instead of drifting.
    expect = 2 * (14.3 - 9.55) * (GY - 32.0 - 100.0)
    if not 0.8 * expect < STATE['bed_inner'].area < 1.15 * expect:
        raise RuntimeError(f"V15 verge beds {STATE['bed_inner'].area:.0f} m2, expected ~{expect:.0f} m2: site layout changed?")
    STATE['median'] = med
    road_all = _poly(union_all([g for m, g in res if m in (name['paver_road'], M['asphalt'].name)] + [band]))
    curb_all = _poly(union_all([g for m, g in res if m == name['curb']]))
    soft_all = _poly(union_all([bed, med]))
    open_edge = make_valid(soft_all.boundary.intersection(road_all.buffer(0.05)).difference(curb_all.buffer(0.08)))
    STATE['open_edge'] = open_edge
    LOG['open_bed_edge_m'] = round(open_edge.length, 2)
    LOG['partition'] = {'bed_m2': round(bed.area, 1), 'bed_inner_m2': round(STATE['bed_inner'].area, 1),
                        'median_m2': round(med.area, 1), 'band_m2': round(band.area, 1),
                        'edge_to_kerb_m2': round(curb_add.area, 2)}
    return res


def _edge_distance_fn(geom):
    segs = []
    for p in _geoms(geom):
        for ring in [p.exterior, *p.interiors]:
            co = list(ring.coords)
            segs.extend(LineString(co[i:i + 9]) for i in range(0, len(co) - 1, 8))
    if not segs:
        return lambda x, y: 99.
    tree = STRtree(segs)

    def d(x, y):
        q = Point(x, y)
        return segs[int(tree.nearest(q))].distance(q)
    return d


def bed_height(datum):
    """Raised bed soil 0.16 m above datum at its edge (kerb top 0.24: ~8 cm reveal, C02), rising by a
    1.2 cm mound (over 2 m) toward the centre. ESTIMATED. Unkerbed bed edges meet soil/lawn that ground_system
    grades up to ~+0.17 next to raised surfaces (beds are included in that raised set)."""
    from mathutils import noise
    d = _edge_distance_fn(union_all([STATE.get('bed', Polygon()), STATE.get('median', Polygon())]))
    ol = [l for l in _lines(STATE.get('open_edge', Polygon())) if l.length > 0.01]
    otree = STRtree(ol) if ol else None

    def d_open(x, y):
        if otree is None:
            return 99.
        q = Point(x, y)
        return ol[int(otree.nearest(q))].distance(q)

    def z(x, y):
        e = min(d(x, y), 2.0) / 2.0
        n = noise.noise(Vector((x * 0.6, y * 0.6, 3.3)))
        h = 0.16 + 0.012 * e * e * (3 - 2 * e) + 0.004 * n
        # Where a bed meets the road without a kerb (footway crossings), the soil is graded down
        # to the road surface over 1.2 m instead of leaving a 10 cm open step (QA: see-through crack).
        o = d_open(x, y)
        if o < 1.2:
            t = o / 1.2
            h = 0.06 + (h - 0.06) * t * t * (3 - 2 * t)
        return datum(x, y) + h
    STATE['bed_z'] = z
    return z


def bed_mask():
    d = _edge_distance_fn(union_all([STATE.get('bed', Polygon()), STATE.get('median', Polygon())]))

    def c(x, y):
        e = d(x, y)
        drift = 0.75 * (1.0 - min(1.0, e / 0.55)) ** 1.5      # kerb-side sand/dust (C02)
        return (drift, 0.5, 0.0, 1.0)
    return c


# ----------------------------------------------------------------------------- terrain feather
def feather_fn(terrain, soft_geoms):
    """Weight in [0, 1] toward a shared transition tone at natural-surface boundaries.

    Returns f(x, y) -> alpha for COLOR_0 (1 = no blend). Both sides of a boundary get the
    same weight, so the shader blend is continuous across mesh/material boundaries."""
    fz = FEATHER_ZONE.buffer(FEATHER_FADE)
    t = _poly(terrain.intersection(fz))
    softs = [s for s in (_poly(g.intersection(fz)) for g in soft_geoms if g is not None and not g.is_empty) if not s.is_empty and s.area > 0]
    lines = []
    allsoft = union_all(softs)
    for g in softs:
        others = union_all([t] + [h for h in softs if h is not g])
        bd = g.boundary
        if bd is not None:
            lines.extend(_lines(make_valid(bd.intersection(others.buffer(0.05)))))
    lines.extend(_lines(make_valid(t.boundary.intersection(allsoft.buffer(0.05)))))
    segs = []
    for ln in lines:
        co = list(ln.coords)
        segs.extend(LineString(co[i:i + 9]) for i in range(0, len(co) - 1, 8) if len(co[i:i + 9]) > 1)
    LOG['feather'] = {'boundary_segments': len(segs), 'width_m': FEATHER_W, 'zone': list(FEATHER_ZONE.bounds)}
    if not segs:
        return lambda x, y: 1.0
    tree = STRtree(segs)
    fz_prep = prep(FEATHER_ZONE)

    def f(x, y):
        q = Point(x, y)
        dz = 0. if fz_prep.contains(q) else FEATHER_ZONE.distance(q)
        if dz >= FEATHER_FADE:
            return 1.0
        d = segs[int(tree.nearest(q))].distance(q)
        if d >= FEATHER_W:
            return 1.0
        s = d / FEATHER_W
        w = (1.0 - s * s * (3 - 2 * s)) * (1.0 - min(1.0, dz / FEATHER_FADE))
        return 1.0 - w
    return f


# ----------------------------------------------------------------------------- kerb units
UNIT = 1.0          # straight precast unit (C02 joints ~1 m). ESTIMATED.
UNIT_CURVED = 0.5   # radius kerb units on tight curves. ESTIMATED.
GROOVE = 0.006      # V-joint depth/inset at each unit end
JOINT_LEN = 0.008


def _split_sharp(line, max_turn=80.0):
    """Split a face line at vertices turning more than max_turn degrees (mitres would pinch)."""
    co = list(line.coords)
    if len(co) < 3:
        return [line]
    out, cur = [], [co[0]]
    for i in range(1, len(co) - 1):
        cur.append(co[i])
        a = math.atan2(co[i][1] - co[i - 1][1], co[i][0] - co[i - 1][0])
        b = math.atan2(co[i + 1][1] - co[i][1], co[i + 1][0] - co[i][0])
        if abs((b - a + math.pi) % (2 * math.pi) - math.pi) > math.radians(max_turn):
            out.append(LineString(cur))
            cur = [co[i]]
    cur.append(co[-1])
    out.append(LineString(cur))
    return [l for l in out if l.length > 0.2]


def _stations(line):
    L = line.length
    closed = line.is_ring or Point(line.coords[0]).distance(Point(line.coords[-1])) < 1e-4
    st = [0.0]
    s = 0.0
    while s < L - 1e-6:
        a = line.interpolate(s); b = line.interpolate(min(L, s + 1.0)); c = line.interpolate(min(L, s + 2.0))
        h1 = math.atan2(b.y - a.y, b.x - a.x); h2 = math.atan2(c.y - b.y, c.x - b.x)
        turn = abs((h2 - h1 + math.pi) % (2 * math.pi) - math.pi)
        step = UNIT if turn < math.radians(3.5) else UNIT_CURVED
        nxt = s + step
        if L - nxt < 0.35 * step:
            nxt = L
        st.append(min(nxt, L))
        s = nxt
    pts = [line.interpolate(v) for v in st]
    return [(p.x, p.y) for p in pts], closed


def build_kerb_units(curb_geom, road, datum, mat, coll):
    """Modular precast kerb units along the exposed kerb faces in ZONE (visual only)."""
    rng = random.Random(15)
    cz = _poly(curb_geom.intersection(ZONE))
    if cz.is_empty:
        return None, Polygon()
    road = _poly(road)
    cz_prep = prep(cz.buffer(0.012))
    roadb = road.buffer(0.03)
    lo_surf = union_all([STATE.get('bed_inner', Polygon())]).buffer(0.03)
    face_road = [l for l in _lines(make_valid(cz.boundary.intersection(roadb))) if l.length > 0.3]
    face_bed = [l for l in _lines(make_valid(cz.boundary.intersection(lo_surf).difference(road.buffer(0.45))))
                if l.length > 0.3]
    merged = []
    for group in (face_road, face_bed):
        if group:
            m = linemerge(MultiLineString(group))
            for l in _lines(m):
                merged.extend(x for x in _split_sharp(l) if x.length > 0.4)
    bm = bmesh.new()
    footprints = []
    n_units = 0
    face_failures = 0
    skipped_overlap = 0
    covered = []
    widths = []

    def width_at(p, n):
        w = 0.06
        while w < 0.6 and cz_prep.contains(Point(p[0] + n[0] * w, p[1] + n[1] * w)):
            w += 0.01
        return max(0.12, min(0.45, w - 0.005))

    for line in merged:
        pts, closed = _stations(line)
        if len(pts) < 2:
            continue
        if closed and math.dist(pts[0], pts[-1]) < 1e-3:
            pts[-1] = pts[0]
        dirs = []
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            l = math.hypot(x1 - x0, y1 - y0) or 1.
            dirs.append(((x1 - x0) / l, (y1 - y0) / l))
        # Which side is the kerb body? Majority vote along the line.
        vote = 0
        for (x0, y0), (dx, dy) in zip(pts[:-1], dirs):
            mx, my = x0 + dx * 0.3, y0 + dy * 0.3
            vote += 1 if cz_prep.contains(Point(mx - dy * 0.08, my + dx * 0.08)) else -1
        sgn = 1. if vote >= 0 else -1.
        perp = [(-dy * sgn, dx * sgn) for dx, dy in dirs]
        nseg = len(dirs)
        miter = []
        for i in range(len(pts)):
            a = perp[i - 1] if i > 0 else (perp[-1] if closed else None)
            b = perp[i] if i < nseg else (perp[0] if closed else None)
            if a is None:
                a = b
            if b is None:
                b = a
            sx, sy = a[0] + b[0], a[1] + b[1]
            dot = a[0] * b[0] + a[1] * b[1]
            k = 1.0 / max(0.35, (1.0 + dot) / 2.0) ** 0.5
            l = math.hypot(sx, sy) or 1.
            miter.append((sx / l * k, sy / l * k))
        uw = []
        for i in range(nseg):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            ws = sorted(width_at((x0 + (x1 - x0) * f, y0 + (y1 - y0) * f), perp[i]) for f in (0.25, 0.5, 0.75))
            uw.append(ws[1])
        for i in range(nseg):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            L = math.hypot(x1 - x0, y1 - y0)
            if L < 0.05:
                continue
            w0 = (uw[i] + uw[i - 1]) / 2 if (i > 0 or closed) else uw[i]
            w1 = (uw[i] + uw[(i + 1) % nseg]) / 2 if (i < nseg - 1 or closed) else uw[i]
            dz = rng.uniform(-0.0015, 0.0015)
            dx, dy = dirs[i]
            n = perp[i]
            # A narrow strip with road on both sides yields face lines on both sides: build once.
            cxy = Point((x0 + x1) / 2 + n[0] * uw[i] / 2, (y0 + y1) / 2 + n[1] * uw[i] / 2)
            if any(c.contains(cxy) for c in covered[-600:]):
                skipped_overlap += 1
                continue
            g = min(JOINT_LEN, L * 0.2)
            secs = [((x0, y0), miter[i], w0, True), ((x0 + dx * g, y0 + dy * g), n, uw[i], False),
                    ((x1 - dx * g, y1 - dy * g), n, uw[i], False), ((x1, y1), miter[i + 1], w1, True)]
            rings = []
            for (px, py), nv, w, inset in secs:
                zr = datum(px, py) + 0.06
                zt = datum(px, py) + 0.24 + dz
                zb = zr - 0.12
                prof = [(0.0, zb), (0.0, zr + 0.025), (0.010, zt - 0.018), (0.014, zt - 0.009), (0.020, zt - 0.003),
                        (0.030, zt), (w - 0.008, zt), (w, zt - 0.008), (w, zb)]
                if inset:
                    prof = [(o + (GROOVE if 1 <= j <= 5 else 0.) - (GROOVE if j in (6, 7) else 0.),
                             z - (GROOVE if 2 <= j <= 7 else 0.)) for j, (o, z) in enumerate(prof)]
                rings.append([bm.verts.new((px + nv[0] * o, py + nv[1] * o, z)) for o, z in prof])
            for ra, rb in zip(rings[:-1], rings[1:]):
                m = len(ra)
                for j in range(m):
                    k = (j + 1) % m
                    try:
                        bm.faces.new((ra[j], rb[j], rb[k], ra[k]))
                    except ValueError:
                        face_failures += 1
            for ring in (rings[0], rings[-1]):
                try:
                    bm.faces.new(ring)
                except ValueError:
                    face_failures += 1
            # Footprint from the actual (mitred) end sections so the trim covers corner wedges too.
            fpoly = Polygon([(r[0].co.x, r[0].co.y) for r in rings] +
                            [(r[-1].co.x, r[-1].co.y) for r in reversed(rings)]).buffer(0)
            footprints.append(fpoly)
            covered.append(prep(fpoly.buffer(-0.01)) if fpoly.area > 0.01 else prep(fpoly))
            widths.append(uw[i])
            n_units += 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('Road_Curb_Precast_Units')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    obj = bpy.data.objects.new('Road_Curb_Precast_Units', me)
    coll.objects.link(obj)
    obj['zc_visual_only'] = True
    obj['zc_v15'] = 'Precast kerb units (visual); collision = Kerb_Box_Collision_Proxy'
    fp = make_valid(union_all(footprints)) if footprints else Polygon()
    LOG['kerb_units'] = {'units': n_units, 'lines': len(merged), 'face_lines_road': len(face_road),
                         'face_lines_bed': len(face_bed), 'triangles': sum(len(p.vertices) - 2 for p in me.polygons),
                         'mean_width_m': round(sum(widths) / max(1, len(widths)), 3),
                         'unit_m': UNIT, 'curved_unit_m': UNIT_CURVED,
                         'covered_m2': round(fp.area, 2), 'zone_curb_m2': round(cz.area, 2),
                         'face_failures': face_failures, 'skipped_overlapping_units': skipped_overlap}
    if face_failures:
        raise RuntimeError(f'V15 kerb units: {face_failures} faces could not be created (non-manifold units)')
    return obj, fp


def trim_profiled_kerb(kerb_obj, footprint):
    """Delete visual profiled-kerb faces now covered by precast units (collision proxy untouched)."""
    if footprint.is_empty:
        return 0
    import numpy as np
    fp = footprint.buffer(0.012)
    me = kerb_obj.data
    mw = kerb_obj.matrix_world
    # A face goes when its centroid OR any vertex lies in a unit footprint (straddling triangles
    # would otherwise survive a few mm under the unit tops and z-fight at range).
    co = np.array([tuple((mw @ v.co)[:2]) for v in me.vertices]) if len(me.vertices) else np.zeros((0, 2))
    vin = contains_xy(fp, co[:, 0], co[:, 1]) if len(co) else np.zeros(0, bool)
    cs = [mw @ f.center for f in me.polygons]
    inside = contains_xy(fp, np.array([c.x for c in cs]), np.array([c.y for c in cs]))
    for k, f in enumerate(me.polygons):
        if not inside[k] and any(vin[v] for v in f.vertices):
            inside[k] = True
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    kill = [bm.faces[i] for i in np.nonzero(inside)[0]]
    bmesh.ops.delete(bm, geom=kill, context='FACES_ONLY')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(me); bm.free(); me.update()
    LOG['profiled_kerb_faces_removed'] = int(len(kill))
    return len(kill)


# ----------------------------------------------------------------------------- groundcover
ICEPLANT = ROOT / 'references/assets/crystalline_iceplant/crystalline_iceplant_1k.gltf'


def _iceplant_variants():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ICEPLANT))
    new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    variants = []
    for o in new:
        if o.type != 'MESH':
            continue
        me = o.data.copy()
        me.transform(Matrix.Diagonal((*o.matrix_world.to_scale(), 1.0)))
        # glTF Y-up was already converted; centre on origin, base at z=0.
        lo = [min(v.co[i] for v in me.vertices) for i in range(3)]
        hi = [max(v.co[i] for v in me.vertices) for i in range(3)]
        me.transform(Matrix.Translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])))
        variants.append(me)
    for mat in (variants[0].materials if variants else []):
        # V15: greener derived albedo (x(0.80, 1.0, 0.74), +15 % saturation) of the CC0 map;
        # the provider rosettes are yellow-olive, C02 groundcover reads mid green.
        for nd in (mat.node_tree.nodes if mat and mat.node_tree else []):
            if nd.type == 'TEX_IMAGE' and nd.image and 'diff' in nd.image.name:
                nd.image = _img(ICEPLANT.parent / 'textures/crystalline_iceplant_diff_1k_v15green.jpg', 'sRGB')
        if mat and not mat.get('zc_v12_foliage'):
            mat.name = 'M_V15_Iceplant_' + mat.name
            mat['zc_v12_foliage'] = True
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    return variants


def _clump(variants, seed, n, radius, ratio):
    mats = {tuple(m.name for m in v.materials) for v in variants}
    if len(mats) != 1:
        raise RuntimeError(f'iceplant variants use different material slots: {mats}')
    rng = random.Random(seed)
    bm = bmesh.new()
    for k in range(n):
        src = variants[rng.randrange(len(variants))]
        a = rng.uniform(0, 2 * math.pi); r = radius * math.sqrt(rng.random())
        s = rng.uniform(0.85, 1.35)
        M_ = Matrix.Translation((r * math.cos(a), r * math.sin(a), rng.uniform(-0.01, 0.0))) @ \
            Matrix.Rotation(rng.uniform(0, 2 * math.pi), 4, 'Z') @ Matrix.Scale(s, 4)
        tmp = src.copy(); tmp.transform(M_)
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    me = bpy.data.meshes.new(f'ASSET_V15_Groundcover_Iceplant_{seed}')
    bm.to_mesh(me); bm.free()
    for m in variants[0].materials:
        me.materials.append(m)
    o = bpy.data.objects.new('tmp_clump', me)
    bpy.context.scene.collection.objects.link(o)
    mod = o.modifiers.new('dec', 'DECIMATE'); mod.ratio = ratio; mod.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    baked = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.meshes.remove(me)
    baked.name = f'ASSET_V15_Groundcover_Iceplant_{seed}'
    return baked


def remove_plants_on_pavement():
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    zp = prep(ZONE)
    veg = {'Shrubs', 'Trees', 'Palms'}
    gone = []
    for o in list(bpy.data.objects):
        if o.type != 'MESH' or 'Shrubs' not in {c.name for c in o.users_collection}:
            continue
        x, y = o.location.x, o.location.y
        if not zp.contains(Point(x, y)):
            continue
        start = Vector((x, y, 30.0))
        for _ in range(30):
            hit, loc, nor, idx, ob, _m = sc.ray_cast(dg, start, Vector((0, 0, -1)))
            if not hit:
                break
            if {c.name for c in ob.users_collection} & veg:
                start = loc - Vector((0, 0, 0.01))
                continue
            if ob.name.startswith(('Road_', 'Plaza_Paving')):
                gone.append([o.name, o.data.name, round(x, 2), round(y, 2), ob.name])
                bpy.data.objects.remove(o, do_unlink=True)
            break
    return gone


def plant_groundcover():
    """Rows of ice-plant groundcover in the kerbed verge beds (C02). Positions avoid tree trunks.
    Asset: Poly Haven crystalline_iceplant (CC0), clumps of 12 rosettes, decimated to ~5 %."""
    if 'bed_inner' not in STATE:
        raise RuntimeError('V15 plant_groundcover: ground_system.rebuild() did not run in this process')
    bed = STATE['bed_inner']
    coll = bpy.data.collections.get('Shrubs')
    if coll is None:
        raise RuntimeError('V15 plant_groundcover: Shrubs collection missing')
    # V14 inherited defect: low planting standing ON road/paving in the pilot zone (median-gap
    # shrubs, G1 exterior xerophytes over the curved carriageways); runs independently of the beds.
    LOG['plants_on_pavement_removed'] = remove_plants_on_pavement()
    variants = _iceplant_variants()
    clumps = [_clump(variants, s, 12, 0.42, 0.05) for s in (1, 2, 3, 4)]
    for v in variants:
        if v.users == 0:
            bpy.data.meshes.remove(v)
    # C02 shows no round shrubs on the verges or the median: the procedural blob shrubs that
    # stood there are removed (the groundcover replaces them on the verges).
    zone_soft = union_all([bed, STATE.get('median', Polygon())]).buffer(0.3)
    zprep = prep(zone_soft)
    removed = 0
    for o in list(bpy.data.objects):
        if o.type != 'MESH' or not o.data.name.startswith(('ASSET_Shrub_Green_', 'ASSET_V7_Round_Shrub_')):
            continue
        if zprep.contains(Point(o.location.x, o.location.y)):
            bpy.data.objects.remove(o, do_unlink=True)
            removed += 1
    LOG['blob_shrubs_removed'] = removed
    trunks = [Point(o.location.x, o.location.y) for o in bpy.data.objects if o.type == 'MESH' and
              {c.name for c in o.users_collection} & {'Trees', 'Palms'} and bed.distance(Point(o.location.x, o.location.y)) < 1.]
    tprep = prep(union_all([t.buffer(0.7) for t in trunks])) if trunks else None
    core = make_valid(bed.buffer(-0.38))
    cprep = prep(core)
    rng = random.Random(1515)
    dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
    n = 0
    misses = 0
    minx, miny, maxx, maxy = core.bounds
    rows = []
    x = minx + 0.3
    while x <= maxx:
        rows.append(x); x += 0.7
    for xr in rows:
        y = miny + rng.uniform(0, 0.6)
        while y <= maxy:
            px, py = xr + rng.uniform(-0.08, 0.08), y
            y += rng.uniform(0.55, 0.75)
            q = Point(px, py)
            if not cprep.contains(q) or (tprep and tprep.contains(q)):
                continue
            # Ground only: skip tree crowns, palms and poles; accept the Lawns (bed) surface near bed level.
            start, loc = Vector((px, py, 30.0)), None
            for _ in range(30):
                hit, hl, nor, idx, ob, _m = sc.ray_cast(dg, start, Vector((0, 0, -1)))
                if not hit:
                    break
                if ob.name != 'Lawns':
                    start = hl - Vector((0, 0, 0.01))
                    continue
                loc = hl
                break
            if loc is None or abs(loc.z - STATE['bed_z'](px, py)) > 0.3:
                misses += 1
                continue
            o = bpy.data.objects.new(f'Groundcover_{n:05d}', clumps[rng.randrange(4)])
            o.location = (px, py, loc.z - 0.01)
            o.rotation_euler.z = rng.uniform(0, 2 * math.pi)
            s = rng.uniform(0.85, 1.1)
            o.scale = (s, s, s)
            o['zc_v15_groundcover'] = True
            coll.objects.link(o)
            n += 1
    LOG['groundcover'] = {'instances': n, 'rows_m': 0.7, 'clump_tris': [sum(len(p.vertices) - 2 for p in c.polygons) for c in clumps],
                          'asset': 'Poly Haven crystalline_iceplant (CC0)', 'trunk_clearance_m': 0.7,
                          'rejected_no_bed_ground': misses}
    return LOG['groundcover']


def write_log():
    out = ROOT / 'output/validation/v11'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'v15_corridor.json').write_text(json.dumps(LOG, indent=2), encoding='utf-8')
    print('[v15-corridor]', json.dumps(LOG), flush=True)
