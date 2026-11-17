"""V19 photograph-supported facade depth and planted garden reconstruction.

Photo13/25: three glazed bands, supported side galleries; photo16/17: dense
garden beds and continuous residential cornices. All metric fits are estimates.
No classrooms, private rooms, or newly claimed surveyed paths are introduced.
"""
import math, random, json
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
from shapely.geometry import Point
from .geometry import instance

ROOT=Path(__file__).resolve().parents[2]

def gate_a_screen(P,M,e,upper,height):
    # Three distinct photographic storeys. Real slabs already extend behind
    # these spandrels. Lower band has open upper-hall doorways at +/-11.3m.
    for z0,z1 in ((upper,8.7),(9.35,15.45),(16.15,height-1.8)):
        if z0==upper:
            for a,b in ((2.5,8.),(10.5,e.L-10.5),(e.L-8.,e.L-2.5)):
                if b>a:P.curtain(e,a,b,z0,z1,mull=1.6,transom=3.6,mat=M['upper_lobby_glass'])
        else:P.curtain(e,2.5,e.L-2.5,z0,z1,mull=1.6,transom=3.2,mat=M['upper_lobby_glass'])
    for z in (8.7,15.5):
        P.det.fbox(M['metal'],e,e.L/2,.11,.24,e.L-5.,z,z+.48)
        P.det.fbox(M['metal_light'],e,e.L/2,.24,.04,e.L-5.,z+.48,z+.52)

def _palette(M):
    # Large court foreground in photo19/23 is neutral honed granite. Keep
    # the existing licensed fine PBR maps and physical UV scale.
    for key,a,b,joint in (
        ('plaza_light',(.135,.145,.15),(.17,.18,.185),(.12,.13,.135)),
        ('plaza_grey',(.115,.125,.13),(.15,.16,.165),(.10,.11,.115))):
        m=M[key]
        for n in m.node_tree.nodes:
            if n.type=='TEX_BRICK':
                n.inputs['Color1'].default_value=(*a,1)
                n.inputs['Color2'].default_value=(*b,1)
                n.inputs['Mortar'].default_value=(*joint,1)
            if n.type=='BSDF_PRINCIPLED' and not n.inputs['Roughness'].is_linked:
                n.inputs['Roughness'].default_value=.64
        mid=[(a[i]+b[i])/2 for i in range(3)]
        m.diffuse_color=(*mid,1);m['gltf_base_color']=mid;m.roughness=.64
    for key in ('court_glass','upper_lobby_glass'):
        m=M[key];color=(.16,.21,.24) if key=='court_glass' else (.13,.18,.22)
        m.diffuse_color=(*color,1);m['gltf_base_color']=list(color)
        for n in m.node_tree.nodes:
            if n.type=='BSDF_PRINCIPLED':
                n.inputs['Base Color'].default_value=(*color,1)
                n.inputs['Roughness'].default_value=.16
                n.inputs['Metallic'].default_value=.20
                if key=='upper_lobby_glass':n.inputs['Alpha'].default_value=.36

def _shrub_meshes():
    found=[m for m in bpy.data.meshes if m.name.startswith('ASSET_V19_Hedge_ClippedLeaf_')]
    if found:return found
    path=ROOT/'references/assets/v19/shrub_01/shrub_01_1k.blend'
    # The native library includes provider-authored leafy cluster meshes g/h/i
    # and genuine LODs absent from the flattened glTF download.
    with bpy.data.libraries.load(str(path),link=False) as (src,dst):
        dst.objects=[n for n in src.objects if n in ('shrub_01_g_LOD2','shrub_01_h_LOD2','shrub_01_i_LOD2')]
    selected=dst.objects
    for o in selected:bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.update();meshes=[]
    for o in selected:
        pts=[o.matrix_world@v.co for v in o.data.vertices]
        lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)))
        hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
        scale=min(1.2/max(hi.x-lo.x,hi.y-lo.y),.65/(hi.z-lo.z))
        xf=Matrix.Diagonal((scale,scale,scale,1.))@Matrix.Translation((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))
        me=o.data.copy();me.transform(xf@o.matrix_world);me.update()
        me.name=f'ASSET_V19_Hedge_ClippedLeaf_{len(meshes):02}'
        for mat in me.materials:
            mat['zc_v12_foliage']=True
            mat['zc_v19_source']='https://polyhaven.com/a/shrub_01 | CC0; provider g/h/i cluster LOD2'
            for n in mat.node_tree.nodes:
                if n.type=='TEX_IMAGE' and n.image:
                    target=path.parent/'textures'/Path(n.image.filepath).name
                    if target.exists():n.image.filepath=str(target);n.image.reload()
        meshes.append(me)
    for o in selected:bpy.data.objects.remove(o,do_unlink=True)
    if len(meshes)!=3:raise RuntimeError('Missing provider cluster LOD2 objects')
    return meshes

def _garden(M,C):
    from . import dormitory as D
    from .v17_elevation import datum
    root=bpy.data.objects['AB_East_Residential_Pair_Estimated']
    meshes=_shrub_meshes()
    if not meshes:return {'shrubs':0,'flowers':0,'installed':False}
    for o in list(bpy.data.objects):
        if o.name.startswith(('V19_Garden_','V19_Admin_','V19_Clipped_')):bpy.data.objects.remove(o,do_unlink=True)
    # Dense leaf meshes replace the visual cuboid hedge; keep the established
    # circulation/paver/terrain partition and building transforms intact.
    for name in ('Dorm_Garden_Hedges_Details','Dorm_Garden_Shrub_Rows_Details'):
        o=bpy.data.objects.get(name)
        if o:bpy.data.objects.remove(o,do_unlink=True)
    # Preserve the photographed clipped hedge alignment as a low core, with
    # actual imported foliage breaking the formerly smooth silhouette.
    core=D.build_hedges(M,bpy.data.collections['Planters_And_Hedges'],root)
    core.name='V19_Clipped_Hedge_Core_Details'
    core['zc_no_ground_collision']=True;core['zc_collision']=False
    # Ground-linked native hedge body follows the same residential pad datum.
    for v in core.data.vertices:v.co.z*=.85
    bpy.context.view_layer.update()
    low=min((core.matrix_world@v.co).z for v in core.data.vertices)
    core.location.z+=(.032+root.get('zc_v17_pad_datum_m',-1.55))-low
    rng=random.Random(19019);count=0;flowers=0
    coll=C['veg_shrubs'] if 'veg_shrubs' in C else C['veg_trees']
    shape=D.HEDGE.union(D.SHRUB_ROW).intersection(D.PLANTED)
    x0,y0,x1,y1=shape.bounds
    y=y0+.4
    while y<y1:
        x=x0+.4
        while x<x1:
            p=Point(x,y)
            # Full shrub radius clear of hardscape and actual building skin.
            if shape.distance(p)<.04 and D.PLANTED.buffer(-.43).covers(p) and D.SHELL.distance(p)>.8:
                angle=rng.uniform(0,math.tau);sc=rng.uniform(.82,1.08)
                for me in (meshes[count%len(meshes)],):
                    o=instance(me,f'V19_Garden_Shrub_{count:04}',coll,(x,y,.032+datum(x,y)),angle,sc)
                    o['zc_v19_vegetation']=True;o['zc_no_ground_collision']=True
                    o['zc_evidence']='Photo16/17 dense planted border; species and spacing estimated'
                count+=1
            x+=1.32
        y+=1.32
    # The existing licensed Gazania adds photographed flower accents inside
    # the beds, avoiding the playable paths and the tree-free Academic court.
    flowers_mesh=[m for m in bpy.data.meshes if m.name.startswith('ASSET_V18_Gazania_')]
    for line in D.LINES[:5]:
        for i in range(1,int(line.length/.85)):
            p=line.interpolate(i*.85);q=line.interpolate(min(line.length,i*.85+.1))
            v=Vector((q.x-p.x,q.y-p.y));v.normalize()
            for side in (-1,1):
                x,y=p.x-side*v.y*3.65,p.y+side*v.x*3.65
                pt=Point(x,y)
                if not D.PLANTED.buffer(-.35).covers(pt) or not flowers_mesh:continue
                me=flowers_mesh[flowers%len(flowers_mesh)]
                o=instance(me,f'V19_Garden_Flower_{flowers:04}',coll,(x,y,.035+datum(x,y)),rng.random()*math.tau,4.6)
                o['zc_no_ground_collision']=True;o['zc_v19_vegetation']=True;flowers+=1
    return {'shrubs':count,'flowers':flowers,'installed':True,'mesh_variants':len(meshes)}

def seat_vegetation():
    from mathutils.bvhtree import BVHTree
    vertices=[];faces=[]
    for s in bpy.data.objects:
        if s.type!='MESH' or s.name not in ('Lawns','Flower_Beds','Ground_Campus_Plot','Plaza_Paving'):continue
        offset=len(vertices);vertices.extend(s.matrix_world@v.co for v in s.data.vertices)
        faces.extend(tuple(offset+i for i in f.vertices) for f in s.data.polygons)
    ground=BVHTree.FromPolygons(vertices,faces);rows=[];removed=[]
    bpy.context.view_layer.update()
    for o in list(bpy.data.objects):
        if not o.name.startswith('V19_Garden_'):continue
        p=o.matrix_world.translation
        hit=ground.ray_cast(Vector((p.x,p.y,p.z+3)),Vector((0,0,-1)),8.)[0]
        if hit is None:
            removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True);continue
        low=min((o.matrix_world@v.co).z for v in o.data.vertices)
        o.location.z+=hit.z-low
        rows.append({'name':o.name,'xy':[round(p.x,5),round(p.y,5)],'z':o.location.z,'mesh':o.data.name,'root_gap_m':0.0})
    out=ROOT/'output/build_metadata/v19';out.mkdir(parents=True,exist_ok=True)
    (out/'vegetation_placement.json').write_text(json.dumps({'instances':rows,'removed_without_ground':removed},indent=1))
    return {'contacted':len(rows),'removed_without_ground':len(removed)}

def finish(M,C):
    _palette(M)
    # Shorter central crown leaves the photographed Administration portal
    # readable. The inherited imported palm is retained with a uniform scale.
    for o in bpy.data.objects:
        if o.type=='MESH' and o.data.name=='ASSET_V18_Central_Palm':
            width=max(max(v.co[k] for v in o.data.vertices)-min(v.co[k] for v in o.data.vertices) for k in (0,1))
            scale=5.04/width;o.scale=(scale,scale,scale);o['zc_v19_palm_fit']=True
    stats=_garden(M,C)
    stats.update(seat_vegetation())
    bpy.context.scene['zc_v19_revision']='Photo13 upper gallery shell / GateA screen / photo19 court / photo16 garden'
    out=ROOT/'output/build_metadata/v19';out.mkdir(parents=True,exist_ok=True)
    (out/'source_changes.json').write_text(json.dumps(stats,indent=2))
    print('[V19] facade depth, neutral court and real garden leaves:',stats,flush=True)
