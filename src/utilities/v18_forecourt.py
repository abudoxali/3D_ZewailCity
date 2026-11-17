"""Administration photo01 circular flower bed; native source geometry, not an overlay road.

Restores the photographed low planting/white pebble rings in the existing
mapped wedge lawn at (0,82). Radius/plant species and inner motif remain
photo-guided estimates. The source lawn is cut before the bed top is emitted.
"""
from pathlib import Path
import math,random,json
import bpy,bmesh
from mathutils import Vector,Matrix
from shapely.geometry import Point,Polygon,LineString
from shapely import constrained_delaunay_triangles
ROOT=Path(__file__).resolve().parents[2]
CENTER=(0.,82.);RADIUS=7.

def _flower_meshes():
 meshes=[m for m in bpy.data.meshes if m.name.startswith('ASSET_V18_Gazania_')]
 if meshes:return meshes
 path=ROOT/'references/assets/v18/flower_gazania/flower_gazania_1k.gltf'
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));bpy.context.view_layer.update()
 new=[o for o in bpy.data.objects if o not in before];meshes=[]
 for o in new:
  if o.type!='MESH' or 'LOD0' not in o.name:continue
  me=o.data.copy();me.name=f'ASSET_V18_Gazania_{len(meshes):02}'
  me.transform(o.matrix_world)
  lo=[min(v.co[i] for v in me.vertices) for i in range(3)]
  hi=[max(v.co[i] for v in me.vertices) for i in range(3)]
  me.transform(Matrix.Translation((-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2])))
  for mat in me.materials:
   mat['zc_v12_foliage']=True
   mat['zc_v18_source']='https://polyhaven.com/a/flower_gazania | CC0'
  meshes.append(me)
 for o in new:bpy.data.objects.remove(o,do_unlink=True)
 if not meshes:raise RuntimeError('No actual Gazania LOD0 mesh imported')
 return meshes

def apply(M,C):
 lawn=bpy.data.objects['Lawns'];disc=Point(CENTER).buffer(RADIUS,quad_segs=64)
 inv=lawn.matrix_world.inverted();bm=bmesh.new();bm.from_mesh(lawn.data)
 base=None
 # Read the actual current lawn datum before cutting, rather than assuming Z=0.
 for face in bm.faces:
  vs=[lawn.matrix_world@v.co for v in face.verts]
  if max(v.x for v in vs)<-RADIUS or min(v.x for v in vs)>RADIUS:continue
  if max(v.y for v in vs)<82-RADIUS or min(v.y for v in vs)>82+RADIUS:continue
  if face.normal.z<.5:continue
  poly=Polygon([(v.x,v.y) for v in vs])
  if poly.is_valid and poly.area>1e-10 and poly.covers(Point(CENTER)):
   base=sum(v.z for v in vs)/len(vs);break
 if lawn.get('zc_v18_flower_bed_cut'):
  base=float(lawn['zc_v18_flower_bed_base'])
 if base is None:raise RuntimeError('Photographed bed has no real source lawn floor')
 uv=bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
 color=bm.loops.layers.float_color.get('Col') or bm.loops.layers.float_color.new('Col')
 def add_tri(coords,mat,zfn):
  if (coords[1][0]-coords[0][0])*(coords[2][1]-coords[0][1])-(coords[1][1]-coords[0][1])*(coords[2][0]-coords[0][0])<0:coords=list(reversed(coords))
  if mat.name not in lawn.data.materials:lawn.data.materials.append(mat)
  index=lawn.data.materials.find(mat.name)
  verts=[bm.verts.new(inv@Vector((x,y,zfn(x,y)))) for x,y in coords]
  face=bm.faces.new(verts);face.material_index=index
  for loop,(x,y) in zip(face.loops,coords):loop[uv].uv=(x/3,y/3);loop[color]=(0.,.5,0.,1.)
 def patch(shape,mat,z):
  if shape.is_empty:return
  for tri in constrained_delaunay_triangles(shape).geoms:
   co=list(tri.exterior.coords)[:3]
   if (co[1][0]-co[0][0])*(co[2][1]-co[0][1])-(co[1][1]-co[0][1])*(co[2][0]-co[0][0])<0:co.reverse()
   add_tri(co,mat,lambda x,y:z)
 if not lawn.get('zc_v18_flower_bed_cut'):
  for face in list(bm.faces):
   vs=[lawn.matrix_world@v.co for v in face.verts]
   if face.normal.z<.5:continue
   if max(v.x for v in vs)<-RADIUS or min(v.x for v in vs)>RADIUS:continue
   if max(v.y for v in vs)<82-RADIUS or min(v.y for v in vs)>82+RADIUS:continue
   poly=Polygon([(v.x,v.y) for v in vs])
   if not poly.is_valid or poly.area<1e-10 or not poly.intersects(disc):continue
   mat=lawn.data.materials[face.material_index];normal=(vs[1]-vs[0]).cross(vs[2]-vs[0]);origin=vs[0]
   def zfn(x,y,n=normal,p=origin):return p.z-(n.x*(x-p.x)+n.y*(y-p.y))/n.z
   rest=poly.difference(disc);bm.faces.remove(face)
   for tri in constrained_delaunay_triangles(rest).geoms:
    co=list(tri.exterior.coords)[:3]
    if tri.area>1e-10:add_tri(co,mat,zfn)
  outer=disc.difference(Point(CENTER).buffer(6.6,quad_segs=64))
  patch(outer,M['pebbles'],base+.08)
  patch(Point(CENTER).buffer(6.6,quad_segs=64),M['soil'],base+.06)
  inner=Point(CENTER).buffer(2.8,quad_segs=64)
  patch(inner,M['granite'],base+.075)
  patch(inner.difference(inner.buffer(-.28)),M['pebbles'],base+.085)
  # Photo01 light pebble curl: a bounded decorative interpretation, not a logo claim.
  curl=LineString([(-1.5,83.5),(-.1,83.25),(.9,82.5),(-.8,81.7),(.1,80.75),(1.5,80.5)]).buffer(.28)
  patch(curl.intersection(inner.buffer(-.3)),M['pebbles'],base+.09)
  bm.to_mesh(lawn.data);lawn.data.update()
  lawn['zc_v18_flower_bed_cut']=True;lawn['zc_v18_flower_bed_base']=base
 # This is a top-only heightfield. Constrained triangulation may return either
 # winding: downward remainder faces rendered/collided from their underside,
 # creating two real failed Godot grid samples north of the new flower bed.
 bm.normal_update();flipped=0
 for face in bm.faces:
  if face.normal.z<-.1:face.normal_flip();flipped+=1
 if flipped:
  bm.to_mesh(lawn.data);lawn.data.update()
  lawn['zc_v18_lawn_winding_repaired']=int(lawn.get('zc_v18_lawn_winding_repaired',0))+flipped
 print('[V18 source lawn] downward top faces repaired',flipped,flush=True)
 bm.free()
 # Replace the old low red/orange cylinder proxies at the photographed arm
 # beds. Their real soil/pebble geometry stays; only proxy plant faces go.
 beds=bpy.data.objects.get('Flower_Beds')
 if beds and not beds.get('zc_v18_proxy_flowers_removed'):
  fb=bmesh.new();fb.from_mesh(beds.data)
  remove=[f for f in fb.faces if any(s in beds.data.materials[f.material_index].name for s in ('Shrub_Red','Shrub_Orange'))]
  if remove:bmesh.ops.delete(fb,geom=remove,context='FACES_ONLY')
  fb.to_mesh(beds.data);fb.free();beds['zc_v18_proxy_flowers_removed']=True
 for o in list(bpy.data.objects):
  if o.name.startswith('V18_Admin_Flower_'):bpy.data.objects.remove(o,do_unlink=True)
 meshes=_flower_meshes();rng=random.Random(1801);count=0
 for ix in range(-15,16):
  for iy in range(-15,16):
   x=ix*.43+rng.uniform(-.08,.08);y=82+iy*.43+rng.uniform(-.08,.08);r=math.hypot(x,y-82)
   if not 3.2<r<6.45:continue
   o=bpy.data.objects.new(f'V18_Admin_Flower_{count:04}',meshes[count%len(meshes)])
   C['veg_shrubs'].objects.link(o);o.location=(x,y,base+.055);o.rotation_euler.z=rng.uniform(0,math.tau)
   scale=rng.uniform(1.6,2.4);o.scale=(scale,scale,scale)
   o['zc_v18_photo']='Owner annotated01 circular flower bed; orange groundcover form, species/scale estimated'
   count+=1
 # Low flower rows directly against the low arm facades are photo-supported.
 bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
 for side in (-1,1):
  for i in range(26):
   for row in range(2):
    x=side*(50.15+i*.42);y=36.7+row*.65;start=Vector((x,y,30.));loc=None
    for attempt in range(24):
     hit,point,normal,index,obj,mat=bpy.context.scene.ray_cast(deps,start,Vector((0,0,-1)))
     if not hit:break
     if obj.type=='MESH' and not obj.data.name.startswith('ASSET_') and not obj.name.startswith('V18_Admin_Flower_'):
      loc=point;break
     start=point-Vector((0,0,.01))
    if loc is None:raise RuntimeError('No actual ground contact for Administration flower row')
    o=bpy.data.objects.new(f'V18_Admin_Flower_{count:04}',meshes[count%len(meshes)])
    C['veg_shrubs'].objects.link(o);o.location=(x,y,loc.z-.005);o.rotation_euler.z=rng.uniform(0,math.tau)
    s=rng.uniform(1.5,2.2);o.scale=(s,s,s);o['zc_v18_photo']='Photo01/15 low facade flower border; species estimated';count+=1
 # Keep the retained central tree/palm in actual contact with the raised bed.
 for o in bpy.data.objects:
  if o.type!='MESH' or not o.data.name.startswith(('ASSET_V13_Palm','ASSET_V13_Date_Palm','ASSET_V13_Pachira')):continue
  x,y=o.matrix_world.translation.xy
  if math.hypot(x,y-82)>2.8:continue
  if o.data.name.startswith(('ASSET_V13_Palm','ASSET_V13_Date_Palm')):
   # Annotated01 has a compact, broad date-palm crown, not the slender
   # umbrella crown of the inherited fan-palm stand-in. Reuse licensed V13
   # date-palm geometry; crown envelope is a photographic estimate.
   me=bpy.data.meshes.get('ASSET_V18_Central_Palm')
   if me is None:
    source=bpy.data.meshes.get('ASSET_V13_Date_Palm')
    if source:
     # Preserve frond proportions. Compress only bare trunk length for the
     # short photographed palm; the earlier whole-Z scaling flattened its crown.
     verts=[v.co.copy() for v in source.vertices];faces=[tuple(p.vertices) for p in source.polygons]
     slots=[p.material_index for p in source.polygons]
     for v in verts:v.z=v.z*2.7/9.2 if v.z<9.2 else v.z-6.5
     # One offset crown layer gives the dense retained fronds visible in01.
     # Uses the same CC0 leaves/UVs. No speculative new species is introduced.
     crown=[p for p in source.polygons if min(source.vertices[i].co.z for i in p.vertices)>9.2 and max(math.hypot(source.vertices[i].co.x,source.vertices[i].co.y) for i in p.vertices)>.7]
     used=sorted({i for p in crown for i in p.vertices});remap={i:len(verts)+k for k,i in enumerate(used)}
     rotation=Matrix.Rotation(.43,3,'Z')
     for i in used:
      v=rotation@source.vertices[i].co;v.z-=6.5;verts.append(v)
     for p in crown:faces.append(tuple(remap[i] for i in p.vertices));slots.append(p.material_index)
     me=bpy.data.meshes.new('ASSET_V18_Central_Palm');me.from_pydata(verts,[],faces)
     for mat in source.materials:me.materials.append(mat)
     for p,slot in zip(me.polygons,slots):p.material_index=slot;p.use_smooth=True
     for uv in source.uv_layers:
      target=me.uv_layers.new(name=uv.name)
      for p in source.polygons:
       for li in p.loop_indices:target.data[li].uv=uv.data[li].uv
      for new,old in zip(list(me.polygons)[len(source.polygons):],crown):
       for li,oi in zip(new.loop_indices,old.loop_indices):target.data[li].uv=uv.data[oi].uv
   if me:
    o.data=me
    dims=[max(v.co[k] for v in me.vertices)-min(v.co[k] for v in me.vertices) for k in range(3)]
    scale=7./max(dims[:2]);o.scale=(scale,scale,scale)
    o['zc_v18_photo']='Annotated01 central date-palm crown; 7m spread/5.5m height estimated, V13 CC0 source retained'
    bpy.context.view_layer.update()
  low=min((o.matrix_world@Vector(v)).z for v in o.bound_box)
  o.location.z+=(base+.075-.04)-low
 dest=ROOT/'output/build_metadata/v18/forecourt_geometry.json';dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_text(json.dumps({'center':CENTER,'radius_m_estimated':RADIUS,'source_lawn_base':base,'flower_instances':count,'asset_variants':len(meshes),'source':'owner-marked01 + owner photo15; metric fit/species/motif estimated','source_lawn_cut':True,'road_geometry_covered':False},indent=2))
 print('[V18 photo forecourt]',count,'licensed flower instances on source-partitioned lawn')
