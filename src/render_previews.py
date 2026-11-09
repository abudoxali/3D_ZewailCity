"""Render the presentation cameras of output/Zewail_City_3D.blend to output/previews/.

Usage (from the project root):
    blender -b output/Zewail_City_3D.blend --python src/render_previews.py -- [--samples N] [--scale P] [CAM_...]
"""
import os
import sys

import bpy

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SRC)
sys.path.insert(0, SRC)

from utilities.scene_setup import PREVIEW_FILES, enable_gpu  # noqa: E402


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opts = {'samples': None, 'scale': 100, 'cams': []}
    i = 0
    while i < len(argv):
        if argv[i] == "--samples":
            opts['samples'] = int(argv[i + 1]); i += 2
        elif argv[i] == "--scale":
            opts['scale'] = int(argv[i + 1]); i += 2
        else:
            opts['cams'].append(argv[i]); i += 1
    return opts


def main():
    opts = parse_args()
    scene = bpy.context.scene
    print("[render] device:", enable_gpu(scene))
    if opts['samples']:
        scene.cycles.samples = opts['samples']
    scene.render.resolution_percentage = opts['scale']
    out_dir = os.path.join(ROOT, "output", "previews")
    os.makedirs(out_dir, exist_ok=True)
    for name in opts['cams'] or list(PREVIEW_FILES):
        cam = bpy.data.objects[name]
        scene.camera = cam
        scene.render.resolution_x, scene.render.resolution_y = cam.get('resolution', (1920, 1080))
        scene.render.filepath = os.path.join(out_dir, PREVIEW_FILES.get(name, name + ".png"))
        bpy.ops.render.render(write_still=True)
        print("[render] wrote", scene.render.filepath)


if __name__ == "__main__":
    main()
