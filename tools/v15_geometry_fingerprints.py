"""Blender audit: hash actual source geometry, independently of material/UV changes."""
import bpy,hashlib,json,sys,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];O=R/'output/validation/v15';C=R
def scan(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    result={}
    for o in bpy.data.objects:
        if o.type!='MESH':continue
        me=o.data
        p=np.empty(len(me.vertices)*3,dtype=np.float32);me.vertices.foreach_get('co',p)
        idx=np.empty(len(me.loops),dtype=np.int32);me.loops.foreach_get('vertex_index',idx)
        mats=np.empty(len(me.polygons),dtype=np.int32);me.polygons.foreach_get('material_index',mats)
        ends=np.empty(len(me.polygons),dtype=np.int32);me.polygons.foreach_get('loop_total',ends)
        h=hashlib.sha256()
        for a in [p,idx,ends,mats]:h.update(a.tobytes())
        h.update(np.array(o.matrix_world,dtype=np.float64).round(7).tobytes())
        result[o.name]={'geometry_sha256':h.hexdigest(),'vertices':len(me.vertices),'faces':len(me.polygons),'materials':[m.name for m in me.materials if m],'finite':bool(np.isfinite(p).all()),'collections':[c.name for c in o.users_collection]}
    return result
mode=sys.argv[-1]
if mode=='baseline':
    data=scan(R/'output/validation/v14/candidate/output/Zewail_City_3D.blend')
    (O/'geometry_v14_reference.json').write_text(json.dumps(data,indent=2));print('baseline meshes',len(data))
else:
    path=C/'output'/('clean_rebuild.blend' if mode=='clean' else 'Zewail_City_3D.blend')
    now=scan(path);base=json.loads((O/'geometry_v14_reference.json').read_text())
    changed=[n for n in base if n in now and base[n]['geometry_sha256']!=now[n]['geometry_sha256']]
    veg=[n for n in changed if set(base[n]['collections'])&{'Shrubs','Trees','Palms'}]
    nonveg=[n for n in changed if n not in veg]
    rep={'source':str(path),'meshes':len(now),'changed':changed,'vegetation_changed':veg,'nonvegetation_changed':nonveg,'missing':sorted(set(base)-set(now)),'added':sorted(set(now)-set(base)),'nonfinite':[n for n,x in now.items() if not x['finite']],'unchanged':len([n for n in base if n in now and n not in changed])}
    (O/f'geometry_{mode}.json').write_text(json.dumps(rep,indent=2));print(json.dumps({k:v for k,v in rep.items() if k!='changed'}))
