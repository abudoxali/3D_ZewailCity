"""Render the CAM_Turntable orbit as PNG frames.

Usage (from the project root):
    blender -b output/Zewail_City_3D.blend --python src/render_turntable.py -- <frames_dir> [samples] [step]
Then encode, e.g.:
    ffmpeg -framerate 30 -i <frames_dir>/frame_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 20 output/previews/turntable.mp4
"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utilities.scene_setup import enable_gpu  # noqa: E402


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out_dir = os.path.abspath(argv[0]) if argv else os.path.join(os.path.dirname(bpy.data.filepath), "turntable_frames")
    samples = int(argv[1]) if len(argv) > 1 else 24
    step = int(argv[2]) if len(argv) > 2 else 1
    scene = bpy.context.scene
    enable_gpu(scene)
    scene.camera = bpy.data.objects["CAM_Turntable"]
    scene.cycles.samples = samples
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    scene.render.resolution_percentage = 75
    os.makedirs(out_dir, exist_ok=True)
    # render frame by frame so output names stay sequential even when step > 1
    for i, frame in enumerate(range(scene.frame_start, scene.frame_end + 1, step), start=1):
        scene.frame_set(frame)
        scene.render.filepath = os.path.join(out_dir, f"frame_{i:04d}.png")
        bpy.ops.render.render(write_still=True)
    print("[turntable] frames in", out_dir)


if __name__ == "__main__":
    main()
