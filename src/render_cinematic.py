"""Render one editable cinematic shot (CIN_* / TOUR_* camera) to an MP4 in Blender.

Edit the shot in Blender first if you like (see src/utilities/cinematics.py),
save the .blend, then:

    blender -b output/Zewail_City_3D.blend --python src/render_cinematic.py -- CIN_Admin_Closeup
    blender -b output/Zewail_City_3D.blend --python src/render_cinematic.py -- CIN_Aerial_Flyover --res 1920x1080 --engine cycles --samples 64

Options: --res WxH (default 1280x720), --engine eevee|cycles (default eevee),
--samples N, --step K (render every K-th frame, played back at fps/K), --out PATH.
Frames go to output/tours/frames_<shot>/, the MP4 to output/tours/<shot>.mp4 (needs ffmpeg on PATH).
"""
import os
import shutil
import subprocess
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from utilities import scene_setup  # noqa: E402


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not argv:
        raise SystemExit("usage: ... --python src/render_cinematic.py -- <SHOT_NAME> [--res WxH] [--engine eevee|cycles]")
    opts = {"shot": argv[0], "res": "1280x720", "engine": "eevee", "samples": None, "step": 1, "out": None}
    it = iter(argv[1:])
    for a in it:
        key = a.lstrip("-")
        opts[key] = next(it)
    return opts


def main():
    o = parse()
    scene = bpy.context.scene
    cam = bpy.data.objects.get(o["shot"])
    if cam is None or cam.type != 'CAMERA':
        names = [ob.name for ob in scene.objects if ob.get("zc_shot")]
        raise SystemExit(f"shot {o['shot']!r} not found; available: {names}")
    w, h = (int(v) for v in o["res"].lower().split("x"))
    step = int(o["step"])
    fps = int(cam.get("zc_fps", 30))
    scene.camera = cam
    scene.frame_start = int(cam["zc_frame_start"])
    scene.frame_end = int(cam["zc_frame_end"])
    scene.frame_step = step
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.resolution_percentage = 100
    scene.render.fps = fps
    if o["engine"].lower().startswith("eevee"):
        ids = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
        scene.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in ids else 'BLENDER_EEVEE_NEXT'
        if o["samples"]:
            scene.eevee.taa_render_samples = int(o["samples"])
        else:
            scene.eevee.taa_render_samples = 32
    else:
        scene.render.engine = 'CYCLES'
        scene_setup.enable_gpu(scene)
        scene.cycles.samples = int(o["samples"] or 64)
        scene.cycles.use_denoising = True
    frames_dir = os.path.join(ROOT, "output", "tours", f"frames_{cam.name}")
    if os.path.isdir(frames_dir):
        shutil.rmtree(frames_dir)
    os.makedirs(frames_dir)
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = os.path.join(frames_dir, "f_")
    bpy.ops.render.render(animation=True)
    out = o["out"] or os.path.join(ROOT, "output", "tours", f"{cam.name}.mp4")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print(f"[cinematic] frames in {frames_dir}; ffmpeg not found, skipping MP4")
        return
    files = sorted(f for f in os.listdir(frames_dir) if f.endswith(".png"))
    listfile = os.path.join(frames_dir, "frames.txt")
    with open(listfile, "w") as fh:
        for f in files:
            fh.write(f"file '{f}'\nduration {step / fps:.6f}\n")
    subprocess.run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", listfile, "-r", str(fps),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out], check=True)
    print(f"[cinematic] wrote {out} ({len(files)} frames)")


if __name__ == "__main__":
    main()
