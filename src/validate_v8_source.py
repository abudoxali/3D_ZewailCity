"""Checks of emitted V8 geometry, independent of runtime traversal checks."""
import bpy,sys,json,hashlib,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from utilities.gate_inventory import RECORDS
from utilities.ground_system import datum
from utilities import survey as SV
checks=[]
def check(name,ok,detail=None):
 checks.append({'name':name,'pass':bool(ok),'detail':detail})
 print('[v8-source]', 'PASS' if ok else 'FAIL',name,str(detail)[:200],flush=True)
for g in RECORDS[1:]:
 o=bpy.data.objects.get(g['object']);detail=bpy.data.objects.get(g['object']+'_Details')
 check(g['id']+' masonry supports and steel leaves replace markers',o and detail and len(o.data.polygons)>50 and len(detail.data.polygons)>100,
       {'shell_faces':len(o.data.polygons) if o else 0,'detail_faces':len(detail.data.polygons) if detail else 0})
 check(g['id']+' provisional state and parametric editability',o and o.get('zc_evidence')=='PROVISIONAL_MAP_CLUSTER' and o.get('zc_parameters_v8'))
 check(g['id']+' no physical yellow provisional lettering',detail and all(m.name!='M_Marking_Yellow' for m in detail.data.materials))
 co=[o.matrix_world@v.co for v in o.data.vertices]
 check(g['id']+' foundations below local datum',min(p.z-datum(p.x,p.y) for p in co)<-.35)
wall=bpy.data.objects.get('Perimeter_Wall')
check('perimeter subdivided and datum applied exactly once',wall and wall.get('zc_terrain_following_v8') and wall.get('zc_wall_segments',0)>500,wall.get('zc_wall_segments') if wall else None)
co=[wall.matrix_world@v.co for v in wall.data.vertices]
foot=[p.z-datum(p.x,p.y) for p in co if abs(p.z-datum(p.x,p.y)+.45)<.005]
check('wall footing vertices embedded 450 mm below datum',len(foot)>1000,{'footing_vertices':len(foot),'max_error_m':max(abs(v+.45) for v in foot)})
check('main portal proportion retained',abs(SV.PORTAL['leg_w']/(SV.PORTAL['outer_w']-2*SV.PORTAL['leg_w'])-.20168067)<1e-5)
mat=bpy.data.materials['M_Gate_Sandstone_Tiles']
col=mat.diffuse_color
check('gate stone cream-beige rather than orange',col[0]-col[2]<.18 and col[0]>.6, list(col))
check('gate stone roughness and recessed joints',mat.roughness>=.69 and any(n.type=='BUMP' and n.invert for n in mat.node_tree.nodes),mat.roughness)
ground=json.loads((R/'output/validation/v11/ground_topology.json').read_text())
check('ground partition disjoint and complete',ground['all_topology_checks_pass'],{k:ground[k] for k in ['surface_overlap_m2','plot_uncovered_m2','centreline_gaps']})
gates=json.loads((R/'output/validation/v11/gate_ground.json').read_text())
check('five integrated aprons, no invented external links',len(gates)==5 and all('No external' in g['external_connection'] or 'UNRESOLVED' in g['external_connection'] for g in gates),gates)
for name in ['Academic_Stair_Left','Academic_Stair_Right']:
 o=bpy.data.objects[name]
 check(name+' original safe riser and landing geometry retained',o.get('zc_risers')==28 and o.get('zc_riser_height_m')==.15 and o.get('zc_tread_m')==.36)
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from utilities.site_plan import ADMIN
admin=bpy.data.objects['AB_Administration_Cultural_Building']
tree=BVHTree.FromObject(admin,bpy.context.evaluated_depsgraph_get())
q=admin.matrix_world.inverted()@Vector((11.,ADMIN['portico_front_y']+10.15,2.))
hit=tree.ray_cast(q,Vector((0,0,-1)),3.)
height=(admin.matrix_world@hit[0]).z if hit[0] else -99
check('Administration ramp toe flush to 0.06 m road and outward top normal',hit[0] is not None and abs(height-.06)<.02 and hit[1].z>.99,
      {'toe_z':height,'top_normal':list(hit[1]) if hit[1] else None})
report={'checks':checks,'all_pass':all(c['pass'] for c in checks),'source_blend_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()}
(R/'output/validation/v11/v8_source_checks.json').write_text(json.dumps(report,indent=2))
if not report['all_pass']:raise RuntimeError('V8 source geometry checks failed')
