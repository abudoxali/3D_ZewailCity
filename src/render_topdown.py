"""Orthographic top-down render in the survey overlay frame (1 px = 1 m).

The frame matches references/geodata/s2_20260916_axis.png and the OSM overlays:
x -560..560, axis-frame y -560..640, i.e. Blender y -806.1..393.9 (dome at axis y 246.1).
Used by tools/geo/overlay.js for the masterplan comparison.

Usage:
    blender -b <file.blend> --python src/render_topdown.py -- <out.png> [--samples 16] [--scale 1.0]
        [--rect x0 x1 y0 y1]   (Blender metres; default = survey overlay frame)
"""
import math
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = argv[0] if argv else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                        "output", "validation", "v4_topdown.png")
samples = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 16
scale = float(argv[argv.index("--scale") + 1]) if "--scale" in argv else 1.0

X0, X1, Y0, Y1 = -560.0, 560.0, -806.1, 393.9
if "--rect" in argv:
    i = argv.index("--rect")
    X0, X1, Y0, Y1 = (float(v) for v in argv[i + 1:i + 5])
sc = bpy.context.scene
for c in ("Unverified_Masterplan_Proposals",):
    coll = bpy.data.collections.get(c)
    if coll:
        coll.hide_render = True
cam_data = bpy.data.cameras.new("TOPDOWN")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = max(X1 - X0, Y1 - Y0)
cam_data.clip_start, cam_data.clip_end = 1.0, 3000.0
cam = bpy.data.objects.new("TOPDOWN", cam_data)
sc.collection.objects.link(cam)
cam.location = ((X0 + X1) / 2, (Y0 + Y1) / 2, 1500.0)
cam.rotation_euler = (0.0, 0.0, 0.0)
sc.camera = cam
sc.render.resolution_x = int((X1 - X0) * scale)
sc.render.resolution_y = int((Y1 - Y0) * scale)
sc.render.resolution_percentage = 100
sc.render.engine = 'CYCLES'
sc.cycles.samples = samples
sc.cycles.use_denoising = True
try:
    sc.cycles.device = 'GPU'
except Exception:
    pass
sc.render.film_transparent = False
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("[topdown] wrote", out)
