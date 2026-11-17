"""Nonintersecting estimated stall geometry within mapped parking envelopes.

The map supports parking aisles, not surveyed painted stall stations. No road
surface is added or covered here. Junctions and every shared drive aisle stay clear.
"""
import json,math
from pathlib import Path
from shapely import union_all
from shapely.geometry import LineString,Point,Polygon
from .v6_academic import polygon_prism

def emit_markings(mb,M,table):
    lines={name:LineString(spec['pts']) for name,spec in table.items() if len(spec['pts'])>1}
    parking={name:q for name,q in lines.items() if table[name].get('parking')}
    # A crossing aisle retains its full carriageway. Paint ends before it.
    accepted=[];rows=[];collisions=0;curves=0;clipped=0
    for name,line in parking.items():
        spec=table[name]
        own=line.buffer(8.45,cap_style='flat').difference(line.buffer(3.05))
        others=union_all([q.buffer(3.25 if table[n].get('parking') else (table[n]['half'] or 3.5)+.45)
                          for n,q in lines.items() if n!=name and q.distance(line)<15.])
        allowed=own.difference(others)
        count=0
        for k in range(int(max(0.,line.length-12.)/2.6)):
            d=6.+k*2.6;p=line.interpolate(d)
            pa=line.interpolate(max(0,d-3));pb=line.interpolate(min(line.length,d+3))
            pc=line.interpolate(max(0,d-.5));pd=line.interpolate(min(line.length,d+.5))
            a=math.atan2(p.y-pa.y,p.x-pa.x);b=math.atan2(pb.y-p.y,pb.x-p.x)
            if abs(math.atan2(math.sin(b-a),math.cos(b-a)))>.16:
                curves+=2;continue
            dx,dy=pd.x-pc.x,pd.y-pc.y;length=math.hypot(dx,dy)
            if length<1e-6:continue
            nx,ny=-dy/length,dx/length
            for side in (-1,1):
                stripe=LineString([(p.x+nx*side*3.12,p.y+ny*side*3.12),
                                   (p.x+nx*side*8.35,p.y+ny*side*8.35)]).buffer(.05,cap_style='flat')
                if not allowed.buffer(.005).covers(stripe):clipped+=1;continue
                if any(stripe.distance(q)<.18 for q in accepted):collisions+=1;continue
                accepted.append(stripe);count+=1
                polygon_prism(mb,M['marking'],stripe,.055,.075)
        rows.append({'source':name,'accepted_stall_dividers':count})
    out=Path(__file__).resolve().parents[2]/'output/build_metadata/v18/parking_geometry.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'evidence':'Dated parking aisle positions; paint stations ESTIMATED',
        'accepted':len(accepted),'crossing_candidates_rejected':collisions,'tight_curve_candidates_rejected':curves,
        'shared_aisle_or_boundary_candidates_rejected':clipped,'sources':rows,
        'road_surface_added':False,'minimum_between_stripes_m':.18},indent=1))
