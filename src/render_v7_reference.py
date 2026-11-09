"""V7: one isolated reference view per Blender process, on a specified source .blend."""
import sys,os,json,hashlib
from pathlib import Path
import bpy
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from utilities.v6_photo_cameras import PHOTOS,build
from utilities.scene_setup import enable_gpu
args=sys.argv[sys.argv.index('--')+1:]
key=args[0];tag=args[1] if len(args)>1 else 'after'
scene=bpy.context.scene
build(scene,scene.collection)
scene.camera=bpy.data.objects['REF_V6_'+key]
scene.render.engine='CYCLES';enable_gpu(scene);scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x,scene.render.resolution_y=PHOTOS[key][4];scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
out=R/'output/validation/v7/reference_views';out.mkdir(parents=True,exist_ok=True)
scene.render.filepath=str(out/(tag+'_'+key+'.png'))
if key=='P04':
    from utilities.scene_setup import setup_world
    world=scene.world
    for n in world.node_tree.nodes:
        if n.type=='BACKGROUND':n.inputs['Strength'].default_value=.12
        if n.type=='TEX_SKY':n.sun_elevation=-.05
    for o in bpy.data.objects:
        if o.type=='LIGHT' and o.data.type=='SUN':o.data.energy=.08
        elif o.type=='LIGHT' and o.get('zc_night_energy'):o.data.energy=float(o['zc_night_energy'])
    scene.view_settings.exposure=.7
bpy.ops.render.render(write_still=True)
(out/(tag+'_'+key+'.json')).write_text(json.dumps({'source_blend':bpy.data.filepath,'source_blend_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'camera':PHOTOS[key][1:],'photo':PHOTOS[key][0],'alignment':'Before/after use the same fixed pose. Photo viewpoint is APPROXIMATE, NOT CALIBRATED.','tag':tag},indent=2))
print('[v6-render]',scene.render.filepath,flush=True)
sys.exit(0)
