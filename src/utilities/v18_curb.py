"""Exact kerb/profile subtraction: preserve uncovered portions of boundary faces.

The inherited any-vertex deletion removed whole triangles even when modular
units covered only a corner. This left visible holes beside otherwise solid
collision kerbs. Clip the original profile to the actual unit footprint instead.
No road, terrain or second covering surface is added.
"""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
from shapely import constrained_delaunay_triangles,union_all,make_valid
from shapely.geometry import Polygon,LineString,box,shape
from shapely.prepared import prep
ROOT=Path(__file__).resolve().parents[2]

def pieces(g,kind):
    if g.is_empty:return
    if g.geom_type==kind:yield g
    elif hasattr(g,'geoms'):
        for q in g.geoms:yield from pieces(q,kind)

def trim(obj,footprint):
    if footprint.is_empty:return 0
    fp=make_valid(footprint);ready=prep(fp);lo,bot,hi,top=fp.bounds
    me=obj.data;mw=obj.matrix_world;inv=mw.inverted()
    vertices=[v.co.copy() for v in me.vertices];faces=[];mats=[];changed=0;removed_area=0.;retained_split_area=0.
    def emit(coords,mi,normal):
        if len(coords)<3:return
        n=(coords[1]-coords[0]).cross(coords[2]-coords[0])
        if n.length<1e-12:return
        if n.dot(normal)<0:coords.reverse()
        start=len(vertices);vertices.extend(inv@v for v in coords)
        faces.append(tuple(range(start,start+len(coords))));mats.append(mi)
    for f in me.polygons:
        points=[mw@me.vertices[i].co for i in f.vertices]
        if max(v.x for v in points)<lo or min(v.x for v in points)>hi or max(v.y for v in points)<bot or min(v.y for v in points)>top:
            faces.append(tuple(f.vertices));mats.append(f.material_index);continue
        normal=mw.to_3x3()@f.normal
        xy=Polygon([(v.x,v.y) for v in points])
        if xy.area>1e-10 and abs(normal.z)>1e-7:
            xy=make_valid(xy)
            if not ready.intersects(xy):faces.append(tuple(f.vertices));mats.append(f.material_index);continue
            rest=xy.difference(fp);changed+=1
            removed_area+=max(0.,xy.area-rest.area)
            if not rest.is_empty:retained_split_area+=rest.area
            for p in pieces(rest,'Polygon'):
                for tri in pieces(constrained_delaunay_triangles(p),'Polygon'):
                    coords=[]
                    for x,y in list(tri.exterior.coords)[:-1]:
                        z=points[0].z-(normal.x*(x-points[0].x)+normal.y*(y-points[0].y))/normal.z
                        coords.append(Vector((x,y,z)))
                    emit(coords,f.material_index,normal)
        else:
            # Vertical faces have zero XY area. Parameterise their actual face
            # in (distance along XY edge,height), clip only covered intervals.
            a,b=max(((a,b) for a in points for b in points),key=lambda q:(Vector(q[0].xy)-Vector(q[1].xy)).length_squared)
            direction=Vector((b.x-a.x,b.y-a.y,0.));length=direction.length
            if length<1e-8:faces.append(tuple(f.vertices));mats.append(f.material_index);continue
            direction/=length;line=LineString([(a.x,a.y),(b.x,b.y)])
            if not ready.intersects(line):faces.append(tuple(f.vertices));mats.append(f.material_index);continue
            changed+=1;tz=make_valid(Polygon([((p-a).dot(direction),p.z) for p in points]))
            z0=min(p.z for p in points)-1;z1=max(p.z for p in points)+1
            for segment in pieces(line.difference(fp),'LineString'):
                ts=[(Vector((x,y,a.z))-a).dot(direction) for x,y in segment.coords]
                strip=tz.intersection(box(min(ts),z0,max(ts),z1))
                for p in pieces(strip,'Polygon'):
                    for tri in pieces(constrained_delaunay_triangles(p),'Polygon'):
                        emit([Vector((a.x+direction.x*t,a.y+direction.y*t,z)) for t,z in list(tri.exterior.coords)[:-1]],f.material_index,normal)
    result=bpy.data.meshes.new('Road_Curb_Exact_Unit_Cut');result.from_pydata(vertices,[],faces)
    for m in me.materials:result.materials.append(m)
    for f,mi in zip(result.polygons,mats):f.material_index=mi
    result.update();obj.data=result;obj['zc_v18_exact_curb_cut']=True
    uv=result.uv_layers.new(name='UVMap')
    for f in result.polygons:
        ax=max(range(3),key=lambda k:abs(f.normal[k]))
        for li in f.loop_indices:
            p=mw@result.vertices[result.loops[li].vertex_index].co
            uv.data[li].uv=((p.y/3,p.z/3) if ax==0 else (p.x/3,p.z/3) if ax==1 else (p.x/3,p.y/3))
    out=ROOT/'output/build_metadata/v18/curb_geometry_repair.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'changed_original_faces':changed,'removed_projected_area_m2':removed_area,'retained_partial_face_area_m2':retained_split_area,'method':'Exact planar/vertical-face difference against modular unit footprint. Uncovered face portions retained, no any-vertex deletion or road cover.','road_mesh_modified':False},indent=1))
    print('[V18 exact curb cut]',changed,'faces;',retained_split_area,'m2 of partial boundary faces retained',flush=True)
    return changed

def refresh_existing():
    obj=bpy.data.objects.get('Road_Curb_Edges')
    if obj is None or obj.get('zc_v18_exact_curb_cut'):return
    proxy=bpy.data.objects['Kerb_Box_Collision_Proxy']
    obj.data=proxy.data.copy();obj.data.transform(proxy.matrix_world);obj.matrix_world=Matrix.Identity(4)
    from .ground_system import profile_kerb
    doc=json.loads((ROOT/'output/build_metadata/v17/generated_network.geojson').read_text())
    road=union_all([shape(f['geometry']) for f in doc['features'] if f['properties']['surface'] in ('vehicle','external')])
    profile_kerb(obj,road)
    units=bpy.data.objects['Road_Curb_Precast_Units'];polys=[]
    for f in units.data.polygons:
        coords=[units.matrix_world@units.data.vertices[i].co for i in f.vertices]
        p=Polygon([(v.x,v.y) for v in coords])
        if p.area>1e-10:polys.append(make_valid(p))
    # Float32 sweeps contain coincident arris edges. A10micrometre overlay
    # precision grid resolves GEOS ring-edge ambiguity without mm-sized fills.
    trim(obj,union_all(polys,grid_size=.00001))
