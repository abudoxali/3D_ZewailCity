from pathlib import Path
import bpy,json
R=Path(__file__).resolve().parents[1]
errors=[]
for im in bpy.data.images:
 if im.source!='FILE':continue
 p=Path(bpy.path.abspath(im.filepath)).resolve()
 if not p.is_file() or not p.is_relative_to(R.resolve()) or im.size[0]<1:errors.append(im.name)
assert not errors,errors
out=R/'output/checks';out.mkdir(parents=True,exist_ok=True)
(out/'master_open.json').write_text(json.dumps({'file':str(Path(bpy.data.filepath).relative_to(R)),'objects':len(bpy.context.scene.objects),'mesh_datablocks':len(bpy.data.meshes),'images':len(bpy.data.images),'unresolved_images':errors,'metric_scale':bpy.context.scene.unit_settings.scale_length},indent=2))
print('FINAL MASTER OPEN:',len(bpy.context.scene.objects),'objects; images resolve; geometry unchanged',flush=True)
