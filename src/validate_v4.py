"""V4 photo-matched validation renders and comparisons -> output/validation/v4/.

Each reference photograph has a camera pose estimated from features whose position is
known independently of the model (gate frame and circular bed from OSM/photo scale, the
dome, the approach axis). The same camera is rendered from the V3 backup scene and the V4
scene, so the comparison shows what changed, not a different viewpoint. No numerical
"accuracy score" is produced; mismatches are recorded in output/validation/v4/PHOTO_MATCH_REPORT.md.

Usage (from the project root):
    blender -b <scene.blend> --python src/validate_v4.py -- --tag v4|v3 [--only C02,A02] [--samples 32] [--scale 0.5]
    blender -b --python src/validate_v4.py -- --compose          (ffmpeg composites only)

Camera table: (photo file, location, target, lens mm (36 mm sensor width), photo aspect,
evidence note for the pose).
"""
import math
import os
import shutil
import subprocess
import sys

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SRC)
OUT = os.environ.get('ZC_VALIDATE_OUT') or os.path.join(ROOT, "output", "validation", "v4")
REF = os.path.join(ROOT, "references", "source_images")
GY = 314.6

CAMS = {
    # C02 (Commons, 2017-11-18 14:55): taken from the admin portico roof looking back at the gate.
    # Pose from the bed centre (row 980/1126) and the gate frame width (353/2000 px):
    # camera y ~30 m, z ~11 m, horizontal FOV 38 deg.
    "C02_gate_from_admin": ("v4/C02_commons_zewail_city_approach_2017.jpg", (0.0, 30.0, 11.0),
                            (0.0, GY, -8.9), 52.3, (2000, 1126)),
    # C01 / D03 (Commons 2017-11-18 10:46 = official "Landscape" image): outside the gate, on the
    # landscaped island, looking at the gatehouse and the portal frame.
    "C01_gate_exterior": ("v4/C01_commons_zewail_city_gates_2017.jpg", (8.0, GY + 38.0, 1.6),
                          (-12.0, GY + 4.0, 6.5), 26.0, (2000, 1164)),
    # A02 (Hassan Allam): eye height on the wedge lawn behind the circular bed (bed spans 0.66 of
    # the frame width, ellipse ratio 0.106 -> ~18 m from the bed, 1.9 m high); HFOV ~63 deg.
    "A02_admin_front": ("A02_hassanallam_admin_building.jpg", (0.0, 98.0, 1.9), (0.0, 0.0, 19.0), 29.4,
                        (1536, 1024)),
    # A03 (official close-up of the drum, dome and west side).
    "A03_dome_west": ("A03_official_admin_building.jpg", (-44.0, 64.0, 2.0), (-2.0, -2.0, 22.0), 48.0,
                      (1500, 1317)),
    # A01 (official 2025 drone aerial above the approach).
    "A01_aerial": ("A01_official_campus_aerial.jpg", (0.0, 208.7, 61.0), (0.0, -60.0, -8.0), 24.0, (1280, 719)),
    # D05 (official "Academic Building Gate A"): eye height in the courtyard between the prongs.
    "D05_academic_gate_A": ("v4/D05_official_academic_gate_A.png", (0.0, -150.0, 1.7), (0.0, -229.0, 8.0), 16.5,
                            (2117, 743)),
}


def ffmpeg(*args):
    exe = shutil.which("ffmpeg")
    if not exe:
        print("[v4] ffmpeg not found")
        return
    subprocess.run([exe, "-v", "error", "-y", *args, ], check=True)


def render_all(tag, only, samples, scale):
    import bpy
    from mathutils import Vector
    sys.path.insert(0, SRC)
    from utilities.scene_setup import enable_gpu
    sc = bpy.context.scene
    enable_gpu(sc)
    for c in ("Unverified_Masterplan_Proposals",):
        coll = bpy.data.collections.get(c)
        if coll:
            coll.hide_render = True
    os.makedirs(OUT, exist_ok=True)
    for key, (ref, loc, tgt, lens, res) in CAMS.items():
        if only and key not in only:
            continue
        cd = bpy.data.cameras.new("V4CAM_" + key)
        cd.lens = lens
        cd.sensor_width = 36.0
        cd.sensor_fit = 'HORIZONTAL'
        cd.clip_start, cd.clip_end = 0.1, 20000.0
        cam = bpy.data.objects.new("V4CAM_" + key, cd)
        sc.collection.objects.link(cam)
        cam.location = loc
        d = Vector(tgt) - Vector(loc)
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        sc.camera = cam
        sc.render.engine = 'CYCLES'
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        sc.render.resolution_x, sc.render.resolution_y = int(res[0] * scale), int(res[1] * scale)
        sc.render.resolution_percentage = 100
        sc.render.film_transparent = False
        sc.render.image_settings.file_format = 'PNG'
        sc.render.filepath = os.path.join(OUT, f"_{tag}_{key}.png")
        bpy.ops.render.render(write_still=True)
        print("[v4] wrote", sc.render.filepath)


def compose(h=560):
    font = "C\\:/Windows/Fonts/arialbd.ttf"

    def label(txt):
        return (f"drawtext=fontfile='{font}':text='{txt}':x=14:y=12:fontsize=26:fontcolor=white:"
                f"box=1:boxcolor=black@0.55:boxborderw=8")
    for key, (ref, *_rest) in CAMS.items():
        r3, r4 = os.path.join(OUT, f"_v3_{key}.png"), os.path.join(OUT, f"_v4_{key}.png")
        if not (os.path.exists(r3) and os.path.exists(r4)):
            continue
        photo = os.path.join(REF, ref)
        # photo | V3 | V4, each scaled to the same height
        ffmpeg("-i", photo, "-i", r3, "-i", r4, "-filter_complex",
               f"[0]scale=-2:{h},{label('Reference photo')}[a];[1]scale=-2:{h},{label('V3 (before)')}[b];"
               f"[2]scale=-2:{h},{label('V4 (after)')}[c];[a][b][c]hstack=inputs=3",
               "-frames:v", "1", os.path.join(OUT, f"compare_{key}.png"))
        # 50 % overlay of the V4 render on the photo (same aspect, same frame)
        ffmpeg("-i", photo, "-i", r4, "-filter_complex",
               f"[0]scale=-2:{h * 2 // 2},format=rgba[a];[1]scale=-2:{h * 2 // 2},format=rgba,colorchannelmixer=aa=0.5[b];"
               f"[a][b]overlay=shortest=1,{label('Overlay - photo + V4 render 50 percent')}",
               "-frames:v", "1", os.path.join(OUT, f"overlay_{key}.png"))
        print("[v4] composed", key)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--compose" in argv:
        compose()
        return
    tag = argv[argv.index("--tag") + 1] if "--tag" in argv else "v4"
    only = set(argv[argv.index("--only") + 1].split(",")) if "--only" in argv else None
    samples = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 32
    scale = float(argv[argv.index("--scale") + 1]) if "--scale" in argv else 0.5
    render_all(tag, only, samples, scale)


if __name__ == "__main__":
    main()
