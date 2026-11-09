"""Editable cinematic camera paths and the guided-tour path.

Each shot is a camera `CIN_*` / `TOUR_*` with keyframed location, plus a
keyframed `<camera>_Target` empty that the camera tracks (Track To constraint).
They live in the `Cinematic_Paths` collection of output/Zewail_City_3D.blend.

Editing workflow (no campus rebuild needed):
  1. Open the .blend, select a CIN_/TOUR_ camera or its _Target empty, move it at a
     keyframe and re-key it (I), or edit the curves in the Graph Editor.
  2. Save the .blend.
  3. Run `src/export_camera_paths.py` to resample the paths to JSON for Godot,
     or `src/render_cinematic.py` to render a video in Blender.

Re-running build_scene.py recreates these shots from the tables below. To keep
hand edits permanently, copy the new key positions into these tables.

Every position below is in Blender metres (origin = dome centre, +Y = toward the
main gate). The paths were checked for clearance against the collision proxies
by the Godot validation script (game/godot/tests/validate_tour.gd).
"""
import json
import math

import bpy

FPS = 30

# name: (lens mm, camera keys [(frame, (x, y, z))], target keys [(frame, (x, y, z))], labels [(frame, text)])
GY = 314.6        # main gate line (utilities/survey.py GATE_Y)

SHOTS = {
    "CIN_Aerial_Flyover": (
        30.0,
        [(1, (-420, 560, 190)), (120, (-180, 420, 150)), (240, (120, 300, 135)), (360, (380, -40, 170))],
        [(1, (0, 150, 10)), (180, (0, -40, 10)), (360, (0, -130, 10))],
        [(1, "Aerial flyover")],
    ),
    # V4: ground-level landmark shot of the main gate from the exterior island (C01 viewpoint)
    "CIN_Main_Gate": (
        26.0,
        [(1, (-46, GY + 52, 1.7)), (150, (-26, GY + 44, 1.7)), (300, (-4, GY + 46, 1.9))],
        [(1, (0, GY, 9.5)), (300, (0, GY, 8.5))],
        [(1, "Main gate (portal frame and gatehouse)")],
    ),
    # V4: walk from outside the gate through the west pedestrian gate and down the approach walkway
    "CIN_Ground_Approach": (
        28.0,
        [(1, (-19.0, GY + 13, 1.7)), (90, (-19.0, GY - 4, 1.7)), (160, (-16.3, GY - 34, 1.7)),
         (360, (-16.3, 200, 1.7)), (560, (-16.3, 110, 1.7)), (650, (-9.0, 60, 1.7)), (720, (-3.0, 40, 1.7))],
        [(1, (-15, GY - 40, 2.5)), (160, (-10, 150, 3)), (500, (0, 20, 12)), (720, (0, 20, 9))],
        [(1, "Main gate, pedestrian entrance"), (160, "Approach walkway"),
         (560, "Approach lawn and flower bed"), (650, "Administration & Cultural Building")],
    ),
    "CIN_Admin_Closeup": (
        35.0,
        [(1, (-44, 60, 9)), (120, (-6, 64, 10)), (220, (34, 58, 13)), (300, (34, 40, 30))],
        [(1, (0, 22, 9)), (120, (0, 20, 11)), (220, (0, 12, 16)), (300, (0, 0, 29))],
        [(1, "Administration & Cultural Building"), (220, "Copper dome")],
    ),
    "CIN_Overview_Orbit": (
        32.0,
        [(1 + i * 50, (440 * math.sin(i * 0.5236), -110 + 440 * math.cos(i * 0.5236), 250))
         for i in range(13)],
        [(1, (0, -110, 0)), (601, (0, -110, 0))],
        [(1, "Campus overview")],
    ),
    # 2880 frames = 96 s at 30 fps
    "TOUR_Guided": (
        30.0,
        [(1, (-420, 640, 210)), (220, (-90, 470, 70)), (400, (-16, GY + 46, 4.0)), (500, (-9.45, GY + 20, 3.2)),
         (560, (-9.45, GY - 8, 3.2)), (640, (-5.8, GY - 46, 4.0)), (800, (-5.8, 170, 4.5)), (930, (-12, 105, 6)),
         (1050, (-10, 62, 9)), (1160, (24, 52, 11)), (1270, (36, 42, 15)), (1380, (38, 16, 31)),
         (1490, (30, -22, 40)), (1610, (0, -95, 36)), (1720, (0, -140, 14)), (1830, (0, -184, 6.5)),
         (1930, (0, -170, 30)), (2040, (-62, -118, 38)), (2150, (-84, -10, 34)), (2260, (0, 46, 30)),
         (2380, (92, 4, 30)), (2480, (112, -22, 28)), (2690, (210, 210, 140)), (2880, (330, 430, 230))],
        [(1, (0, 140, 0)), (220, (0, GY, 6)), (400, (0, GY, 9)), (500, (0, GY - 10, 6)), (640, (0, 150, 4)),
         (800, (0, 0, 15)), (1050, (0, 22, 10)), (1270, (0, 0, 28)), (1490, (0, 0, 28)),
         (1610, (0, -229, 10)), (1830, (0, -229, 6)), (1930, (-130, -69, 10)), (2150, (-130, -69, 10)),
         (2260, (147, -63, 10)), (2480, (147, -63, 10)), (2880, (0, -120, 0))],
        [(1, "Establishing aerial view"), (220, "Main gate (portal frame and gatehouse)"),
         (560, "Approach road"), (930, "Approach lawn and flower bed"),
         (1050, "Administration & Cultural Building"), (1270, "Copper dome"), (1610, "Academic Building"),
         (1720, "Academic Building, Gate (A)"), (1930, "Helmy Institute for Medical Sciences"),
         (2260, "East research institute (identity unconfirmed)"), (2690, "Campus overview")],
    ),
}

# V5 keeps every V4 guided-tour stop, then adds the reconstructed public route
# and the explicitly unconfirmed dormitory candidate. No long video is required.
_lens,_cams,_targets,_labels=SHOTS['TOUR_Guided']
SHOTS['TOUR_Guided']=(_lens,_cams+[
    (3000,(0,-170,110)),(3120,(0,-180,8)),(3240,(0,-215,2)),(3360,(0,-245,2)),
    (3480,(0,-280,3)),(3600,(0,-320,3)),(3720,(0,-365,2)),(3840,(80,-430,65)),
    (3960,(430,-555,65)),(4080,(416,-590,5)),(4200,(416,-603,3)),(4320,(390,-629,6)),
    (4440,(390,-603,75)),(4560,(0,-237,850))],
    _targets+[(3000,(0,-250,0)),(3120,(0,-229,6)),(3240,(0,-245,2)),(3360,(0,-280,2)),
    (3480,(0,-315,2)),(3600,(0,-355,2)),(3720,(0,-410,1)),(3840,(390,-603,0)),
    (3960,(390,-603,0)),(4080,(390,-603,2)),(4200,(390,-603,1)),(4320,(390,-603,1)),
    (4440,(390,-603,0)),(4560,(0,-237,0))],
    _labels+[(3000,'Academic public route (estimated geometry)'),(3240,'Central covered passage'),
    (3480,'Academic courtyard: palms and student seating'),(3600,'Rear courtyard passage'),
    (3720,'Natural rear campus soil'),(3960,'Dormitory candidate (identity unconfirmed)'),
    (4200,'Estimated central garden'),(4440,'Campus overview')])

SHOTS['CIN_Academic_Public_Route']=(24.,
    [(1,(0,-205,1.83)),(180,(0,-239,1.83)),(360,(0,-280,1.83)),(540,(0,-320,1.83)),(720,(0,-365,1.83))],
    [(1,(0,-239,1.83)),(180,(0,-280,1.83)),(360,(0,-320,1.83)),(540,(0,-365,1.83)),(720,(0,-390,1.83))],
    [(1,'Academic entrance'),(180,'Central passage'),(360,'Academic courtyard'),(540,'Rear exit')])
SHOTS['CIN_Dormitory_Candidate_Garden']=(24.,
    [(1,(425,-555,35)),(180,(416,-603,4)),(360,(390,-629,7)),(540,(390,-603,65))],
    [(1,(390,-603,0)),(180,(390,-603,1)),(360,(390,-603,1)),(540,(390,-603,0))],
    [(1,'Dormitory candidate: identity unconfirmed'),(180,'Estimated garden layout')])
from .gate_inventory import RECORDS as _GATES
from .ground_system import datum as _datum
for _g in _GATES[1:]:
    _x,_y=_g['model_position_blender_m']
    _dx,_dy=_g['inward']
    SHOTS['CIN_'+_g['id']+'_Provisional_Gate']=(24.,
        [(1,(_x-_dx*18,_y-_dy*18,_datum(_x,_y)+1.8)),(180,(_x-_dx*11,_y-_dy*11,_datum(_x,_y)+1.8))],
        [(1,(_x,_y,1.8)),(180,(_x,_y,1.8))],[(1,_g['label']+' — provisional marker, not verified architecture')])


def _key_all(obj, keys):
    for f, p in keys:
        obj.location = p
        obj.keyframe_insert("location", frame=f)
    ad = obj.animation_data
    if ad and ad.action:
        for fc in _fcurves(ad):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR' if obj.name.startswith(('CIN_V6_', 'CIN_V7_')) else 'BEZIER'
                # V4: AUTO_CLAMPED. Plain AUTO handles overshoot when a key is held (e.g. the target
                # resting on the dome) next to a large move, which swung the tour camera off its subject.
                kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
            fc.update()


def _fcurves(ad):
    act = ad.action
    if hasattr(act, "fcurves") and len(getattr(act, "fcurves", [])):
        return list(act.fcurves)
    # Blender 4.4+ layered actions
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for bag in strip.channelbags:
                out += list(bag.fcurves)
    return out


def build(scene, parent_coll):
    from .v6_walkthrough import shot
    SHOTS['CIN_V6_Photo_Walkthrough']=shot()
    from .v7_showcase import shot as v7_shot
    SHOTS['CIN_V7_Architectural_Showcase']=v7_shot()
    coll = bpy.data.collections.get("Cinematic_Paths") or bpy.data.collections.new("Cinematic_Paths")
    if coll.name not in parent_coll.children:
        parent_coll.children.link(coll)
    made = []
    for name, (lens, cam_keys, tgt_keys, labels) in SHOTS.items():
        cd = bpy.data.cameras.new(name)
        cd.lens = lens
        cd.clip_start, cd.clip_end = 0.1, 6000.0
        cam = bpy.data.objects.new(name, cd)
        tgt = bpy.data.objects.new(name + "_Target", None)
        tgt.empty_display_type = 'SPHERE'
        tgt.empty_display_size = 2.0
        coll.objects.link(cam)
        coll.objects.link(tgt)
        _key_all(cam, cam_keys)
        _key_all(tgt, tgt_keys)
        con = cam.constraints.new('TRACK_TO')
        con.target = tgt
        con.track_axis = 'TRACK_NEGATIVE_Z'
        con.up_axis = 'UP_Y'
        cam["zc_shot"] = True
        cam["zc_frame_start"] = int(cam_keys[0][0])
        cam["zc_frame_end"] = int(cam_keys[-1][0])
        cam["zc_fps"] = FPS
        cam["zc_labels"] = json.dumps(labels)
        made.append(name)
    scene.frame_end=max(int(bpy.data.objects[n]['zc_frame_end']) for n in made)
    return made
