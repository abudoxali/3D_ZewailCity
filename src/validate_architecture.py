"""Architectural validation renders + reference comparisons -> output/validation/.

Comparison method (no numerical "accuracy score" is claimed):
1. plan_overlay.png: the model is rendered with an orthographic camera whose
   frame matches the B04 site-plan image pixel-for-pixel (0.595 m/px, same origin
   as site_plan.py). The flat-shaded render is alpha-composited over the plan, so
   footprint and road misalignments are directly visible.
2. compare_A01/A02/A03: Cycles renders from cameras placed to approximate the
   viewpoints of the official photographs, shown side by side with them.
3. blockout_aerial / massing_overview / admin_front_elevation: neutral massing
   views for silhouette and proportion checks.

Usage (from the project root; needs ffmpeg on PATH for the composites):
    blender -b output/Zewail_City_3D.blend --python src/validate_architecture.py -- [--samples N]
"""
import os
import shutil
import subprocess
import sys

import bpy

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SRC)
sys.path.insert(0, SRC)
from utilities.scene_setup import enable_gpu  # noqa: E402

OUT = os.path.join(ROOT, "output", "validation")
REF = os.path.join(ROOT, "references", "source_images")
PLAN = os.path.join(ROOT, "references", "source_images", "B04_site_plan_extracted.jpg")


def render(cam, path, engine='CYCLES', samples=64, transparent=False, res=None, flat=False):
    sc = bpy.context.scene
    sc.camera = bpy.data.objects[cam]
    sc.render.engine = 'BLENDER_WORKBENCH' if engine == 'WORKBENCH' else 'CYCLES'
    sc.cycles.samples = samples
    sc.render.film_transparent = transparent
    sc.render.resolution_x, sc.render.resolution_y = res or tuple(sc.camera.get('resolution', (1920, 1080)))
    sc.render.resolution_percentage = 100
    sc.render.image_settings.color_mode = 'RGBA' if transparent else 'RGB'
    if engine == 'WORKBENCH':
        sh = sc.display.shading
        sh.light = 'FLAT' if flat else 'STUDIO'
        sh.color_type = 'MATERIAL' if flat else 'SINGLE'
        sh.single_color = (0.85, 0.85, 0.85)
        sh.show_shadows = not flat
        sh.show_cavity = not flat
        sc.display.render_aa = '8'
        if sc.world:
            sc.world.color = (0.80, 0.80, 0.80)   # light neutral background for massing views
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("[validate] wrote", path)


def ffmpeg(*args):
    exe = shutil.which("ffmpeg")
    if not exe:
        print("[validate] ffmpeg not found; skipping composite", args[-1])
        return
    subprocess.run([exe, "-v", "error", "-y", *args[:-1], "-frames:v", "1", args[-1]], check=True)
    print("[validate] wrote", args[-1])


def side_by_side(ref, render_path, out, h=720):
    ffmpeg("-i", ref, "-i", render_path, "-filter_complex",
           f"[0]scale=-2:{h}[a];[1]scale=-2:{h}[b];[a][b]hstack", out)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    samples = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 64
    os.makedirs(OUT, exist_ok=True)
    sc = bpy.context.scene
    enable_gpu(sc)
    view_tf = sc.view_settings.view_transform

    # 1. plan overlay (flat colours, transparent background)
    sc.view_settings.view_transform = 'Standard'
    p = os.path.join(OUT, "_plan_model.png")
    render('CAM_Plan_Overlay', p, engine='WORKBENCH', transparent=True, flat=True)
    if os.path.exists(PLAN):
        ffmpeg("-i", PLAN, "-i", p, "-filter_complex",
               "[0]scale=1346:1193,format=rgba[a];[1]format=rgba,colorchannelmixer=aa=0.55[b];[a][b]overlay",
               os.path.join(OUT, "plan_overlay.png"))
        ffmpeg("-i", PLAN, "-i", p, "-filter_complex", "[0]scale=1346:1193[a];[1]format=rgba[b];"
               "color=c=white:s=1346x1193[w];[w][b]overlay[m];[a][m]hstack", os.path.join(OUT, "plan_side_by_side.png"))
    # 3. massing views (studio-lit grey workbench)
    render('CAM_Aerial', os.path.join(OUT, "blockout_aerial.png"), engine='WORKBENCH')
    render('CAM_Isometric', os.path.join(OUT, "massing_overview.png"), engine='WORKBENCH')
    render('CAM_Admin_Front_Elevation', os.path.join(OUT, "admin_front_elevation_massing.png"), engine='WORKBENCH')
    sc.view_settings.view_transform = view_tf
    # 2. photo-matched Cycles renders
    for cam, ref, tag in (('CAM_Ref_A01', "A01_official_campus_aerial.jpg", "A01"),
                          ('CAM_Ref_A02', "A02_hassanallam_admin_building.jpg", "A02"),
                          ('CAM_Detail', "A03_official_admin_building.jpg", "A03")):
        rp = os.path.join(OUT, f"_render_{tag}.png")
        render(cam, rp, samples=samples)
        side_by_side(os.path.join(REF, ref), rp, os.path.join(OUT, f"compare_{tag}.png"))
    sc.render.engine = 'CYCLES'


if __name__ == "__main__":
    main()
