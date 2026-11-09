"""Render actual source geometry: ground, roads, elevation, and eye-height views."""
import sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from utilities.scene_setup import enable_gpu
from utilities.ground_system import datum
sc=bpy.context.scene
enable_gpu(sc)
sc.render.engine='CYCLES'
sc.cycles.samples=12
sc.cycles.use_denoising=True
sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
out=ROOT/'output/validation/v5'
out.mkdir(parents=True,exist_ok=True)
cd=bpy.data.cameras.new('V5_Validation')
cam=bpy.data.objects.new('V5_Validation',cd)
sc.collection.objects.link(cam)
sc.camera=cam
cd.clip_end=10000
original={o.name:o.hide_render for o in sc.objects}
ONLY={'academic_entry','academic_stair_left','academic_stair_right','academic_passage','academic_courtyard',
      'academic_seating','academic_cafeteria_context','academic_rear_exit'} if '--academic-only' in sys.argv else None
SINGLE=sys.argv[sys.argv.index('--only')+1] if '--only' in sys.argv else None
if SINGLE:
    ONLY={SINGLE}
def render(name,loc,tgt,top=False):
    if ONLY is not None and name not in ONLY:
        return
    cam.location=loc
    cam.rotation_euler=(Vector(tgt)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    cd.type='ORTHO' if top else 'PERSP'
    cd.ortho_scale=1200
    cd.lens=24
    sc.render.resolution_x,sc.render.resolution_y=(1120,1200) if top else (1280,720)
    sc.render.filepath=str(out/(name+'.png'))
    bpy.ops.render.render(write_still=True)
    if SINGLE:
        print('[v5-visual] saved isolated view',name,flush=True)
        sys.exit(0)
def reset():
    for o in sc.objects:
        o.hide_render=original.get(o.name,False)
def ground():
    for o in sc.objects:
        if o.type=='MESH':
            o.hide_render=not (o.name.startswith(('Ground_','Road_','Plaza_Academic_')) or o.name in ('Plaza_Paving','Lawns','Flower_Beds'))
ground()
render('ground_only_top',(0,-206.1,1500),(0,-206.1,0),True)
for o in sc.objects:
    if o.type=='MESH':
        o.hide_render=not o.name.startswith('Road_Network')
render('roads_only_top',(0,-206.1,1500),(0,-206.1,0),True)
ground()
mat=bpy.data.materials.new('V5_Elevation_Diagnostic')
mat.use_nodes=True
nt=mat.node_tree
nt.nodes.clear()
geo=nt.nodes.new('ShaderNodeNewGeometry')
sep=nt.nodes.new('ShaderNodeSeparateXYZ')
nt.links.new(geo.outputs['Position'],sep.inputs[0])
mapping=nt.nodes.new('ShaderNodeMapRange')
mapping.inputs['From Min'].default_value=-.7
mapping.inputs['From Max'].default_value=.7
nt.links.new(sep.outputs['Z'],mapping.inputs['Value'])
ramp=nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color=(.015,.1,.8,1)
ramp.color_ramp.elements[1].color=(1,.3,.015,1)
nt.links.new(mapping.outputs['Result'],ramp.inputs[0])
em=nt.nodes.new('ShaderNodeEmission')
nt.links.new(ramp.outputs[0],em.inputs[0])
output=nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(em.outputs[0],output.inputs['Surface'])
sc.view_layers[0].material_override=mat
render('terrain_elevation_minus070_to_plus070_m',(0,-206.1,1500),(0,-206.1,0),True)
sc.view_layers[0].material_override=None
reset()
for name,loc,tgt in [('external_road',(-345,-210,1.7),(-345,-270,1.0)),
                     ('approach_walkway',(16.3,205,1.7),(16.3,145,1.7)),
                     ('ring_road',(299,-245,1.7),(294,-180,1.7)),
                     ('academic_approach',(0,-130,1.7),(0,-220,5.0))]:
    render(name, (loc[0],loc[1],loc[2]+datum(loc[0],loc[1])),tgt)
if '--all' in sys.argv or '--academic-only' in sys.argv or SINGLE:
    for name,loc,tgt in [('academic_entry',(0,-210,1.9),(0,-245,4)),
        ('academic_stair_left',(-15,-214,1.9),(-12,-234,3)),
        ('academic_stair_right',(15,-214,1.9),(12,-234,3)),
        ('academic_passage',(0,-240,1.9),(0,-270,2)),
        ('academic_courtyard',(0,-225,75),(0,-285,0)),
        ('academic_seating',(-20,-278,1.9),(-32,-290,1.6)),
        ('academic_cafeteria_context',(12,-278,1.9),(18,-260,2)),
        ('academic_rear_exit',(0,-320,1.9),(0,-360,1.2)),
        ('rear_soil',(0,-400,1.7),(0,-500,1)),
        ('dormitory_estimate',(455,-555,55),(390,-603,0))]:
        render(name,loc,tgt)
reset()
render('campus_masterplan',(0,-206.1,1500),(0,-206.1,0),True)
