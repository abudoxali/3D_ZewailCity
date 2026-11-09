"""V8 estimated secondary architecture and terrain-connected boundary masonry.

No secondary-gate photograph is available. Node spacing constrains the assembly
envelope, NOT a surveyed opening or lane count. All parameters remain editable.
Only short INTERNAL missing links are filled. G2's external sand gap is retained.
"""
import json
import math
from pathlib import Path
import bpy
from shapely import union_all
from shapely.geometry import Point, Polygon, LineString, box
from . import survey as SV
from .architecture import Parts
from .geometry import MeshBuilder

ROOT=Path(__file__).resolve().parents[2]


def configuration(r):
    from .gate_inventory import NODES
    a,b=[NODES[n]['p'] for n in r['osm_nodes']]
    spacing=math.dist(a,b)
    # These are independent parameters, with per-ID overrides in this module.
    return dict(opening_width=spacing+1.2, orientation=r['wall_angle_radians'],
                support_width=.65,support_depth=.95,support_height=3.55,
                frame_height=3.15,frame_depth=.32,pedestrian_width=1.7,
                leaf_height=2.65,leaf_parking='sliding_flanks',wall_height=3.5,threshold_offset=.06,
                threshold_depth=6.,wall_connection_half=10.,node_spacing=spacing)


def axes(r,c):
    a=c['orientation'];u=(math.cos(a),math.sin(a));v=(-u[1],u[0])
    if sum(v[i]*r['inward'][i] for i in (0,1))<0:v=(-v[0],-v[1])
    return u,v


def xy(r,u,v,s,t):
    x,y=r['model_position_blender_m']
    return x+s*u[0]+t*v[0],y+s*u[1]+t*v[1]


def threshold_polygon(r,c):
    u,v=axes(r,c);w=c['opening_width']/2;d=c['threshold_depth']/2
    return Polygon([xy(r,u,v,s,t) for s,t in [(-w,-d),(w,-d),(w,d),(-w,d)]])


def threshold_core(r,c):
    """Full-width strip 1.2 m either side of the wall line: the opening itself."""
    u,v=axes(r,c);w=c['opening_width']/2
    return Polygon([xy(r,u,v,s,t) for s,t in [(-w,-1.2),(w,-1.2),(w,1.2),(-w,1.2)]])


def ground_regions(road):
    """A disjoint replacement surface goes through ground_system's union pass."""
    from .gate_inventory import RECORDS
    from .ground_system import datum
    from shapely.ops import nearest_points
    plot=Polygon(SV.PLOT)
    regions=[];details=[]
    for r in RECORDS[1:]:
        c=configuration(r);p=Point(r['model_position_blender_m'])
        threshold=threshold_polygon(r,c)
        # Limit nearest search to mapped road surface inside the perimeter.
        internal=road.intersection(plot.buffer(-.25))
        q=nearest_points(p,internal)[1]
        distance=p.distance(q);link=Polygon()
        if .1<distance<=12.:
            link=LineString([p,q]).buffer(2.6,cap_style='square').intersection(plot)
        # V9: no abrupt rectangular slab. Close (fillet, r 2.4 m) the concave
        # junction where the apron meets the internal link/road, then open (round,
        # r 0.9 m) the outer corners. The clear opening at the wall line is kept.
        shaped=threshold.union(link).buffer(2.4,quad_segs=6).buffer(-2.4,quad_segs=6)
        shaped=shaped.buffer(-.9,quad_segs=4).buffer(.9,quad_segs=4)
        shaped=shaped.union(threshold_core(r,c))
        regions.append(shaped)
        details.append({'id':r['id'],'parameters':c,'position':r['model_position_blender_m'],
                        'threshold_elevation_m':datum(p.x,p.y)+c['threshold_offset'],
                        'internal_surface_gap_m':round(distance,3),'internal_connector_m2':round(link.area,3),'v9_apron_m2':round(regions[-1].area,3) if regions else None,
                        'external_connection':'UNRESOLVED: mapped branches end ~25 m before external road; no extension' if r['id']=='G2' else 'No external connector invented',
                        'evidence':'PROVISIONAL_MAP_CLUSTER; architectural dimensions and open state estimated'})
    out=ROOT/'output/validation/v11';out.mkdir(parents=True,exist_ok=True)
    (out/'gate_ground.json').write_text(json.dumps(details,indent=2))
    return union_all(regions)


def graded_prism(mb,mat,a,b,width,z0,z1):
    """A watertight masonry run whose lower and upper edges follow the datum."""
    from .ground_system import datum
    dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy)
    if L<.001:return
    nx,ny=-dy/L*width/2,dx/L*width/2
    corners=[(a[0]+nx,a[1]+ny),(a[0]-nx,a[1]-ny),
             (b[0]-nx,b[1]-ny),(b[0]+nx,b[1]+ny)]
    vertices=[(x,y,datum(x,y)+h) for h in (z0,z1) for x,y in corners]
    mb.raw(mat,vertices,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])


def perimeter(M,C,gap_half):
    from .gate_inventory import RECORDS
    mb=MeshBuilder();n=0;burial=[]
    from .v11_gates import wing_half
    # V11: each secondary-gate cut matches its G1-family wing length (wing walls meet the cut).
    g1box=box(-gap_half,SV.GATE_Y-20,gap_half,SV.GATE_Y+30)
    openings=union_all([Point(r['model_position_blender_m']).buffer(wing_half(configuration(r))-.05) for r in RECORDS[1:]]+[g1box])
    pieces=[]
    for a,b in zip(SV.PLOT,SV.PLOT[1:]+[SV.PLOT[0]]):
        cut=LineString([a,b]).difference(openings)
        pieces.extend([g for g in ([cut] if cut.geom_type=='LineString' else getattr(cut,'geoms',[])) if g.geom_type=='LineString' and g.length>=.1])
    # V11 (owner 04): the G1 complex frontage ends at x = +-62 (lattice portal, GY+2..2.8),
    # but the stepped 2017 plot line leaves the G1 cut box elsewhere, leaving open sand
    # beside the gate. Join each complex end to the nearest wall end on the cut box.
    ends=[]
    for g in pieces:
        for p in (g.coords[0],g.coords[-1]):
            if g1box.exterior.distance(Point(p))<.05:ends.append(p)
    connectors=[]
    for sx in (-1,1):
        start=(sx*61.7,SV.GATE_Y+2.4)
        side=[p for p in ends if p[0]*sx>0]
        if side:
            q=min(side,key=lambda p:math.dist(p,start))
            if math.dist(q,start)>.3:
                connectors.append(LineString([start,q]))
    for line in pieces+connectors:
        if True:
            count=max(1,math.ceil(line.length/3.))
            for i in range(count):
                aa,bb=line.interpolate(i/count,normalized=True),line.interpolate((i+1)/count,normalized=True)
                pa,pb=(aa.x,aa.y),(bb.x,bb.y)
                # C02 frontage ~6 m. Other walls remain the prior 3.5 m estimate.
                h=6. if (aa.y+bb.y)/2>SV.GATE_Y-25 else 3.5
                graded_prism(mb,M['curb'],pa,pb,.9,-.45,.10)
                graded_prism(mb,M['stucco'],pa,pb,.42,-.12,h)
                graded_prism(mb,M['gate_stone'],pa,pb,.58,h,h+.16)
                if i%2==0:
                    t=math.atan2(pb[1]-pa[1],pb[0]-pa[0]);ux,uy=math.cos(t)*.32,math.sin(t)*.32
                    graded_prism(mb,M['stucco'],(aa.x-ux,aa.y-uy),(aa.x+ux,aa.y+uy),.7,-.18,h+.2)
                n+=1
    obj=mb.to_object('Perimeter_Wall',C['gate']);obj['zc_terrain_following_v8']=True
    obj['zc_wall_segments']=n
    obj['zc_v11_g1_connectors']=json.dumps([[list(map(lambda v:round(v,2),c_.coords[0])),list(map(lambda v:round(v,2),c_.coords[-1]))] for c_ in connectors])
    obj['zc_evidence']='OSM boundary; C02 frontage 6 m estimate; other walls 3.5 m estimate; 450 mm embedded footings, no DEM.'
    return obj


def build(M,C):
    from .gate_inventory import RECORDS,write
    from .ground_system import datum
    for r in RECORDS[1:]:
        c=configuration(r);u,v=axes(r,c);w=c['opening_width']/2
        P=Parts(r['object'],M);base=datum(*r['model_position_blender_m'])+c['threshold_offset']
        def block(mb,mat,s,t,z,width,depth,height):
            x,y=xy(r,u,v,s,t)
            mb.obox(mat,(x,y,base+z+height/2),(width,depth,height),c['orientation'])
        # Three masonry supports, a smaller pedestrian lintel, recessed cap/plinth.
        divider=w-c['pedestrian_width']-.35
        for s in (-w-.325,divider,w+.325):
            x,y=xy(r,u,v,s,0)
            bottom=datum(x,y)-.40
            block(P.shell,M['curb'],s,0,bottom-base,1.1,1.3,base+.16-bottom)
            block(P.shell,M['gate_stone'],s,0,-.08,c['support_width'],c['support_depth'],c['support_height']+.08)
            # V9 (restrained, ESTIMATED): projecting 0.55 m plinth course and a thin
            # stone cap slab over the dark band, echoing the G1 stone family.
            block(P.shell,M['gate_stone'],s,0,-.08,c['support_width']+.12,c['support_depth']+.12,.63)
            block(P.det,M['band'],s,0,c['support_height'],.8,1.08,.13)
            block(P.det,M['gate_stone'],s,0,c['support_height']+.13,.9,1.18,.07)
        # Header only above the pedestrian opening, no monumental vehicle portal.
        block(P.shell,M['gate_stone'],(divider+w)/2,0,c['frame_height'],w-divider+.65,c['frame_depth'],.35)
        # Masonry wings meet the perimeter cut ends; footings follow actual grade.
        for sign in (-1,1):
            a=xy(r,u,v,sign*(w+.65),0);b=xy(r,u,v,sign*c['wall_connection_half'],0)
            graded_prism(P.shell,M['curb'],a,b,.9,-.45,.10)
            graded_prism(P.shell,M['stucco'],a,b,.42,-.12,c['wall_height'])
            graded_prism(P.det,M['gate_stone'],a,b,.58,c['wall_height'],c['wall_height']+.16)
        # Park open sliding leaves along the flank walls, outside the clear
        # opening. Inward-swinging panels obstructed G3's original diagonal spawn
        # approach despite the perpendicular crossing being clear.
        length=(divider-.5-(-w+.10))/2
        for sign in (-1,1):
            center=sign*(w+.8+length/2);t=-.36
            for z in (.15,c['leaf_height']):
                block(P.det,M['steel_dark'],center,t,z,length,.12,.12)
            for s in (center-length/2,center+length/2):
                block(P.det,M['steel_dark'],s,t,.15,.14,.14,c['leaf_height'])
            count=max(2,int(length/.18))
            for j in range(1,count):
                s=center-length/2+j*length/count
                block(P.det,M['steel_dark'],s,t,.25,.035,.035,c['leaf_height']-.15)
            block(P.det,M['steel_dark'],center,t,1.45,length,.10,.08)
            for s in (center-length*.35,center+length*.35):
                block(P.det,M['steel_dark'],s,t,.03,.12,.16,.12)
        # V9: flush steel ground track for the sliding leaves across the vehicle
        # opening (top 4 mm above the threshold; walkable, no step).
        block(P.det,M['steel_dark'],(divider-w)/2,-.36,-.012,divider+w,.07,.016)
        # Pedestrian leaf parked parallel to the return, leaving 1.7 m clear.
        for z in (.15,2.55):block(P.det,M['steel_dark'],w-.08,.8,z,.10,1.6,.10)
        for j in range(9):block(P.det,M['steel_dark'],w-.08,j*.2,.15,.035,.035,2.5)
        obj=P.finish(C,'provisional_gates',bevel=.015)
        obj['zc_evidence']=r['status'];obj['zc_parameters_v8']=json.dumps(c)
        obj['zc_note']='Estimated subordinate masonry/steel assembly; parked-open leaves are an explorer interpretation, not proof of public access.'
        r.update(appearance='V8 parametric subordinate masonry/steel assembly; architecture ESTIMATED, no secondary photos',
                 pedestrian_route='Local open threshold and pedestrian bay, provisional; no external public access claimed',
                 parameters_v8=c,external_access='UNRESOLVED_SAND_GAP_25M' if r['id']=='G2' else 'UNVERIFIED_NO_EXTERNAL_EXTENSION')
    write()
