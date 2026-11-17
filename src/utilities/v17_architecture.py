"""Photo-grounded V17 public architecture, in the original local building datum.

Source filenames and hypotheses are retained on each editable native object.
No recovered survey dimensions, room plan or unobserved furnished interior.
"""
import math,json
from pathlib import Path
import bpy
from shapely.geometry import Point,box,LineString,Polygon
from shapely import union_all
from .geometry import MeshBuilder,Edge,parent_keep,arc_points,arc_band

ROOT=Path(__file__).resolve().parents[2]
PHOTO_GATE='photo_13_2026-11-10_20-28-31.jpg'
PHOTO_COURT='photo_19_2026-11-10_20-28-31.jpg + photo_10_2026-11-10_20-26-04.jpg'
UPPER=4.41
STAIR_SPEC={'width_m':10.5,'inner_x_m':9.5,'upper_m':UPPER,'base_m':.21,
            'preferred_riser_m':.15,'tread_m':.48,'mid_landing_m':4.0,'head_y_m':-219.,
            'confidence':'PHOTO-SUPPORTED paired form/cheeks/landings; ALL METRIC DIMENSIONS ESTIMATED'}

def sloping_bar(mb,mat,a,b,width=.045):
    # True 3D square-section rail; no horizontal box standing in for a slope.
    from mathutils import Vector
    u=Vector(a);v=Vector(b);d=v-u
    n=Vector((1,0,0)) if abs(d.normalized().x)<.8 else Vector((0,1,0))
    p=d.cross(n).normalized()*width/2;q=d.normalized().cross(p).normalized()*width/2
    verts=[tuple(c+s*p+t*q) for c in (u,v) for s,t in ((-1,-1),(1,-1),(1,1),(-1,1))]
    mb.raw(mat,verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])

def stairs(M,C,root):
    spec=STAIR_SPEC;n=round((UPPER-.21)/spec['preferred_riser_m']);rise=(UPPER-.21)/n
    half=n//2;run=n*spec['tread_m']+spec['mid_landing_m'];head=spec['head_y_m'];foot=head+run
    reports=[]
    for side in (-1,1):
        mb=MeshBuilder();lo,hi=sorted((side*spec['inner_x_m'],side*(spec['inner_x_m']+spec['width_m'])))
        stations=[(foot,.21)];cursor=foot
        for k in range(n):
            if k==half:
                mb.box(M['plaza_grey'],lo,cursor-spec['mid_landing_m'],-.15,hi,cursor,.21+k*rise)
                cursor-=spec['mid_landing_m'];stations.append((cursor,.21+k*rise))
            z=.21+(k+1)*rise;y=cursor
            mb.box(M['plaza_grey'],lo,y-spec['tread_m'],-.15,hi,y,z)
            mb.box(M['granite'],lo+.06,y-.055,z-.012,hi-.06,y,z+.003)
            cursor-=spec['tread_m'];stations.append((cursor,z))
        mb.box(M['stone'],lo,head-3.,UPPER-.24,hi,head,UPPER)
        # Paired stone cheeks and inclined stainless rails are visible in photo13.
        # Keep the stair head open to the upper circulation plate.
        for x in (lo+.12,hi-.12):
            for (ya,za),(yb,zb) in zip(stations[:-1],stations[1:]):
                if abs(ya-yb)<1e-6:continue
                width=.18
                verts=[(x-width,ya,za),(x+width,ya,za),(x+width,yb,zb),(x-width,yb,zb),
                       (x-width,ya,za+.42),(x+width,ya,za+.42),(x+width,yb,zb+.42),(x-width,yb,zb+.42)]
                mb.raw(M['stone'],verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
                for zz in (.70,1.05):sloping_bar(mb,M['metal_light'],(x,ya,za+zz),(x,yb,zb+zz))
            for i,(y,z) in enumerate(stations):
                if i%3==0:mb.cylinder(M['metal_light'],(x,y),z+.4,z+1.07,.025,segs=8)
            # Inner guard terminates at the stair head so the transverse upper
            # landing is actually accessible. Continue only the exposed outer
            # side; two inner extensions would fence the stairs off the deck.
            outer=(x<lo+.3) if side<0 else (x>hi-.3)
            if outer:
                for y in (head-1.4,head-2.8):mb.cylinder(M['metal_light'],(x,y),UPPER,UPPER+1.05,.025,segs=8)
                sloping_bar(mb,M['metal_light'],(x,head,UPPER+1.05),(x,head-2.95,UPPER+1.05))
        o=mb.to_object('Academic_Stair_'+('Left' if side<0 else 'Right'),C['academic_stairs']);parent_keep(o,root)
        o['zc_collision']=True;o['zc_v17_exact_stairs']=True
        for k,v in {'zc_risers':n,'zc_riser_height_m':rise,'zc_tread_m':spec['tread_m'],'zc_width_m':hi-lo}.items():o[k]=v
        o['zc_evidence']=PHOTO_GATE+'; '+spec['confidence']
        o['zc_mid_landing_m']=spec['mid_landing_m'];o['zc_upper_datum_m']=UPPER
        reports.append({'object':o.name,'foot_y':foot,'head_y':head,'risers':n,'riser_m':rise,'stations_y_z':stations})
    out=ROOT/'output/build_metadata/v17';out.mkdir(parents=True,exist_ok=True)
    (out/'academic_stairs.json').write_text(json.dumps({'source':PHOTO_GATE,'specification':spec,'stairs':reports},indent=1))

def core(P,M,A):
    # Retain the independently editable supported shell/voids. Correct deck
    # height and build an actual lower entry threshold beneath the upper landing.
    from . import v11_academic as old
    old.DECK_Z0,old.DECK_Z1=UPPER-.21,UPPER
    old.STAIR_IN,old.STAIR_OUT=9.5,20.
    old.PASS_HALF=9.5
    plate=old.core(P,M,A)
    # Photo13 has a glazed lower entrance framed under the transverse landing,
    # rather than an unbounded blank tunnel. Leave two 2.2 m open door leaves.
    y=-222.0;z=.89;top=3.65
    for a,b in ((-6.5,-3.4),(-1.2,1.2),(3.4,6.5)):
        P.shell.box(M['lobby_glass'],a,y,z,b,y+.055,top)
        P.det.box(M['metal'],a-.04,y-.025,z,a+.04,y+.1,top)
        P.det.box(M['metal'],b-.04,y-.025,z,b+.04,y+.1,top)
    P.shell.box(M['stone'],-9.5,y-.25,top,9.5,y+.25,UPPER-.21)
    # Four broad entrance steps are visible below the Gate A portal in photo13.
    # Reserve their floor footprint rather than overlaying a second ramp/plate.
    for k in range(4):
        ya=-218.8-k*.38
        P.shell.box(M['plaza_grey'],-6.8,ya-.38,.20,6.8,ya,.21+(k+1)*.17)
    P.shell.box(M['plaza_light'],-6.8,-222.1,.20,6.8,-220.32,.89)
    P.shell.box(M['plaza_light'],-6.8,-223.0,.20,6.8,-222.1,.89)
    # Unseen interior connection is an explicit functional estimate: shallow
    # return treads bring the vestibule back to the retained public-route floor.
    for k in range(4):
        ya=-223.0-k*.38
        P.shell.box(M['plaza_grey'],-6.8,ya-.38,.20,6.8,ya,.89-(k+1)*.17)
    # Slim threshold, inset dark mat and explicit glazing returns. Free passage
    # continues to the courtyard without inventing offices or classrooms.
    P.det.box(M['granite'],-6.8,y-1.2,.212,6.8,y-.1,.225)
    # Upper hall entry, three glazed bands in photo13. Doorway gaps align with
    # the two supported side paths around the central railed void.
    for a,b in ((-19.2,-12.5),(-10.1,10.1),(12.5,19.2)):
        a=max(a,-16.);b=min(b,16.)
        P.shell.box(M['lobby_glass'],a,-243.05,UPPER,b,-243.,8.6)
        P.det.box(M['metal'],a-.04,-243.1,UPPER,a+.04,-242.95,8.65)
        P.det.box(M['metal'],b-.04,-243.1,UPPER,b+.04,-242.95,8.65)
    return plate

def ring(P,M,A):
    # Preserve the exterior mapped shell and known rear opening, but rebuild
    # the curved courtyard glazing as planar projecting bays with true returns.
    from . import v6_academic as old
    old.ring(P,M,A)
    # old.ring now delegates upper bay geometry to this function's helper.

def glass_bays(P,M,A):
    cx,cy=A['curve_c'];ri=A['r_out']-A['ring_depth']
    for i,(a,b) in enumerate([(182,207),(220,246),(258,282),(294,320),(333,358)]):
        r=ri-2.2
        pa=(cx+r*math.cos(math.radians(b)),cy+r*math.sin(math.radians(b)))
        pb=(cx+r*math.cos(math.radians(a)),cy+r*math.sin(math.radians(a)))
        e=Edge(pa,pb)
        P.curtain(e,.04,e.L-.04,8.3,19.9,mull=1.6,transom=4.0,mat=M['court_glass'])
        P.det.fbox(M['band'],e,e.L/2,-.1,2.7,e.L+.04,7.7,8.3)
        P.det.fbox(M['stone'],e,e.L/2,-.1,2.7,e.L+.04,19.9,20.15)
        for angle,p in ((b,pa),(a,pb)):
            q=(cx+(ri+3)*math.cos(math.radians(angle)),cy+(ri+3)*math.sin(math.radians(angle)))
            ret=Edge(p,q);P.curtain(ret,.01,ret.L-.01,8.3,19.9,mull=1.6,transom=4.0,mat=M['court_glass'])

def court_platforms():
    # These are offset crescents with straight/tangent boundaries and broad
    # transverse circulation. They are not stacked circular arena discs.
    court=Point(0,-249).buffer(72.5,quad_segs=80).intersection(box(-74,-327,74,-270.5))
    rear_route=box(-6.,-350.,6.,-300.)
    ramps=box(10.,-315.,14.,-280.)
    rows=[]
    for radius,top,north,cx in ((61.,.51,-274.,-2.),(49.,.81,-278.,-2.),(35.,1.11,-279.,1.)):
        g=Point(cx,-250.).buffer(radius,quad_segs=80).intersection(court).intersection(box(-75,-335,75,north))
        g=g.difference(rear_route).difference(ramps)
        # Photo19/23: discrete straight stair breaks interrupt curved coping.
        # Keep transverse slots broad enough for real movement; exact stations
        # are an explicit estimate, not a recovered measured landscape plan.
        g=g.difference(box(-38.,-318.,-34.,-278.)).difference(box(29.,-318.,33.,-278.))
        rows.append((top,g))
    return rows,ramps

def terraces(M,C,root):
    from .v6_academic import _tier_prism,polygon_prism
    mb=MeshBuilder();rows,ramps=court_platforms()
    # Emit each exposed top once; lower platforms are trimmed beneath the next.
    for i,(top,g) in enumerate(rows):
        above=union_all([q for _,q in rows[i+1:]])
        _tier_prism(mb,M['plaza_light'],M['granite'],g.difference(above),.20,top)
        coping=g.difference(g.buffer(-.28)).difference(above)
        polygon_prism(mb,M['granite'],coping,top,top+.035)
        # The actual offset boundary supplies every intermediate tread. A
        # bounding-box-Y rectangle would detach from these curved tier edges.
        # The continuous 0.55m dark tread makes each 0.30m level change two
        # physical 0.15m rises, including the route toward the rear passage.
        outer=g.buffer(.55,quad_segs=16).difference(g).difference(above).difference(ramps)
        if i:outer=outer.intersection(rows[i-1][1])
        _tier_prism(mb,M['granite'],M['granite'],outer,.20,top-.15)
    # Each cut crosses every platform using source-derived physical treads.
    # At each local Y, find the adjacent platform height, then subdivide the
    # actual transition rather than lay an overlapping ramp over paving.
    # These routes retain all platform surfaces outside the reserved slots.
    for lo,hi in ((-38.,-34.),(29.,33.)):
        y=-317.5
        while y < -278.0:
            yy=y+.25
            heights=[.21]
            for z,g in rows:
                if g.buffer(.02).covers(Point(lo-.02,yy)) or g.buffer(.02).covers(Point(hi+.02,yy)):heights.append(z)
            top=max(heights)
            # A 0.30m platform edge gets a half-height approach tread.
            future=[.21]
            for z,g in rows:
                if g.buffer(.02).covers(Point(lo-.02,yy+.55)) or g.buffer(.02).covers(Point(hi+.02,yy+.55)):future.append(z)
            ahead=max(future)
            if ahead>top+.20:top+=.15
            if top>.211:mb.box(M['plaza_light'],lo,y,.20,hi,min(y+.25,-278.),top)
            y+=.25
    # Graded side connection, physically visible and collided with the same mesh.
    for x0,x1,ya,yb,za,zb in [(10.,14.,-315.,-280.,.21,1.11)]:
        mb.raw(M['plaza_light'],[(x0,ya,za),(x1,ya,za),(x1,yb,zb),(x0,yb,zb)],[(0,1,2,3)])
        for x in (x0,x1):mb.raw(M['granite'],[(x,ya,.20),(x,yb,.20),(x,yb,zb),(x,ya,za)],[(0,1,2,3)])
    o=mb.to_object('Academic_Terraced_Court_Details',C['academic_court']);parent_keep(o,root);o['zc_collision']=True;o['zc_evidence']=PHOTO_COURT+'; boundaries/heights ESTIMATED'
    poles=MeshBuilder();lights=[]
    # Photograph poles follow the curved lower platform, not a garden grid.
    for deg in (198.,211.,225.,239.,253.,282.,298.,313.,329.,342.):
        r=57.;a=math.radians(deg);x,y=-2.+r*math.cos(a),-250.+r*math.sin(a)
        if y>-275 or abs(x)<8:continue
        top=max([.21]+[z for z,g in rows if g.covers(Point(x,y))])
        poles.cylinder(M['metal'],(x,y),top,top+3.25,.045,segs=8)
        poles.box(M['lamp'],x-.10,y-.07,top+3.15,x+.10,y+.07,top+3.25);lights.append((x,y,top+3.1))
    o=poles.to_object('Academic_Court_Poles_Details',C['academic_court']);parent_keep(o,root);o['zc_collision']=True
    out=ROOT/'output/build_metadata/v17';out.mkdir(parents=True,exist_ok=True)
    (out/'academic_court.json').write_text(json.dumps({'sources':PHOTO_COURT,'classification':'PHOTO-SUPPORTED FORM / ESTIMATED DIMENSIONS',
        'platforms':[{'top_local_m':z,'boundary_wkt':g.wkt,'area_m2':g.area} for z,g in rows],
        'trees':0,'rear_route_width_m':12.,'continuous_side_ramp':'10..14 m x; -315..-280 y; ESTIMATED'},indent=1))
    return lights

def admin_rear(P,M,open_passages=False):
    # Academic-facing elevation is identifiable in photos25/26 looking out
    # from the Academic forecourt. Photo5 is not assumed to be G1-facing.
    from .gate import FONT_LAT,FONT_AR,_text_mesh
    from mathutils import Matrix
    e=Edge((-16.,-94.15),(16.,-94.15));top=17.2
    for a,b in ((1.,7.8),(11.,21.),(24.2,31.)):
        P.curtain(e,a,b,5.0 if open_passages and a!=11. else .5,top,mull=2.3,transom=5.6,off=.04)
        P.frame(e,a,b,.72,top,t=.58,depth=.32)
    for text,x,z,size in [('Administrative\nand Cultural\nComplex',-11.1,13.8,.60),('ZEWAIL CITY',0.,9.7,.60),('SCIENCE AND TECHNOLOGY',0.,8.7,.25)]:
        me=_text_mesh(text,FONT_LAT,size)
        if me:P.det.add_mesh(M['stone_plain'],me,Matrix.Translation((x,-94.5,z))@Matrix.Rotation(math.pi/2,4,'X'))
    # Narrow course joints and segmented stone tower piers match the readable
    # vertical glazing rhythm; no logo or private image texture is embedded.
    for x in (-15.,-7.5,7.5,15.):
        for z in (3.6,7.,10.4,13.8):P.det.box(M['band'],x-.5,-94.51,z,x+.5,-94.48,z+.025)

def admin_circulation(P,M):
    # Keep V16 owner-confirmed side/rear routes. Rebuild the visible floor and
    # soffit language as bounded structural bays, with real bearing columns.
    from . import v16_admin
    v16_admin.circulation(P,M)
    deck=v16_admin.DECK
    # Broad central hall threshold rhythm, physically inlaid and non-overlapping
    # with floor tops (3mm detail); dimensions remain an interpretation.
    for y in (-17.,-36.,-50.,-64.,-78.,-91.):
        P.det.box(M['granite'],-14.5,y-.16,deck+.002,14.5,y+.16,deck+.005)
    # Column capitals + shallow beams articulate the roofed plaza rather than
    # unsupported uniformly empty 90 m tunnels. No office doors are invented.
    for sx in (-1,1):
        for y in (-22.,-34.,-47.,-61.,-75.,-89.):
            x=sx*15.1
            P.det.box(M['plaza_light'],x-.65,y-.65,4.55,x+.65,y+.65,5.)
            P.det.box(M['plaza_light'],sx*7.8-.18,y-.18,4.58,sx*7.8+.18,y+.18,4.88)
    # The separately source-carved rotunda is implemented in v17_rotunda.py.
    # Its form is supported by the contractor photo; dimensions and links to
    # these retained side galleries remain explicitly estimated.

