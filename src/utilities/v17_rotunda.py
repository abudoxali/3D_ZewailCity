"""Bounded Administration rotunda supported by contractor photograph 4556.

Same project's windowed dome supports the association. Radius, height, gallery
grid and doorway positions are estimates; no office/auditorium plans inferred.
"""
import math,json
from pathlib import Path
from shapely.geometry import Point,Polygon,box
from shapely import constrained_delaunay_triangles,make_valid
from shapely.geometry.polygon import orient
from mathutils import Vector
from .geometry import MeshBuilder,Edge,arc_points,arc_band

R=10.85;FLOOR=.72;VOID_BOTTOM=.735;VOID_TOP=26.79

def parts(g):
    if g.is_empty:return
    if g.geom_type=='Polygon':
        if g.area>1e-8:yield g
    elif hasattr(g,'geoms'):
        for x in g.geoms:yield from parts(x)

def carve(builder):
    """Clip architectural face polygons, retaining original material and winding.

    Horizontal slabs are annuli; vertical faces are clipped in their own s/z
    plane. New visible interior lining supplies the cylinder reveals. This is
    source geometry, not an invisible collision volume or runtime hide.
    """
    output=MeshBuilder();circle=Point(0,0).buffer(R,quad_segs=64);removed=0
    builder.bm.normal_update()
    for face in builder.bm.faces:
        vs=[v.co.copy() for v in face.verts];mat=builder.mats[face.material_index]
        if max(v.z for v in vs)<=VOID_BOTTOM or min(v.z for v in vs)>=VOID_TOP:
            output.raw(mat,[tuple(v) for v in vs],[tuple(range(len(vs)))]);continue
        if abs(face.normal.z)>.995:
            z=sum(v.z for v in vs)/len(vs);poly=make_valid(Polygon([(v.x,v.y) for v in vs]));g=poly.difference(circle)
            if poly.area-g.area<1e-8:
                output.raw(mat,[tuple(v) for v in vs],[tuple(range(len(vs)))]);continue
            removed+=1
            for p in parts(g):
                for tri in constrained_delaunay_triangles(p).geoms:
                    co=list(tri.exterior.coords)[:3]
                    area=sum(co[i][0]*co[(i+1)%3][1]-co[(i+1)%3][0]*co[i][1] for i in range(3))
                    if area*face.normal.z<0:co.reverse()
                    output.raw(mat,[(x,y,z) for x,y in co],[(0,1,2)])
        elif abs(face.normal.z)<.005:
            if 'Copper' in mat.name:
                output.raw(mat,[tuple(v) for v in vs],[tuple(range(len(vs)))]);continue
            origin=Vector((vs[0].x,vs[0].y,0));d=max((Vector((v.x,v.y,0))-origin for v in vs),key=lambda v:v.length)
            if d.length<1e-8:
                output.raw(mat,[tuple(v) for v in vs],[tuple(range(len(vs)))]);continue
            d.normalize();along=origin.dot(d);perp2=max(0.,origin.length_squared-along*along)
            if perp2>=R*R:
                output.raw(mat,[tuple(v) for v in vs],[tuple(range(len(vs)))]);continue
            extent=math.sqrt(R*R-perp2);lo,hi=-along-extent,-along+extent
            poly=make_valid(Polygon([((Vector((v.x,v.y,0))-origin).dot(d),v.z) for v in vs]))
            g=poly.difference(box(lo,VOID_BOTTOM,hi,VOID_TOP))
            if poly.area-g.area<1e-8:
                output.raw(mat,[tuple(v) for v in vs],[tuple(range(len(vs)))]);continue
            removed+=1
            for p in parts(g):
                for tri in constrained_delaunay_triangles(p).geoms:
                    verts=[origin+d*s+Vector((0,0,z)) for s,z in list(tri.exterior.coords)[:3]]
                    if (verts[1]-verts[0]).cross(verts[2]-verts[0]).dot(face.normal)<0:verts.reverse()
                    output.raw(mat,[tuple(v) for v in verts],[(0,1,2)])
        else:output.raw(mat,[tuple(v) for v in vs],[tuple(range(len(vs)))])
    return output,removed

def build(P,M):
    # Existing opaque sub-dome slabs/drum are actually removed from active
    # geometry. Copper exterior cap/windows retain their true visible silhouette.
    counts={}
    for key in ('shell','det'):
        old=getattr(P,key);new,n=carve(old);setattr(P,key,new);counts[key]=n
    from .v6_academic import polygon_prism
    floor=Point(0,0).buffer(R,quad_segs=64)
    # Original central floor is retained. A subtle radial inlay follows the
    # photographed material language without copying the detailed floor artwork.
    for radius,width in ((3.8,.18),(8.6,.10)):
        ring=Point(0,0).buffer(radius,quad_segs=64).difference(Point(0,0).buffer(radius-width,quad_segs=64))
        polygon_prism(P.det,M['granite'],ring,FLOOR+.004,FLOOR+.008)
    for i in range(16):
        a=2*math.pi*i/16;x,y=7.*math.cos(a),7.*math.sin(a)
        P.det.obox(M['band'],(x,y,FLOOR+.007),(1.8,.10,.008),a)
    # Photograph shows two gallery bands, stone piers and orange drum lining.
    # Four ground portals remain open to the source-confirmed circulation.
    for i in range(16):
        a=2*math.pi*(i+.5)/16;x,y=10.65*math.cos(a),10.65*math.sin(a)
        P.shell.obox(M['stone'],(x,y,(FLOOR+21.4)/2),(.7,.85,21.4-FLOOR),a)
    for z in (5.,10.2):
        ring=orient(Point(0,0).buffer(11.5,quad_segs=64).difference(Point(0,0).buffer(10.05,quad_segs=64)),sign=1.)
        polygon_prism(P.shell,M['stone'],ring,z-.25,z)
        # Open galleries are bounded by a real guard, not a solid floor filling
        # the atrium. These are visual upper boundaries; no invented staircases.
        rail=arc_points(0,0,10.07,0,360,96)
        for p,q in zip(rail[:-1],rail[1:]):
            e=Edge(p,q)
            P.det.fbox(M['copper'],e,e.L/2,-.03,.12,e.L,z,z+.65)
            P.det.fbox(M['metal_light'],e,e.L/2,0,.06,e.L,z+.95,z+1.0)
    # Explicit cylindrical reveals/backing close the clipped source solids.
    # Photo4556 shows open lower circulation, two galleries and a tall white
    # upper panel zone; no third balcony is inferred at the drum cornice.
    for z0,z1 in ((FLOOR,4.75),(5.,9.95)):
        for a,b in ((-80,-10),(10,80),(100,170),(190,260)):
            wall=orient(Polygon(arc_band(0,0,11.85,12.05,a,b,24)),sign=1.)
            polygon_prism(P.shell,M['plaster'],wall,z0,z1)
    upper=orient(Point(0,0).buffer(11.0,quad_segs=64).difference(Point(0,0).buffer(10.78,quad_segs=64)),sign=1.)
    polygon_prism(P.shell,M['plaster'],upper,11.0,21.5)
    cornice=orient(Point(0,0).buffer(10.91,quad_segs=64).difference(Point(0,0).buffer(10.65,quad_segs=64)),sign=1.)
    polygon_prism(P.det,M['copper'],cornice,17.8,18.15)
    # Interior drum rings are thin shells; daylight enters the original windows.
    for z0,z1 in ((18.,21.5),(25.3,26.78)):
        ring=Polygon(arc_band(0,0,10.80,10.95,0,360,96))
        polygon_prism(P.det,M['copper'],ring,z0,z1)
    report={'source':'https://content.hassanallam.com/app/uploads/2022/05/4556-2560x1707.jpg',
            'source_local':'evidence/public_sources/hassanallam_4556.jpg','classification':'SAME PROJECT PHOTO / PLACEMENT AND ALL DIMENSIONS ESTIMATED',
            'radius_m':R,'ground_level_m':FLOOR,'gallery_levels_m':[5.,10.2],
            'source_faces_clipped':counts,'no_inferred_rooms':True,'sensitive_spaces':False}
    dest=Path(__file__).resolve().parents[2]/'output/build_metadata/v17/administration_rotunda.json';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(report,indent=1))
    print('[V17 Administration] source-carved skylit rotunda',counts,flush=True)
