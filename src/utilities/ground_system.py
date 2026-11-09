"""V5 surface topology and a single estimated engineering datum.

OSM plan positions and photo-supported materials are retained. No DEM exists:
the gentle sub-metre grading is explicitly ESTIMATED, flattened at buildings.
Polygon unions replace layered road ribbons; material regions never overlap.
Requires project-local Shapely (see tools/requirements-v5.txt).
"""
import json
import math
from pathlib import Path
import sys
from functools import lru_cache
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/vendor'))
from shapely import constrained_delaunay_triangles, make_valid, union_all
from shapely.geometry import Polygon, LineString, Point, box
from shapely.strtree import STRtree
from shapely.prepared import prep
from shapely.geometry.polygon import orient
import bmesh
from . import survey as SV
from .geometry import MeshBuilder

PADS = [box(-105, -111, 105, 42), box(-108, -359, 108, -156),
        box(245, -660, 478, -388), box(-66, SV.GATE_Y - 10, 66, SV.GATE_Y + 18)]
for spec in (SV.HELMY, SV.EAST_INSTITUTE):
    x, y = spec['center']
    PADS.append(Point(x, y).buffer(spec['length'] / 2 + 12))
PAD = union_all(PADS)

def smooth(t):
    t = max(0., min(1., t))
    return t * t * (3 - 2 * t)

@lru_cache(maxsize=400000)
def datum(x, y):
    # No invented hills: 0.08% longitudinal / 0.02% crossfall, smooth pad collars.
    w = smooth(PAD.distance(Point(x, y)) / 35.)
    fade = 1. - smooth((max(abs(x), abs(y)) - 1200.) / 500.)
    return (0.0008 * y + 0.0002 * x) * w * fade

def polygons(g):
    if g.is_empty:
        return
    if g.geom_type == 'Polygon':
        if g.area > 1e-7:
            yield g
    elif hasattr(g, 'geoms'):
        for c in g.geoms:
            yield from polygons(c)

def top_regions(obj):
    out = {}
    mw = obj.matrix_world
    for f in obj.data.polygons:
        if f.normal.z < .9:
            continue
        co = [mw @ obj.data.vertices[i].co for i in f.vertices]
        if max(p.z for p in co) - min(p.z for p in co) > .001:
            continue
        mat = obj.data.materials[f.material_index]
        poly = make_valid(Polygon([(p.x, p.y) for p in co]))
        if not poly.is_empty and poly.area > 1e-7:
            out.setdefault(mat.name, []).append(poly)
    return out

def trim_raised_beds(obj, road):
    """Remove V4 parterre/bed volumes crossing carriageways, including their collision."""
    bm=bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    seen=set()
    out=MeshBuilder()
    changed=0
    cutter=road.buffer(.10)
    for start in bm.faces:
        if start in seen:
            continue
        stack=[start]
        island=[]
        while stack:
            f=stack.pop()
            if f in seen:
                continue
            seen.add(f)
            island.append(f)
            stack.extend(n for e in f.edges for n in e.link_faces if n not in seen)
        tops=[f for f in island if f.normal.z>.9]
        footprint=union_all([Polygon([(v.co.x,v.co.y) for v in f.verts]) for f in tops])
        if footprint.is_empty or not footprint.intersects(cutter):
            for f in island:
                out.raw(obj.data.materials[f.material_index],[tuple(v.co) for v in f.verts],[tuple(range(len(f.verts)))])
            continue
        changed+=1
        z0=min(v.co.z for f in island for v in f.verts)
        z1=max(v.co.z for f in island for v in f.verts)
        mat=obj.data.materials[tops[0].material_index]
        for poly in polygons(footprint.difference(cutter)):
            poly=orient(poly,sign=1.)
            for tri in constrained_delaunay_triangles(poly).geoms:
                co=list(orient(tri,sign=1.).exterior.coords)[:3]
                out.raw(mat,[(x,y,z1) for x,y in co],[(0,1,2)])
                out.raw(mat,[(x,y,z0) for x,y in co],[(2,1,0)])
            for ring in [poly.exterior,*poly.interiors]:
                co=list(ring.coords)
                for (x,y),(u,v) in zip(co[:-1],co[1:]):
                    out.raw(mat,[(x,y,z0),(u,v,z0),(u,v,z1),(x,y,z1)],[(0,1,2,3)])
    bm.free()
    me=out.to_mesh(obj.name+'_V5_Trimmed')
    obj.data=me
    obj.matrix_world.identity()
    print('[ground-v5] raised bed components trimmed off roads:',changed,flush=True)

def foundations():
    """Extend exposed 0.21 m building bases below the soil; keep floor/roof levels."""
    count=0
    for obj in bpy.data.objects:
        if obj.type!='MESH' or obj.parent or not obj.name.startswith('AB_') or obj.get('zc_foundation_v5'):
            continue
        bm=bmesh.new()
        bm.from_mesh(obj.data)
        faces=[f for f in bm.faces if f.normal.z<-.9 and all(.19 < (obj.matrix_world@v.co).z < .22 for v in f.verts)]
        for f in faces:
            old=list(f.verts)
            lower=[bm.verts.new(v.co-Vector((0,0,.4))) for v in old]
            cap=bm.faces.new(lower)
            cap.material_index=f.material_index
            for i,v in enumerate(old):
                j=(i+1)%len(old)
                side=bm.faces.new([v,old[j],lower[j],lower[i]])
                side.material_index=f.material_index
            bm.faces.remove(f)
            count+=1
        bm.to_mesh(obj.data)
        bm.free()
        obj['zc_foundation_v5']=True
        obj['zc_foundation_winding_v5']=True
    print('[ground-v5] foundation bases extended:',count,flush=True)

def repair_foundation_winding():
    # Upgrade the first V5 candidate, whose new skirt winding pointed inward.
    for obj in bpy.data.objects:
        if obj.type!='MESH' or not obj.get('zc_foundation_v5') or obj.get('zc_foundation_winding_v5'):
            continue
        bm=bmesh.new()
        bm.from_mesh(obj.data)
        for f in bm.faces:
            zs=[(obj.matrix_world@v.co).z for v in f.verts]
            if abs(f.normal.z)<.1 and min(zs)<0 and .19<max(zs)<.22:
                f.normal_flip()
        bm.to_mesh(obj.data)
        bm.free()
        obj['zc_foundation_winding_v5']=True

MASK_ATTR = 'ZC_Ground_Mask'


def region_triangles(poly, step):
    """Constrained triangulation with conforming interior refinement.

    Clipping at every grid line used to introduce arbitrarily short boundary
    segments. Keep the exact polygon instead, then bisect long *shared* edges
    on both incident triangles. No needle is discarded and no area is lost.
    """
    import heapq
    points, lookup, triangles, edges, queue = [], {}, {}, {}, []
    def point(xy):
        key = tuple(xy)
        if key not in lookup:
            lookup[key] = len(points)
            points.append(key)
        return lookup[key]
    limit2 = (2 * step) ** 2
    def add(t):
        # IDs must remain unique after removals.
        ti = add.serial; add.serial += 1
        triangles[ti] = t
        for a, b in zip(t, t[1:] + t[:1]):
            e = tuple(sorted((a, b)))
            if e not in edges:
                edges[e] = set()
                x, y = points[a]; u, v = points[b]
                d2 = (x-u)**2 + (y-v)**2
                if d2 > limit2:
                    heapq.heappush(queue, (-d2, e))
            edges[e].add(ti)
    add.serial = 0
    for tri in constrained_delaunay_triangles(poly.segmentize(step)).geoms:
        add(tuple(point(xy) for xy in list(tri.exterior.coords)[:3]))
    while queue:
        _, e = heapq.heappop(queue)
        incident = list(edges.get(e, ()))
        if not incident:
            continue
        a, b = e
        mid = point(((points[a][0]+points[b][0])/2, (points[a][1]+points[b][1])/2))
        for ti in incident:
            t = triangles.pop(ti)
            for u, v in zip(t, t[1:] + t[:1]):
                edges[tuple(sorted((u, v)))].discard(ti)
            c = next(v for v in t if v not in e)
            add((a, mid, c)); add((mid, b, c))
    for t in triangles.values():
        yield [points[i] for i in t]


def grid_triangles(poly, cell):
    """Retain the established boundary sampling on unaffected surface classes."""
    x0,y0,x1,y1 = poly.bounds
    for iy in range(math.floor(y0/cell), math.ceil(y1/cell)):
        row = poly.intersection(box(x0-1,iy*cell,x1+1,(iy+1)*cell))
        for strip in polygons(row):
            xa,_,xb,_ = strip.bounds
            for ix in range(math.floor(xa/cell), math.ceil(xb/cell)):
                piece = strip.intersection(box(ix*cell,iy*cell,(ix+1)*cell,(iy+1)*cell))
                for p in polygons(piece):
                    for tri in constrained_delaunay_triangles(p).geoms:
                        yield list(tri.exterior.coords)[:3]


def mesh_region(name, regions, coll, step=8., skirts=False):
    """Constrained triangles preserve holes and limit grade interpolation.

    regions: (material, geometry, height[, opts]); opts may set 'step' (grid cell),
    'band' (an inner offset ring, m, so per-vertex gradients and graded shoulders
    resolve at the edge) and 'color' (x, y) -> (r, g, b) for the V9 ground mask.
    V9 validity: skirts only on the outer boundary of the combined footprint (V8
    emitted both sides of shared internal edges: 5,635 duplicate faces in
    Plaza_Paving), no repeated-vertex or zero-area faces, no duplicate faces.
    """
    verts, faces, mids, mats, idx, colfn = [], [], [], [], {}, {}
    seen = set()
    curb_work_area = Polygon(SV.PLOT).buffer(10).union(box(-24,280,24,345)) if name == 'Road_Curb_Edges' else None
    def vid(x, y, z, cf=None):
        # Blender stores float32 coordinates. Merge at that same precision,
        # otherwise distinct Python keys become coincident native vertices.
        key = tuple(Vector((round(x,5),round(y,5),round(z,5))))
        if key not in idx:
            idx[key] = len(verts)
            verts.append(key)
            if cf is not None:
                colfn[idx[key]] = cf
        return idx[key]
    def emit(face, mi):
        uniq = []
        for v in face:
            if v not in uniq:
                uniq.append(v)
        if len(uniq) < 3:
            return
        if len(uniq) == 3:
            a,b,c = (Vector(verts[v]) for v in uniq)
            if (b-a).cross(c-a).length_squared == 0.:
                return
        k = frozenset(uniq)
        if k in seen:
            return
        seen.add(k)
        faces.append(tuple(uniq))
        mids.append(mi)
    outer_edge = None
    if skirts:
        from shapely.prepared import prep
        from shapely.geometry import MultiPolygon
        footprint = MultiPolygon(list(polygons(union_all([p for _, g, *_ in regions for p in polygons(g)]))))
        outer_edge = prep(footprint.boundary.buffer(2e-4))
    for region in regions:
        mat, geom, height = region[:3]
        opts = region[3] if len(region) > 3 else {}
        if geom.is_empty:
            continue
        cf = opts.get('color')
        if mat in mats:
            mi = mats.index(mat)
        else:
            mi = len(mats)
            mats.append(mat)
        rstep = opts.get('step', step)
        batches = [(geom,opts.get('band'),name != 'Road_Curb_Edges')]
        if name.startswith('Road_Network_'):
            # Preserve the existing tessellation on the gate threshold and
            # distant public streets. Only the campus road interior needs the
            # new triangulation; no alignments or class boundaries move.
            campus = box(-608,-768,632,464).difference(box(-24,272,24,352))
            batches = [(geom.intersection(campus),1.8,False),
                       (geom.difference(campus),opts.get('band'),True)]
        elif name == 'Road_Curb_Edges':
            threshold = box(-12,304,12,352)
            batches = [(geom.difference(threshold),None,False), (geom.intersection(threshold),None,True)]
        elif name == 'Plaza_Paving':
            campus = box(-608,-768,632,464)
            batches = [(geom.intersection(campus),None,False), (geom.difference(campus),None,True)]
        for shape,w,legacy in batches:
            pieces = []
            for poly in polygons(shape):
                if w:
                    core = poly.buffer(-w, quad_segs=2)
                    pieces.extend(polygons(make_valid(poly.difference(core))))
                    pieces.extend(polygons(core))
                else:
                    pieces.append(poly)
            for poly in pieces:
                cell = 50000. if poly.area > 1e8 else rstep
                keep_grid = legacy or (curb_work_area is not None and poly.disjoint(curb_work_area))
                triangulate = grid_triangles if keep_grid else region_triangles
                for coords in triangulate(poly, cell):
                    a, b, c = coords
                    area2 = (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
                    if abs(area2) < 2e-8:
                        continue
                    if area2 < 0:
                        coords.reverse()
                    emit(tuple(vid(x, y, height(x, y), cf) for x, y in coords), mi)
    if skirts:
        # Use the actual triangulation boundary: separately resampled skirts
        # left T junctions and doubled-back curb outlines at grid intersections.
        boundary = {}
        for face, mi in zip(faces, mids):
            for a, b in zip(face, face[1:] + face[:1]):
                key = tuple(sorted((a, b)))
                if key in boundary:
                    boundary[key] = None
                else:
                    boundary[key] = (a, b, mi)
        for edge in boundary.values():
            if edge is None:
                continue
            a, b, mi = edge
            x,y,_ = verts[a]; u,v,_ = verts[b]
            if outer_edge.contains(Point((x+u)/2, (y+v)/2)):
                emit((b,a,vid(x,y,datum(x,y)-.12),vid(u,v,datum(u,v)-.12)),mi)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    for m in mats:
        me.materials.append(m)
    for f, mi in zip(me.polygons, mids):
        f.material_index = mi
    if colfn:
        attr = me.color_attributes.new(MASK_ATTR, 'FLOAT_COLOR', 'POINT')
        data = [0., .5, 0., 1.] * len(verts)
        for i, fn in colfn.items():
            c = fn(verts[i][0], verts[i][1])
            data[4*i:4*i+len(c)] = c
        attr.data.foreach_set('color', data)
        me.color_attributes.active_color = attr
    me.update()
    if name in ('Road_Curb_Edges','Plaza_Paving'):
        # Rotate interior diagonals only; material boundaries, boundary
        # vertices and coverage remain fixed.
        bm = bmesh.new()
        bm.from_mesh(me)
        top = [f for f in bm.faces if f.normal.z > .9 and len(f.verts) == 3]
        tops = set(top)
        internal = [e for e in bm.edges if len(e.link_faces) == 2 and
                    all(f in tops for f in e.link_faces) and
                    e.link_faces[0].material_index == e.link_faces[1].material_index and
                    all(-608 <= v.co.x <= 632 and -768 <= v.co.y <= 464
                        for f in e.link_faces for v in f.verts)]
        bmesh.ops.beautify_fill(bm,faces=top,edges=internal,method='AREA')
        bm.to_mesh(me)
        bm.free()
        me.update()
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    obj['zc_vertical_datum'] = 'V5 estimated grading; see SOURCE_EVIDENCE.md'
    return obj

def g1_exterior_asphalt(obj, asphalt):
    """C01 (2017): asphalt outside G1, pavers inside the lane-gate plane.

    Split only triangles crossing that plane. Keep the existing road object,
    vertex heights, ground mask, road footprint and marking policy unchanged.
    The bounded window contains the two approach branches to Side Zewail Street.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    crosses = [f for f in bm.faces
               if min(v.co.y for v in f.verts) < SV.GATE_Y < max(v.co.y for v in f.verts)
               and all(-80. < v.co.x < 85. for v in f.verts)]
    if crosses:
        edges = sorted({e for f in crosses for e in f.edges}, key=lambda e: e.index)
        vertices = sorted({v for f in crosses for v in f.verts}, key=lambda v: v.index)
        bmesh.ops.bisect_plane(bm, geom=[*crosses, *edges, *vertices], dist=1e-7,
                              plane_co=(0., SV.GATE_Y, 0.), plane_no=(0., 1., 0.))
    if asphalt not in list(obj.data.materials):
        obj.data.materials.append(asphalt)
    mi = list(obj.data.materials).index(asphalt)
    area = 0.
    for f in bm.faces:
        c = f.calc_center_median()
        if -80. < c.x < 85. and SV.GATE_Y < c.y < 375.:
            f.material_index = mi
            area += f.calc_area()
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    obj['zc_g1_exterior_surface'] = 'C01 (2017): asphalt outside surveyed G1 lane-gate plane'
    print('[ground-waveC] G1 exterior asphalt', round(area, 3), 'm2; plane', SV.GATE_Y, flush=True)
    return obj


def profile_kerb(obj,road):
    """Sweep the precast profile along the accepted, shared top/skirt boundary.

    Dimensions are engineering estimates: road arris 30 mm at 45 degrees,
    10 mm face batter, back arris 6 mm wide by 10 mm deep. Tiny existing
    end facets and narrow cap components retain their accepted outline.
    """
    from collections import defaultdict
    me=obj.data
    verts=[v.co.copy() for v in me.vertices];faces=[tuple(f.vertices) for f in me.polygons]
    mids=[f.material_index for f in me.polygons]
    edge={}; skirt_edges=set()
    for f in me.polygons:
        if f.normal.z<.9:
            skirt_edges.update(tuple(sorted((a,b))) for a,b in
                               zip(f.vertices,tuple(f.vertices[1:])+tuple(f.vertices[:1])))
            continue
        for a,b in zip(f.vertices,tuple(f.vertices[1:])+tuple(f.vertices[:1])):
            k=tuple(sorted((a,b)))
            edge[k]=None if k in edge else (a,b)
    nxt={};prev={}
    for key,ab in edge.items():
        # The retained legacy gate grid has T junctions at batch seams.
        # They are internal to the kerb, never exposed arrises to bevel.
        if ab is not None and key in skirt_edges:
            a,b=ab;nxt[a]=b;prev[b]=a
    parts=[]
    for p in polygons(road):
        for ring in [p.exterior,*p.interiors]:
            co=list(ring.coords);parts.extend(LineString(co[i:i+17]) for i in range(0,len(co)-1,16))
    tree=STRtree(parts)
    parent=list(range(len(me.polygons)));areas=defaultdict(float);face_edges={};component={}
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for f in me.polygons:
        if f.normal.z<.9:continue
        for a,b in zip(f.vertices,tuple(f.vertices[1:])+tuple(f.vertices[:1])):
            key=tuple(sorted((a,b)))
            if key in face_edges:parent[root(f.index)]=root(face_edges[key])
            else:face_edges[key]=f.index
    for f in me.polygons:
        if f.normal.z>.9:
            areas[root(f.index)]+=f.area
            for i in f.vertices:component[i]=root(f.index)
    foot={};fronts={};small=0; params={}; original_verts=[v.copy() for v in verts]
    for i,j in nxt.items():
        if i not in prev:continue
        p=verts[i];a=p-verts[prev[i]];b=verts[j]-p;a.z=b.z=0
        if min(a.length,b.length)<.1 or a.normalized().dot(b.normalized())<math.cos(math.radians(15)) or areas[component[i]]<2.:
            small+=1;continue
        a.normalize();b.normalize()
        normal=Vector((-a.y-b.y,a.x+b.x,0))/(1+a.dot(b))
        # Keep collinear section stations on retained grid cuts. Sliding along
        # the same offset line changes tessellation, not the kerb profile.
        if a.dot(b)>1.-1e-8:
            if abs(p.y/4.-round(p.y/4.))<1e-6 and abs(a.y)>.5:
                normal=Vector((-1./a.y,0.,0.))
            elif abs(p.x/4.-round(p.x/4.))<1e-6 and abs(a.x)>.5:
                normal=Vector((0.,1./a.x,0.))
        q=Point(p.x,p.y)
        front=parts[int(tree.nearest(q))].distance(q)<.02
        # Road side: 30 mm bevel plus 10 mm face batter. Back: 6 mm x 10 mm arris.
        inset,drop,batter=(.03,.03,.01) if front else (.006,.01,0.)
        params[i]=(normal,inset,drop,batter,front)
    # Taper into very short rounded cap facets, without offset reversals or
    # crossing the narrow strips already present in the accepted mesh.
    strength={i:1. if i in params else 0. for i in nxt}
    for repeat in range(20):
        changed=False
        for i,j in nxt.items():
            length=(original_verts[i]-original_verts[j]).length
            limit=length*.5
            a,b=strength[i],strength.get(j,0.)
            if a>b+limit:strength[i]=b+limit;changed=True
            if b>a+limit:strength[j]=a+limit;changed=True
        if not changed:break
    for repeat in range(20):
        test=[p.copy() for p in original_verts]
        for i,(normal,inset,drop,batter,front) in params.items():
            s=strength[i]
            s=0. if s<.25 else max(.9,s)
            test[i]+=normal*((inset+batter)*s)
        bad=set()
        for f in me.polygons:
            if f.normal.z<.9:continue
            ids=list(f.vertices)
            if len(ids)!=3:continue
            a,b,c=[test[v] for v in ids];normal=(b-a).cross(c-a)
            if normal.z<=0 or normal.z/max(normal.length,1e-20)<.9:
                bad.update(i for i in ids if i in params and strength[i]>.0001)
        for i,j in nxt.items():
            if i not in prev:
                continue
            a,b=test[i]-test[prev[i]],test[j]-test[i]
            a.z=b.z=0.
            if min(a.length,b.length)>.4 and a.normalized().dot(b.normalized())<math.cos(math.radians(25)):
                bad.update(k for k in (prev[i],i,j) if k in params and strength[k]>.0001)
        if not bad:break
        for i in bad:strength[i]=0.
        for _ in range(8):
            for i,j in nxt.items():
                limit=(original_verts[i]-original_verts[j]).length*.5
                strength[i]=min(strength[i],strength.get(j,0)+limit)
                strength[j]=min(strength.get(j,0),strength[i]+limit)
    for i,(normal,inset,drop,batter,front) in params.items():
        s=strength[i]
        if s<.25:continue
        # Do not make a sub-10-mm sloped strip while tapering to a cap.
        s=max(.9,s)
        p=original_verts[i];fp=p+normal*(batter*s);fp.z-=drop*s
        foot[i]=len(verts);fronts[i]=front;verts.append(fp)
        verts[i]=p+normal*((batter+inset)*s)
    original=len(faces)
    for k in range(original):
        f=me.polygons[k]
        if f.normal.z>.9:continue
        face=list(faces[k])
        for n,i in enumerate(face):
            if i in foot:
                face[n]=foot[i]
        # Keep the toe on the unchanged road edge. A 10-micrometre height
        # bias avoids a float32 road/kerb ray-hit tie at their shared seam.
        for n,i in enumerate(face):
            p=verts[i]
            if p.z<datum(p.x,p.y) and any(fronts.get(j,False) for j in f.vertices):
                p.z=datum(p.x,p.y)+.06001
        faces[k]=tuple(face)
    for i,j in nxt.items():
        f=(j,i,foot.get(i,i),foot.get(j,j))
        f=tuple(dict.fromkeys(f))
        if len(f)>=3:faces.append(f);mids.append(0)
    mesh=bpy.data.meshes.new('Road_Curb_Edges_Profile');mesh.from_pydata(verts,[],faces)
    for mat in me.materials:mesh.materials.append(mat)
    for f,mi in zip(mesh.polygons,mids):f.material_index=mi
    mesh.update();obj.data=mesh
    obj['zc_kerb_profile']='ESTIMATED: 30 mm road chamfer; 10 mm batter; 6 x 10 mm back arris'
    obj['zc_kerb_profile_vertices']=len(foot)
    print('[ground-waveC] kerb profile vertices',len(foot),'preserved cap vertices',small,flush=True)
    return obj


# V10 junction geometry. V9 unioned the independent road ribbons, so the surface
# was already one disjoint mesh, but every junction kept the raw strip outline:
# square re-entrant corners, 0.25-1.25 m width steps where a 2.75-3.6 m road meets
# the 4.0 m ring, and curbs that simply stopped at the junction circle. Inside the
# existing junction zones the road outline is now closed with a kerb radius
# (morphological closing), and a curb return follows the new edge. Radius is a
# standard engineering ESTIMATE, not a survey of the built kerbs.
JUNCTION_RADIUS = 4.0
JUNCTION_MAX_FILL_M2 = 90.0  # 3 fills > 40 m2 inspected top-down in V10 (output/validation/v11/junctions/)


def junction_fillets(regions, road_names, M):
    from .site import junction_zones, roads as road_table
    zones = union_all([Point(x, y).buffer(r, quad_segs=16) for x, y, r in junction_zones(road_table())])
    report = {'radius_m': JUNCTION_RADIUS, 'fills': [], 'rejected': [], 'curb_return_m2': 0.0}
    all_road = union_all([g for m, g in regions.items() if m in road_names])
    new_edges = []
    for name in sorted(road_names):
        g = regions.get(name)
        if g is None or g.is_empty:
            continue
        closed = g.buffer(JUNCTION_RADIUS, quad_segs=12).buffer(-JUNCTION_RADIUS, quad_segs=12)
        fill = make_valid(closed.difference(g).intersection(zones))
        keep = []
        for piece in polygons(fill):
            if piece.area < .05:
                continue
            c = piece.representative_point()
            rec = {'material': name, 'x': round(c.x, 1), 'y': round(c.y, 1), 'area_m2': round(piece.area, 2)}
            # never bridge the approach median or fill a large enclosed area
            if piece.area > JUNCTION_MAX_FILL_M2 or (abs(c.x) < 4.0 and c.y > 60.0):
                report['rejected'].append(rec)
                continue
            keep.append(piece)
            report['fills'].append(rec)
        if keep:
            add = make_valid(union_all(keep).difference(all_road))
            regions[name] = make_valid(g.union(add))
            new_edges.append(add)
    if new_edges:
        road_now = union_all([g for m, g in regions.items() if m in road_names])
        # curb return: a 0.3 m kerb hugging the filleted edge, only where a fill was added
        near_fill = union_all(new_edges).buffer(1.2)
        ret = make_valid(road_now.buffer(.3, quad_segs=8).difference(road_now).intersection(near_fill).intersection(zones))
        cn = M['curb'].name
        regions[cn] = make_valid(regions.get(cn, Polygon()).union(ret))
        report['curb_return_m2'] = round(ret.area, 2)
    report['fill_total_m2'] = round(sum(f['area_m2'] for f in report['fills']), 2)
    print('[ground-v10] junction fillets', len(report['fills']), 'pieces', report['fill_total_m2'], 'm2;',
          len(report['rejected']), 'rejected; curb returns', report['curb_return_m2'], 'm2', flush=True)
    out = ROOT / 'output' / 'validation' / 'v11'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'junction_fillets.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
    return report


def rebuild(M, C):
    """Consume V4 survey surfaces before save/export, producing a disjoint V5 partition."""
    bpy.context.view_layer.update()
    foundations()
    # V15 pilot (G1 -> Administration corridor): evidence-based kerbs, beds, bands, feathered terrain.
    from . import v15_corridor as V15
    V15.create_materials(M)
    print('[ground-v5] collecting survey surfaces',flush=True)
    sources = [o for o in bpy.data.objects if o.type == 'MESH' and
               (o.name.startswith('Road_') or o.name in ('Parking_Lots','Plaza_Paving','Lawns','Academic_Public_Paving','Dorm_Garden_Surfaces','Rear_Compacted_Path','Photo_Context_Paving'))]
    raw, marking = {}, {}
    road_names = {M[k].name for k in ('asphalt','paver_road')}
    for o in sources:
        for mat, polys in top_regions(o).items():
            target = marking if 'Marking' in mat else raw
            target.setdefault(mat, []).extend(polys)
    regions = {m: union_all(ps) for m, ps in raw.items()}
    print('[ground-v5] surface unions ready',flush=True)
    junction_report = junction_fillets(regions, road_names, M)
    road = union_all([g for m,g in regions.items() if m in road_names])
    # V8: actual threshold surfaces, not stacked slabs. Five short gate aprons
    # and bounded internal gaps enter the same disjoint surface partition.
    from .v8_gates import ground_regions
    gate_aprons=ground_regions(road)
    regions[M['paver_road'].name]=regions.get(M['paver_road'].name,Polygon()).union(gate_aprons)
    # V9: a flush 0.2 m concrete edge restraint where the gate aprons meet soil (the
    # V8 aprons ended as bare slab edges); it is cut out of the apron, so disjoint.
    apron_edge=make_valid(gate_aprons.difference(gate_aprons.buffer(-.2)).difference(road.buffer(.05)))
    regions[M['paver_road'].name]=make_valid(regions[M['paver_road'].name].difference(apron_edge))
    regions[M['edge'].name]=regions.get(M['edge'].name,Polygon()).union(apron_edge)
    road=road.union(gate_aprons)
    trim_raised_beds(bpy.data.objects['Flower_Beds'],road)
    boundaries=[]
    for p in polygons(road):
        for ring in [p.exterior,*p.interiors]:
            pts=list(ring.coords)
            boundaries.extend(LineString(pts[i:i+17]) for i in range(0,len(pts)-1,16))
    tree=STRtree(boundaries)
    @lru_cache(maxsize=100000)
    def road_distance(x,y):
        p=Point(x,y)
        return boundaries[int(tree.nearest(p))].distance(p)
    plot = Polygon(SV.PLOT)
    # Short missing links are functional approximations, explicitly registered.
    connectors = [((0.,-117.88),(0.,-155.)), ((-16.3,100.),(-31.,60.)),
                  ((16.3,100.),(36.,60.))]
    link = union_all([LineString(p).buffer(1.5, cap_style='flat') for p in connectors])
    regions[M['paving'].name] = regions.get(M['paving'].name, Polygon()).union(link)
    # V11 (owner 05): footways that stop in sand are joined to the nearest hard surface.
    from . import v11_ground
    v11_hard = {M[k].name for k in ('paving','paving_light','plaza_grey','plaza_light','plaza_inlay','garden_paver','curb')} | set(road_names)
    v11_ground.extend_footways(regions, M, v11_hard)
    v11_ground.g1_lane_paving(regions, M)
    # Footway crossings and the two gate-loop crossing points remove obstructing curb ends.
    crossing = union_all([LineString(w['pts']).buffer(1.65) for w in SV.campus_footways()] +
        [box(-20, SV.PERIMETER_LOOP_Y-6, -13, SV.PERIMETER_LOOP_Y+6),
         box(13, SV.PERIMETER_LOOP_Y-6, 20, SV.PERIMETER_LOOP_Y+6)] +
        [LineString(p).buffer(1.65) for p in connectors])
    curb_name = M['curb'].name
    regions[curb_name] = regions.get(curb_name, Polygon()).difference(crossing.union(gate_aprons.buffer(.25)))
    # Avoid paving/lawn through building walls: terrain remains underneath foundations.
    from . import dormitory
    footprints = union_all([Polygon(v['pts']).buffer(0) for k,v in SV.OSM['buildings'].items() if not k.startswith('east_pair_')]+[dormitory.SHELL])
    public_court=None
    if bpy.data.objects['AB_Academic_Building'].get('zc_public_route_v5'):
        from .academic_public import public_ground_mask
        public_court=public_ground_mask()
        footprints=footprints.difference(public_court)
    bed = union_all([g for ps in top_regions(bpy.data.objects['Flower_Beds']).values() for g in ps])
    paving_names={M[k].name for k in ('paving','paving_light','plaza_grey','plaza_light','plaza_inlay','garden_paver')}
    road_names=set(road_names)
    order = [M[k].name for k in ('asphalt','paver_road','curb','plaza_inlay','plaza_grey','plaza_light','garden_paver','paving','paving_light',
                                'groundcover','grass','planted_soil','soil')]
    occupied, built, partition = Polygon(), [], []
    for mat in order + [n for n in regions if n not in order]:
        if mat not in regions:
            continue
        g = make_valid(regions[mat]).difference(occupied)
        if mat not in road_names:
            g = g.difference(bed)
        # Keep measured apron geometry outside footprints, no tiled overlay on foundations.
        if mat in paving_names:
            g = g.difference(footprints)
        if g.is_empty:
            continue
        occupied = occupied.union(g)
        partition.append((mat, g))
    # V11 (owner 03/12/15): enclosed sand slivers between hard surfaces become paving.
    partition, occupied = v11_ground.close_slivers(partition, occupied, bed, footprints, M, v11_hard)
    partition = v11_ground.repair_curb_runs(partition, M)
    partition, occupied = v11_ground.g1_shoulders(partition, occupied, bed, footprints, M)
    # Rounded curb tips can fill a hairline gap formerly assigned to terrain.
    # Recompute occupancy so the terrain mesh remains disjoint there too.
    occupied = union_all([g for _, g in partition])
    # V7: concrete edge restraint where unit paving meets soil/planting (standard for
    # interlocking/slab paving; P07/P11 show paving ending at earth/beds). It is cut out
    # of the paving itself, flush, so the partition stays disjoint.
    hard_names = set(paving_names) | {curb_name} | road_names
    hard = union_all([g for m, g in partition if m in hard_names])
    edges = []
    for i, (mat, g) in enumerate(partition):
        if mat not in paving_names:
            continue
        others = union_all([h for m, h in partition if m in hard_names and m != mat] + [footprints])
        band = g.difference(g.buffer(-.16, join_style='mitre')).difference(others.buffer(.25))
        band = make_valid(band)
        if band.area < .01:
            continue
        partition[i] = (mat, make_valid(g.difference(band)))
        edges.append(band)
    if edges:
        partition.append((M['edge'].name, make_valid(union_all(edges))))
        paving_names = paving_names | {M['edge'].name}
    partition = V15.adjust_partition(partition, M)
    band_name, bed_names = M['v15_band'].name, {M['v15_bed'].name, M['v15_median'].name}
    band_geom = union_all([g for m, g in partition if m == band_name])
    partition_mesh = [(m, g) for m, g in partition if m != band_name]
    # V11 (owner 05): no tree trunk on a walk, plaza, road or curb.
    v11_ground.relocate_trees(make_valid(union_all([g for m, g in partition if m in paving_names or m in road_names or m == curb_name])))
    v11_ground.write_log()
    # V7: graded shoulders. V6 left 0.18-0.20 m vertical paving/curb/foundation faces
    # above level soil and lawn; real landscaping is filled up to just below the hard
    # edge. Vertices within 1.6 m (soil) / 1.2 m (lawn) of a raised edge are lifted.
    raised = union_all([g for m, g in partition if m in paving_names or m == curb_name or m in bed_names] + [footprints]).difference(apron_edge.buffer(.05))  # V9: flush apron edges are not raised
    rb = []
    for poly in polygons(raised):
        for ring in [poly.exterior, *poly.interiors]:
            pts = list(ring.coords)
            rb.extend(LineString(pts[i:i+17]) for i in range(0, len(pts)-1, 16))
    rtree = STRtree(rb)
    @lru_cache(maxsize=400000)
    def raised_distance(x, y):
        q = Point(x, y)
        return rb[int(rtree.nearest(q))].distance(q)
    def shoulder(x, y, width, lift):
        d = raised_distance(x, y)
        return 0. if d >= width else lift * (1. - smooth(d / width))
    # ---- V9: graded flush road edges, estimated micro-relief and the ground mask.
    # V8 left soil 4.8 cm (lawn 2.8 cm) below the road surface with no edge face, so
    # every road and gate apron read as a floating slab at eye height. Soil is now
    # graded up to the finished road level at the edge (0 cm step), fading over 1.6 m.
    def road_lift(x, y, width, lift):
        d = road_distance(x, y)
        return 0. if d >= width else lift * (1. - smooth(d / width))
    terrain = plot.difference(occupied.union(bed))
    planted_geom = union_all([g for m, g in partition if m == M['planted_soil'].name])
    outer_all = box(-1800,-1800,1800,1800).difference(plot.union(occupied).union(bed))
    near = plot.buffer(450.)
    outer_near = make_valid(outer_all.intersection(near))
    outer_far = make_valid(outer_all.difference(near))
    zone = make_valid(union_all([terrain, planted_geom, outer_near]))
    zone_prep, plot_prep = prep(zone), prep(plot)
    def segments(geom):
        out = []
        for poly in polygons(geom):
            for ring in [poly.exterior, *poly.interiors]:
                pts = list(ring.coords)
                out.extend(LineString(pts[i:i+17]) for i in range(0, len(pts)-1, 16))
        return out
    zseg = segments(zone); ztree = STRtree(zseg)
    vseg = segments(footprints) + [LineString(list(plot.exterior.coords))]; vtree = STRtree(vseg)
    @lru_cache(maxsize=800000)
    def zone_distance(x, y):
        q = Point(x, y)
        return zseg[int(ztree.nearest(q))].distance(q)
    @lru_cache(maxsize=800000)
    def vertical_distance(x, y):
        q = Point(x, y)
        return vseg[int(vtree.nearest(q))].distance(q)
    from mathutils import noise as _noise
    def _n(x, y, f, seed):
        return _noise.noise(Vector((x * f + seed * 17.13, y * f - seed * 9.31, seed * 3.7)), noise_basis='PERLIN_ORIGINAL')
    @lru_cache(maxsize=800000)
    def relief(x, y):
        """ESTIMATED sub-decimetre undulation (no DEM). Zero within 1.5 m of every
        road, paving, wall, building, bed and lawn edge; full beyond 12 m."""
        q = Point(x, y)
        if not zone_prep.contains(q):
            return 0.
        m = smooth((zone_distance(x, y) - 1.5) / 10.5)
        if m <= 0.:
            return 0.
        if plot_prep.contains(q):
            n = .11 * _n(x, y, 1/38., 1) + .035 * _n(x, y, 1/13., 2)
        else:
            n = .22 * _n(x, y, 1/90., 3) + .065 * _n(x, y, 1/30., 4)
        return m * n
    def mask_zone(x, y):
        r = 1. - smooth(zone_distance(x, y) / 1.4)
        amp = .14 if plot_prep.contains(Point(x, y)) else .28
        g = .5 + .5 * max(-1., min(1., relief(x, y) / amp))
        b = 1. - smooth(vertical_distance(x, y) / 1.2)
        return (r, g, b)
    zone_core_v15 = V15.ZONE.buffer(-6.)
    def mask_road(x, y):
        # V15 (pilot zone): a narrower kerb-side sand margin (V14's 0.9 m fringe read as a blur),
        # faded into the legacy fringe over 6 m at the zone edge so there is no seam.
        d = road_distance(x, y)
        old = 1. - smooth(d / .9)
        q = Point(x, y)
        if not V15.ZONE.contains(q):
            return (old, .5, 0.)
        k = smooth(V15.ZONE.exterior.distance(q) / 6.) if not zone_core_v15.contains(q) else 1.
        new = .8 * (1. - smooth(d / .5))
        return (old + (new - old) * k, .5, 0.)
    # Resolve the three audited lawn/footway steps locally. Preserve the
    # established planting and bed-edge levels everywhere else.
    grade_zones = union_all([box(8,-128,48,-104), box(264,-360,288,-336), box(0,-560,32,-536)])
    grade_prep = prep(grade_zones)
    @lru_cache(maxsize=100000)
    def lawn_shoulder(x,y):
        base = shoulder(x,y,1.2,.14)
        q = Point(x,y)
        if not grade_prep.contains(q):
            return base
        blend = smooth(grade_zones.boundary.distance(q)/4.)
        return base + blend*(shoulder(x,y,2.4,.16)-base)
    # Remove old overlapping ribbons only after their complete footprint has been captured.
    for o in sources + [bpy.data.objects['Ground_Desert_Sand'], bpy.data.objects['Ground_Campus_Plot']]:
        bpy.data.objects.remove(o, do_unlink=True)
    pave_regions, lawn_regions = [], []
    bed_z, bed_col = V15.bed_height(datum), V15.bed_mask()
    feather = V15.feather_fn(terrain, [planted_geom, union_all([g for m, g in partition if m == M['grass'].name])])
    fz = V15.FEATHER_ZONE.buffer(V15.FEATHER_FADE)
    def mask_zone4(x, y):
        return (*mask_zone(x, y), feather(x, y))
    def mask_lawn4(x, y):
        return (0., .5, 0., feather(x, y))
    for mat, g in partition_mesh:
        print('[ground-v5] meshing',mat,flush=True)
        material = bpy.data.materials[mat]
        if mat in road_names:
            nm = 'Road_Network_External' if mat == M['asphalt'].name else 'Road_Network_Internal'
            rr = [(material,g,lambda x,y: datum(x,y)+.06,{'band':.9,'color':mask_road})]
            if mat == M['paver_road'].name and not band_geom.is_empty:
                # V15: crossover bands, same level and mask as the carriageway (C02).
                rr.append((M['v15_band'],band_geom,lambda x,y: datum(x,y)+.06,{'band':.9,'color':mask_road}))
            obj = mesh_region(nm, rr, C['roads'], step=8)
            if mat == M['paver_road'].name:
                g1_exterior_asphalt(obj, M['asphalt'])
            built.append(obj)
        elif mat == curb_name:
            kerb=mesh_region('Road_Curb_Edges', [(material,g,lambda x,y: datum(x,y)+.23)],
                             C['roads'], step=4, skirts=True)
            # V14 (regression V11GateCoverage G6): the precast profile is VISUAL. The player
            # controller's kerb step-up is tuned to the vertical V13 kerb face; on the 45 deg
            # chamfer it stalled. Keep the unprofiled box kerb as a collision-only proxy
            # (hidden from render; build_game_assets uses it for COL_Ground, export_glb strips
            # *_Collision_Proxy objects).
            kerb_box=bpy.data.objects.new('Kerb_Box_Collision_Proxy',kerb.data.copy())
            kerb_box.data.name='Kerb_Box_Collision_Proxy';kerb_box.matrix_world=kerb.matrix_world.copy()
            for coll in kerb.users_collection:coll.objects.link(kerb_box)
            kerb_box.hide_render=True;kerb_box.display_type='WIRE';kerb_box['zc_collision']=True
            kerb_box['zc_collision_proxy_for']='Road_Curb_Edges'
            built.append(profile_kerb(kerb,road))
            # V15: modular precast units replace the extruded visual kerb inside the pilot zone.
            units, unit_fp = V15.build_kerb_units(g, road, datum, material, C['roads'])
            V15.trim_profiled_kerb(kerb, unit_fp)
            if units is not None:
                built.append(units)
        elif mat in paving_names:
            def paving_z(x,y):
                from . import dormitory
                if dormitory.PATH.covers(Point(x,y)):
                    return dormitory.height(x,y)
                if public_court and public_court.covers(Point(x,y)):
                    rear=smooth((-y-348.)/17.) if y < -348. else 0.
                    return datum(x,y)+.21*(1.-rear)+.012*rear
                return datum(x,y)+.06+.15*smooth(road_distance(x,y)/2.4)
            pave_regions.append((material,g,paving_z))
        elif mat in bed_names:
            lawn_regions.append((material,g,bed_z,{'step':1.5,'band':.5,'color':bed_col}))
        elif mat==M['compacted'].name:
            lawn_regions.append((material,g,lambda x,y:datum(x,y)+.012+max(shoulder(x,y,1.6,.15),road_lift(x,y,1.6,.048)),{'band':1.2}))
        else:
            planted = mat == M['planted_soil'].name
            def lawn_z(x,y,planted=planted):
                return datum(x,y)+.032+max(lawn_shoulder(x,y),road_lift(x,y,1.2,.028))+(relief(x,y) if planted else 0.)
            original_opts = {'step':5.,'band':1.2,'color':mask_zone4} if planted else {'color':mask_lawn4}
            local_opts = {'step':5.,'band':2.4}
            local_opts['color'] = mask_zone4 if planted else mask_lawn4
            # V15: denser grid inside the feathered corridor so the soft transitions resolve.
            fine_opts = dict(original_opts, step=2.5, band=1.2)
            outside = g.difference(grade_zones)
            lawn_regions.append((material,outside.difference(fz),lawn_z,original_opts))
            lawn_regions.append((material,outside.intersection(fz),lawn_z,fine_opts))
            graded = g.intersection(grade_zones)
            lawn_regions.append((material,graded.difference(fz),lawn_z,local_opts))
            lawn_regions.append((material,graded.intersection(fz),lawn_z,dict(local_opts, step=2.5)))
    if public_court:
        court=[(m,g.intersection(public_court),h) for m,g,h in pave_regions]
        pave_regions=[(m,g.difference(public_court),h) for m,g,h in pave_regions]
        built.append(mesh_region('Plaza_Academic_Courtyard',court,C['academic_court'],step=3,skirts=True))
    built.append(mesh_region('Plaza_Paving', pave_regions, C['roads'], step=3, skirts=True))
    built.append(mesh_region('Lawns', lawn_regions, C['veg_lawns'], step=8))
    # Retain evidence-based external lane markings; trim all at actual junctions.
    from .site import roads, junction_zones
    exclusions = union_all([Point(x,y).buffer(r) for x,y,r in junction_zones(roads())])
    for mat, ps in marking.items():
        g = union_all(ps).intersection(road).difference(exclusions)
        # V7: 12 mm above asphalt (V6: 4 mm, which can depth-fight at range in real time).
        built.append(mesh_region('Road_Markings_'+mat, [(bpy.data.materials[mat],g,lambda x,y:datum(x,y)+.072)],
                                 C['roads'], step=8))
    print('[ground-v5] meshing graded terrain',flush=True)
    plot_z = lambda x,y:datum(x,y)+.012+max(shoulder(x,y,1.6,.16),road_lift(x,y,1.6,.048))+relief(x,y)
    built.append(mesh_region('Ground_Campus_Plot', [(M['soil_light'],terrain.difference(fz),plot_z,
                    {'step':5.,'band':1.6,'color':mask_zone4}),
                    (M['soil_light'],terrain.intersection(fz),plot_z,{'step':2.5,'band':1.6,'color':mask_zone4})],
                    C['ground'], step=12))
    # A finite, graded near-field connects to the distant desert without a stacked campus plane.
    # V9: the 450 m band around the wall is meshed at 10 m for the estimated relief.
    horizon = box(-25000,-25000,25000,25000).difference(box(-1800,-1800,1800,1800))
    built.append(mesh_region('Ground_Desert_Sand', [
                    # V11 (QA defect 5): sand is graded up to raised apron/paving edges like the
                    # plot soil (V5-V10: 0.198 m bare paving face against the desert sand at G1).
                    (M['sand'],outer_near.difference(fz),lambda x,y:datum(x,y)+.012+max(shoulder(x,y,1.6,.16),road_lift(x,y,1.6,.048))+relief(x,y),
                     {'step':10.,'band':1.6,'color':mask_zone4}),
                    (M['sand'],outer_near.intersection(fz),lambda x,y:datum(x,y)+.012+max(shoulder(x,y,1.6,.16),road_lift(x,y,1.6,.048))+relief(x,y),
                     {'step':2.5,'band':1.6,'color':mask_zone4}),
                    (M['sand'],outer_far,lambda x,y:datum(x,y)+.012+road_lift(x,y,1.6,.048)),
                    (M['sand'],horizon,lambda x,y:.012)], C['ground'], step=60))
    # Site assets share the datum; architecture stays rigid on level pads.
    for o in bpy.data.objects:
        if o in built or o.type != 'MESH' or o.parent:
            continue
        if o.get('zc_terrain_following_v8'):
            continue
        if o.name.startswith(('AB_', 'Perimeter_')) or o.name in ('Flower_Beds','Pergola_Admin_Side'):
            meshes = [o, *list(o.children)]
            for child in meshes:
                if child.type != 'MESH':
                    continue
                # Detailed masonry remains rigid; pads are level at every building.
                if o.name.startswith('AB_'):
                    continue
                inv = child.matrix_world.inverted()
                for v in child.data.vertices:
                    w = child.matrix_world @ v.co
                    w.z += datum(w.x,w.y)
                    v.co = inv @ w
        elif any(c.name in ('Palms','Trees','Shrubs','Site_Furniture','Optional_Vehicles_Disabled') for c in o.users_collection):
            # V9: planting on soil follows the estimated relief as well.
            o.location.z += datum(o.location.x,o.location.y)+relief(o.location.x,o.location.y)
    # Topological checks independent of the emitted mesh count.
    gaps=[]
    for name,r in roads().items():
        misses=[list(p) for p in r['pts'] if road.distance(Point(p.x,p.y)) > .02]
        if misses:
            gaps.append({'road':name,'misses':misses[:5]})
    overlap=sum(a.intersection(b).area for i,(_,a) in enumerate(partition) for _,b in partition[i+1:])
    cover=terrain.union(occupied).union(bed)
    report={'phase':'A', 'datum':'ESTIMATED, no DEM; 0.08% longitudinal / 0.02% crossfall; level pads',
            'plot_area_m2':plot.area, 'road_area_m2':road.area, 'surface_overlap_m2':overlap,
            'plot_uncovered_m2':plot.difference(cover).area, 'centreline_gaps':gaps,
            'surface_regions':{m:round(g.area,3) for m,g in partition},
            'estimated_pedestrian_links':connectors,
            'v7_edge_restraint_m2':round(sum(e.area for e in edges),2),
            'v7_shoulders':'soil +0.16 m over 1.6 m, lawn/planting +0.14 m over 1.2 m, toward raised paving/curb/foundation edges (ESTIMATED grading)',
            'v9_relief':{'status':'ESTIMATED, no DEM','inside_wall':'<=0.11 m @38 m + 0.035 m @13 m','outside_wall':'<=0.22 m @90 m + 0.065 m @30 m, within 450 m',
                         'fade':'0 within 1.5 m of every road/paving/wall/building/bed/lawn edge, full beyond 12 m',
                         'zone_m2':round(zone.area,1),'sampled_max_abs_m':round(max(abs(relief(x,y)) for x in range(-600,601,7) for y in range(-900,700,7)),4)},
            'v9_road_edges':'soil graded flush with road surface at the edge (was 4.8 cm below), lawn/planting flush (was 2.8 cm), 1.6/1.2 m fade',
            'v9_apron_edge_restraint_m2':round(apron_edge.area,2),
            'all_topology_checks_pass':not gaps and overlap < .001 and plot.difference(cover).area < .001}
    out=ROOT/'output/validation/v11'
    out.mkdir(parents=True,exist_ok=True)
    (out/'ground_topology.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    samples=[]
    for name,r in roads().items():
        for p in r['pts'][::2]:
            samples.append({'road':name,'godot':[p.x,datum(p.x,p.y)+.06,-p.y]})
    (out/'road_floor_samples.json').write_text(json.dumps(samples),encoding='utf-8')
    V15.LOG['topology'] = {k: report[k] for k in ('surface_overlap_m2','plot_uncovered_m2','all_topology_checks_pass')}
    V15.write_log()
    if not report['all_topology_checks_pass']:
        raise RuntimeError('V5 surface topology failed; see ground_topology.json')
    print('[ground-v5]',json.dumps({k:report[k] for k in ('road_area_m2','surface_overlap_m2','plot_uncovered_m2')}))
