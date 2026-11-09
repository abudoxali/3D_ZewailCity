"""Validate the actual game blend, exported source provenance, UVs and PBR files."""
import json,hashlib,math
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'output/game_ready/campus_manifest.json').read_text(encoding='utf-8'))
checks=[]
def check(name,ok,detail):
    checks.append({'name':name,'pass':bool(ok),'detail':detail})
source=ROOT/manifest['source_blend']
check('source blend hash matches exported scene',hashlib.sha256(source.read_bytes()).hexdigest()==manifest['source_blend_sha256'],str(source))
drift=[p for p,h in manifest['generator_sha256'].items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
check('procedural generators match exported asset provenance',not drift,drift)
meshes=[o for o in bpy.data.objects if o.type=='MESH' and not o.name.endswith('-colonly')]
bad_uv=[o.name for o in meshes if len(o.data.polygons) and (not o.data.uv_layers or len(o.data.uv_layers.active.data)!=len(o.data.loops))]
bad_materials=[o.name for o in meshes if not o.data.materials or any(m is None for m in o.data.materials)]
bad_scale=[o.name for o in meshes if any(abs(v-1)>1e-5 for v in o.scale) and not o.name.startswith(('VEG_','PROP_'))]
bad_normals=[o.name for o in meshes if any(not all(math.isfinite(c) for c in p.normal) or p.normal.length<.99 for p in o.data.polygons if p.area>1e-8)]
check('all game render meshes have complete UV layers',not bad_uv,bad_uv)
check('all game render meshes have materials',not bad_materials,bad_materials)
check('structural meshes retain metre scale',not bad_scale,bad_scale)
check('nondegenerate faces have finite unit normals',not bad_normals,bad_normals)
acad=bpy.data.objects['BLD_Academic']
from mathutils import Vector
ys=[(acad.matrix_world@Vector(p)).y for p in acad.bound_box]
check('Academic render bounds stay in the surveyed Academic precinct',min(ys)>-350 and max(ys)<-165,[min(ys),max(ys)])
missing=[i.filepath for i in bpy.data.images if i.source=='FILE' and i.filepath and not Path(bpy.path.abspath(i.filepath)).exists()]
check('all baked PBR resources resolve',not missing,missing)
check('six gates retain evidence labels',len(manifest['gates'])==6 and all(g['status']=='PROVISIONAL_MAP_CLUSTER' for g in manifest['gates'][1:]),[(g['id'],g['status']) for g in manifest['gates']])
check('fourteen spawn records',len(manifest['spawn_points'])==14,len(manifest['spawn_points']))
# V11: Academic entrances live in their own registry (A/C/F + unnamed), separate from G1-G6.
_ae=manifest.get('academic_entrances_v11',{}).get('entrances',[])
check('V11 Academic entrance registry separate from the six boundary gates',
      'NOT' not in str(manifest.get('academic_entrances_v11',{}).get('classification','')) and len(_ae)>=6
      and {'A','C','F'}<={e['id'] for e in _ae} and all(not e['id'].startswith('G') for e in _ae)
      and all(e['label']==False for e in _ae if '?' in e['id'] or e['id']=='HALL'),[(e['id'],e['name']) for e in _ae])
check('V11 vehicle AND pedestrian interactive leaves for G1-G6',
      {g: {l['leaf'] for l in manifest.get('gate_leaves',[]) if l['gate']==g} for g in ('G1','G2','G3','G4','G5','G6')} ==
      {'G1': {'E','W','PedE','PedW'}, **{g: {'A','B','Ped'} for g in ('G2','G3','G4','G5','G6')}},
      [(l['gate'],l['leaf'],l['start_closed']) for l in manifest.get('gate_leaves',[])])
lights=manifest.get('evening_lights',[])
kinds={}
for l in lights:kinds[l.get('kind')]=kinds.get(l.get('kind'),0)+1
check('V7 evening lights explicit, kind-labelled and range-bounded (32 garden bollards)',
      kinds.get('bollard')==32 and all(l.get('kind') and 0<l['range_m']<=20 for l in lights) and len(lights)<=200,kinds)
col=bpy.data.objects.get('COL_Ground-colonly')
check('V7 ground collision simplified (surface-guarded) and smaller than its render source',
      bool(col) and col.get('zc_tris_before_simplify',0)>sum(len(p.vertices)-2 for p in col.data.polygons),
      {'before':col.get('zc_tris_before_simplify') if col else None,'after':sum(len(p.vertices)-2 for p in col.data.polygons) if col else None})
copy=ROOT/'game/godot/assets/campus'
check('Godot GLB and manifest copies exactly match exports',all((copy/f).read_bytes()==(ROOT/'output/game_ready'/f).read_bytes() for f in ('campus_full.glb','campus_manifest.json')),str(copy))
report={'checks':checks,'all_pass':all(c['pass'] for c in checks)}
(ROOT/'output/validation/v11/game_asset_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
for c in checks:
    print('[asset-check]', 'PASS' if c['pass'] else 'FAIL',c['name'],str(c['detail'])[:250])
if not report['all_pass']:
    raise RuntimeError('V5 asset checks failed')
