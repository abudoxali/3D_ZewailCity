"""Owner-photo form corrections P09/P13/P15. All metric dimensions are estimates.

OSM footprint retained. Segmented inner facade replaces the generic V5 glass arc;
balcony voids, projecting bays, portal and court levels are actual geometry.
"""
import math
import bpy
from shapely.geometry import Point,Polygon,box,LineString
from shapely import union_all,constrained_delaunay_triangles
from .geometry import MeshBuilder,Edge,arc_points,arc_band,parent_keep,instance

ENTRY_HALF=8.0
COURT_CENTER=(0.,-272.)
AXIS=box(-5.5,-370,5.5,-228)

def ring(P,M,A):
    cx,cy=A['curve_c'];ro=A['r_out'];ri=ro-A['ring_depth'];h=A['h_wing']
    # Floor body, split at the rear walking axis. Behind-glass mass is set back.
    for a,b in [(180,266),(274,360)]:
        P.shell.prism(M['stone'],arc_band(cx,cy,ri+.45,ro,a,b,32),.21,7.6)
    P.shell.prism(M['stone'],arc_band(cx,cy,ri+.45,ro,266,274,8),7.4,7.6)
    P.shell.prism(M['stone'],arc_band(cx,cy,ri+3.,ro,180,360,64),7.6,h)
    P.det.prism(M['roof'],arc_band(cx,cy,ri+3.,ro,180,360,64),h-.01,h+.04)
    # Outer photographed stone facade: storey bands / paired punched windows.
    outer=arc_points(cx,cy,ro,180,360,64)
    from .v11_academic import ring_window_skip
    for a,b in zip(outer[:-1],outer[1:]):
        e=Edge(a,b)
        at_rear=abs(e.at(e.L/2).x)<11
        m=e.at(e.L/2)
        if ring_window_skip(math.degrees(math.atan2(m.y-cy,m.x-cx))%360):continue  # V11 entrance bays
        P.window_rows(e,[5.2,9.2,13.2,17.2] if at_rear else [1.2,5.2,9.2,13.2,17.2],w=1.55,h=2.35,spacing=.65,margin=.3)
        for z in [4.5,8.5,12.5,16.5,20.5]:P.band(e,0,e.L,z,z+.13)
    # Lower glazing grid is continuous only where there is no physical rear aperture.
    inner=arc_points(cx,cy,ri,360,180,72)
    for a,b in zip(inner[:-1],inner[1:]):
        e=Edge(a,b);rear=abs(e.at(e.L/2).x)<7
        if not rear:P.curtain(e,.02,e.L-.02,.45,7.6,mull=1.2,transom=2.4,mat=M['court_glass'])
        # V10 (P13): the crown is a deep, tall cream stone fascia over the dark glass,
        # not a thin 1 m strip (V9). Height/depth ESTIMATED from P13 proportions.
        P.det.fbox(M['stone'],e,e.L/2,-.05,.55,e.L,19.95,22.)
    # P13: repeated deep glazed boxes, separated by real recessed open-air bays.
    for i,(a,b) in enumerate([(182,207),(220,246),(258,282),(294,320),(333,358)]):
        r=ri-2.2 if i%2==0 else ri-1.2
        pts=arc_points(cx,cy,r,b,a,12)
        for u,v in zip(pts[:-1],pts[1:]):
            e=Edge(u,v)
            P.curtain(e,.01,e.L-.01,8.3,18.9,mull=1.25,transom=2.65,mat=M['court_glass'])
            # V10 (P13): the cantilever soffits read dark; the head stays a thin stone cap.
            P.det.fbox(M['band'],e,e.L/2,-.1,2.7,e.L+.04,7.7,8.3)
            P.det.fbox(M['stone'],e,e.L/2,-.1,2.7,e.L+.04,18.9,19.45)
        for a2 in [a,b]:
            ar=math.radians(a2)
            u=(cx+r*math.cos(ar),cy+r*math.sin(ar));v=(cx+(ri+3)*math.cos(ar),cy+(ri+3)*math.sin(ar))
            P.curtain(Edge(u,v),0,math.dist(u,v),8.3,18.9,mull=1.3,transom=2.65,mat=M['court_glass'])
    for a,b in [(207,220),(246,258),(282,294),(320,333)]:
        # V10 (P13): the recessed balcony bays are glazed behind the rails (V9 showed a
        # blank white wall); dark glass on the set-back face, grey spandrel at each slab.
        back=arc_points(cx,cy,ri+3.,b,a,8)
        for u,v in zip(back[:-1],back[1:]):
            e=Edge(u,v)
            P.curtain(e,.01,e.L-.01,7.62,19.9,mull=1.4,transom=4.6,mat=M['court_glass'],off=.01)
        for z in [8.,12.6,17.2]:
            P.det.prism(M['stone'],arc_band(cx,cy,ri-.1,ri+3.1,a,b,8),z-.2,z+.14)
            rail=arc_points(cx,cy,ri+.1,a,b,8)
            for u,v in zip(rail[:-1],rail[1:]):
                e=Edge(u,v)
                for zz in [z+.58,z+1.08]:P.det.fbox(M['metal_light'],e,e.L/2,0,.04,e.L,zz,zz+.045)
                P.det.cylinder(M['metal_light'],u,z,z+1.12,.025,segs=6)
    # Real rear aperture stays unobstructed; Gate C motif is a separately qualified hypothesis.
    e=Edge((-7.,cy-ro-.3),(7.,cy-ro-.3))
    P.frame(e,0,14.,.21,21.,t=.55,depth=.55)
    P.curtain(e,.25,13.75,7.6,20.8,mull=1.4,transom=2.65,mat=M['court_glass'])

def polygon_prism(mb,mat,g,z0,z1):
    if g.is_empty:return
    if g.geom_type!='Polygon':
        for p in g.geoms:polygon_prism(mb,mat,p,z0,z1)
        return
    # Constrained triangulation supports inset bands and nonconvex terrace pieces.
    for t in constrained_delaunay_triangles(g).geoms:
        pts=list(t.exterior.coords)[:3]
        area=(pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1])-(pts[1][1]-pts[0][1])*(pts[2][0]-pts[0][0])
        if area<0:pts.reverse()
        mb.raw(mat,[(x,y,z1) for x,y in pts],[(0,1,2)])
    for ring_ in [g.exterior,*g.interiors]:
        pts=list(ring_.coords)
        for (x,y),(u,v) in zip(pts[:-1],pts[1:]):
            mb.raw(mat,[(x,y,z0),(u,v,z0),(u,v,z1),(x,y,z1)],[(0,1,2,3)])

# V7: tiers follow the court arc itself (centre of the inner glass ring), not a
# separate disc. P13 shows the dark-coped platform edge running parallel to the
# curved glazing a few metres from a ground-level viewer, with a walkway between.
# Radii/levels/ramp remain ESTIMATES (no survey); see SOURCE_EVIDENCE V7 section.
TIER_CENTER=(0.,-249.)
TIERS=[(62.,.51,-262.),(51.,.81,-263.5),(40.,1.11,-265.)]   # radius, top level, north cut y
RAMP=(9.,12.,-312.,-285.5)                                  # x0, x1, foot y, head y
POLE_R=56.5

def _tier_prism(mb,top_mat,side_mat,g,z0,z1):
    """Top in paving stone, vertical risers in dark polished granite (P13)."""
    if g.is_empty:return
    if g.geom_type!='Polygon':
        for q in g.geoms:_tier_prism(mb,top_mat,side_mat,q,z0,z1)
        return
    for t in constrained_delaunay_triangles(g).geoms:
        pts=list(t.exterior.coords)[:3]
        area=(pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1])-(pts[1][1]-pts[0][1])*(pts[2][0]-pts[0][0])
        if area<0:pts.reverse()
        mb.raw(top_mat,[(x,y,z1) for x,y in pts],[(0,1,2)])
    for ring_ in [g.exterior,*g.interiors]:
        pts=list(ring_.coords)
        for (x,y),(u,v) in zip(pts[:-1],pts[1:]):
            mb.raw(side_mat,[(x,y,z0),(u,v,z0),(u,v,z1),(x,y,z1)],[(0,1,2,3)])

def tier_discs():
    cx,cy=TIER_CENTER
    x0,x1,y0,y1=RAMP
    cut=AXIS.union(box(x0,y0,x1,y1))
    out=[]
    for radius,top,north in TIERS:
        disc=Point(cx,cy).buffer(radius,quad_segs=64).intersection(box(-80,-340,80,north))
        out.append((radius,top,disc,disc.difference(cut),cut))
    return out

def terrace_geometry(M,C,root):
    mb=MeshBuilder();cx,cy=TIER_CENTER
    for radius,top,disc,g,cut in tier_discs():
        _tier_prism(mb,M['plaza_light'],M['granite'],g,.20,top)
        edge=g.difference(g.buffer(-.32))
        polygon_prism(mb,M['granite'],edge,top,top+.045)
        # Half-height tread around every outer/north edge; 150 mm maximum riser.
        step=disc.buffer(.5).difference(disc).difference(cut)
        # V10 (P13): the platform edges read as continuous dark granite curbs; the
        # 150 mm intermediate tread keeps walkability but is dark granite too, so the
        # edge no longer reads as a grey staircase.
        _tier_prism(mb,M['granite'],M['granite'],step,.2,top-.15)
    x0,x1,y0,y1=RAMP
    v=[(x0,y0,.21),(x1,y0,.21),(x1,y1,1.11),(x0,y1,1.11)]
    mb.raw(M['plaza_light'],v,[(0,1,2,3)])
    for x in [x0,x1]:mb.raw(M['granite'],[(x,y0,.20),(x,y1,.20),(x,y1,1.11),(x,y0,.21)],[(0,1,2,3)])
    o=mb.to_object('Academic_Terraced_Court_Details',C['academic_court']);parent_keep(o,root)
    o['zc_collision']=True
    o['zc_evidence']='P13/P15 tiered raised courts concentric with the inner glazing; V7 radii 62/51/40 m, levels and ramp ESTIMATED.'
    # P13: many slender dark poles stand on the raised platform at a regular rhythm.
    poles=MeshBuilder();lights=[]
    for k in range(17):
        a=math.radians(194.+k*9.5)
        x,y=cx+POLE_R*math.cos(a),cy+POLE_R*math.sin(a)
        if abs(x)<7. or x0-1.<x<x1+1. or y>TIERS[0][2]-1.:continue
        poles.cylinder(M['metal'],(x,y),.51,4.1,.06,.05,segs=10)
        poles.box(M['metal'],x-.14,y-.09,4.0,x+.14,y+.09,4.32)
        poles.box(M['lamp'],x-.11,y-.07,3.96,x+.11,y+.07,4.0)
        lights.append((x,y,3.9))
    o=poles.to_object('Academic_Court_Poles_Details',C['academic_court']);parent_keep(o,root)
    o['zc_collision']=True
    o['zc_evidence']='P13/P15 slender dark poles on the platform; spacing, height and luminaire function ESTIMATED.'
    # P13 lower-left: low black stone seat blocks on the lower walkway.
    seats=MeshBuilder()
    for deg in (200.,214.,326.,340.):
        a=math.radians(deg);r=65.
        x,y=cx+r*math.cos(a),cy+r*math.sin(a)
        seats.obox(M['granite'],(x,y,.21+.225),(1.6,.55,.45),a+math.pi/2)
    o=seats.to_object('Academic_Court_Seat_Blocks',C['academic_court']);parent_keep(o,root)
    o['zc_collision']=True
    o['zc_evidence']='P13 low dark seat blocks; count/positions ESTIMATED.'
    return lights

def paving_regions(mask,M):
    # P09: nested rectangular dark inlays. P13/P15: light slabs and dark borders.
    fore=box(-19.65,-218.,19.65,-169.4)
    lines=[]
    for inset in [3.,6.5,10.]:
        p=box(-19.65+inset,-215.+inset,19.65-inset,-171.-inset)
        if not p.is_empty and p.area>1:lines.append(p.difference(p.buffer(-.55)))
    inlay=union_all(lines).intersection(fore)
    public=mask.union(fore)
    # True material partition: no coplanar painted plane above the paving.
    return [(M['plaza_inlay'],inlay),(M['plaza_grey'],fore.difference(inlay)),(M['plaza_light'],mask.difference(fore))]

def rail_stairs(mb,M,lo,hi,front,back,top):
    # P09 directly depicts slender metal rails. Profile measurements remain estimated.
    for x in [lo+.13,hi-.13]:
        for k in range(11):
            t=k/10;y=front+(back-front)*t;z=.21+(top-.21)*t
            mb.cylinder(M['metal_light'],(x,y),z,z+1.02,.027,segs=8)
        for rise in [.56,1.02]:
            y0,y1=front,back;z0=.21+rise;z1=top+rise
            # A thin closed prism follows the sloping flight, not a solid stone guard.
            v=[(xx,yy,zz) for xx in [x-.025,x+.025] for yy,zz in [(y0,z0-.025),(y1,z1-.025),(y1,z1+.025),(y0,z0+.025)]]
            mb.raw(M['metal_light'],v,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)])

def admin_rear(P,M):
    """P09 directly locates the south admin face in the Academic visual axis."""
    # V11 (owner 16 / P09): the rear block is 18 m; bays and frames stop below its parapet
    # (V10 ran them to 24 m, which also hid the dome once the block was lowered).
    top=17.2
    e=Edge((-16,-94.15),(16,-94.15))
    for a,b in [(1.,7.8),(11.,21.),(24.2,31.)]:
        P.curtain(e,a,b,.5,top,mull=2.,transom=5.6,off=.04)
        P.frame(e,a,b,.4,top,t=.55,depth=.2)
    from .gate import FONT_LAT,_text_mesh,_on_face
    from mathutils import Matrix
    me=_text_mesh('Administrative\nand Cultural\nComplex',FONT_LAT,.72)
    if me:
        mat=Matrix.Translation((-11.3,-94.4,13.6))@Matrix.Rotation(math.pi,4,'Z')@Matrix.Rotation(math.pi/2,4,'X')
        P.det.add_mesh(M['stone_plain'],me,mat)
