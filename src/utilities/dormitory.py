"""P04/P06/P10/P11/P16 housing design on an UNVERIFIED geographic candidate.
OSM five-storey pair retained. Inner curve interpolation, dimensions, core/garden
positions and lighting are photo-supported estimates, not a geolocation proof.
"""
import math,json
from pathlib import Path
import bpy
from mathutils import Vector
from shapely.geometry import Polygon,Point,LineString
from shapely import union_all
from . import survey as SV
from .geometry import MeshBuilder,instance,get_collection,ccw,smooth_polyline,parent_keep

CENTER=(390.,-603.)
INGRESS=(425.,-555.)

def photo_outline(fp,index):
    p=fp[:-1] if fp[0]==fp[-1] else fp[:]
    count=11 if index else 10
    return ccw([tuple(v) for v in smooth_polyline(p[:count],2)]+p[count:])

OUTLINES=[photo_outline(fp,i) for i,fp in enumerate(SV.EAST_PAIR)]
SHELL=union_all([Polygon(p).buffer(0) for p in OUTLINES])
# V10 (P16, owner photo): lawn compartments and hedges run up to the building
# inside the courtyard; V9's 43 m circle left a large bare-soil wedge between the
# garden and the north (ingress) wing. The garden now fills the courtyard's convex
# enclosure (within 56 m of the centre). Extent ESTIMATED; identity UNVERIFIED.
GARDEN=Point(CENTER).buffer(56.,quad_segs=48).intersection(Polygon(OUTLINES[1]).convex_hull).union(
    Point(CENTER).buffer(43.,quad_segs=48)).difference(SHELL.buffer(1.2))
def curve(points):return [tuple(v) for v in smooth_polyline(points,3)]
BRANCHES=[
 [INGRESS,(425.,-568.),(410.,-584.),(401.,-601.),(384.,-619.),(370.,-631.)],
 [(410.,-584.),(396.,-589.),(380.,-605.),(366.,-617.),(364.,-629.)],
 [(410.,-584.),(426.,-594.),(424.,-612.),(413.,-629.)],
 [(366.,-617.),(381.,-621.),(398.,-623.),(413.,-629.)],
 [(439.,-579.),(433.,-602.),(420.,-621.),(398.,-631.),(366.,-630.),(347.,-618.),(340.,-602.),(349.,-586.),(369.,-581.),(396.,-581.),(410.,-584.)],
 [(425.,-568.),(439.,-579.)],
]
LINES=[LineString(curve(p)) for p in BRANCHES]
PATH=union_all([line.buffer(2.0 if i in [0,4] else 1.55,cap_style='round',join_style='round') for i,line in enumerate(LINES)]).difference(SHELL)
PLANTED=GARDEN.difference(PATH.buffer(.72))
HEDGE=PLANTED.difference(PLANTED.buffer(-.42))
# V7 (P11): the 0.72 m strip between paver path and planting is a loose-stone
# border, not exposed graded soil as V6 left it.
PEBBLE=GARDEN.intersection(PATH.buffer(.72)).difference(PATH)
# V7 (P16/P04/official image): continuous low clipped shrub rows inside the hedge,
# 0.9 m wide, rather than isolated balls. Plan and width ESTIMATED.
SHRUB_ROW=PLANTED.intersection(PATH.buffer(.72+.42+.25+.9)).difference(PATH.buffer(.72+.42+.25)).buffer(-.02)
LIGHT_POINTS=[]
for line in LINES[:5]:
    for d in range(4,int(line.length)-2,9):
        p=line.interpolate(d);q=line.interpolate(min(d+.1,line.length))
        dx,dy=q.x-p.x,q.y-p.y;n=math.hypot(dx,dy)
        if n<1e-6:continue
        for side in [-1,1]:
            x,y=p.x-side*dy/n*2.6,p.y+side*dx/n*2.6
            if GARDEN.covers(Point(x,y)) and not PATH.buffer(.25).covers(Point(x,y)):
                LIGHT_POINTS.append((round(x,3),round(y,3),.9))
LIGHT_POINTS=LIGHT_POINTS[::2][:32]

CURTAINS=('res_curtain_a','res_curtain_b','res_curtain_c')

def window(P,M,e,s,z,w=2.1,h=1.4,lit=False,seed=0):
    # V7 (P16 zoom): two-pane aluminium sliding window, light frame, sky-reflective
    # pane; interior curtains drawn to varied heights (occupied housing, not a pattern).
    P.glass.fbox(M['res_lit'] if lit else M['res_glass'],e,s,.07,.08,w,z,z+h)
    k=(seed*2654435761)%997
    if k%3:
        drop=.25+.65*((k//3)%7)/6.
        cw=w*(.5 if k%5<2 else .96)
        cs=s+(w-cw)/2*(1 if k%2 else -1)
        P.det.fbox(M[CURTAINS[k%3]],e,cs,.17,.02,cw-.06,z+h*(1-drop),z+h-.03)
    for a in [-w/2,w/2]:P.det.fbox(M['metal_light'],e,s+a,.1,.12,.06,z-.06,z+h+.06)
    for zz in [z-.06,z+h]:P.det.fbox(M['metal_light'],e,s,.08,.14,w+.12,zz,zz+.06)
    P.det.fbox(M['metal'],e,s,.16,.035,.035,z,z+h)
    P.det.fbox(M['res_stone'],e,s,.02,.22,w+.24,z-.16,z-.06)

# V7: six storeys (ground + 5). Owner photo P16 and the official Zewail City dorms
# image (zewailcity.edu.eg/dorms, 2026-11-07) both show six window rows on the curved
# courtyard building. OSM tags the candidate footprint building:levels=5; that
# conflict is retained in the register (candidate identity remains UNVERIFIED).
STOREY_Z=[5.1,8.5,11.9,15.3,18.7]
ROOF_Z=21.4
CORE_TOP=25.0

# V10 (P16, P10): windows are punched into the cream stone, not applied on top of it.
# A SKIN-deep stone layer of piers and spandrels now stands proud of the block, so
# every pane sits SKIN behind the facade plane with real reveals and shadow. This
# also replaces V9's eight-box window assembly (jambs, rails, sill, frames: ~96
# tris/window, 299k tris total) by four parts. Depth/pitch ESTIMATED.
SKIN=.2
CORE_EDGES=[]
ROWS=[(1.15,2.2,2.4)]+[(z,1.4,2.1) for z in STOREY_Z]      # (sill z, height, max width)

def window_v10(P,M,e,s,z,w,h,lit=False,seed=0):
    P.det.fbox(M['metal_light'],e,s,.01,.03,w+.1,z-.05,z+h+.05)           # aluminium frame rim
    P.glass.fbox(M['res_lit'] if lit else M['res_glass'],e,s,.03,.03,w,z,z+h)
    k=(seed*2654435761)%997
    if k%3:
        drop=.25+.65*((k//3)%7)/6.
        cw=w*(.5 if k%5<2 else .96)
        cs=s+(w-cw)/2*(1 if k%2 else -1)
        P.det.fbox(M[CURTAINS[k%3]],e,cs,.065,.015,cw-.06,z+h*(1-drop),z+h-.03)
    P.det.fbox(M['res_stone'],e,s,SKIN,.05,w+.2,z-.12,z-.02)                # projecting sill

def skin_edge(P,M,e,slots):
    """Stone skin of edge e with window openings slots=[(s,w)] in every row."""
    st=M['res_stone']
    tops=[.21]+[z+h for z,h,_ in ROWS]
    bottoms=[z for z,_,_ in ROWS]+[ROOF_Z]
    if not slots:
        P.det.fbox(st,e,e.L/2,0,SKIN,e.L+.02,.21,ROOF_Z);return
    for z0,z1 in zip(tops,bottoms):                                         # spandrels
        if z1-z0>.02:P.det.fbox(st,e,e.L/2,0,SKIN,e.L+.02,z0,z1)
    for (z,h,_) in ROWS:                                                    # piers per row
        edges=[0.]
        for s_,w in slots:edges+= [s_-w/2,s_+w/2]
        edges.append(e.L+.01)
        for a,b in zip(edges[::2],edges[1::2]):
            if b-a>.02:P.det.fbox(st,e,(a+b)/2,0,SKIN,b-a,z,z+h)

def build_pair(M,C):
    from .architecture import Parts
    CORE_EDGES.clear()
    P=Parts('AB_East_Residential_Pair_Estimated',M)
    for index,poly in enumerate(OUTLINES):
        edges=P.block(poly,.21,ROOF_Z,M['res_stone'])
        P.parapet(poly,ROOF_Z,h=.65,t=.30,band=False)
        centre=CENTER if index else (350.,-460.)
        for j,e in enumerate(edges):
            # V7: P16 window pitch ~3.3 m (V6 3.8 m).
            n=max(1,int(e.L/3.3));spacing=e.L/n
            slots=[]
            if spacing>=2.35:
                for k in range(n):
                    slots.append(((k+.5)*spacing,min(2.1,spacing-.6)))
            skin_edge(P,M,e,slots)
            for k,(s_,w) in enumerate(slots):
                # ground row wider in V9; V10 keeps one opening width per bay so the
                # piers align vertically as in P16
                window_v10(P,M,e,s_,1.15,w,2.2,seed=index*7919+j*131+k)
                for f,z in enumerate(STOREY_Z):
                    window_v10(P,M,e,s_,z,w,1.4,lit=(index+j+k+f)%17==0,seed=index*7919+j*131+k*7+f*3+1)
            # P16: horizontal course bands at each floor, slightly proud of the skin
            for z in [4.35,7.75,11.15,14.55,17.95,21.35]:
                P.det.fbox(M['res_stone'],e,e.L/2,SKIN,.05,e.L+.02,z,z+.14)
            # V7 (P16): grey stone plinth along the ground floor.
            P.det.fbox(M['res_plinth'],e,e.L/2,SKIN,.05,e.L+.02,.21,.95)
        targets=[(365.,-636.),(420.,-630.)] if index else [(315.,-416.),(395.,-427.)]
        candidates=[e for e in edges if (centre[0]-e.at(e.L/2).x)*e.n.x+(centre[1]-e.at(e.L/2).y)*e.n.y>0]
        for target in targets:
            e=min(candidates,key=lambda ed:(ed.at(ed.L/2)-Vector(target)).length);s=e.L/2
            CORE_EDGES.append((e,s))
            # V7 (P16): stair cores rise about one storey above the roof parapet.
            P.det.fbox(M['res_stone'],e,s,0,1.05,5.6,.21,CORE_TOP)
            # V10 (P16): the cores carry one narrow (~1.1 m) stacked window per landing in
            # stone, not a 2.5 m glass strip; a glazed entrance door at the base.
            for z in [4.6,8.,11.4,14.8,18.1,21.5]:
                P.curtain(e,s-.55,s+.55,z+.35,min(z+2.35,CORE_TOP-1.2),mull=1.1,transom=2.,off=1.08)
            P.curtain(e,s-1.1,s+1.1,.81,3.3,mull=1.1,transom=2.5,off=1.08)
            P.det.fbox(M['res_plinth'],e,s,1.05,.08,2.6,3.3,3.55)              # door head
            for z in [4.35,7.75,11.15,14.55,17.95,21.35]:
                P.det.fbox(M['res_plinth'],e,s,1.05,.05,5.62,z,z+.12)
            P.det.fbox(M['res_stone'],e,s,-.05,1.55,6.2,CORE_TOP-.2,CORE_TOP+.3)
            for k in range(5):P.shell.fbox(M['res_stone'],e,s,.1,.6*(5-k),5.,.21,.21+(k+1)*.12)
    root=P.finish(C,'secondary',bevel=.025)
    # V10: collision proxy. The skin's hundreds of pier/spandrel/window parts would
    # otherwise enter the collider as near-ground islands (104k tris in the first V10
    # build, V9 48k). One closed SKIN-thick ring per block plus the stair cores and
    # their steps reproduce the walkable envelope; the details are skipped.
    from .geometry import MeshBuilder as _MB, parent_keep as _pk
    from .v6_academic import polygon_prism
    col=_MB()
    for index,poly in enumerate(OUTLINES):
        ring_=Polygon(poly).buffer(SKIN,join_style='mitre').difference(Polygon(poly).buffer(-.05,join_style='mitre'))
        polygon_prism(col,M['res_stone'],ring_,.21,ROOF_Z)
    for e,s_ in CORE_EDGES:
        col.fbox(M['res_stone'],e,s_,0,1.05,5.6,.21,CORE_TOP)
        for k in range(5):col.fbox(M['res_stone'],e,s_,.1,.6*(5-k),5.,.21,.21+(k+1)*.12)
    o=col.to_object('AB_East_Residential_Collision_Proxy',C['secondary'])
    _pk(o,root);o['zc_collision']=True;o.hide_render=True;o.display_type='WIRE'
    o['zc_evidence']='Collision-only envelope of the V10 stone skin and stair cores (not rendered).'
    for k in root.children:
        if k.name.endswith('_Details'):k['zc_no_ground_collision']=True
    root['zc_identity']='Student accommodation candidate; geographic identity UNVERIFIED'
    root['zc_photo_sources']='P04,P06,P10,P11,P16; design visible, candidate map association estimated'
    root['zc_garden']='Southern C-block; branching paths/hedges from photos; exact plan estimated'
    return root

def height(x,y):
    from .ground_system import datum,smooth
    return datum(x,y)+.012+.198*smooth((-y-555.)/12.)

def build(M,C,A):
    from .ground_system import mesh_region
    from .v6_academic import polygon_prism
    coll=get_collection('Dormitory_Estimated_Garden')
    mesh_region('Dorm_Garden_Surfaces',[(M['grass'],PLANTED,lambda x,y:.032),
                (M['garden_paver'],PATH,lambda x,y:.21),(M['pebbles'],PEBBLE,lambda x,y:.06)],coll,step=3)
    root=bpy.data.objects['AB_East_Residential_Pair_Estimated']
    # V7: clipped hedge with a softened two-step crown instead of a sharp block.
    hedges=MeshBuilder();polygon_prism(hedges,M['hedge'],HEDGE,.032,.52)
    polygon_prism(hedges,M['hedge'],HEDGE.buffer(-.07),.52,.63)
    o=hedges.to_object('Dorm_Garden_Hedges_Details',coll);parent_keep(o,root);o['zc_collision']=True
    for obj in list(bpy.data.objects):
        if obj.type=='MESH' and any(c.name in ('Palms','Trees','Shrubs') for c in obj.users_collection):
            if GARDEN.buffer(1).union(PATH.buffer(.4)).covers(Point(obj.location.x,obj.location.y)):
                bpy.data.objects.remove(obj,do_unlink=True)
    # Layered whorled boughs, rather than the first review's plain stacked cones.
    from mathutils import Matrix
    cone=MeshBuilder();cone.cylinder(M['bark'],(0,0),0,5.8,.12,segs=8)
    branch=MeshBuilder();branch.ico(M['hedge'],(0,0,0),1.,subdiv=1,scale=(1.,.42,.22),jitter=.10,seed=11.)
    branch_mesh=branch.to_mesh('ASSET_V6_Evergreen_Bough')
    for i in range(6):
        radius=2.-i*.27;z=1.4+i*.77
        cone.cylinder(M['hedge'],(0,0),z-.4,z+1.0,radius*.45,.05,segs=9)
        for k in range(7):
            a=k*2*math.pi/7+i*.43
            xf=Matrix.Translation((math.cos(a)*radius*.50,math.sin(a)*radius*.50,z))@Matrix.Rotation(a,4,'Z')@Matrix.Diagonal((radius*.85,radius*.85,1.,1.))
            cone.add_mesh(M['hedge'],branch_mesh,xf)
    conifer=cone.to_mesh('ASSET_V6_Garden_Evergreen')
    for i,(x,y) in enumerate([(374,-598),(388,-609),(401,-616),(416,-606),(390,-586),(356,-608),(407,-629)]):
        if PLANTED.buffer(-1.).covers(Point(x,y)):
            mesh=conifer if i<4 else A['trees'][i%len(A['trees'])]
            o=instance(mesh,f'Dorm_Photo_Tree_{i+1}',C['veg_trees'],(x,y,.032),i*.7,.8 if i%2 else 1.)
            coll.objects.link(o)
    # V7: mounded shrub rows (two-step crown) plus sparse flowering accents set into
    # them along the two main branches (official image: red / golden-green beds).
    rows=MeshBuilder();polygon_prism(rows,M['shrub'],SHRUB_ROW,.032,.40)
    polygon_prism(rows,M['shrub'],SHRUB_ROW.buffer(-.12),.40,.50)
    o=rows.to_object('Dorm_Garden_Shrub_Rows_Details',coll);parent_keep(o,root)
    shrub_pts=[]
    for i,line in enumerate(LINES[:5]):
        if i not in (0,4):continue
        off=2.0+.72+.42+.25+.45
        for d in [x*3.2 for x in range(1,int((line.length-1)/3.2))]:
            p=line.interpolate(d);q=line.interpolate(min(d+.1,line.length))
            dx,dy=q.x-p.x,q.y-p.y;n=math.hypot(dx,dy)
            if n<1e-6:continue
            for side in [-1,1]:
                x,y=p.x-side*dy/n*off,p.y+side*dx/n*off
                if SHRUB_ROW.buffer(-.2).covers(Point(x,y)) and min(math.dist((x,y),(lx,ly)) for lx,ly,_ in LIGHT_POINTS)>.9:
                    shrub_pts.append((x,y))
    for i,(x,y) in enumerate(shrub_pts):
        # V10 (P16): the clipped shrubs in the owner photo are green; V7's red/golden
        # accents came from a lower-priority official image.
        k=i%2
        o=instance(A['garden_shrub'][k],f'Dorm_Bed_Shrub_{i+1}',C['veg_shrubs'],(x,y,.10),i*1.7,1.05)
        coll.objects.link(o)
    mb=MeshBuilder()
    for x in [-.085,.085]:mb.box(M['metal_light'],x-.035,-.08,0,x+.035,.08,1.05)
    mb.box(M['metal_light'],-.12,-.08,1.02,.12,.08,1.10)
    mb.box(M['lamp'],-.052,.015,.28,.052,.045,.81)
    bollard=mb.to_mesh('ASSET_V6_Dorm_Bollard')
    for i,(x,y,z) in enumerate(LIGHT_POINTS):
        o=instance(bollard,f'Dorm_Path_Bollard_{i+1}',C['furniture'],(x,y,.032),i*.4,1.)
        coll.objects.link(o)
        ld=bpy.data.lights.new(f'V6_DormLight_{i+1}','POINT');ld.energy=0;ld.color=(1.,.70,.38);ld.shadow_soft_size=.35
        o=bpy.data.objects.new(ld.name,ld);C['lighting'].objects.link(o);o.location=(x,y,z)
        o['zc_night_energy']=55.;o['zc_evidence']='P04/P11 low garden lighting; positions/brightness estimated'
    from .geometry import resample
    routes=[[(0,-365),(0,-430),(0,-500),(0,-534)],[(0,-500),(150,-520),(250,-525),(350,-525),INGRESS]]
    mb=MeshBuilder()
    # V7: a worn desire line has irregular, not ruler-straight, edges (estimated).
    for r_i,route in enumerate(routes):
        pts=resample(route,2.)
        ab=[(-(1.25+.35*math.sin(i*.37+r_i)+.2*math.sin(i*1.13)),1.25+.3*math.sin(i*.29+2.+r_i)+.22*math.sin(i*.91)) for i in range(len(pts))]
        mb.ribbon_var(M['compacted'],pts,ab,.012)
    o=mb.to_object('Rear_Compacted_Path',C['ground'])
    o['zc_evidence']='Owner bare rear ground; connecting desire line is an engineering estimate, not a mapped road.'
    out=Path(__file__).resolve().parents[2]/'output/validation/v11';out.mkdir(parents=True,exist_ok=True)
    (out/'dorm_garden_plan.json').write_text(json.dumps({'status':'PHOTO-SUPPORTED DESIGN; CANDIDATE GEOGRAPHIC IDENTITY UNVERIFIED','branches':BRANCHES,'garden_area_m2':GARDEN.area,'paved_area_m2':PATH.area,'pebble_border_m2':PEBBLE.area,'bed_shrubs':len(shrub_pts),'lights':LIGHT_POINTS,
        'storey_note':'V7 models six storeys (ground + 5): P16 and the official zewailcity.edu.eg/dorms image both show six window rows. The OSM candidate footprint is tagged building:levels=5; the conflict is retained and the candidate geographic identity remains UNVERIFIED.',
        'official_page_facts':'Dorms inaugurated 2018-09-15 (281 beds); additional building received 2021-03-13 (93 rooms); 241 rooms / 467 beds total; laundry room per building (source: zewailcity.edu.eg/dorms, read 2026-11-07).'},indent=2))
    plan=json.loads((out/'dorm_garden_plan.json').read_text())
    plan['walk_paths_godot']=[[[round(p.x,3),round(-p.y,3)] for p in
        [line.interpolate(min(i,line.length)) for i in list(range(0,int(line.length),4))+[line.length]]]
        for line in LINES]
    plan['branch_shell_intersection_m']=[line.intersection(SHELL).length for line in LINES]
    (out/'dorm_garden_plan.json').write_text(json.dumps(plan,indent=2))

