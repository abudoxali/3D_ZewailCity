"""Idempotent final source pass, also valid on a frame-zero build."""
from pathlib import Path
import sys,bpy
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
# V18 architecture is generated from current sources in this final pipeline
# stage too. This keeps incremental scene builds and full builds identical;
# the same generators rebuild actual meshes, then re-seat roots and project UVs.
exec(compile((R/'tools/regenerate_architecture.py').read_text(),str(R/'tools/regenerate_architecture.py'),'exec'))
from utilities import dormitory
from utilities import v18_refresh_housing
v18_refresh_housing.apply(M,C)
old=bpy.data.objects.get('Dorm_Garden_Hedges_Details')
if old:
    root=old.parent;coll=old.users_collection[0];world=old.matrix_world.copy()
    bpy.data.objects.remove(old,do_unlink=True)
    hedge=dormitory.build_hedges(M,coll,root);hedge.matrix_world=world
    uv=hedge.data.uv_layers.new(name='UVMap')
    for face in hedge.data.polygons:
        axis=max(range(3),key=lambda k:abs(face.normal[k]))
        for li in face.loop_indices:
            q=hedge.matrix_world@hedge.data.vertices[hedge.data.loops[li].vertex_index].co
            uv.data[li].uv=((q.y/3,q.z/3) if axis==0 else (q.x/3,q.z/3) if axis==1 else (q.x/3,q.y/3))
from utilities import v17_elevation,v17_finalize
from utilities import v18_curb
v18_curb.refresh_existing()
from utilities import cinematics
coll=bpy.data.collections.get('Cinematic_Paths')
if coll:
    for obj in list(coll.objects):
        if obj.type=='CAMERA' or obj.name.endswith('_Target'):bpy.data.objects.remove(obj,do_unlink=True)
parent=bpy.data.collections.get('Cameras') or bpy.context.scene.collection
cinematics.build(bpy.context.scene,parent)
v17_elevation.seat_cameras_and_lights();v17_finalize.clean_surfaces()
from utilities import v18_forecourt
v18_forecourt.apply(M,C)
from utilities import v19_architecture
v19_architecture.finish(M,C)
bpy.ops.file.pack_all()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(R/'output/Zewail_City_3D.blend'),compress=True)
print('V17 native source finalization complete')
