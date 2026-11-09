"""V9 matched Blender reference renders (V8 before / V9 after).

    blender -b <blend> --python src/render_v9.py -- <tag> [view ...]

The first run resolves every view to an exact camera pose (eye views ray-cast
the floor and sit 1.70 m above it) and stores the poses in
output/validation/v9/reference_cameras_v9.json. Every later run reuses those
stored poses unchanged, so before/after pairs share camera, lens, resolution,
samples, denoiser and lighting.
"""
import bpy, sys, json, hashlib
from pathlib import Path
from mathutils import Vector
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'src'))
from utilities.scene_setup import enable_gpu

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
tag = args[0] if args else 'after'
only = args[1:]
OUT = R / 'output/validation/v9/reference_views'
OUT.mkdir(parents=True, exist_ok=True)
POSES = R / 'output/validation/v9/reference_cameras_v9.json'

# name: (camera, target, ortho_scale or None, eye) -- eye views give floor xy and a
# target height above that floor; others are absolute Blender positions (V8 poses).
VIEWS = {
    'G1_exterior': ((-45, 368, 7), (0, 317, 7), None, False),
    'G1_pedestrian_eye': ((-21, 288), (-17, 312, 1.2), None, True),
    'G2_gap_topdown': ((6, -662, 140), (6, -662, 0), 150, False),
    'G2_outside_eye': ((13.7, -658.2), (6.4, -638.7, 1.4), None, True),
    'G3_inside_eye': ((-261.5, 110.4), (-270.9, 132.5, 1.4), None, True),
    'G4_inside_eye': ((-324.7, -245.0), (-342.3, -238.0, 1.4), None, True),
    'G5_inside_eye': ((221.4, 68.3), (237.8, 76.2, 1.4), None, True),
    'G6_inside_eye': ((328.5, -227.9), (346.6, -236.8, 1.4), None, True),
    'ground_overview': ((660, -950, 660), (0, -170, 0), None, False),
    'main_approach_roads': ((60, 230, 65), (0, 110, 0), None, False),
    'main_approach_eye': ((-12.5, 268), (-12.5, 150, 0.0), None, True),
    'ring_road_eye': ((290, -152), (262, -56, 0.6), None, True),
    'academic_stairs': ((0, -189, 14), (0, -225, 2.7), None, False),
    'academic_court_paving_eye': ((18, -258), (30, -276, -0.8), None, True),
    'admin_ramp_landing_eye': ((17.5, 54), (11, 36, 0.4), None, True),
    'dorm_garden_eye': ((425, -568), (419, -583, -0.6), None, True),
    'desert_soil_rear_eye': ((20, -377), (0, -348, 0.0), None, True),
    'wall_inside_soil_eye': ((-300, -40), (-330, -10, 0.6), None, True),
    'planted_soil_grove_eye': ((-62, 205), (-40, 175, -0.3), None, True),
}
# V8 oblique gate views (same formula as render_v8.py) for G2-G6.
from utilities.gate_inventory import RECORDS
from utilities.v8_gates import configuration, axes
from utilities.ground_system import datum
for r in RECORDS[1:]:
    c = configuration(r); u, v = axes(r, c); x, y = r['model_position_blender_m']; z = datum(x, y)
    VIEWS[r['id'] + '_oblique'] = ((x - v[0] * 22 + u[0] * 15, y - v[1] * 22 + u[1] * 15, z + 9), (x, y, z + 1.2), None, False)

scene = bpy.context.scene
deps = bpy.context.evaluated_depsgraph_get()


def floor_z(x, y):
    hit, loc, *_ = scene.ray_cast(deps, Vector((x, y, 6.0)), Vector((0, 0, -1)))
    return loc.z if hit else 0.0


poses = json.loads(POSES.read_text()) if POSES.exists() else {}
changed = False
for k, (cam, tgt, ortho, eye) in VIEWS.items():
    if k in poses:
        continue
    if eye:
        f = floor_z(*cam)
        cam = (cam[0], cam[1], f + 1.70)
        tgt = (tgt[0], tgt[1], f + tgt[2])
    poses[k] = {'position': list(cam), 'target': list(tgt), 'ortho': ortho, 'lens': 32, 'eye_view': eye,
                'resolved_by': tag}
    changed = True
if changed:
    POSES.write_text(json.dumps(poses, indent=1))

scene.render.engine = 'CYCLES'; enable_gpu(scene)
scene.cycles.samples = 16; scene.cycles.use_denoising = True
scene.render.resolution_x = 1280; scene.render.resolution_y = 720; scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
camdata = bpy.data.cameras.new('V9_Evidence'); cam = bpy.data.objects.new('V9_Evidence', camdata)
scene.collection.objects.link(cam); scene.camera = cam; camdata.clip_end = 6000; camdata.lens = 32
camdata.clip_start = 0.05
digest = hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()
for key, p in poses.items():
    if only and key not in only:
        continue
    cam.location = p['position']
    cam.rotation_euler = (Vector(p['target']) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    camdata.type = 'ORTHO' if p['ortho'] else 'PERSP'
    if p['ortho']:
        camdata.ortho_scale = p['ortho']
    scene.render.filepath = str(OUT / f'{tag}_{key}.png')
    bpy.ops.render.render(write_still=True)
    (OUT / f'{tag}_{key}.json').write_text(json.dumps({'pose': p, 'size': [1280, 720], 'samples': 16,
        'source_blend': bpy.data.filepath, 'source_blend_sha256': digest, 'tag': tag}, indent=1))
    print('[v9-render]', key, tag, flush=True)
