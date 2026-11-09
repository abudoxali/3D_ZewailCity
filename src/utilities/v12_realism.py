"""Durable, deterministic V12 material/selected foliage integration. No ground geometry edits."""
from pathlib import Path
import bpy,json,math,random,bmesh
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2]
PBR=ROOT/'game/godot/assets/pbr'
# Provider surfaces (whole surface from CC0 maps, mean colour matched to the approved V11
# surface): material -> (asset, physical tile m, normal strength, contrast). Mirrors
# game/godot/scripts/pbr_materials.gd; tints from assets/pbr/tone_targets.json
# (tools/v12_tone_targets.py). Claude V12 review: natural sand/soil/earth keep the V11
# procedural surfaces (sand_01 read as grey cracked crust) and receive detail only.
MAP={
 'M_Asphalt':('asphalt_01',2.1,.5,1.),
}
DETAIL={'M_Paver_Road_Grey':'concrete_pavement_03','M_V6_Garden_Pavers':'concrete_pavement_03','M_Paving_Limestone':'concrete_pavement_03','M_Paving_Light':'concrete_pavement_03','M_V6_Plaza_Grey':'concrete_pavement_03','M_V6_Plaza_Light':'concrete_pavement_03','M_Concrete_Curb':'concrete_pavement_03','M_V7_Paving_Edge_Restraint':'concrete_pavement_03','M_Grass_Lawn':'sparse_grass',
 'M_Desert_Sand':'sand_01','M_Graded_Campus_Soil':'sand_01','M_Compacted_Earth':'sand_01','M_Planted_Soil_Sparse':'sparse_grass'}
TONE_KEY={'M_Asphalt':'Asphalt'}
def tones():
    p=PBR/'tone_targets.json'
    return json.loads(p.read_text()) if p.exists() else {}
def image(asset,kind):
    res={'paving_stones_125a':'2k'}.get(asset,'1k')
    im=bpy.data.images.load(str(PBR/asset/f'{asset}_{kind}_{res}.jpg'),check_existing=True)
    im.colorspace_settings.name='sRGB' if kind=='diff' else 'Non-Color'
    return im
def apply_materials():
    done=[];T=tones()
    for name,(asset,tile,strength,contrast) in MAP.items():
        m=bpy.data.materials.get(name)
        if not m:continue
        m.use_nodes=True;nt=m.node_tree;nt.nodes.clear()
        b=nt.nodes.new('ShaderNodeBsdfPrincipled');out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(b.outputs['BSDF'],out.inputs['Surface'])
        for kind,sock in [('diff','Base Color'),('rough','Roughness'),('nor_gl','Normal')]:
            t=nt.nodes.new('ShaderNodeTexImage');t.image=image(asset,kind)
            if kind=='nor_gl':
                n=nt.nodes.new('ShaderNodeNormalMap');n.inputs['Strength'].default_value=strength;nt.links.new(t.outputs['Color'],n.inputs['Color']);nt.links.new(n.outputs[0],b.inputs[sock])
            elif kind=='diff':
                tt=T.get(TONE_KEY[name],{});sat=tt.get('saturation',1.);tint=tt.get('tint',[1,1,1]);pm=tt.get('pbr_mean_linear',[.2,.2,.2])
                L=.2126*pm[0]+.7152*pm[1]+.0722*pm[2];pmd=[L+(c-L)*sat for c in pm]
                bw=nt.nodes.new('ShaderNodeRGBToBW');nt.links.new(t.outputs['Color'],bw.inputs[0])
                mix=nt.nodes.new('ShaderNodeMixRGB');mix.inputs[0].default_value=sat
                nt.links.new(bw.outputs[0],mix.inputs[1]);nt.links.new(t.outputs['Color'],mix.inputs[2])
                con=nt.nodes.new('ShaderNodeMixRGB');con.inputs[0].default_value=contrast;con.inputs[1].default_value=(pmd[0],pmd[1],pmd[2],1.)
                nt.links.new(mix.outputs[0],con.inputs[2])
                mult=nt.nodes.new('ShaderNodeVectorMath');mult.operation='MULTIPLY';mult.inputs[1].default_value=tint
                nt.links.new(con.outputs[0],mult.inputs[0]);nt.links.new(mult.outputs[0],b.inputs[sock])
            else:
                floor=nt.nodes.new('ShaderNodeMath');floor.operation='MAXIMUM';floor.inputs[1].default_value=.93 if name=='M_Asphalt' else .72
                nt.links.new(t.outputs['Color'],floor.inputs[0]);nt.links.new(floor.outputs[0],b.inputs[sock])
        m['zc_v12_asset']=asset;m['zc_tile_m']=tile;m['gltf_base_color']=[1.,1.,1.];m.roughness=1.
        done.append(name)
    # Source UVs are assigned in metres from the actual world coordinate of each face.
    meshes=set()
    for o in bpy.data.objects:
        if o.type!='MESH' or o.data.name in meshes:continue
        if not any(m and (m.name in MAP or m.name in DETAIL or 'Stone' in m.name or 'Stucco' in m.name) for m in o.data.materials):continue
        meshes.add(o.data.name);uv=o.data.uv_layers.get('UVMap') or o.data.uv_layers.new(name='UVMap')
        for f in o.data.polygons:
            if f.material_index>=len(o.data.materials):continue
            m=o.data.materials[f.material_index]
            if not m or not (m.name in MAP or m.name in DETAIL or 'Stone' in m.name or 'Stucco' in m.name):continue
            tile=MAP[m.name][1] if m.name in MAP else ({'M_Grass_Lawn':2.,'M_Planted_Soil_Sparse':2.,'M_Desert_Sand':1.5,'M_Graded_Campus_Soil':1.5,'M_Compacted_Earth':1.5}.get(m.name,2.1) if m.name in DETAIL else 3.);axis=max(range(3),key=lambda i:abs(f.normal[i]))
            for li in f.loop_indices:
                co=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
                uv.data[li].uv=((co.x if axis!=0 else co.y)/tile,(co.y if axis==2 else co.z)/tile)
    # Architectural panel grids stay authoritative. Add only physical fine normal/roughness.
    for m in bpy.data.materials:
        if not ('Stone' in m.name or 'Stucco' in m.name or m.name in DETAIL) or not m.use_nodes:continue
        b=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
        if b is None:continue
        nt=m.node_tree
        geom=nt.nodes.new('ShaderNodeNewGeometry');scale=nt.nodes.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs['Scale'].default_value=1/3
        nt.links.new(geom.outputs['Position'],scale.inputs[0])
        for kind in ['nor_gl','rough']:
            t=nt.nodes.new('ShaderNodeTexImage');t.image=image(DETAIL.get(m.name,'beige_wall_001'),kind)
            if kind=='nor_gl':
                normal=nt.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.22
                nt.links.new(t.outputs[0],normal.inputs['Color']);nt.links.new(normal.outputs[0],b.inputs['Normal'])
            else:
                t.projection='BOX';t.projection_blend=.15;nt.links.new(scale.outputs[0],t.inputs['Vector'])
                floor=nt.nodes.new('ShaderNodeMath');floor.operation='MAXIMUM';floor.inputs[1].default_value=.78;nt.links.new(t.outputs[0],floor.inputs[0]);nt.links.new(floor.outputs[0],b.inputs['Roughness'])
        done.append(m.name+' (fine architectural response)')
    return done
def foliage_mesh():
    existing=bpy.data.meshes.get('ASSET_V12_Pachira_Shrub')
    if existing:return existing
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'references/assets/pachira_aquatica_01/pachira_aquatica_01_1k.gltf'))
    imported=[o for o in bpy.data.objects if o not in before]
    imported_names=[o.name for o in imported]
    meshes=[o for o in imported if o.type=='MESH' and o.name.endswith('_c')]
    # Provider supplies four complete variants. Select c (20,551 triangles).
    for o in bpy.context.scene.objects:o.select_set(False)
    for o in meshes:o.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    if len(meshes)>1:
        with bpy.context.temp_override(active_object=meshes[0],object=meshes[0],selected_objects=meshes,selected_editable_objects=meshes):
            bpy.ops.object.join()
    o=meshes[0]
    o.data.transform(o.matrix_world);o.matrix_world=Matrix.Identity(4)
    lo=[min(v.co[i] for v in o.data.vertices) for i in range(3)]
    hi=[max(v.co[i] for v in o.data.vertices) for i in range(3)]
    o.data.transform(Matrix.Translation((-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2])))
    me=o.data;me.name='ASSET_V12_Pachira_Shrub'
    for mat in me.materials:
        mat.name='M_V12_'+mat.name;mat['zc_v12_foliage']=True
    for name in imported_names:
        ob=bpy.data.objects.get(name)
        if ob:bpy.data.objects.remove(ob,do_unlink=True)
    return me
def apply_vegetation(stage='prototype'):
    # 'trees' (V12): 14 roadside/Administration trees use the Pachira model; shrubs stay V11
    # (scaled-down Pachira shrubs read as sparse twigs, Claude QA).
    # 'corridor' (V12.1): EVERY tree of the two main-approach roadside rows and of the
    # Administration frontage uses it, so neither row mixes two tree styles (QA finding;
    # C02 shows the approach lined with slender broadleaf trees). Positions, original
    # dimensions and collision scale are kept; palms and all other campus trees untouched.
    if stage=='none':return {'stage':'none','rejected':'shrub_04 branch prototype failed visual acceptance; not expanded','replaced':[]}
    me=foliage_mesh()
    # Replace actual planting objects only, keeping existing origins/rotation/scale.
    main=[];admin=[];dorm=[]
    for o in bpy.data.objects:
        if o.type!='MESH' or o.data==me:continue
        if 'Shrub' not in o.data.name or 'V12' in o.data.name:continue
        x,y,z=o.matrix_world.translation
        if abs(x)<25 and 120<y<285:main.append(o)
        elif abs(x)<85 and 45<y<115:admin.append(o)
        elif 390<x<440 and -600<y<-550:dorm.append(o)
    main.sort(key=lambda o:(o.location-Vector((0,260,0))).length)
    chosen=[] if stage in ['trees','corridor'] else main[:1] if stage=='prototype' else main[:18]+sorted(admin,key=lambda o:o.name)[:16]+sorted(dorm,key=lambda o:o.name)[:24]
    rows=[]
    for o in chosen:
        old=o.data.name;dims=list(o.dimensions);o.data=me
        bpy.context.view_layer.update()
        for i in range(3):
            if o.dimensions[i]>.0001:o.scale[i]*=dims[i]/o.dimensions[i]
        bpy.context.view_layer.update()
        o['zc_v12_foliage_source']='https://polyhaven.com/a/pachira_aquatica_01'
        rows.append(dict(name=o.name,prior_mesh=old,position=list(o.matrix_world.translation),prior_dimensions=dims,new_dimensions=list(o.dimensions)))
    trees=[]
    if stage in ['tree_prototype','expanded','trees','corridor']:
        tree_me=me.copy();tree_me.name='ASSET_V12_Tree_Pachira'
        candidates=[o for o in bpy.data.objects if o.type=='MESH' and o.data.name.startswith('ASSET_Tree_') and abs(o.location.x)<60 and 150<o.location.y<300]
        candidates.sort(key=lambda o:(o.location-Vector((30,260,0))).length)
        selected=candidates[:1] if stage=='tree_prototype' else candidates[:10]
        if stage=='corridor':
            zone=lambda o:(abs(o.location.x)<60 and 140<o.location.y<320) or (abs(o.location.x)<85 and 45<o.location.y<115)
            selected=sorted([o for o in bpy.data.objects if o.type=='MESH' and o.data.name.startswith('ASSET_Tree_') and zone(o)],key=lambda o:o.name)
        elif stage in ['expanded','trees']:
            selected += sorted([o for o in bpy.data.objects if o.type=='MESH' and o.data.name.startswith('ASSET_Tree_') and abs(o.location.x)<85 and 45<o.location.y<115],key=lambda o:o.name)[:4]
        for o in selected:
            pos=list(o.matrix_world.translation);dims=list(o.dimensions);prior=o.data.name
            o['zc_v12_original_collision_scale']=o.scale.x
            o.data=tree_me;bpy.context.view_layer.update()
            if stage=='corridor':
                # V12.1 QA: per-axis fitting to wide low-poly crowns squashed the model into
                # flat sprawling shapes and inherited tilts made trunks lean. Keep natural
                # proportions (uniform scale from the original height) and an upright trunk.
                o.rotation_euler.x=0.;o.rotation_euler.y=0.;bpy.context.view_layer.update()
                k=dims[2]/o.dimensions.z if o.dimensions.z>.0001 else 1.
                o.scale=(o.scale.x*k,o.scale.y*k,o.scale.z*k)
            else:
                for i in range(3):
                    if o.dimensions[i]>.0001:o.scale[i]*=dims[i]/o.dimensions[i]
            bpy.context.view_layer.update()
            trees.append(dict(name=o.name,position=pos,prior_mesh=prior,prior_dimensions=dims,dimensions=list(o.dimensions)))
    return {'stage':stage,'prototype_candidates':len(main),'replaced':rows,'trees':trees,'asset_triangles':sum(len(p.vertices)-2 for p in me.polygons)}
# ---------------------------------------------------------------- V13 vegetation
# Every procedural broadleaf tree (ASSET_Tree_0/1/2) becomes one of the four Poly Haven
# pachira_aquatica_01 variants (CC0; deterministic per object name), procedural date palms
# (ASSET_Palm_*) become the Innerscene "Mature date palm tree" and procedural fan palms
# (ASSET_Fan_Palm_*) the Innerscene "Palm, detailed" (both CC0; no CC0 fan-palm model was
# found, so that species is approximated and recorded). Object location, yaw and original
# height are kept; trunks are upright; scale is uniform (natural proportions); the trunk
# collider keeps the original procedural scale (zc_v12_original_collision_scale).
V13_PALMS={'ASSET_V13_Date_Palm':'references/assets/innerscene_mature_date_palm/mature-date-palm-tree.glb',
           'ASSET_V13_Palm_Detailed':'references/assets/innerscene_palm_detailed/palm-detailed.glb'}
def _import_joined(path,mesh_name,keep=lambda n:True,material_prefix='M_V13_'):
    me=bpy.data.meshes.get(mesh_name)
    if me:return me
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new_names=[o.name for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    meshes=[bpy.data.objects[n] for n in new_names if bpy.data.objects[n].type=='MESH' and keep(n)]
    world={o.name:o.matrix_world.copy() for o in meshes}
    for o in meshes:
        o.data=o.data.copy();o.parent=None;o.data.transform(world[o.name]);o.matrix_world=Matrix.Identity(4)
    for o in bpy.context.scene.objects:o.select_set(False)
    for o in meshes:o.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    if len(meshes)>1:
        with bpy.context.temp_override(active_object=meshes[0],object=meshes[0],selected_objects=meshes,selected_editable_objects=meshes):
            bpy.ops.object.join()
    o=meshes[0];me=o.data
    lo=[min(v.co[i] for v in me.vertices) for i in range(3)];hi=[max(v.co[i] for v in me.vertices) for i in range(3)]
    me.transform(Matrix.Translation((-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2])))
    me.name=mesh_name
    for mat in me.materials:
        if mat and not mat.get('zc_v12_foliage'):
            mat.name=material_prefix+mesh_name.replace('ASSET_V13_','')+'_'+mat.name;mat['zc_v12_foliage']=True
    for n in new_names:
        if n in bpy.data.objects:bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
    return me
def _import_pachira_variants(gl):
    # One import (shared bark/leaf materials and textures); one joined mesh per variant.
    if all(bpy.data.meshes.get(f'ASSET_V13_Pachira_{v.upper()}') for v in 'abcd'):
        return {v:bpy.data.meshes[f'ASSET_V13_Pachira_{v.upper()}'] for v in 'abcd'}
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(gl))
    new_names=[o.name for o in bpy.data.objects if o not in before];bpy.context.view_layer.update()
    world={n:bpy.data.objects[n].matrix_world.copy() for n in new_names if bpy.data.objects[n].type=='MESH'}
    out={}
    for v in 'abcd':
        meshes=[bpy.data.objects[n] for n in new_names if n in bpy.data.objects and bpy.data.objects[n].type=='MESH' and n.endswith('_'+v)]
        for o in meshes:
            o.data=o.data.copy();o.parent=None;o.data.transform(world[o.name]);o.matrix_world=Matrix.Identity(4)
        for o in bpy.context.scene.objects:o.select_set(False)
        for o in meshes:o.select_set(True)
        bpy.context.view_layer.objects.active=meshes[0]
        if len(meshes)>1:
            with bpy.context.temp_override(active_object=meshes[0],object=meshes[0],selected_objects=meshes,selected_editable_objects=meshes):
                bpy.ops.object.join()
        me=meshes[0].data
        lo=[min(x.co[i] for x in me.vertices) for i in range(3)];hi=[max(x.co[i] for x in me.vertices) for i in range(3)]
        me.transform(Matrix.Translation((-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2])));me.name=f'ASSET_V13_Pachira_{v.upper()}';out[v]=me
    for mat in {m for me in out.values() for m in me.materials if m}:
        if not mat.get('zc_v12_foliage'):mat.name='M_V12_'+mat.name;mat['zc_v12_foliage']=True
    for n in new_names:
        if n in bpy.data.objects:bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
    return out
def _leafy_shrub(src_me,name,seed,clusters=60):
    # V13 shrubs: authored Poly Haven pachira leaf geometry (real leaf texture/UVs), its
    # leaf clusters (loose parts of the leaf material) re-arranged over a dome so the
    # shrub reads as a dense clipped ornamental bush instead of a faceted blob.
    me=bpy.data.meshes.get(name)
    if me:return me
    rng=random.Random(seed)
    bm=bmesh.new();bm.from_mesh(src_me);bm.faces.ensure_lookup_table()
    leaf_idx=max(range(len(src_me.materials)),key=lambda i:('leaves' in src_me.materials[i].name.lower()))
    faces=[f for f in bm.faces if f.material_index==leaf_idx]
    # islands by shared vertices
    seen=set();islands=[]
    for f in faces:
        if f.index in seen:continue
        stack=[f];isl=[]
        seen.add(f.index)
        while stack:
            g=stack.pop();isl.append(g)
            for v in g.verts:
                for h in v.link_faces:
                    if h.material_index==leaf_idx and h.index not in seen:seen.add(h.index);stack.append(h)
        if 40<=len(isl)<=420:islands.append(isl)
    uv=bm.loops.layers.uv.active
    out=bmesh.new();ouv=out.loops.layers.uv.new('UVMap')
    pick=[islands[rng.randrange(len(islands))] for _ in range(clusters)]
    for i,isl in enumerate(pick):
        vs={v for f in isl for v in f.verts};c=sum((v.co for v in vs),Vector())/len(vs)
        ext=max((v.co-c).length for v in vs) or 1.
        # point on an ellipsoid dome (r=0.5, h=0.65), slightly inside for density
        th=rng.uniform(0,2*math.pi);ph=math.acos(rng.uniform(.05,1.))
        rr=rng.uniform(.8,1.)
        pos=Vector((math.sin(ph)*math.cos(th)*.5*rr,math.sin(ph)*math.sin(th)*.5*rr,.32+math.cos(ph)*.33*rr))
        k=rng.uniform(.3,.42)/ext
        rot=(Vector((0,0,1)).rotation_difference(pos-Vector((0,0,.2)))).to_matrix()@Matrix.Rotation(rng.uniform(0,2*math.pi),3,'Z')
        vmap={}
        for v in vs:vmap[v]=out.verts.new(pos+rot@((v.co-c)*k))
        for f in isl:
            try:nf=out.faces.new([vmap[v] for v in f.verts])
            except ValueError:continue
            for l,ol in zip(f.loops,nf.loops):ol[ouv].uv=l[uv].uv
    me=bpy.data.meshes.new(name);out.to_mesh(me);out.free();bm.free()
    me.materials.append(src_me.materials[leaf_idx])
    for poly in me.polygons:poly.use_smooth=True
    lo=[min(v.co[i] for v in me.vertices) for i in range(3)]
    me.transform(Matrix.Translation((0,0,-lo[2])))
    return me
def _swap_fit(objs,me):
    rows=[]
    for o in objs:
        dims=list(o.dimensions);prior=o.data.name;o.data=me;bpy.context.view_layer.update()
        for i in range(3):
            if o.dimensions[i]>.0001:o.scale[i]*=dims[i]/o.dimensions[i]
        bpy.context.view_layer.update();o['zc_v13_vegetation_source']=me.name
        rows.append(o.name)
    return rows
VEG_COLLECTIONS={'Trees','Palms','Shrubs','Dormitory_Estimated_Garden'}
def _ground_snap(o,embed=.04,reach=1.):
    # V13 (MCP audit): authored models start exactly at their origin, unlike the procedural
    # trunks that extended below it, so 8 palms floated 0.17-0.39 m. Seat every replaced
    # plant on the actual ground under it (vegetation ignored), a few cm embedded.
    dg=bpy.context.evaluated_depsgraph_get();sc=bpy.context.scene
    base=o.matrix_world.translation.copy();start=base+Vector((0,0,30))
    for _ in range(40):
        hit,loc,nor,idx,ob,_m=sc.ray_cast(dg,start,Vector((0,0,-1)))
        if not hit:return None
        if {c.name for c in ob.users_collection}&VEG_COLLECTIONS:start=loc-Vector((0,0,.01));continue
        gap=base.z-loc.z
        if abs(gap)<=reach:o.location.z-=gap+embed;return round(gap,3)
        return None
    return None
def _swap(objs,me):
    rows=[]
    for o in objs:
        dims=list(o.dimensions);prior=o.data.name
        if 'zc_v12_original_collision_scale' not in o:o['zc_v12_original_collision_scale']=o.scale.x
        o.data=me;o.rotation_euler.x=0.;o.rotation_euler.y=0.;bpy.context.view_layer.update()
        k=dims[2]/o.dimensions.z if o.dimensions.z>.0001 else 1.
        o.scale=(o.scale.x*k,o.scale.y*k,o.scale.z*k);bpy.context.view_layer.update()
        o['zc_v13_vegetation_source']=me.name;o['zc_v13_ground_gap_before_snap']=_ground_snap(o) or 0.;bpy.context.view_layer.update()
        rows.append(dict(name=o.name,prior_mesh=prior,position=[round(v,3) for v in o.matrix_world.translation],prior_dimensions=[round(v,2) for v in dims],dimensions=[round(v,2) for v in o.dimensions]))
    return rows
V13_LEAFY_SHRUBS=False
def apply_v13_vegetation():
    gl=ROOT/'references/assets/pachira_aquatica_01/pachira_aquatica_01_1k.gltf'
    variants=_import_pachira_variants(gl)
    trees=sorted([o for o in bpy.data.objects if o.type=='MESH' and (o.data.name.startswith('ASSET_Tree_') or o.data.name in ('ASSET_V12_Tree_Pachira',))],key=lambda o:o.name)
    import zlib
    # Variants c and d only: a is the braided-trunk potted form, b a sparse sapling.
    by={v:[] for v in 'cd'}
    for o in trees:by['cd'[zlib.crc32(o.name.encode())%2]].append(o)
    rep={'trees':{v:_swap(by[v],variants[v]) for v in 'cd'}}
    palms={k:_import_joined(ROOT/p,k) for k,p in V13_PALMS.items()}
    date=sorted([o for o in bpy.data.objects if o.type=='MESH' and o.data.name.startswith('ASSET_Palm_')],key=lambda o:o.name)
    fan=sorted([o for o in bpy.data.objects if o.type=='MESH' and o.data.name.startswith('ASSET_Fan_Palm_')],key=lambda o:o.name)
    rep['date_palms']=_swap(date,palms['ASSET_V13_Date_Palm'])
    rep['fan_palms_as_palm_detailed']=_swap(fan,palms['ASSET_V13_Palm_Detailed'])
    # Leaf-geometry shrubs (_leafy_shrub) were tried twice and REJECTED by independent QA
    # (read as dead leaf piles / sprigs); the V12.1 shrubs stay until a CC0 dense-shrub
    # model is available. Kept switchable for evaluation only.
    shrubs=[]
    if V13_LEAFY_SHRUBS:
        shrubs=[_leafy_shrub(variants['d'],'ASSET_V13_Shrub_Leafy_A',13),_leafy_shrub(variants['c'],'ASSET_V13_Shrub_Leafy_B',29)]
        blob=sorted([o for o in bpy.data.objects if o.type=='MESH' and (o.data.name.startswith('ASSET_Shrub_Green_') or o.data.name.startswith('ASSET_V7_Round_Shrub_'))],key=lambda o:o.name)
        rep['shrubs']={m.name:len(_swap_fit([o for o in blob if zlib.crc32(o.name.encode())%2==i],m)) for i,m in enumerate(shrubs)}
    else:
        rep['shrubs']='unchanged V12.1 shrubs (leaf-geometry shrubs rejected in QA)'
    rep['asset_triangles']={m.name:sum(len(p.vertices)-2 for p in m.polygons) for m in [variants['c'],variants['d']]+list(palms.values())+shrubs}
    for v in 'ab':
        if variants[v].users==0:bpy.data.meshes.remove(variants[v])
    for n in ['ASSET_Tree_0','ASSET_Tree_1','ASSET_Tree_2','ASSET_Palm_0','ASSET_Palm_1','ASSET_Palm_2','ASSET_Palm_3','ASSET_Fan_Palm_0','ASSET_Fan_Palm_1','ASSET_Fan_Palm_2','ASSET_Shrub_Green_0','ASSET_Shrub_Green_1','ASSET_V7_Round_Shrub_0','ASSET_V7_Round_Shrub_1']:
        m=bpy.data.meshes.get(n)
        rep.setdefault('procedural_meshes_remaining_users',{})[n]=m.users if m else 0
    return rep
def apply(stage='prototype'):
    if stage=='v13':
        report={'materials':apply_materials(),'vegetation':apply_v13_vegetation()}
        p=ROOT/'output/v12_integration.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(report,indent=2))
        print('[V13 integration]',json.dumps({k:(len(v) if isinstance(v,list) else v) for k,v in report['vegetation'].items() if k!='trees'}))
        return report
    report={'materials':apply_materials(),'vegetation':apply_vegetation(stage)}
    p=ROOT/'output/v12_integration.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(report,indent=2))
    print('[V12 integration]',json.dumps(report))
    return report
