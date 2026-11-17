"""Native geometry checks for owner-corrected stairs, hollow glazing and fixtures.

These verify emitted form/contact, never photographic accuracy or a 95% score.
"""
from pathlib import Path
import sys,json,hashlib,math,bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(R/'tools/vendor'))
from utilities.v17_elevation import datum
from utilities import dormitory

def tree(objects,exclude_glass=False):
    vertices=[];faces=[]
    for o in objects:
        if o.type!='MESH' or o.hide_render:continue
        off=len(vertices);vertices.extend(o.matrix_world@v.co for v in o.data.vertices)
        for f in o.data.polygons:
            mat=o.data.materials[f.material_index] if o.data.materials else None
            # A curtain is an observed nonstructural infill behind a real
            # opening. Do not confuse that with the rejected solid stone mass.
            if exclude_glass and mat and any(q in mat.name for q in ('Glass','Curtain')):continue
            faces.append(tuple(off+i for i in f.vertices))
    return BVHTree.FromPolygons(vertices,faces)

checks=[]
def check(name,value,data=None):checks.append({'name':name,'pass':bool(value),'data':data})

for side,label in ((-1,'Left'),(1,'Right')):
    o=bpy.data.objects['Academic_Stair_'+label];bv=tree([o]);errors=[];heights=[]
    # Independent owner-corrected design expectation: 28 x 150mm with 480mm
    # treads and one 4m intermediate landing, not the rejected 34-riser stair.
    foot=-201.56;cursor=foot
    for i in range(28):
        if i==14:cursor-=4.
        for x in (side*12.,side*14.5):
            y=cursor-.24;expected=.21+(i+1)*.15+datum(0,-249)
            hit=bv.ray_cast(Vector((x,y,expected+.12)),Vector((0,0,-1)),.3)[0]
            if hit is None or abs(hit.z-expected)>.012:errors.append({'x':x,'y':y,'expected':expected,'hit':list(hit) if hit else None})
        heights.append(.21+(i+1)*.15);cursor-=.48
    check(label+' emitted tread contacts',not errors,{'samples':56,'failures':errors})
    check(label+' source/native physical specification',o.get('zc_risers')==28 and abs(o.get('zc_riser_height_m',0)-.15)<1e-5 and abs(o.get('zc_width_m',0)-10.5)<.001)

root=bpy.data.objects['AB_Academic_Building'];bv=tree([root],True)
dz=root.get('zc_v17_pad_datum_m',0.)
for x in (-8.,0.,8.):
    a=Vector((x,-244.,11.+dz));b=Vector((x,-248.,11.+dz))
    check('Upper facade has actual interior depth x='+str(x),bv.ray_cast(a,(b-a).normalized(),(b-a).length)[0] is None)

root=bpy.data.objects['AB_East_Residential_Pair_Estimated'];bv=tree([root,*root.children_recursive],True)
world_bounds=[root.matrix_world@Vector(p) for p in root.bound_box]
cx=(min(p.x for p in world_bounds)+max(p.x for p in world_bounds))/2
cy=(min(p.y for p in world_bounds)+max(p.y for p in world_bounds))/2
check('Housing floor pad is seated at its actual campus coordinates',abs(root.get('zc_v17_pad_datum_m',100)-datum(cx,cy))<.001,{'expected_pad_m':datum(cx,cy),'actual_pad_m':root.get('zc_v17_pad_datum_m'),'xy':[cx,cy]})
from utilities.geometry import poly_edges
from shapely.geometry import LineString,Point
samples=[]
for index,poly in enumerate(dormitory.OUTLINES):
    source=dormitory.SV.EAST_PAIR[index][:-1];cut=11 if index else 10
    caps=[LineString((source[0],source[-1])),LineString((source[cut-1],source[cut]))]
    for e in poly_edges(poly):
        n=max(1,int(e.L/3.3));spacing=e.L/n;p=e.at(e.L/2)
        if spacing<2.35 or any(q.distance(Point(p.x,p.y))<.2 for q in caps):continue
        s=(n//2+.5)*spacing;p=e.at(s);z=1.6+root.get('zc_v17_pad_datum_m',0.)
        # The four photographed stair cores supersede the regular room-window
        # grid. Their solid pier/door surrounds are not room-window apertures.
        if min(math.dist((p.x,p.y),q) for q in ((315.,-416.),(395.,-427.),(365.,-636.),(420.,-630.)))<5.:continue
        a=Vector((p.x+e.n.x*.75,p.y+e.n.y*.75,z));b=Vector((p.x-e.n.x*.025,p.y-e.n.y*.025,z))
        h=bv.ray_cast(a,(b-a).normalized(),(b-a).length)[0]
        samples.append({'index':index,'xy':list(p),'clear':h is None,'hit':list(h) if h is not None else None,'normal_xy':list(e.n)})
        if len(samples)>=30:break
    if len(samples)>=30:break
check('Housing windows are structural openings (glazing/curtains excluded)',len(samples)>=15 and all(r['clear'] for r in samples),samples)

lights=[o for o in bpy.data.objects if o.type=='LIGHT' and o.name.startswith('V7_V18_Academic_')]
check('Permanent interior fixtures are bounded downward spots, off in daylight',len(lights)>=20 and all(o.data.type=='SPOT' and o.data.energy==0 and o.parent for o in lights),len(lights))
ground=tree([o for o in bpy.data.objects if o.name in ('Lawns','Flower_Beds','Ground_Campus_Plot','Plaza_Paving')])
downward=[f.index for f in bpy.data.objects['Lawns'].data.polygons if f.normal.z<-.1]
check('Lawn remainder and flower-bed top faces point upwards',not downward,{'downward_faces':downward[:20],'count':len(downward)})
flowers=[]
for o in bpy.data.objects:
    if not o.name.startswith('V18_Admin_Flower_') or o.type!='MESH':continue
    p=o.matrix_world.translation;hit=ground.ray_cast(p+Vector((0,0,1.)),Vector((0,0,-1)),2.)[0]
    gap=p.z-hit.z if hit is not None else None
    flowers.append({'object':o.name,'gap_m':gap,'pass':gap is not None and -.04<=gap<=.03})
check('All licensed flower instances contact actual native planting ground',len(flowers)>500 and all(q['pass'] for q in flowers),{'count':len(flowers),'failures':[q for q in flowers if not q['pass']]})
report={'native_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'checks':checks,'all_pass':all(r['pass'] for r in checks),'accuracy_note':'Physical/source verification only. All metric architectural estimates remain subject to photographic and owner review.'}
p=R/'output/build_metadata/v18/architecture_geometry_audit.json';p.write_text(json.dumps(report,indent=1))
print('[V18 native architecture]',sum(r['pass'] for r in checks),'/',len(checks),'checks')
if not report['all_pass']:raise RuntimeError('Native architecture check failed; inspect report')
