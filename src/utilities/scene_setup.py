"""Units, render engine, world lighting, sun and presentation cameras."""
import math

import bpy
from mathutils import Matrix, Vector

# +Y = front of the admin = toward the main gate along the campus axis (N36.5W), see survey.py.
# name: (location, target, lens_mm | None for ortho, ortho_scale, resolution, clip_start)
PLAN_CENTER = ((1346 - 1574) * 0.595, -(1193 - 817) * 0.595)   # centre of the B04 plan image
CAMERAS = {
    'CAM_Aerial':          ((0.0, 340.0, 170.0), (0.0, -90.0, 0.0), 26.0, None, (1920, 1080), 1.0),
    'CAM_Isometric':       None,  # built separately (true orthographic isometric)
    'CAM_Masterplan_Top':  ((20.0, -160.0, 1500.0), (20.0, -160.0, 0.0), None, 1250.0, (1600, 1600), 1.0),
    'CAM_Plan_Overlay':    ((PLAN_CENTER[0], PLAN_CENTER[1], 1500.0), (PLAN_CENTER[0], PLAN_CENTER[1], 0.0), None,
                            2692 * 0.595, (1346, 1193), 1.0),
    'CAM_Admin_Front_Elevation': ((0.0, 300.0, 17.0), (0.0, 0.0, 17.0), None, 180.0, (1920, 720), 262.0),
    # V4: photo-matched poses (see src/validate_v4.py for how each was estimated)
    'CAM_Ref_A01':         ((0.0, 208.7, 61.0), (0.0, -60.0, -8.0), 24.0, None, (1280, 719), 1.0),
    'CAM_Ref_A02':         ((0.0, 98.0, 1.9), (0.0, 0.0, 19.0), 29.4, None, (1536, 1024), 1.0),
    'CAM_Main_Gate':       ((-30.0, 360.0, 1.7), (0.0, 314.6, 9.0), 26.0, None, (1920, 1080), 0.5),
    'CAM_Ref_C02':         ((0.0, 30.0, 11.0), (0.0, 314.6, -8.9), 52.3, None, (2000, 1126), 1.0),
    'CAM_Detail':          ((-38.0, 62.0, 10.0), (0.0, -2.0, 25.0), 45.0, None, (1500, 1317), 1.0),
}
PREVIEW_FILES = {
    'CAM_Aerial': 'aerial.png', 'CAM_Masterplan_Top': 'masterplan_top.png', 'CAM_Isometric': 'isometric.png',
    'CAM_Admin_Front_Elevation': 'admin_front_elevation.png', 'CAM_Ref_A02': 'entrance.png',
    'CAM_Detail': 'details.png', 'CAM_Main_Gate': 'main_gate.png', 'CAM_Ref_C02': 'gate_from_admin.png',
}


def setup_units(scene):
    us = scene.unit_settings
    us.system = 'METRIC'
    us.scale_length = 1.0
    us.length_unit = 'METERS'


def enable_gpu(scene):
    """Use OptiX/CUDA when available; falls back to CPU silently."""
    scene.cycles.device = 'CPU'
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
    except KeyError:
        return 'CPU'
    for kind in ('OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL'):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
        except Exception:
            continue
        devs = [d for d in prefs.devices if d.type == kind]
        if devs:
            for d in prefs.devices:
                d.use = d.type == kind
            scene.cycles.device = 'GPU'
            return kind
    return 'CPU'


def setup_render(scene, samples=256):
    scene.render.engine = 'CYCLES'
    c = scene.cycles
    c.samples = samples
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.015
    c.use_denoising = True
    c.max_bounces = 6
    c.diffuse_bounces = 3
    c.glossy_bounces = 3
    c.transmission_bounces = 4
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.sample_clamp_indirect = 8.0
    scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_depth = '8'
    vs = scene.view_settings
    vs.view_transform = 'AgX'
    for look in ('AgX - Medium High Contrast', 'Medium High Contrast', 'None'):
        try:
            vs.look = look
            break
        except TypeError:
            continue
    vs.exposure = -0.75


def setup_world(scene, sun_elev=38.0, sun_azimuth=215.0):
    """Physical sky for ambient light + a sun lamp for crisp shadows.
    sun_azimuth is a compass bearing (degrees clockwise from north)."""
    w = bpy.data.worlds.get("World_Desert_Sky") or bpy.data.worlds.new("World_Desert_Sky")
    scene.world = w
    try:
        w.use_nodes = True
    except Exception:
        pass
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    sky = nt.nodes.new('ShaderNodeTexSky')
    try:
        sky.sky_type = 'MULTIPLE_SCATTERING'
    except TypeError:
        sky.sky_type = 'HOSEK_WILKIE'
    sky.sun_disc = False
    sky.sun_elevation = math.radians(sun_elev)
    # Only shapes the sky gradient (the sun disc is off; the lamp casts shadows).
    sky.sun_rotation = math.radians((90.0 - sun_azimuth) % 360.0) - math.pi / 2
    try:
        sky.altitude = 150.0
        sky.air_density = 1.0
        sky.aerosol_density = 0.8
    except Exception:
        pass
    bg.inputs['Strength'].default_value = 0.22
    nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])

    sun_data = bpy.data.lights.get("Sun") or bpy.data.lights.new("Sun", 'SUN')
    sun_data.energy = 3.8
    sun_data.angle = math.radians(0.8)
    sun_data.color = (1.0, 0.94, 0.86)
    sun = bpy.data.objects.get("Sun_Key_Light") or bpy.data.objects.new("Sun_Key_Light", sun_data)
    # light travels opposite to the bearing of the sun
    az = math.radians(sun_azimuth)
    to_sun = Vector((math.sin(az) * math.cos(math.radians(sun_elev)),
                     math.cos(az) * math.cos(math.radians(sun_elev)),
                     math.sin(math.radians(sun_elev))))
    sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    sun.location = to_sun * 600.0
    return sun


def _look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def _camera(name, coll, loc, target, lens=None, ortho=None, clip_start=1.0):
    cam = bpy.data.cameras.new(name)
    cam.clip_start = clip_start
    cam.clip_end = 30000.0
    if ortho:
        cam.type = 'ORTHO'
        cam.ortho_scale = ortho
    else:
        cam.lens = lens
    cam.sensor_width = 36.0
    obj = bpy.data.objects.new(name, cam)
    obj.location = loc
    _look_at(obj, target)
    coll.objects.link(obj)
    return obj


def build_cameras(scene, coll):
    cams = {}
    for name, spec in CAMERAS.items():
        if spec is None:
            continue
        loc, tgt, lens, ortho, res, clip = spec
        cams[name] = _camera(name, coll, loc, tgt, lens, ortho, clip)
        cams[name]['resolution'] = list(res)
    # elevation shows the admin building only (clip before the academic complex behind it)
    cams['CAM_Admin_Front_Elevation'].data.clip_end = 400.0
    # true isometric: 35.264 deg elevation, viewed from the front-west (lit side)
    t = Vector((0.0, -150.0, 0.0))
    d = Vector((-1.0, 1.0, math.sqrt(2.0) * math.tan(math.radians(35.264)))).normalized()
    iso = _camera('CAM_Isometric', coll, tuple(t + d * 2000.0), tuple(t), ortho=880.0)
    iso['resolution'] = [1920, 1080]
    cams['CAM_Isometric'] = iso
    # turntable: camera parented to a rotating empty
    pivot = bpy.data.objects.new("Turntable_Pivot", None)
    pivot.location = (0.0, -150.0, 0.0)
    pivot.empty_display_type = 'CIRCLE'
    pivot.empty_display_size = 50
    coll.objects.link(pivot)
    tt = _camera("CAM_Turntable", coll, (0.0, 560.0, 300.0), (0.0, -150.0, 10.0), lens=35.0)
    tt.parent = pivot
    tt.matrix_parent_inverse = Matrix.Translation(pivot.location).inverted()
    tt['resolution'] = [1280, 720]
    pivot.rotation_euler = (0, 0, 0)
    pivot.keyframe_insert('rotation_euler', index=2, frame=1)
    pivot.rotation_euler = (0, 0, math.radians(360.0))
    pivot.keyframe_insert('rotation_euler', index=2, frame=241)
    try:
        for fc in pivot.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
    except AttributeError:  # layered actions (Blender 4.4+)
        try:
            for layer in pivot.animation_data.action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for fc in bag.fcurves:
                            for kp in fc.keyframe_points:
                                kp.interpolation = 'LINEAR'
        except Exception:
            pass
    scene.frame_start, scene.frame_end = 1, 240
    scene.render.fps = 30
    cams['CAM_Turntable'] = tt
    scene.camera = cams['CAM_Aerial']
    return cams
