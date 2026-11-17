from pathlib import Path
import bpy,json
R=Path(__file__).resolve().parents[1];bad=[];packed_blank=[]
for im in bpy.data.images:
 if im.source!='FILE':continue
 p=Path(bpy.path.abspath(im.filepath)).resolve()
 if not p.is_file() or not p.is_relative_to(R.resolve()) or im.size[0]<1:bad.append({'image':im.name,'path':str(p),'size':list(im.size)})
 for q in im.packed_files:
  if not q.filepath:packed_blank.append({'image':im.name,'writable':not q.bl_rna.properties['filepath'].is_readonly})
print('PORTABILITY_CHECK',json.dumps({'bad':bad,'blank_packed_paths':packed_blank,'objects':len(bpy.context.scene.objects)}),flush=True)
if bad:raise RuntimeError('Unresolved portable images')
