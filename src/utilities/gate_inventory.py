"""Six owner-described entrances, grouped from dated OSM gate nodes.

Right/left face inward from the main gate: right is -X (SW), left +X (NE).
Side/rear architecture and exact operating openings are unverified.
"""
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/vendor'))
from shapely.geometry import LineString, Point
from . import survey as SV

GROUPS=[('G1','Main/front gate',[5225739523,5225739528]),
        ('G2','Rear gate',[5225739664,5225739665]),
        ('G3','Right-side gate A',[5225739797,8478493617]),
        ('G4','Right-side gate B',[5225739800,6424866649]),
        ('G5','Left-side gate A',[5225739729,8478493632]),
        ('G6','Left-side gate B',[5225739801,8478493550])]
NODES={g['id']:g for g in SV.OSM['gates']}
BOUNDARY=LineString(SV.PLOT)
RECORDS=[]
for i,(gid,label,ids) in enumerate(GROUPS):
    x=sum(NODES[n]['p'][0] for n in ids)/len(ids)
    y=sum(NODES[n]['p'][1] for n in ids)/len(ids)
    t=BOUNDARY.project(Point(x,y))
    q=BOUNDARY.interpolate(t)
    a,b=BOUNDARY.interpolate(max(0,t-1)),BOUNDARY.interpolate(min(BOUNDARY.length,t+1))
    angle=math.atan2(b.y-a.y,b.x-a.x)
    bx,by=(0.,SV.GATE_Y) if i==0 else (q.x,q.y)
    dx,dy=-bx,-220.-by
    length=math.hypot(dx,dy)
    inward=(dx/length,dy/length)
    row={'id':gid,'label':label,'osm_nodes':ids,'osm_position_blender_m':[round(x,3),round(y,3)],
         'model_position_blender_m':[round(bx,3),round(by,3)],'wall_angle_radians':angle,
         'boundary_projection_offset_m':round(math.hypot(bx-x,by-y),3),
         'inward':inward,'owner_gate_count':6,
         'status':'PHOTO_AND_MAP' if i==0 else 'PROVISIONAL_MAP_CLUSTER',
         'appearance':'C01/C02/D02/D03; V4 portal retained' if i==0 else 'generic labelled marker; NOT a surveyed gate design',
         'pedestrian_route':'V4 open pedestrian door' if i==0 else 'open estimated wall gap on walkable ground; not confirmed as an operational entrance',
         'unknowns':[] if i==0 else ['current gate existence/state','owner A/B identity','precise location','opening dimensions','architectural appearance','pedestrian/vehicle access class'],
         'spawn':'SPAWN_07_Main_Gate_Exterior' if i==0 else f'SPAWN_{i+7:02d}_Gate_{gid}',
         'object':'AB_Main_Gate_Complex' if i==0 else f'AB_Gate_{gid}_Provisional'}
    RECORDS.append(row)
    row['owner_v6_clarification']='Six boundary gates: main/rear opposite; one at each Academic side-road end; another near each upper parking area. Building entrances also exist and are a separate layer.'
    row['functional_context_hypothesis']={'G1':'main axis front','G2':'main axis rear (map centre offset ~6 m; not a surveyed correction)',
        'G3':'owner-right upper parking connection','G4':'owner-right Academic side-road terminus',
        'G5':'owner-left upper parking connection','G6':'owner-left Academic side-road terminus'}[gid]
    row['context_confidence']='Owner-confirmed topology; association of individual map clusters estimated.'
assert len(RECORDS)==6 and len({r['id'] for r in RECORDS})==6

def write():
    dst=ROOT/'references/six_gate_inventory.json'
    dst.write_text(json.dumps({'orientation':{'gate_axis_bearing_deg':323.46,'looking_inward_deg':143.46,
                     'owner_right_axis':'-X, bearing 233.46 SW','owner_left_axis':'+X, bearing 53.46 NE'},
                     'excluded_nearby_nodes':[8478493504,8478493505],
                     'note':'Two adjacent lane nodes form one entrance; six clusters are a map-based interpretation of the owner requirement, not confirmation of current architecture.',
                     'gates':RECORDS},indent=2),encoding='utf-8')

# Metadata must also be present when build_game_assets imports this module afresh.
# V11 (Codex review): the same V11 values the scene build writes, so a fresh asset export agrees.
from .v8_gates import configuration
from .v11_gates import v11_parameters
for r in RECORDS[1:]:
    r.update(appearance='V11 G1-family monumental portal (stone pylons, ledgestone inlay, numbered lintel, lattice leaves); ESTIMATED',
             pedestrian_route='Framed pedestrian bay with interactive sliding leaf (ESTIMATED)',
             parameters_v8=v11_parameters(configuration(r)),
             external_access='UNRESOLVED_SAND_GAP_25M' if r['id']=='G2' else 'UNVERIFIED_NO_EXTERNAL_EXTENSION')

def build_provisional(M,C):
    # V11 (owner 06): G1-family monumental gates replace the V8 subordinate assemblies.
    from .v11_gates import secondary
    return secondary(M,C)
