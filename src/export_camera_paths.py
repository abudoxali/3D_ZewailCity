"""Resample the editable CIN_* / TOUR_* camera paths to JSON for the Godot explorer.

Run after editing a path in Blender; the campus does not need rebuilding:
    blender -b output/Zewail_City_3D.blend --python src/export_camera_paths.py

Writes output/tours/<shot>.json and copies each file to game/godot/assets/tours/.

JSON per shot (Godot coordinates: x, z, -y of Blender; metres):
    {"name", "fps", "frame_start", "frame_end", "fov_v_deg",
     "labels": [[t_seconds, text], ...],
     "samples": [[t, px, py, pz, fx, fy, fz, ux, uy, uz], ...]}   # p = position, f = forward, u = up
"""
import json
import math
import os
import shutil

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output", "tours")
GODOT = os.path.join(ROOT, "game", "godot", "assets", "tours")


def to_godot(v):
    return (v[0], v[2], -v[1])


def vfov_deg(cam):
    d = cam.data
    sensor = d.sensor_width
    hfov = 2.0 * math.atan(sensor / (2.0 * d.lens))
    return math.degrees(2.0 * math.atan(math.tan(hfov / 2.0) * 9.0 / 16.0))


def export_shot(scene, cam):
    f0, f1 = int(cam["zc_frame_start"]), int(cam["zc_frame_end"])
    fps = int(cam.get("zc_fps", 30))
    samples = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        m = cam.matrix_world
        p = to_godot(m.translation)
        fwd = to_godot(-m.col[2].xyz.normalized())
        up = to_godot(m.col[1].xyz.normalized())
        t = (f - f0) / fps
        samples.append([round(t, 4)] + [round(c, 3) for c in (*p, *fwd, *up)])
    labels = [[round((f - f0) / fps, 3), text] for f, text in json.loads(cam.get("zc_labels", "[]"))]
    data = {"name": cam.name, "fps": fps, "frame_start": f0, "frame_end": f1,
            "fov_v_deg": round(vfov_deg(cam), 3), "labels": labels, "samples": samples}
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, cam.name + ".json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, separators=(",", ":"))
    if os.path.isdir(os.path.dirname(GODOT)):
        os.makedirs(GODOT, exist_ok=True)
        shutil.copy2(path, os.path.join(GODOT, cam.name + ".json"))
    return path, len(samples)


def main():
    scene = bpy.context.scene
    cams = [o for o in scene.objects if o.type == 'CAMERA' and o.get("zc_shot")]
    if not cams:
        raise SystemExit("[paths] no CIN_/TOUR_ cameras found (rebuild with build_scene.py)")
    index = []
    for cam in sorted(cams, key=lambda o: o.name):
        path, n = export_shot(scene, cam)
        index.append({"name": cam.name, "file": os.path.basename(path), "samples": n})
        print(f"[paths] {cam.name}: {n} samples -> {path}")
    with open(os.path.join(OUT, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=1)
    if os.path.isdir(GODOT):
        shutil.copy2(os.path.join(OUT, "index.json"), os.path.join(GODOT, "index.json"))
    scene.frame_set(1)


if __name__ == "__main__":
    main()
