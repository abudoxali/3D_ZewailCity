"""Rebase packed image dependencies without changing any scene geometry."""
from pathlib import Path
import bpy,hashlib,json,os
R=Path(__file__).resolve().parents[1]
def fingerprint():
 import array
 h=hashlib.sha256();cache={}
 for o in sorted(bpy.context.scene.objects,key=lambda o:o.name):
  h.update((o.name+'|'+o.type).encode());h.update(str([list(v) for v in o.matrix_world]).encode())
  if o.type=='MESH':
   me=o.data;key=me.as_pointer()
   if key not in cache:
    mh=hashlib.sha256()
    for collection,prop,code,size in ((me.vertices,'co','f',len(me.vertices)*3),(me.loops,'vertex_index','i',len(me.loops)),(me.polygons,'loop_total','i',len(me.polygons)),(me.polygons,'material_index','i',len(me.polygons))):
     buf=array.array(code,[0])*size;collection.foreach_get(prop,buf);mh.update(buf.tobytes())
    mh.update(str([m.name if m else None for m in me.materials]).encode());cache[key]=mh.digest()
   h.update(cache[key])
 return h.hexdigest()
before=fingerprint();lookup={}
for base in ('references','game/godot/assets','output/game_ready/textures'):
 for p in (R/base).rglob('*'):
  if p.suffix.lower() in ('.png','.jpg','.jpeg','.exr','.hdr','.tga') and p.is_file():
   lookup.setdefault(hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),p)
rows=[]
for im in bpy.data.images:
 if im.source!='FILE':continue
 if im.packed_file:
  raw=bytes(im.packed_file.data);h=hashlib.sha256(raw).hexdigest();p=lookup.get(h)
  if p is None:
   suffix=Path(im.filepath).suffix or '.png';p=R/'references/assets/master_textures'/(h[:12]+suffix);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);lookup[h]=p
 else:
  old=Path(bpy.path.abspath(im.filepath))
  if not old.is_file():raise RuntimeError('Missing unpacked image: '+im.name+' '+str(old))
  h=hashlib.file_digest(old.open('rb'),'sha256').hexdigest();p=lookup.get(h)
  if p is None:raise RuntimeError('Image outside portable project: '+str(old))
 im.filepath='//'+os.path.relpath(p,Path(bpy.data.filepath).parent).replace('\\','/')
 for q in im.packed_files:q.filepath=im.filepath
 rows.append({'image':im.name,'path':im.filepath,'sha256':h,'packed':bool(im.packed_file)})
assert fingerprint()==before,'Geometry changed during packaging'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True,relative_remap=False)
D=R/'output/checks';D.mkdir(parents=True,exist_ok=True)
(D/(Path(bpy.data.filepath).stem+'_portability.json')).write_text(json.dumps({'geometry_fingerprint':before,'objects':len(bpy.context.scene.objects),'images':rows,'file':str(Path(bpy.data.filepath).relative_to(R))},indent=2))
print('PORTABLE',Path(bpy.data.filepath).name,'objects',len(bpy.context.scene.objects),'images',len(rows),'geometry unchanged',before,flush=True)
