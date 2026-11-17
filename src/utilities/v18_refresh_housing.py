"""Source rebuild of housing facades, retaining the world-space garden partition."""
import bpy
from .geometry import parent_keep
from .v17_elevation import datum

def apply(M,C):
    print('[V18 housing] rebuilding window geometry',flush=True)
    from . import dormitory
    name='AB_East_Residential_Pair_Estimated'
    old=bpy.data.objects[name];retained=[]
    for o in list(old.children):
        if o.name.startswith(name) or o.name=='AB_East_Residential_Collision_Proxy':continue
        world=o.matrix_world.copy();o.parent=None;o.matrix_world=world;retained.append(o)
    for o in [*old.children_recursive,old]:bpy.data.objects.remove(o,do_unlink=True)
    root=dormitory.build_pair(M,C)
    # Evaluate the recentered Parts transform before sampling world bounds.
    # A new object's matrix_world is otherwise still identity and samples the
    # Administration datum near origin, floating the housing shell above soil.
    bpy.context.view_layer.update()
    from mathutils import Vector
    pts=[root.matrix_world@Vector(p) for p in root.bound_box]
    x=(min(p.x for p in pts)+max(p.x for p in pts))/2;y=(min(p.y for p in pts)+max(p.y for p in pts))/2
    dz=datum(x,y);root.location.z+=dz;root['zc_v17_pad_datum_m']=dz
    bpy.context.view_layer.update()
    for o in retained:parent_keep(o,root)
    print('[V18 housing] projecting facade UVs',flush=True)
    for o in [root,*root.children_recursive]:
        if o in retained or o.type!='MESH':continue
        uv=o.data.uv_layers.get('UVMap') or o.data.uv_layers.new(name='UVMap')
        for f in o.data.polygons:
            ax=max(range(3),key=lambda k:abs(f.normal[k]))
            for li in f.loop_indices:
                q=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
                uv.data[li].uv=((q.y/3,q.z/3) if ax==0 else (q.x/3,q.z/3) if ax==1 else (q.x/3,q.y/3))
    print('[V18 housing] rebuilt facade openings/floors; retained garden children',len(retained),flush=True)
