"""Build the game-ready campus from the authoritative scene.

The architectural scene (output/Zewail_City_3D.blend) is opened read-only. Every
change below happens in memory and is saved to a separate file, so the
authoritative scene is never optimised destructively.

Usage (from the project root):
    blender -b output/Zewail_City_3D.blend --python src/build_game_assets.py

Outputs (output/game_ready/):
    Zewail_City_Game.blend        game scene with the Game_* collections
    campus_full.glb               complete map: render meshes, collision proxies, markers
    buildings/BLD_*.glb           each building alone, origin at its footprint centre
    assets/*.glb                  each vegetation / prop asset at the origin
    textures/*.png                baked albedo + normal tiles (world-scale UVs)
    campus_manifest.json          object list, triangle counts, spawns, landmarks, conventions

Conventions (see docs/GAME_ASSET_GUIDE.md):
    BLD_*  building render mesh (shell + glass + details merged, bevels applied)
    RD_*   road surface, SW_* sidewalks / curbs / plazas, TER_* terrain
    VEG_*  vegetation instance (shared mesh), PROP_* prop instance (shared mesh)
    COL_*-colonly  collision-only proxy (Godot imports it as StaticBody3D + trimesh)
    SPAWN_* / LM_*  empties for spawn points and landmarks
"""
import json
import hashlib
import math
import os
import sys
import time

import bmesh
import bpy
from mathutils import Matrix, Vector

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SRC)
sys.path.insert(0, SRC)

from utilities import game_points, scene_setup  # noqa: E402

OUT = os.path.join(ROOT, "output", "game_ready")
TEX = os.path.join(OUT, "textures")
BLD_DIR = os.path.join(OUT, "buildings")
ASSET_DIR = os.path.join(OUT, "assets")
GAME_BLEND = os.path.join(OUT, "Zewail_City_Game.blend")
GODOT_CAMPUS = os.path.join(ROOT, "game", "godot", "assets", "campus")

GAME_COLLS = ["Game_Terrain", "Game_Roads", "Game_Sidewalks", "Game_Administration", "Game_Academic",
              "Game_Institutes", "Game_Gate", "Game_Vegetation", "Game_Props", "Game_Collision", "Game_Landmarks",
              "Game_Spawn_Points"]

BUILDINGS = {
    "AB_Administration_Cultural_Building": ("BLD_Administration_Cultural", "Game_Administration"),
    "AB_Academic_Building": ("BLD_Academic", "Game_Academic"),
    "AB_Helmy_Institute_Medical_Sciences": ("BLD_Helmy_Institute", "Game_Institutes"),
    "AB_East_Research_Institute_Nano": ("BLD_East_Research_Institute", "Game_Institutes"),
    # V4
    "AB_Main_Gate_Complex": ("BLD_Main_Gate", "Game_Gate"),
    "Perimeter_Wall": ("BLD_Perimeter_Wall", "Game_Gate"),
    "AB_East_Residential_Pair_Estimated": ("BLD_East_Residential_Estimated", "Game_Institutes"),
}
from utilities.gate_inventory import RECORDS as GATE_RECORDS
for record in GATE_RECORDS[1:]:
    BUILDINGS[record['object']]=('BLD_Gate_'+record['id']+'_Provisional','Game_Gate')
SIDEWALK_MATS = {"M_V7_Paving_Edge_Restraint", "M_Paving_Limestone", "M_Paving_Light", "M_Concrete_Curb", "M_V6_Plaza_Grey", "M_V6_Plaza_Light", "M_V6_Plaza_Inlay", "M_V6_Garden_Pavers"}
MARKING_MATS = {"M_Road_Marking_White", "M_Road_Marking_Yellow"}

# Bake orientation: wall materials are baked on a vertical (XZ) plane so the panel
# grid of M_Stone_Cladding (projected on (x + y, z)) shows its rows.
VERTICAL = {"M_Stone_Cladding", "M_Stone_White", "M_Stone_Beige", "M_Granite_Band", "M_Copper_Drum",
            "M_Palm_Trunk", "M_Tree_Bark", "M_Concrete_Curb", "M_Wood_Pergola",
            "M_Gate_Sandstone_Tiles", "M_Ledgestone_Dark", "M_Stucco_Ochre"}
# Tile sizes in metres. Brick-based materials use a multiple of their pattern period
# so the tile is seamless; noise-based ones are made seamless after baking.
BRICK_TILE = {"M_Stone_Cladding": 4.8, "M_Paving_Limestone": 3.6, "M_Paving_Light": 4.8, "M_Solar_Panel": 4.0,
              "M_Gate_Sandstone_Tiles": 4.8, "M_Ledgestone_Dark": 2.4, "M_Paver_Road_Grey": 2.2}
BRICK_TILE.update({'M_V6_Plaza_Grey':3.6,'M_V6_Plaza_Light':3.6,'M_V6_Garden_Pavers':2.2})
BRICK_TILE['M_V6_Residential_Stone']=4.8
VERTICAL.add('M_V6_Residential_Stone')
SMALL_TILE = {"M_V7_Paving_Edge_Restraint": 2.0, "M_Granite_Band": 3.0, "M_Wood_Pergola": 2.0, "M_Concrete_Curb": 2.0, "M_White_Pebbles": 2.0,
              "M_Dark_Gravel": 2.0, "M_Granite_Dark": 3.0, "M_Palm_Trunk": 2.0, "M_Tree_Bark": 2.0,
              "M_Planter_Soil": 2.0, "M_Red_Mulch": 2.0, "M_Groundcover_Planted": 3.0}
HIRES = {"M_Stone_Cladding", "M_Paving_Limestone", "M_Paving_Light", "M_Asphalt", "M_Grass_Lawn",
         "M_Desert_Sand", "M_Graded_Campus_Soil", "M_Roof_Membrane", "M_Concrete_Curb",
         "M_Gate_Sandstone_Tiles", "M_Paver_Road_Grey", "M_Stucco_Ochre"}
DEFAULT_TILE = 6.0

COLLISION_LAYERS = {
    1: "world_static (terrain, roads, buildings, props)",
    2: "player",
    3: "dynamic_props (future)",
    4: "npc (future)",
    5: "vehicles (future)",
    6: "interactables (future: doors, info points)",
    7: "triggers (landmark areas)",
}


def log(*a):
    print("[game]", *a, flush=True)


def tris_of(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def link_only(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)


# --------------------------------------------------------------------------- scene prep
def strip_scene():
    """Drop what the game build does not ship: proposals, cameras, lights."""
    for cname in ("Unverified_Masterplan_Proposals", "Cinematic_Paths", "Cameras", "Lighting",
                  "Optional_Vehicles_Disabled"):  # V10: vehicles never ship in the realistic export
        c = bpy.data.collections.get(cname)
        if not c:
            continue
        for o in list(c.all_objects):
            bpy.data.objects.remove(o, do_unlink=True)
    for o in list(bpy.data.objects):
        if o.type in {'CAMERA', 'LIGHT'}:
            bpy.data.objects.remove(o, do_unlink=True)
    for vl in bpy.context.scene.view_layers:
        def walk(lc):
            lc.exclude = False
            for ch in lc.children:
                walk(ch)
        walk(vl.layer_collection)


def make_collections():
    sc = bpy.context.scene
    out = {}
    for name in GAME_COLLS:
        c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
        if c.name not in sc.collection.children:
            sc.collection.children.link(c)
        out[name] = c
    return out


# --------------------------------------------------------------------------- mesh helpers
def islands(bm):
    bm.faces.ensure_lookup_table()
    seen, out = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        seen.add(f.index)
        stack, isl = [f], []
        while stack:
            g = stack.pop()
            isl.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        out.append(isl)
    return out


def ground_parts_mesh(src_mesh, matrix, name, z_max=2.2, min_h=0.45):
    """World-space copy of the loose parts that start near the ground (columns,
    piers, frame legs, posts): obstacles a walking player must collide with."""
    bm = bmesh.new()
    bm.from_mesh(src_mesh)
    bm.transform(matrix)
    keep = set()
    for isl in islands(bm):
        co = [v.co for f in isl for v in f.verts]
        xs, ys, zs = [c.x for c in co], [c.y for c in co], [c.z for c in co]
        dims = sorted((max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))
        near_ground = min(zs) < z_max and dims[2] > min_h and (max(zs) - min(zs)) > min_h
        # large solid parts higher up (dome bands, drum, canopies, glass-box frames, rooftop plant):
        # thin mullions / fins / ribs are skipped
        bulky = dims[0] > 0.3 and dims[0] * dims[1] * dims[2] > 0.5
        if near_ground or bulky:
            keep.update(f.index for f in isl)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def join_meshes_world(parts, name):
    """parts: list of (mesh, matrix). Returns a world-space mesh (no materials)."""
    bm = bmesh.new()
    for me, mat in parts:
        tmp = me.copy()
        tmp.transform(mat)
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    out = bpy.data.meshes.new(name)
    bm.to_mesh(out)
    bm.free()
    out.materials.clear()
    return out


def drop_faces_with_mats(me, matnames):
    idx = {i for i, m in enumerate(me.materials) if m and m.name in matnames}
    if not idx:
        return
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in idx], context='FACES')
    bm.to_mesh(me)
    bm.free()


def collider_object(name, me, coll):
    me.name = name + "_mesh"
    o = bpy.data.objects.new(name + "-colonly", me)
    coll.objects.link(o)
    o.display_type = 'WIRE'
    o.hide_render = True
    return o


# --------------------------------------------------------------------------- buildings
def stair_collision_parts(obj):
    """Continuous walking proxy for real treads; visual stairs remain untouched.

    Capsule contact at repeated nosings launches the existing controller during
    sprint descent. A source-derived incline deviates by <= one 150 mm riser,
    retains the exact landing level, and keeps separate solid metal rails.
    """
    from utilities.geometry import MeshBuilder
    # Work in the source object's local frame so moving/rotating the editable
    # stair keeps its walking proxy aligned as well.
    mids={i for i,m in enumerate(obj.data.materials) if m and 'Metal' not in m.name}
    ids={v for f in obj.data.polygons if f.material_index in mids for v in f.vertices}
    co=[obj.data.vertices[i].co for i in ids]
    lo,hi=min(v.x for v in co),max(v.x for v in co)
    count=int(obj['zc_risers']);rise=float(obj['zc_riser_height_m']);tread=float(obj['zc_tread_m'])
    front=max(v.y for v in co);back=front-count*tread;top=max(v.z for v in co);base=top-count*rise
    mb=MeshBuilder();mat=obj.data.materials[0]
    bottom=min(v.z for v in co)
    v=[(lo,front,base),(hi,front,base),(hi,back,top),(lo,back,top),
       (lo,front,bottom),(hi,front,bottom),(hi,back,bottom),(lo,back,bottom)]
    mb.raw(mat,v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)])
    mb.box(mat,lo,back-3.,top-.21,hi,back,top)
    ramp=mb.to_mesh(obj.name+'_Walking_Proxy')
    rails=obj.data.copy()
    drop_faces_with_mats(rails,{m.name for m in rails.materials if m and 'Metal' not in m.name})
    return [(ramp,obj.matrix_world.copy()),(rails,obj.matrix_world.copy())]


def build_buildings(G):
    out = {}
    dg = bpy.context.evaluated_depsgraph_get()
    for src, (new, cname) in BUILDINGS.items():
        shell = bpy.data.objects[src]
        kids = list(shell.children)
        details = [k for k in kids if k.name.endswith("_Details") or k.get('zc_collision')]
        # collision: un-bevelled shell + ground-level detail parts (world space)
        parts = [(shell.data, shell.matrix_world.copy())]
        for d in details:
            if d.name.startswith('Academic_Stair_') and d.get('zc_risers'):
                parts.extend(stair_collision_parts(d))
            elif d.get('zc_collision'):
                # V10: includes collision-only proxies (hide_render), never merged for render
                parts.append((d.data,d.matrix_world.copy()))
            elif d.get('zc_no_ground_collision'):
                pass  # V10: a collision proxy object stands in for these details
            else:
                parts.append((ground_parts_mesh(d.data, d.matrix_world, d.name + "_gp"), Matrix.Identity(4)))
        col = collider_object("COL_" + new, join_meshes_world(parts, "COL_" + new), G["Game_Collision"])
        # V10: collision-only proxies never join the render mesh
        for k in [k for k in kids if k.hide_render and k.get('zc_collision')]:
            kids.remove(k)
            bpy.data.objects.remove(k, do_unlink=True)
        # render mesh: bevel applied, glass + details merged into the shell
        baked = bpy.data.meshes.new_from_object(shell.evaluated_get(dg))
        shell.modifiers.clear()
        shell.data = baked
        with bpy.context.temp_override(active_object=shell, object=shell, selected_objects=[shell] + kids,
                                       selected_editable_objects=[shell] + kids):
            bpy.ops.object.join()
        shell.name = new
        shell.data.name = new
        link_only(shell, G[cname])
        shell["zc_kind"] = "building"
        shell["zc_collider"] = col.name
        out[new] = (shell, col)
        log(f"{new}: {tris_of(shell.data)} tris, collider {tris_of(col.data)} tris")
    return out


# --------------------------------------------------------------------------- site
def build_site(G):
    created = {"roads": [], "sidewalks": [], "terrain": []}
    # V5: preserve the source graded desert and its campus cut-out exactly.
    old = bpy.data.objects.get("Ground_Desert_Sand")
    mat = old.data.materials[0] if old else None
    sand = old
    sand.name = "TER_Desert_Sand"
    link_only(sand, G["Game_Terrain"])
    created["terrain"].append(sand)
    for src, new in (("Ground_Campus_Plot", "TER_Campus_Plot"), ("Lawns", "TER_Lawns")):
        o = bpy.data.objects[src]
        o.name = new
        link_only(o, G["Game_Terrain"])
        created["terrain"].append(o)
    # roads: split sidewalks and curbs into SW_ objects
    for o in [o for o in bpy.data.objects if o.name.startswith("Road_") or o.name == "Parking_Lots"]:
        base = o.name.replace("Road_", "")
        if o.data.polygons and all(o.data.materials[f.material_index].name in SIDEWALK_MATS for f in o.data.polygons):
            o.name = 'SW_' + base
            link_only(o, G['Game_Sidewalks'])
            created['sidewalks'].append(o)
            continue
        o.name = "RD_" + base
        link_only(o, G["Game_Roads"])
        created["roads"].append(o)
        me = o.data
        idx = {i for i, m in enumerate(me.materials) if m and m.name in SIDEWALK_MATS}
        if not idx:
            continue
        sw_me = me.copy()
        for mesh, keep_sw in ((me, False), (sw_me, True)):
            bm = bmesh.new()
            bm.from_mesh(mesh)
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if (f.material_index in idx) != keep_sw],
                             context='FACES')
            bm.to_mesh(mesh)
            bm.free()
        sw = bpy.data.objects.new("SW_" + base, sw_me)
        sw.matrix_world = o.matrix_world
        G["Game_Sidewalks"].objects.link(sw)
        created["sidewalks"].append(sw)
    o = bpy.data.objects["Plaza_Paving"]
    o.name = "SW_Plaza_Paving"
    link_only(o, G["Game_Sidewalks"])
    created["sidewalks"].append(o)
    for o in [o for o in bpy.data.objects if o.name.startswith('Plaza_Academic_')]:
        o.name='SW_'+o.name
        link_only(o,G['Game_Sidewalks'])
        created['sidewalks'].append(o)
    o = bpy.data.objects["Flower_Beds"]
    o.name = "VEG_Flower_Beds_Static"
    link_only(o, G["Game_Vegetation"])
    o = bpy.data.objects["Pergola_Admin_Side"]
    o.name = "PROP_Pergola_Admin_Side"
    link_only(o, G["Game_Props"])
    return created


def classify_instances(G):
    veg, props = [], []
    counters = {}
    for o in list(bpy.data.objects):
        if o.type != 'MESH' or not o.users_collection:
            continue
        cn = {c.name for c in o.users_collection}
        if cn.intersection(("Palms", "Trees", "Shrubs")):
            kind, coll, lst = "VEG", G["Game_Vegetation"], veg
        elif 'Site_Furniture' in cn:
            kind, coll, lst = "PROP", G["Game_Props"], props
        else:
            continue
        key = o.data.name
        counters[key] = counters.get(key, 0) + 1
        o.name = f"{kind}_{key}_{counters[key]:04d}"
        link_only(o, coll)
        o["zc_asset"] = key
        lst.append(o)
    log(f"instances: vegetation {len(veg)}, props {len(props)}, unique meshes {len(counters)}")
    return veg, props


def prism_ring(bm, x, y, z0, z1, r, n=6):
    lo = [bm.verts.new((x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n), z0))
          for i in range(n)]
    hi = [bm.verts.new((v.co.x, v.co.y, z1)) for v in lo]
    for i in range(n):
        k = (i + 1) % n
        bm.faces.new((lo[i], lo[k], hi[k], hi[i]))
    bm.faces.new(list(reversed(lo)))
    bm.faces.new(hi)


def build_instance_colliders(G, veg, props):
    bm = bmesh.new()
    n_trunks = 0
    for o in veg:
        name = o.data.name.lower()
        if any(k in name for k in ("shrub", "hedge", "agave", "cactus", "euphorbia", "cycad", "groundcover")):
            continue
        s = float(o.get('zc_v12_original_collision_scale',o.scale.x))
        prism_ring(bm, o.location.x, o.location.y, o.location.z - 0.2, o.location.z + 3.0 * s, 0.22 * max(s, 0.6))
        n_trunks += 1
    me = bpy.data.meshes.new("COL_Vegetation_Trunks")
    bm.to_mesh(me)
    bm.free()
    trunks = collider_object("COL_Vegetation_Trunks", me, G["Game_Collision"])
    bm = bmesh.new()
    n_props = 0
    for o in props:
        name = o.data.name.lower()
        if "lamp" in name or "bollard" in name:
            r = 0.12 if "bollard" not in name else 0.1
            prism_ring(bm, o.location.x, o.location.y, o.location.z - 0.1, o.location.z + 4.0, r + 0.06)
        else:  # cars, benches: oriented bounding box
            corners = [o.matrix_world @ Vector(c) for c in o.bound_box]
            r = bmesh.ops.convex_hull(bm, input=[bm.verts.new(c) for c in corners])
            del r
        n_props += 1
    me = bpy.data.meshes.new("COL_Props")
    bm.to_mesh(me)
    bm.free()
    pg = bpy.data.objects["PROP_Pergola_Admin_Side"]
    pg_me = ground_parts_mesh(pg.data, pg.matrix_world, "pergola_gp")
    me2 = join_meshes_world([(me, Matrix.Identity(4)), (pg_me, Matrix.Identity(4))], "COL_Props")
    propcol = collider_object("COL_Props", me2, G["Game_Collision"])
    log(f"colliders: {n_trunks} trunks ({tris_of(trunks.data)} tris), {n_props} props ({tris_of(propcol.data)} tris)")
    return trunks, propcol


def simplify_planar(me, tile=48.0, angle_deg=0.1):
    """Merge near-coplanar faces tile by tile (one dissolve over the whole 340k-face
    ground ran >15 min). Vertices are welded at 1 mm inside each tile; tile seams
    keep coincident edges. Only faces within angle_deg of each other merge."""
    from collections import defaultdict
    groups = defaultdict(list)
    co = [v.co.copy() for v in me.vertices]
    for poly in me.polygons:
        c = poly.center
        groups[(math.floor(c.x / tile), math.floor(c.y / tile))].append(tuple(poly.vertices))
    verts, faces = [], []
    stats = {'tiles': 0, 'tiles_kept': 0}
    for key, polys in groups.items():
        bm = bmesh.new()
        vmap = {}
        for pv in polys:
            vs = []
            for i in pv:
                k = (round(co[i].x, 3), round(co[i].y, 3), round(co[i].z, 3))
                if k not in vmap:
                    vmap[k] = bm.verts.new(co[i])
                vs.append(vmap[k])
            if len(set(vs)) < 3:
                continue
            try:
                bm.faces.new(vs)
            except ValueError:
                pass
        bm.normal_update()      # new faces have no normals until updated; dissolve needs them
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(angle_deg), use_dissolve_boundaries=False,
                                 verts=list(bm.verts), edges=list(bm.edges))
        bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='BEAUTY')
        bm.verts.index_update()
        # Guard: every new triangle must lie on the original surface (centroid and three
        # inner edge points within 1 cm of an original face), else the tile is kept as is.
        from mathutils.bvhtree import BVHTree
        idx = {}
        tv, tf = [], []
        for pv in polys:
            f = []
            for i in pv:
                if i not in idx:
                    idx[i] = len(tv)
                    tv.append(co[i])
                f.append(idx[i])
            tf.append(f)
        tree = BVHTree.FromPolygons(tv, tf)
        ok = True
        for f in bm.faces:
            c = f.calc_center_median()
            vs = [v.co for v in f.verts]
            # Steep faces too: a curved curb side merged into one n-gon triangulates
            # across its chord. Every probe must lie within 1 cm of an original face.
            for q in [c] + [c.lerp((vs[k] + vs[(k + 1) % 3]) * 0.5, 0.85) for k in range(3)]:
                near = tree.find_nearest(q, 0.05)
                if near[0] is None or near[3] > 0.01:
                    ok = False
                    break
            if not ok:
                break
        base = len(verts)
        if not ok:
            stats['tiles_kept'] += 1
            for pv in polys:
                verts.extend(tuple(co[i]) for i in pv)
                faces.append(tuple(range(len(verts) - len(pv), len(verts))))
        else:
            verts.extend(tuple(v.co) for v in bm.verts)
            faces.extend(tuple(base + v.index for v in f.verts) for f in bm.faces)
        stats['tiles'] += 1
        bm.free()
    me.clear_geometry()
    me.from_pydata(verts, [], faces)
    me.update()
    log(f"ground collider tiles simplified {stats['tiles'] - stats['tiles_kept']}/{stats['tiles']} (surface guard kept {stats['tiles_kept']})")
    return stats


def build_ground_collider(G, site):
    parts = []
    # V5 partitions the terrain: lawns occupy real cut-outs and carry their own floor.
    # V14: the visual precast kerb profile is not walked on; collide with the unprofiled box
    # kerb (Kerb_Box_Collision_Proxy, built by ground_system) exactly as V13 did.
    kerb_proxy = bpy.data.objects.get("Kerb_Box_Collision_Proxy")
    for o in site['terrain'] + site["roads"] + site["sidewalks"] + [bpy.data.objects["VEG_Flower_Beds_Static"]]:
        if o.get('zc_visual_only'):
            # V15: precast kerb units are visual; their footprint collides via the box kerb proxy.
            log(f"ground collider: {o.name} is visual-only, not collided")
            continue
        src = kerb_proxy if (kerb_proxy is not None and o.name == "SW_Curb_Edges") else o
        tmp = src.data.copy()
        drop_faces_with_mats(tmp, MARKING_MATS)
        parts.append((tmp, src.matrix_world.copy()))
    if kerb_proxy is not None:
        log(f"ground collider: kerb collision from {kerb_proxy.name} ({tris_of(kerb_proxy.data)} tris), visual profile not collided")
        bpy.data.objects.remove(kerb_proxy)
    me = join_meshes_world(parts, "COL_Ground")
    for tmp, _ in parts:
        bpy.data.meshes.remove(tmp)
    # V7: the ground proxy copied every render grid triangle (340k in V6) although the
    # surfaces are almost planar. Weld coincident edges and merge faces within 0.1 deg
    # (walkable heights preserved; checked by the road-floor probe at 4 cm and the
    # walking routes). Render meshes are untouched.
    before = tris_of(me)
    simplify_planar(me)
    # V9: the glTF exporter calls Mesh.validate() IN PLACE and only warns; repair
    # explicitly here (and record what changed) so no export ever sees an invalid mesh.
    counts = lambda m: (len(m.vertices), len(m.edges), len(m.loops), len(m.polygons))
    c0 = counts(me)
    repaired = me.validate(verbose=True, clean_customdata=False)
    report_validate = {'repaired': bool(repaired), 'before_v_e_l_f': c0, 'after_v_e_l_f': counts(me)}
    log(f"ground collider validate: {report_validate}")
    col = collider_object("COL_Ground", me, G["Game_Collision"])
    col["zc_validate_v9"] = json.dumps(report_validate)
    col["zc_tris_before_simplify"] = before
    log(f"ground collider: {before} -> {tris_of(me)} tris")
    return col


# --------------------------------------------------------------------------- markers
def to_godot(v):
    return [round(v[0], 3), round(v[2], 3), round(-v[1], 3)]


def build_markers(G):
    spawns, landmarks = [], []
    for sid, label, (x, y), (dx, dy), note in game_points.SPAWN_POINTS:
        e = bpy.data.objects.new(sid, None)
        e.empty_display_type = 'SINGLE_ARROW'
        e.empty_display_size = 3.0
        e.location = (x, y, 0.0)
        # empty +Z points along the facing direction after this rotation, for readability in Blender
        e.rotation_euler = (math.radians(90), 0.0, math.atan2(dy, dx) - math.pi / 2)
        e["zc_label"], e["zc_note"] = label, note
        G["Game_Spawn_Points"].objects.link(e)
        n = math.hypot(dx, dy)
        spawns.append({"id": sid, "label": label, "note": note, "blender": [x, y, 0.0],
                       "godot": to_godot((x, y, 0.0)), "facing_godot": [dx / n, 0.0, -dy / n]})
    for lid, label, (x, y, z), radius, verified, evidence, spawn in game_points.LANDMARKS:
        e = bpy.data.objects.new(lid, None)
        e.empty_display_type = 'PLAIN_AXES'
        e.empty_display_size = 4.0
        e.location = (x, y, z)
        e["zc_label"], e["zc_radius"], e["zc_verified"], e["zc_evidence"] = label, radius, verified, evidence
        e["zc_spawn"] = spawn
        G["Game_Landmarks"].objects.link(e)
        landmarks.append({"id": lid, "label": label, "verified": verified, "evidence": evidence, "radius": radius,
                          "spawn": spawn,
                          "blender": [x, y, z], "godot": to_godot((x, y, z))})
    return spawns, landmarks


# --------------------------------------------------------------------------- materials
def principled(mat):
    if not mat.node_tree:
        return None
    return next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)


def tile_of(name):
    # V9: periodic (Clifford-torus) ground materials carry their own bake tile.
    m = bpy.data.materials.get(name)
    if m is not None and m.get('zc_tile_m'):
        return float(m['zc_tile_m'])
    return BRICK_TILE.get(name) or SMALL_TILE.get(name) or DEFAULT_TILE


def make_seamless(img):
    """Make a noise tile wrap seamlessly: blend with a half-offset copy, first along
    X then along Y. Each roll's own seam lies on the centre line, where the weight
    keeps the original pixels, so no cross-shaped seam remains."""
    import numpy as np
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    a = px.reshape(h, w, 4)
    wx = np.clip((1.0 - np.abs(np.linspace(-1.0, 1.0, w, dtype=np.float32))) * 2.0, 0.0, 1.0)[None, :, None]
    a = a * wx + np.roll(a, w // 2, axis=1) * (1.0 - wx)
    wy = np.clip((1.0 - np.abs(np.linspace(-1.0, 1.0, h, dtype=np.float32))) * 2.0, 0.0, 1.0)[:, None, None]
    a = a * wy + np.roll(a, h // 2, axis=0) * (1.0 - wy)
    img.pixels.foreach_set(a.astype(np.float32).ravel())


def bake_plane(name, vertical, T):
    me = bpy.data.meshes.new(name)
    if vertical:
        verts = [(0, 0, 0), (T, 0, 0), (T, 0, T), (0, 0, T)]
        faces = [(0, 1, 2, 3)]
    else:
        verts = [(0, 0, 0), (T, 0, 0), (T, T, 0), (0, T, 0)]
        faces = [(0, 1, 2, 3)]
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name="UVMap")
    for loop, co in zip(uv.data, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop.uv = co
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def bake(obj, kind, img):
    nt = obj.active_material.node_tree
    node = nt.nodes.new('ShaderNodeTexImage')
    node.image = img
    nt.nodes.active = node
    with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj],
                                   selected_editable_objects=[obj]):
        if kind == 'EMIT':
            bpy.ops.object.bake(type='EMIT', margin=0, use_clear=True)
        else:
            bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT', margin=0, use_clear=True)
    nt.nodes.remove(node)


def material_fingerprint(mat):
    def val(v):
        if isinstance(v,(str,int,float,bool)) or v is None:
            return v
        try:
            return list(v)
        except TypeError:
            return str(v)
    nt=mat.node_tree
    data={'version':'v5-albedo-normal-roughness-1','tile':tile_of(mat.name),
          'vertical':mat.name in VERTICAL,'hires':mat.name in HIRES,
          'nodes':[(n.name,n.bl_idname,[(i.name,val(i.default_value)) for i in n.inputs if hasattr(i,'default_value')],
                    [(p,getattr(n,p)) for p in ('noise_dimensions','noise_type','normalize','operation','blend_type') if hasattr(n,p)]) for n in nt.nodes],
          'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in nt.links]}
    for n in nt.nodes:
        if n.type=='VALTORGB':
            data.setdefault('ramps',[]).append((n.name,[(e.position,list(e.color)) for e in n.color_ramp.elements]))
    return hashlib.sha256(json.dumps(data,sort_keys=True,default=str).encode()).hexdigest()

def bake_material(mat):
    if mat.get('zc_v12_foliage'):
        return None
    if mat.get('zc_v12_asset'):
        from utilities.v12_realism import image
        return tuple(image(mat['zc_v12_asset'],k) for k in ['diff','nor_gl','rough'])
    cache_path=os.path.join(TEX,'bake_cache.json')
    cache=json.load(open(cache_path,encoding='utf-8')) if os.path.exists(cache_path) else {}
    key=material_fingerprint(mat)
    entry=cache.get(mat.name,{})
    if entry.get('fingerprint')==key and all(p is None or os.path.exists(os.path.join(TEX,p)) for p in entry.get('files',[])) and len(entry.get('files',[]))==3:
        files=entry['files']
        if all(p is None or hashlib.sha256(open(os.path.join(TEX,p),'rb').read()).hexdigest()==h for p,h in zip(files,entry.get('sha256',[]))) and len(entry.get('sha256',[]))==3:
            imgs=[bpy.data.images.load(os.path.join(TEX,p),check_existing=True) if p else None for p in files]
            for img in imgs[1:]:
                if img:
                    img.colorspace_settings.name='Non-Color'
            log('reused verified texture bake',mat.name)
            return tuple(imgs)
    result=_bake_material_uncached(mat)
    if result:
        files=[os.path.basename(i.filepath_raw) if i else None for i in result]
        cache[mat.name]={'fingerprint':key,'files':files,
                        'sha256':[hashlib.sha256(open(os.path.join(TEX,p),'rb').read()).hexdigest() if p else None for p in files]}
        with open(cache_path,'w',encoding='utf-8') as f:
            json.dump(cache,f,indent=2)
    return result

def _bake_material_uncached(mat):
    """Returns (albedo_path, normal_path or None) or None for flat materials."""
    b = principled(mat)
    if b is None or not b.inputs['Base Color'].is_linked:
        return None
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
    surf_src = out.inputs['Surface'].links[0].from_socket
    color_src = b.inputs['Base Color'].links[0].from_socket
    T = tile_of(mat.name)
    res = int(mat.get('zc_bake_res') or (1024 if mat.name in HIRES else 512))
    # V9: natively periodic materials need no half-offset blend (it halved their
    # contrast in V8); scene-only macro/vertex-mask layers are switched off.
    seamless = not mat.get('zc_periodic')
    switches = [n for n in nt.nodes if n.name == 'ZC_Bake_Macro']
    for n in switches:
        n.outputs[0].default_value = 0.0
    plane = bake_plane("BAKE_" + mat.name, mat.name in VERTICAL, T)
    plane.data.materials.append(mat)
    stem = mat.name.replace("M_", "", 1).lower()
    # albedo through an emission shortcut (independent of metallic / lighting)
    img = bpy.data.images.new(f"T_{stem}_albedo", res, res, alpha=False)
    em = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(color_src, em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    bake(plane, 'EMIT', img)
    nt.links.new(surf_src, out.inputs['Surface'])
    nt.nodes.remove(em)
    if mat.name not in BRICK_TILE and seamless:
        make_seamless(img)
    img.filepath_raw = os.path.join(TEX, img.name + ".png")
    img.file_format = 'PNG'
    img.save()
    nrm = None
    if b.inputs['Normal'].is_linked:
        nrm = bpy.data.images.new(f"T_{stem}_normal", res, res, alpha=False)
        nrm.colorspace_settings.name = 'Non-Color'
        bake(plane, 'NORMAL', nrm)
        if mat.name not in BRICK_TILE and seamless:
            make_seamless(nrm)
        nrm.filepath_raw = os.path.join(TEX, nrm.name + ".png")
        nrm.file_format = 'PNG'
        nrm.save()
    # V5: retain the source roughness variation, in addition to albedo and normals.
    rough = bpy.data.images.new(f"T_{stem}_roughness", res, res, alpha=False)
    rough.colorspace_settings.name = 'Non-Color'
    em = nt.nodes.new('ShaderNodeEmission')
    rough_input = b.inputs['Roughness']
    if rough_input.is_linked:
        nt.links.new(rough_input.links[0].from_socket, em.inputs['Color'])
    else:
        r = rough_input.default_value
        em.inputs['Color'].default_value = (r,r,r,1.)
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    bake(plane, 'EMIT', rough)
    nt.links.new(surf_src, out.inputs['Surface'])
    nt.nodes.remove(em)
    if mat.name not in BRICK_TILE and seamless:
        make_seamless(rough)
    rough.filepath_raw = os.path.join(TEX, rough.name + '.png')
    rough.file_format = 'PNG'
    rough.save()
    bpy.data.objects.remove(plane, do_unlink=True)
    for n in switches:
        n.outputs[0].default_value = 1.0
    return img, nrm, rough


def game_material(mat, baked):
    if mat.get('zc_v12_foliage'):
        gm=mat.copy()
        gm.name='GM_'+mat.name.replace('M_','',1)
        gm['zc_v12_foliage']=True
        return gm
    gm = bpy.data.materials.new("GM_" + mat.name.replace("M_", "", 1))
    gm.use_nodes = True
    nt = gm.node_tree
    b = principled(gm)
    src = principled(mat)
    rough = float(mat.roughness)
    metal = float(mat.metallic)
    base = mat.get("gltf_base_color", list(mat.diffuse_color[:3]))
    b.inputs['Base Color'].default_value = (*base, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if src is not None:
        es = src.inputs.get('Emission Strength')
        if es is not None and es.default_value > 0:
            b.inputs['Emission Color'].default_value = src.inputs['Emission Color'].default_value
            b.inputs['Emission Strength'].default_value = min(es.default_value, 4.0)
    if "Glass" in mat.name:   # opaque, reflective dark glass reads better in real time than transmission
        b.inputs['Roughness'].default_value = 0.06
        b.inputs['Metallic'].default_value = 0.25
    if baked:
        img, nrm, rough_map = baked
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = img
        nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
        if nrm is not None:
            nt2 = nt.nodes.new('ShaderNodeTexImage')
            nt2.image = nrm
            nm = nt.nodes.new('ShaderNodeNormalMap')
            nm.inputs['Strength'].default_value = 1.0
            nt.links.new(nt2.outputs['Color'], nm.inputs['Color'])
            nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
        rt = nt.nodes.new('ShaderNodeTexImage')
        rt.image = rough_map
        nt.links.new(rt.outputs['Color'], b.inputs['Roughness'])
    gm["zc_tile_m"] = tile_of(mat.name)
    gm["zc_source_material"] = mat.name
    return gm


def box_uv(me, tiles):
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        T = tiles.get(f.material_index, DEFAULT_TILE)
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for lp in f.loops:
            co = lp.vert.co
            if ax == 2:
                u, v = co.x, co.y
            elif ax == 0:
                u, v = co.y, co.z
            else:
                u, v = co.x, co.z
            lp[uv].uv = (u / T, v / T)
    bm.to_mesh(me)
    bm.free()


def convert_materials(objects):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene_setup.enable_gpu(scene)
    scene.cycles.samples = 8
    scene.cycles.use_denoising = False
    os.makedirs(TEX, exist_ok=True)
    used = {}
    for o in objects:
        if o.type == 'MESH':
            for m in list(o.data.materials) + [s.material for s in o.material_slots if s.link == 'OBJECT']:
                if m is not None:
                    used[m.name] = m
    gmap, report = {}, []
    for name in sorted(used):
        m = used[name]
        t0 = time.time()
        baked = bake_material(m)
        gmap[name] = game_material(m, baked)
        report.append({"source": name, "game": gmap[name].name, "tile_m": tile_of(name),
                       "albedo": os.path.basename(baked[0].filepath_raw) if baked else None,
                       "normal": os.path.basename(baked[1].filepath_raw) if baked and baked[1] else None,
                       "roughness": os.path.basename(baked[2].filepath_raw) if baked else None})
        if baked:
            log(f"baked {name} ({time.time() - t0:.1f}s)")
    done = set()
    for o in objects:
        if o.type != 'MESH':
            continue
        for s in o.material_slots:   # object-linked slots (car paint colours)
            if s.link == 'OBJECT' and s.material is not None and s.material.name in gmap:
                s.material = gmap[s.material.name]
        if o.data.name in done:
            continue
        me = o.data
        done.add(me.name)
        tiles = {i: tile_of(m.name) for i, m in enumerate(me.materials) if m}
        if not any(m and m.get('zc_v12_foliage') for m in me.materials):
            box_uv(me, tiles)
        for i, m in enumerate(me.materials):
            if m is not None and m.name in gmap:
                me.materials[i] = gmap[m.name]
    return report


# --------------------------------------------------------------------------- export
GLTF_OPTS = dict(export_format='GLB', export_extras=True, export_apply=True, export_yup=True,
                 export_cameras=False, export_lights=False, export_texcoords=True, export_normals=True,
                 export_image_format='AUTO',
                 # V9: only the ground mask (ground_system.MASK_ATTR) is exported as COLOR_0.
                 export_vertex_color='NAME', export_vertex_color_name='ZC_Ground_Mask')


def export_selection(objs, path):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, **GLTF_OPTS)


def export_buildings(blds):
    os.makedirs(BLD_DIR, exist_ok=True)
    out = []
    for name, (bld, col) in blds.items():
        L = bld.matrix_world.translation.copy()
        shift = Matrix.Translation(-Vector((L.x, L.y, 0.0)))
        saved = [(o, o.matrix_world.copy()) for o in (bld, col)]
        for o, m in saved:
            o.matrix_world = shift @ m
        path = os.path.join(BLD_DIR, name + ".glb")
        export_selection([bld, col], path)
        for o, m in saved:
            o.matrix_world = m
        out.append({"name": name, "file": os.path.relpath(path, OUT), "origin_blender": [L.x, L.y, 0.0],
                    "rotation_z_deg": round(math.degrees(bld.rotation_euler.z), 3)})
    return out


def export_assets(instances):
    os.makedirs(ASSET_DIR, exist_ok=True)
    meshes = {}
    for o in instances:
        meshes.setdefault(o.data.name, o.data)
    out = []
    for name, me in sorted(meshes.items()):
        tmp = bpy.data.objects.new("ASSET_" + name, me)
        bpy.context.scene.collection.objects.link(tmp)
        path = os.path.join(ASSET_DIR, name + ".glb")
        export_selection([tmp], path)
        bpy.data.objects.remove(tmp, do_unlink=True)
        out.append({"asset": name, "file": os.path.relpath(path, OUT), "tris": tris_of(me),
                    "instances": sum(1 for o in instances if o.data == me)})
    return out


def parent_to_groups(G):
    for cname, coll in G.items():
        root = bpy.data.objects.new(cname, None)
        root.empty_display_size = 1.0
        coll.objects.link(root)
        for o in list(coll.objects):
            if o is root or o.parent is not None:
                continue
            mw = o.matrix_world.copy()
            o.parent = root
            o.matrix_world = mw


# --------------------------------------------------------------------------- main
def main():
    t0 = time.time()
    src_path = bpy.data.filepath
    os.makedirs(OUT, exist_ok=True)
    from utilities.v7_lighting import KINDS as LIGHT_KINDS
    evening_lights=[]
    for o in bpy.data.objects:
        if o.type!='LIGHT' or not o.get('zc_night_energy'):
            continue
        kind=o.get('zc_light_kind','bollard')
        e,r,col,spot=LIGHT_KINDS[kind]
        evening_lights.append({'kind':kind,'blender':[round(c,3) for c in o.location],'godot':to_godot(o.location),
                               'energy':e,'range_m':r,'color':list(col),'spot':spot})
    strip_scene()
    G = make_collections()
    blds = build_buildings(G)
    # V11: interactive gate leaves ship as separate meshes (Godot gate_controller animates them).
    gate_leaves = []
    lc = bpy.data.collections.get('V11_Gate_Leaves')
    if lc:
        for o in list(lc.objects):
            for c_ in list(o.users_collection):
                c_.objects.unlink(o)
            G['Game_Gate'].objects.link(o)
            gate_leaves.append({'name': o.name, 'gate': o.get('zc_gate_id'), 'leaf': o.get('zc_leaf'), 'slide_blender_m': list(o.get('zc_slide_m', [0, 0])), 'start_closed': bool(o.get('zc_start_closed'))})
    site = build_site(G)
    veg, props = classify_instances(G)
    ground = build_ground_collider(G, site)
    trunks, propcol = build_instance_colliders(G, veg, props)
    spawns, landmarks = build_markers(G)
    # remove the now-empty source collections
    for c in list(bpy.data.collections):
        if c.name not in G and not c.all_objects:
            bpy.data.collections.remove(c)
    render_objs = [o for c in G.values() for o in c.objects if o.type == 'MESH' and not o.name.endswith("-colonly")]
    mat_report = convert_materials(render_objs)
    # collision proxies carry no materials and stay hidden in renders
    building_files = export_buildings(blds)
    asset_files = export_assets(veg + props)
    parent_to_groups(G)
    full = os.path.join(OUT, "campus_full.glb")
    for o in bpy.context.scene.objects:
        o.select_set(False)
    bpy.ops.export_scene.gltf(filepath=full, use_selection=False, **GLTF_OPTS)
    # manifest
    objects, totals = [], {}
    for cname, coll in G.items():
        t = 0
        for o in coll.objects:
            if o.type == 'MESH':
                n = tris_of(o.data)
                t += n
                if not o.name.startswith(("VEG_", "PROP_")) or o.name.startswith(("VEG_Flower", "PROP_Pergola")):
                    objects.append({"name": o.name, "collection": cname, "tris": n,
                                    "materials": [m.name for m in o.data.materials if m]})
        totals[cname] = {"objects": len(coll.objects), "tris": t}
    render_tris = sum(v["tris"] for k, v in totals.items() if k != "Game_Collision")
    manifest = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_blend": os.path.relpath(src_path, ROOT),
        "source_blend_sha256":hashlib.sha256(open(src_path,'rb').read()).hexdigest(),
        "game_glb_sha256":hashlib.sha256(open(full,'rb').read()).hexdigest(),
        "generator_sha256":{os.path.relpath(p,ROOT):hashlib.sha256(open(p,'rb').read()).hexdigest()
            for p in [os.path.join(SRC,'build_scene.py'),os.path.join(SRC,'build_game_assets.py')]+
            [os.path.join(SRC,'utilities',f) for f in sorted(os.listdir(os.path.join(SRC,'utilities'))) if f.endswith('.py')]},
        "coordinate_system": {"blender": "metres, origin = dome centre, +Y = toward north gate, Z up",
                              "godot": "glTF Y-up: godot = (x_b, z_b, -y_b)"},
        "totals": totals, "render_tris": render_tris,
        "collision_tris": totals["Game_Collision"]["tris"],
        "collision_layers": COLLISION_LAYERS,
        "objects": objects, "buildings": building_files, "assets": asset_files,
        "materials": mat_report, "spawn_points": spawns, "landmarks": landmarks,
        "gates":GATE_RECORDS,
        "evening_lights":evening_lights,
        "reconstruction_version":"15.0.0","v12_asset_manifest":"res://assets/pbr/manifest.json","gate_leaves":gate_leaves,"academic_entrances_v11":json.load(open(os.path.join(ROOT,"references","academic_entrances_v11.json"),encoding="utf-8")),
        "internal_building_entries":"superseded by academic_entrances_v11 (V11)",
        "collision_approximations":{"academic_stairs":"Continuous source-derived walking incline + exact landing/metal rails; visual treads retained; vertical deviation <= one estimated 0.15 m riser."},
        "files": {"campus_full": "campus_full.glb", "size_mb": round(os.path.getsize(full) / 1e6, 2)},
    }
    with open(os.path.join(OUT, "campus_manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    if os.path.exists(GAME_BLEND):
        os.remove(GAME_BLEND)
    bpy.ops.wm.save_as_mainfile(filepath=GAME_BLEND, compress=True, relative_remap=True)
    if os.path.isdir(os.path.dirname(GODOT_CAMPUS)):   # refresh the Godot project's copy
        import shutil
        os.makedirs(GODOT_CAMPUS, exist_ok=True)
        for f in ("campus_full.glb", "campus_manifest.json"):
            shutil.copy2(os.path.join(OUT, f), os.path.join(GODOT_CAMPUS, f))
        log(f"copied campus_full.glb + manifest to {GODOT_CAMPUS}")
    log(f"render tris {render_tris}, collision tris {manifest['collision_tris']}, "
        f"campus_full.glb {manifest['files']['size_mb']} MB, {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
