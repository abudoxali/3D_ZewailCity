"""Fast source-based architectural iteration; full frame-zero build still required."""
from pathlib import Path
import sys,json,bpy
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(R/'tools/vendor'))
import build_scene
from utilities import buildings,v17_architecture,v17_finalize
M={k:bpy.data.materials[v] for k,v in json.loads(bpy.context.scene['zc_material_keys']).items() if v in bpy.data.materials}
from utilities import v18_palette
v18_palette.apply(M)
from utilities import v19_architecture
v19_architecture._palette(M)
C=build_scene.make_collections()
for name in ('AB_Administration_Cultural_Building','AB_Academic_Building'):
    root=bpy.data.objects[name]
    for o in [*root.children_recursive,root]:
        if o.name=='Academic_Court_Seat_Blocks':continue
        bpy.data.objects.remove(o,do_unlink=True)
admin=buildings.admin_cultural(M,C);academic=buildings.academic(M,C)
v17_architecture.terraces(M,C,academic)
bpy.context.view_layer.update()
# Source ground system has already been emitted in this iteration. Shift only
# the regenerated building roots once; do not reapply terrain to the retained scene.
from utilities.v17_elevation import datum
for root in (admin,academic):
    from mathutils import Vector
    pts=[root.matrix_world@Vector(p) for p in root.bound_box]
    x=(min(p.x for p in pts)+max(p.x for p in pts))/2;y=(min(p.y for p in pts)+max(p.y for p in pts))/2
    root.location.z+=datum(x,y);root['zc_v17_pad_datum_m']=datum(x,y)
v17_finalize.clean_surfaces()
bpy.context.view_layer.update()
# World-space UV projection for the freshly reconstructed facade/stone meshes.
print('[V18 source] projecting architecture UVs',flush=True)
for root in (admin,academic):
    for o in [root,*root.children_recursive]:
        if o.type!='MESH':continue
        uv=o.data.uv_layers.get('UVMap') or o.data.uv_layers.new(name='UVMap')
        for f in o.data.polygons:
            ax=max(range(3),key=lambda k:abs(f.normal[k]))
            for li in f.loop_indices:
                q=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
                uv.data[li].uv=((q.y/3,q.z/3) if ax==0 else (q.x/3,q.z/3) if ax==1 else (q.x/3,q.y/3))
print('[V18 source] packing architecture materials',flush=True)
bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(R/'output/Zewail_City_3D.blend'),compress=True)
print('V17 architecture regenerated from corrected source. Full source rebuild remains required.')
