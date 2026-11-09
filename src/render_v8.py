"""Repeatable V7/V8 pairs; camera poses are identical and saved beside images."""
import bpy,sys,json,hashlib,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from utilities.gate_inventory import RECORDS
from utilities.v8_gates import configuration,axes,xy
from utilities.ground_system import datum
from utilities.scene_setup import enable_gpu
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
tag=args[0] if args else 'after'
only=args[1:]
out=R/'output/validation/v8/reference_views';out.mkdir(parents=True,exist_ok=True)
views={'G1_exterior':((-45,368,7),(0,317,7),None),
       'G1_interior':((42,238,8),(0,318,5),None),
       'ground_overview':((660,-950,660),(0,-170,0),None),
       'full_topdown':((0,-205,1500),(0,-205,0),1280),
       'main_approach_roads':((60,230,65),(0,110,0),None),
       'external_G2_unresolved':((6,-662,140),(6,-662,0),150),
       'pedestrian_approach':((-23,287,3),(-17,310,1.5),None),
       'academic_stairs':((0,-189,14),(0,-225,2.7),None),
       'academic_passage':((0,-212,2.1),(0,-249,2.1),None),
       'academic_rear_soil':((20,-377,4),(0,-348,1),None),
       'admin_threshold':((24,60,4),(0,32,1),None)}
for r in RECORDS[1:]:
 c=configuration(r);u,v=axes(r,c);x,y=r['model_position_blender_m'];z=datum(x,y)
 views[r['id']]=((x-v[0]*22+u[0]*15,y-v[1]*22+u[1]*15,z+9),(x,y,z+1.2),None)
 views[r['id']+'_topdown']=((x,y,130),(x,y,0),95)
scene=bpy.context.scene;scene.render.engine='CYCLES';enable_gpu(scene)
scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
camdata=bpy.data.cameras.new('V8_Evidence');cam=bpy.data.objects.new('V8_Evidence',camdata)
scene.collection.objects.link(cam);scene.camera=cam;camdata.clip_end=6000;camdata.lens=32
digest=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()
for key,(position,target,ortho) in views.items():
 if only and key not in only:continue
 scene.render.resolution_x,scene.render.resolution_y=(1280,1440) if key=='full_topdown' else (1280,720)
 cam.location=position;direction=Vector(target)-cam.location
 cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
 camdata.type='ORTHO' if ortho else 'PERSP'
 if ortho:camdata.ortho_scale=ortho
 scene.render.filepath=str(out/(tag+'_'+key+'.png'))
 bpy.ops.render.render(write_still=True)
 metadata={'pose':{'position':position,'target':target,'ortho':ortho,'lens':32,'size':[scene.render.resolution_x,scene.render.resolution_y]},'source_blend':bpy.data.filepath,'source_blend_sha256':digest,'architecture':'G2-G6 PROVISIONAL, not photographic reconstruction','tag':tag}
 if key=='full_topdown':
  from bpy_extras.object_utils import world_to_camera_view
  metadata['gate_pixels']={}
  for r in RECORDS:
   x,y=r['model_position_blender_m'];p=world_to_camera_view(scene,cam,Vector((x,y,2.)))
   metadata['gate_pixels'][r['id']]=[round(p.x*scene.render.resolution_x),round((1-p.y)*scene.render.resolution_y)]
 (out/(tag+'_'+key+'.json')).write_text(json.dumps(metadata,indent=2))
 print('[v8-render]',key,tag,flush=True)
