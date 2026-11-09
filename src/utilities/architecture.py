"""Reusable facade / massing toolkit used by buildings.py.

Each building becomes three objects:
  <name>          shell (walls, roof masses)            -> Main_ / Secondary_Buildings
  <name>_Glass    glazing                                -> Windows_And_Glass
  <name>_Details  fins, frames, bands, parapets, plant  -> Architectural_Details
Glass and details are parented to the shell, so moving or rotating the shell
moves the whole building.
"""
import math

from .geometry import Edge, MeshBuilder, add_bevel, parent_keep, poly_edges, rect_poly

GROUND = 0.21  # top of plaza paving (V4: 0.15 m curbs above the 0.06 m road surface); buildings start here


class Parts:
    def __init__(self, name, M):
        self.name = name
        self.M = M
        self.shell = MeshBuilder()
        self.glass = MeshBuilder()
        self.det = MeshBuilder()

    def finish(self, C, coll_key='main', bevel=0.04, location=None, angle_deg=0.0):
        """Create the three objects. With `location`, geometry built around the
        local origin is placed at location and rotated by angle_deg about Z."""
        shell = self.shell.to_object(self.name, C[coll_key])
        if bevel:
            add_bevel(shell, width=bevel)
        children = []
        for mb, key, suffix in ((self.glass, 'glass', '_Glass'), (self.det, 'details', '_Details')):
            if mb.empty():
                continue
            o = mb.to_object(self.name + suffix, C[key])
            parent_keep(o, shell)
            children.append(o)
        if location is not None:
            # shell origin sits at its bbox centre; move that point to `location`
            off_x, off_y = shell.location.x, shell.location.y
            a = math.radians(angle_deg)
            rx = off_x * math.cos(a) - off_y * math.sin(a)
            ry = off_x * math.sin(a) + off_y * math.cos(a)
            shell.location = (location[0] + rx, location[1] + ry, shell.location.z)
            shell.rotation_euler = (0.0, 0.0, a)
        return shell

    # ------------------------------------------------------------ massing
    def block(self, poly, z0, z1, mat=None):
        self.shell.prism(mat or self.M['stone'], poly, z0, z1)
        return poly_edges(poly)

    def rblock(self, x0, y0, x1, y1, z0, z1, mat=None):
        return self.block(rect_poly(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)), z0, z1, mat)

    def parapet(self, poly, z, h=0.9, t=0.35, band=True):
        self.det.prism(self.M['roof'], poly, z - 0.01, z + 0.04)  # roof membrane finish
        for e in poly_edges(poly):
            self.det.fbox(self.M['stone'], e, e.L / 2, -t, t, e.L, z, z + h)
            if band:  # dark granite coping band seen on every block in A02/A03
                self.det.fbox(self.M['band'], e, e.L / 2, 0.0, 0.05, e.L, z - 1.2, z - 0.5)

    def band(self, e, s0, s1, z0, z1, depth=0.06):
        self.det.fbox(self.M['band'], e, (s0 + s1) / 2, 0.0, depth, s1 - s0, z0, z1)

    def roof_plant(self, x0, y0, x1, y1, z, rng, n=3):
        for _ in range(n):
            w, d, h = rng.uniform(3, 6), rng.uniform(2.5, 4.5), rng.uniform(1.2, 2.2)
            cx = rng.uniform(x0 + w / 2 + 1.5, max(x0 + w / 2 + 1.6, x1 - w / 2 - 1.5))
            cy = rng.uniform(y0 + d / 2 + 1.5, max(y0 + d / 2 + 1.6, y1 - d / 2 - 1.5))
            self.det.box(self.M['metal_light'], cx - w / 2, cy - d / 2, z, cx + w / 2, cy + d / 2, z + h)
            self.det.box(self.M['metal'], cx - w / 2 - 0.05, cy - d / 2 - 0.05, z + h * 0.35,
                         cx + w / 2 + 0.05, cy + d / 2 + 0.05, z + h * 0.7)

    # ------------------------------------------------------------ facades
    def curtain(self, e, s0, s1, z0, z1, mull=1.6, transom=3.6, depth=0.14, mat=None, off=0.0):
        """Glazing with dark mullions/transoms (A02: dark grey framed curtain walls)."""
        w = s1 - s0
        if w <= 0.2 or z1 - z0 <= 0.2:
            return
        self.glass.fbox(mat or self.M['glass'], e, (s0 + s1) / 2, off, 0.06, w, z0, z1)
        n = max(1, int(round(w / mull)))
        for i in range(n + 1):
            self.det.fbox(self.M['metal'], e, s0 + w * i / n, off + 0.04, depth, 0.09, z0, z1)
        m = max(1, int(round((z1 - z0) / transom)))
        for j in range(m + 1):
            z = z0 + (z1 - z0) * j / m
            self.det.fbox(self.M['metal'], e, (s0 + s1) / 2, off + 0.04, depth, w, z - 0.05, z + 0.05)

    def recess(self, e, s0, s1, z0, z1, depth=1.2, mull=1.6, transom=3.6):
        """Glazing set back behind a stone reveal.

        V3 fix: V2 placed the glass `depth` metres *behind* the wall plane, i.e.
        inside the solid shell, so it never rendered. The shell has no opening to
        cut, so the glazing now sits on the wall plane and the stone reveals and
        head project `depth` outward, which gives the same set-back reading."""
        st = self.M['stone']
        self.curtain(e, s0, s1, z0, z1, mull=mull, transom=transom, off=0.02)
        self.det.fbox(st, e, s0 - 0.25, 0.0, depth, 0.5, z0 - 0.2, z1)
        self.det.fbox(st, e, s1 + 0.25, 0.0, depth, 0.5, z0 - 0.2, z1)
        self.det.fbox(st, e, (s0 + s1) / 2, 0.0, depth, s1 - s0 + 1.0, z1, z1 + 0.6)

    def frame(self, e, s0, s1, z0, z1, t=0.9, depth=1.2):
        """Projecting stone portal frame around an opening (A02 ground/upper frames)."""
        st = self.M['stone']
        self.det.fbox(st, e, s0 - t / 2, 0.0, depth, t, z0, z1 + t)
        self.det.fbox(st, e, s1 + t / 2, 0.0, depth, t, z0, z1 + t)
        self.det.fbox(st, e, (s0 + s1) / 2, 0.0, depth, s1 - s0 + 2 * t, z1, z1 + t)

    def slits(self, e, z0, z1, spacing=4.0, w=0.9, floors=1, margin=2.5, s0=None, s1=None, frame=0.25):
        s0 = margin if s0 is None else s0
        s1 = e.L - margin if s1 is None else s1
        span = s1 - s0
        if span < w:
            return
        n = int(span // spacing) + 1
        start = s0 + (span - (n - 1) * spacing) / 2
        fh = (z1 - z0) / floors
        for i in range(n):
            s = start + i * spacing
            for f in range(floors):
                a = z0 + f * fh + 0.12 * fh
                b = z0 + (f + 1) * fh - 0.10 * fh
                self.glass.fbox(self.M['glass'], e, s, 0.0, 0.06, w, a, b)
                self.det.fbox(self.M['band'], e, s, 0.0, 0.1, w + 2 * frame, b, b + frame)

    def window_rows(self, e, z_levels, w=1.6, h=2.0, spacing=3.2, group=1, gap=0.5, margin=2.0, s0=None, s1=None):
        """Punched windows in groups (A01: east institute)."""
        s0 = margin if s0 is None else s0
        s1 = e.L - margin if s1 is None else s1
        unit = group * w + (group - 1) * gap
        n = max(1, int((s1 - s0) // (unit + spacing)))
        start = s0 + ((s1 - s0) - (n * unit + (n - 1) * spacing)) / 2
        for z in z_levels:
            for i in range(n):
                g0 = start + i * (unit + spacing)
                for k in range(group):
                    s = g0 + k * (w + gap) + w / 2
                    self.glass.fbox(self.M['glass'], e, s, 0.0, 0.06, w, z, z + h)
                    self.det.fbox(self.M['band'], e, s, 0.0, 0.08, w, z - 0.15, z)

    def piers(self, e, s0, s1, z0, z1, spacing, w=1.2, depth=1.5, off=0.0, mat=None):
        n = max(1, int(round((s1 - s0) / spacing)))
        for i in range(n + 1):
            self.det.fbox(mat or self.M['stone'], e, s0 + (s1 - s0) * i / n, off, depth, w, z0, z1)

    def steps(self, e, s, w, n=4, rise=0.17, tread=0.4, z0=GROUND):
        for i in range(n):
            self.shell.fbox(self.M['stone'], e, s, 0.0, tread * (n - i), w, z0, z0 + rise * (i + 1))
