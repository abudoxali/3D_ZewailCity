"""Low-level mesh helpers: collections, polylines and a bmesh-based MeshBuilder.

All coordinates are in metres, X = east, Y = north, Z = up.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector, noise


# ---------------------------------------------------------------- collections
def get_collection(name, parent=None):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        (parent if parent else bpy.context.scene.collection).children.link(coll)
    return coll


# ------------------------------------------------------------------ polygons
def signed_area(poly):
    a = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        a += x0 * y1 - x1 * y0
    return a / 2.0


def ccw(poly):
    poly = [(float(p[0]), float(p[1])) for p in poly]
    return poly if signed_area(poly) > 0 else poly[::-1]


def rect_poly(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def circle_poly(cx, cy, r, n=48):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def arc_points(cx, cy, r, a0, a1, n):
    """Points on a circular arc, angles in degrees, inclusive of both ends."""
    pts = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def arc_band(cx, cy, r_in, r_out, a0, a1, n=24):
    outer = arc_points(cx, cy, r_out, a0, a1, n)
    inner = arc_points(cx, cy, r_in, a1, a0, n)
    return ccw(outer + inner)


def bezier(p0, p1, p2, p3, n=24):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0]
        y = u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]
        pts.append((x, y))
    return pts


def join_paths(*paths):
    out = []
    for p in paths:
        for q in p:
            if out and (Vector(out[-1]) - Vector(q)).length < 1e-3:
                continue
            out.append(q)
    return out


def resample(pts, step):
    """Resample an open polyline at roughly uniform spacing (keeps both ends)."""
    pts = [Vector((p[0], p[1])) for p in pts]
    out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        seg = (b - a).length
        n = max(1, int(math.ceil(seg / step)))
        for i in range(1, n + 1):
            out.append(a.lerp(b, i / n))
    return out


def tangents(pts):
    ts = []
    n = len(pts)
    for i in range(n):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = (pts[i + 1] - pts[i]).normalized() + (pts[i] - pts[i - 1]).normalized()
        if t.length < 1e-9:
            t = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        ts.append(t.normalized())
    return ts


def offset(pts, d):
    """Offset a polyline; positive d is to the left of the travel direction."""
    out = []
    for p, t in zip(pts, tangents(pts)):
        out.append(p + Vector((-t.y, t.x)) * d)
    return out


def path_length(pts):
    return sum((b - a).length for a, b in zip(pts[:-1], pts[1:]))


def sample_along(pts, spacing, start=0.0, end_margin=0.0):
    """Yield (position, unit tangent) every `spacing` metres along a polyline."""
    pts = [Vector((p[0], p[1])) for p in pts]
    total = path_length(pts)
    out = []
    d = start
    seg_i, seg_start = 0, 0.0
    while d <= total - end_margin + 1e-6:
        while seg_i < len(pts) - 2 and seg_start + (pts[seg_i + 1] - pts[seg_i]).length < d:
            seg_start += (pts[seg_i + 1] - pts[seg_i]).length
            seg_i += 1
        a, b = pts[seg_i], pts[seg_i + 1]
        seg = (b - a).length
        f = 0.0 if seg < 1e-9 else min(1.0, (d - seg_start) / seg)
        out.append((a.lerp(b, f), (b - a).normalized()))
        d += spacing
    return out


def seg_intersections(pa, pb):
    """All intersection points between two polylines (lists of (x, y))."""
    out = []
    for a0, a1 in zip(pa[:-1], pa[1:]):
        for b0, b1 in zip(pb[:-1], pb[1:]):
            d = (a1[0] - a0[0]) * (b1[1] - b0[1]) - (a1[1] - a0[1]) * (b1[0] - b0[0])
            if abs(d) < 1e-9:
                continue
            t = ((b0[0] - a0[0]) * (b1[1] - b0[1]) - (b0[1] - a0[1]) * (b1[0] - b0[0])) / d
            u = ((b0[0] - a0[0]) * (a1[1] - a0[1]) - (b0[1] - a0[1]) * (a1[0] - a0[0])) / d
            if 0 <= t <= 1 and 0 <= u <= 1:
                out.append((a0[0] + t * (a1[0] - a0[0]), a0[1] + t * (a1[1] - a0[1])))
    return out


def smooth_polyline(pts, iterations=2):
    """Chaikin corner cutting (keeps the end points)."""
    pts = [tuple(p) for p in pts]
    for _ in range(iterations):
        if len(pts) < 3:
            return pts
        out = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            out.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            out.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        out.append(pts[-1])
        pts = out
    return pts


def dist_to_polyline(p, pts):
    best = 1e18
    px, py = p
    for a, b in zip(pts[:-1], pts[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / L2))
        qx, qy = a[0] + t * dx, a[1] + t * dy
        d = (px - qx) ** 2 + (py - qy) ** 2
        if d < best:
            best = d
    return math.sqrt(best)


def in_zones(p, zones):
    return any((Vector((p[0], p[1])) - Vector((z[0], z[1]))).length < z[2] for z in zones)


def runs_outside(pts, zones):
    """Split a dense polyline into runs that avoid circular zones (x, y, r)."""
    runs, cur = [], []
    for p in pts:
        if in_zones(p, zones):
            if len(cur) > 1:
                runs.append(cur)
            cur = []
        else:
            cur.append(p)
    if len(cur) > 1:
        runs.append(cur)
    return runs


# --------------------------------------------------------------------- edges
class Edge:
    """A straight facade line. Outward normal points to the right of p0->p1,
    which is outside for counter-clockwise footprints."""

    def __init__(self, p0, p1):
        self.p0 = Vector((p0[0], p0[1]))
        self.p1 = Vector((p1[0], p1[1]))
        d = self.p1 - self.p0
        self.L = d.length
        self.t = d / self.L
        self.n = Vector((self.t.y, -self.t.x))
        self.angle = math.atan2(self.t.y, self.t.x)

    def at(self, s, off=0.0):
        return self.p0 + self.t * s + self.n * off


def poly_edges(poly):
    poly = ccw(poly)
    return [Edge(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]


# --------------------------------------------------------------- MeshBuilder
class MeshBuilder:
    """Accumulates geometry with per-face material indices, then emits one mesh."""

    def __init__(self):
        self.bm = bmesh.new()
        self.mats = []

    def empty(self):
        return len(self.bm.verts) == 0

    def _mi(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def _tag(self, verts, mat, smooth=False, smooth_sides_only=False):
        mi = self._mi(mat)
        for f in {f for v in verts for f in v.link_faces}:
            f.material_index = mi
            if smooth_sides_only:
                f.smooth = abs(f.normal.z) < 0.5
            else:
                f.smooth = smooth

    # -- primitives
    def obox(self, mat, center, size, angle=0.0):
        sx, sy, sz = size
        if sx <= 0 or sy <= 0 or sz <= 0:
            return
        m = Matrix.Translation(Vector(center)) @ Matrix.Rotation(angle, 4, 'Z') @ Matrix.Diagonal((sx, sy, sz, 1.0))
        r = bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)
        self._tag(r['verts'], mat)

    def box(self, mat, x0, y0, z0, x1, y1, z1):
        self.obox(mat, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)))

    def fbox(self, mat, e, s, off, d, w, z0, z1):
        """Box attached to facade edge `e`: centred at arc length s, inner face at
        `off` metres from the wall plane, `d` deep (outwards), `w` wide."""
        c = e.at(s, off + d / 2.0)
        self.obox(mat, (c.x, c.y, (z0 + z1) / 2.0), (w, d, z1 - z0), e.angle)

    def cylinder(self, mat, xy, z0, z1, r1, r2=None, segs=16, smooth=True, caps=True):
        r2 = r1 if r2 is None else r2
        m = Matrix.Translation((xy[0], xy[1], (z0 + z1) / 2.0))
        res = bmesh.ops.create_cone(self.bm, cap_ends=caps, cap_tris=False, segments=segs,
                                    radius1=r1, radius2=r2, depth=z1 - z0, matrix=m)
        self._tag(res['verts'], mat, smooth_sides_only=smooth)

    def cylinder_matrix(self, mat, matrix, r, depth, segs=16):
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=segs,
                                    radius1=r, radius2=r, depth=depth, matrix=matrix)
        self._tag(res['verts'], mat)

    def ico(self, mat, center, radius, subdiv=2, scale=(1, 1, 1), jitter=0.0, seed=0.0):
        m = Matrix.Translation(Vector(center)) @ Matrix.Diagonal((*scale, 1.0))
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=subdiv, radius=radius, matrix=m)
        if jitter:
            c = Vector(center)
            for v in res['verts']:
                d = v.co - c
                n = noise.noise(v.co * 0.9 + Vector((seed, seed * 1.7, seed * 0.3))) * jitter
                v.co += d.normalized() * n
        self._tag(res['verts'], mat, smooth=True)

    def prism(self, mat, poly, z0, z1):
        poly = ccw(poly)
        bot = [self.bm.verts.new((x, y, z0)) for x, y in poly]
        top = [self.bm.verts.new((x, y, z1)) for x, y in poly]
        faces = [self.bm.faces.new(list(reversed(bot))), self.bm.faces.new(top)]
        n = len(poly)
        for i in range(n):
            j = (i + 1) % n
            faces.append(self.bm.faces.new((bot[i], bot[j], top[j], top[i])))
        mi = self._mi(mat)
        for f in faces:
            f.material_index = mi

    def raw(self, mat, verts, faces, smooth=False):
        bv = [self.bm.verts.new(v) for v in verts]
        mi = self._mi(mat)
        for f in faces:
            face = self.bm.faces.new([bv[i] for i in f])
            face.material_index = mi
            face.smooth = smooth

    def ridge(self, mat, x_c, y0, y1, z0, w, h):
        """Triangular prism with its ridge running along Y."""
        x0, x1 = x_c - w / 2, x_c + w / 2
        v = [(x0, y0, z0), (x1, y0, z0), (x_c, y0, z0 + h), (x0, y1, z0), (x1, y1, z0), (x_c, y1, z0 + h)]
        f = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
        self.raw(mat, v, f)

    def hemisphere(self, mat, c, r, segs=64, rings=18):
        verts, faces = [], []
        for j in range(rings):
            phi = (math.pi / 2) * j / rings
            z = c[2] + r * math.sin(phi)
            rr = r * math.cos(phi)
            for i in range(segs):
                a = 2 * math.pi * i / segs
                verts.append((c[0] + rr * math.cos(a), c[1] + rr * math.sin(a), z))
        verts.append((c[0], c[1], c[2] + r))
        top = len(verts) - 1
        for j in range(rings - 1):
            for i in range(segs):
                a, b = j * segs + i, j * segs + (i + 1) % segs
                faces.append((a, b, b + segs, a + segs))
        base = (rings - 1) * segs
        for i in range(segs):
            faces.append((base + i, base + (i + 1) % segs, top))
        self.raw(mat, verts, faces, smooth=True)

    def ribbon(self, mat, pts, a, b, z, depth=0.0):
        """Strip between lateral offsets a < b along a dense polyline, top at z.
        With depth > 0 the strip gets side walls (curbs, medians, sidewalks)."""
        if len(pts) < 2:
            return
        la, lb = offset(pts, a), offset(pts, b)
        n = len(pts)
        verts = [(p.x, p.y, z) for p in la] + [(p.x, p.y, z) for p in lb]
        faces = [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)]
        if depth > 0:
            zb = z - depth
            base = len(verts)
            verts += [(p.x, p.y, zb) for p in la] + [(p.x, p.y, zb) for p in lb]
            for i in range(n - 1):
                faces.append((base + i, base + i + 1, i + 1, i))
                faces.append((n + i, n + i + 1, base + n + i + 1, base + n + i))
            faces.append((0, n, base + n, base))
            faces.append((n - 1, base + n - 1, base + 2 * n - 1, 2 * n - 1))
        self.raw(mat, verts, faces)

    def ribbon_var(self, mat, pts, ab, z, depth=0.0):
        """Like ribbon(), but with per-point lateral offsets ab[i] = (a_i, b_i)."""
        if len(pts) < 2:
            return
        ts = tangents(pts)
        la = [p + Vector((-t.y, t.x)) * a for p, t, (a, b) in zip(pts, ts, ab)]
        lb = [p + Vector((-t.y, t.x)) * b for p, t, (a, b) in zip(pts, ts, ab)]
        n = len(pts)
        verts = [(p.x, p.y, z) for p in la] + [(p.x, p.y, z) for p in lb]
        faces = [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)]
        if depth > 0:
            zb = z - depth
            base = len(verts)
            verts += [(p.x, p.y, zb) for p in la] + [(p.x, p.y, zb) for p in lb]
            for i in range(n - 1):
                faces.append((base + i, base + i + 1, i + 1, i))
                faces.append((n + i, n + i + 1, base + n + i + 1, base + n + i))
            faces.append((0, n, base + n, base))
            faces.append((n - 1, base + n - 1, base + 2 * n - 1, 2 * n - 1))
        self.raw(mat, verts, faces)

    def add_mesh(self, mat, me, matrix=None):
        """Merge an existing mesh datablock; every merged face gets `mat`."""
        tmp = me.copy()
        if matrix is not None:
            tmp.transform(matrix)
        n0 = len(self.bm.faces)
        self.bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
        mi = self._mi(mat)
        self.bm.faces.ensure_lookup_table()
        for f in self.bm.faces[n0:]:
            f.material_index = mi
            f.smooth = False

    def isoband(self, mat, field, x0, y0, step, nx, ny, lo, hi, z, mask=None):
        """Flat mesh of the region where lo <= field(i, j) < hi on a regular grid
        (marching squares, linear edge interpolation; saddles resolved by the cell
        centre). `mask(x, y)` can exclude whole cells. Returns the face count."""
        def inside(v):
            return lo <= v < hi

        def cross(pa, va, pb, vb, thr):
            t = (thr - va) / (vb - va) if vb != va else 0.5
            t = min(1.0, max(0.0, t))
            return (pa[0] + (pb[0] - pa[0]) * t, pa[1] + (pb[1] - pa[1]) * t)

        def clip_edge(pa, va, pb, vb):
            """Points of segment a->b inside the band (excluding a, including b if inside)."""
            out = []
            for thr in sorted({lo, hi}, reverse=(vb < va)):
                if (va < thr) != (vb < thr):
                    out.append(cross(pa, va, pb, vb, thr))
            if inside(vb):
                out.append(pb)
            return out

        mi = self._mi(mat)
        nf = 0
        for j in range(ny - 1):
            for i in range(nx - 1):
                cx, cy = x0 + (i + 0.5) * step, y0 + (j + 0.5) * step
                if mask is not None and not mask(cx, cy):
                    continue
                ps = [(x0 + i * step, y0 + j * step), (x0 + (i + 1) * step, y0 + j * step),
                      (x0 + (i + 1) * step, y0 + (j + 1) * step), (x0 + i * step, y0 + (j + 1) * step)]
                vs = [field(i, j), field(i + 1, j), field(i + 1, j + 1), field(i, j + 1)]
                ins = [inside(v) for v in vs]
                if not any(ins) and min(vs) >= lo and max(vs) < hi:
                    continue
                if all(ins):
                    poly = ps
                else:
                    poly = [ps[0]] if ins[0] else []
                    for k in range(4):
                        poly += clip_edge(ps[k], vs[k], ps[(k + 1) % 4], vs[(k + 1) % 4])
                    # drop duplicate closing point
                    if len(poly) > 1 and poly[0] == poly[-1]:
                        poly.pop()
                if len(poly) < 3:
                    continue
                # a clipped convex cell can become non-convex only at saddles; fan from the
                # centroid keeps it valid in both cases
                ccx = sum(p[0] for p in poly) / len(poly)
                ccy = sum(p[1] for p in poly) / len(poly)
                if len(poly) <= 4:
                    vv = [self.bm.verts.new((p[0], p[1], z)) for p in poly]
                    try:
                        f = self.bm.faces.new(vv)
                        f.material_index = mi
                        nf += 1
                    except ValueError:
                        pass
                else:
                    c = self.bm.verts.new((ccx, ccy, z))
                    vv = [self.bm.verts.new((p[0], p[1], z)) for p in poly]
                    for k in range(len(vv)):
                        try:
                            f = self.bm.faces.new((c, vv[k], vv[(k + 1) % len(vv)]))
                            f.material_index = mi
                            nf += 1
                        except ValueError:
                            pass
        return nf

    def weld(self, dist=0.001):
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=dist)

    def dashes(self, mat, pts, off, w, dash, gap, z, zones=(), start=0.0):
        for p, t in sample_along(pts, dash + gap, start=start + dash / 2, end_margin=dash / 2):
            c = p + Vector((-t.y, t.x)) * off
            if zones and in_zones(c, zones):
                continue
            self.obox(mat, (c.x, c.y, z), (dash, w, 0.02), math.atan2(t.y, t.x))

    # -- output
    def to_mesh(self, name):
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        return me

    def to_object(self, name, coll, recenter=True):
        me = self.to_mesh(name)
        obj = bpy.data.objects.new(name, me)
        if recenter and len(me.vertices):
            xs = [v.co.x for v in me.vertices]
            ys = [v.co.y for v in me.vertices]
            zs = [v.co.z for v in me.vertices]
            c = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)))
            me.transform(Matrix.Translation(-c))
            obj.location = c
        coll.objects.link(obj)
        return obj


def parent_keep(child, parent):
    child.parent = parent
    child.matrix_parent_inverse = Matrix.Translation(parent.location).inverted()


def add_bevel(obj, width=0.05, segments=1, angle=40.0):
    mod = obj.modifiers.new("Bevel", 'BEVEL')
    mod.width = width
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    mod.angle_limit = math.radians(angle)
    return mod


def instance(mesh, name, coll, loc, rot_z=0.0, scale=1.0):
    """Linked duplicate: a new object that shares `mesh` data."""
    obj = bpy.data.objects.new(name, mesh)
    obj.location = (loc[0], loc[1], loc[2] if len(loc) > 2 else 0.0)
    obj.rotation_euler = (0.0, 0.0, rot_z)
    s = scale if isinstance(scale, (tuple, list)) else (scale, scale, scale)
    obj.scale = s
    coll.objects.link(obj)
    return obj
