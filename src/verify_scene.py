"""Technical checks on the built project; writes output/verification_report.json.

Checks: geometry exists, collections are populated, cameras exist, every mesh
object has materials, units/scale are sane, nothing floats far above/below the
ground, no external file is missing, preview PNGs exist and are not blank, and
the GLB re-imports with geometry.

Usage (from the project root):
    blender -b output/Zewail_City_3D.blend --python src/verify_scene.py
"""
import json
import os
import sys
import hashlib
from pathlib import Path

import bpy
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEWS = ["aerial.png", "masterplan_top.png", "isometric.png", "admin_front_elevation.png", "entrance.png", "details.png"]
GLB = os.path.join(ROOT, "output", "exports", "Zewail_City_3D.glb")
REQUIRED_COLLECTIONS = ["Campus_Ground", "Main_Buildings", "Secondary_Buildings", "Architectural_Details",
                        "Windows_And_Glass", "Roads_And_Pathways", "Vegetation", "Site_Furniture",
                        "Lighting", "Cameras", "Main_Gate_Complex"]
REQUIRED_CAMERAS = ["CAM_Aerial", "CAM_Isometric", "CAM_Masterplan_Top", "CAM_Admin_Front_Elevation",
                    "CAM_Ref_A01", "CAM_Ref_A02", "CAM_Detail", "CAM_Plan_Overlay"]


def check(report, name, ok, detail):
    report["checks"].append({"check": name, "pass": bool(ok), "detail": detail})


def main():
    scene = bpy.context.scene
    report = {"blend": bpy.data.filepath, "blender": bpy.app.version_string, "checks": []}
    objs = list(scene.objects)
    by_type = {}
    for o in objs:
        by_type[o.type] = by_type.get(o.type, 0) + 1
    report["objects_total"] = len(objs)
    report["objects_by_type"] = by_type
    report["mesh_datablocks"] = len(bpy.data.meshes)
    report["materials"] = len(bpy.data.materials)
    deps = bpy.context.evaluated_depsgraph_get()
    tris = 0
    for o in objs:
        if o.type == 'MESH':
            me = o.evaluated_get(deps).data
            tris += sum(len(p.vertices) - 2 for p in me.polygons)
    report["evaluated_triangles"] = tris
    check(report, "real geometry", by_type.get('MESH', 0) > 100 and tris > 100000, f"{by_type.get('MESH', 0)} meshes, {tris} tris")

    colls = {c.name: len(c.all_objects) for c in bpy.data.collections}
    report["collections"] = colls
    missing = [c for c in REQUIRED_COLLECTIONS if colls.get(c, 0) == 0]
    check(report, "collections populated", not missing, f"{len(colls)} collections; empty/missing: {missing}")

    cams = [c for c in REQUIRED_CAMERAS if c in bpy.data.objects and bpy.data.objects[c].type == 'CAMERA']
    check(report, "cameras present", len(cams) == len(REQUIRED_CAMERAS), cams)

    no_mat = [o.name for o in objs if o.type == 'MESH' and (not o.material_slots or any(s.material is None for s in o.material_slots))]
    check(report, "materials assigned", not no_mat, f"{len(no_mat)} mesh objects without material: {no_mat[:10]}")

    us = scene.unit_settings
    check(report, "metric units", us.system == 'METRIC' and abs(us.scale_length - 1) < 1e-6, f"{us.system} scale={us.scale_length}")
    terrace=bpy.data.objects.get('Academic_Terraced_Court_Details')
    zs=[(terrace.matrix_world@v.co).z for v in terrace.data.vertices] if terrace else []
    # V11: building entrances moved from the V6 collection into the Academic parts +
    # references/academic_entrances_v11.json; balustrades/fascia are separate objects.
    reg = os.path.join(ROOT, 'references', 'academic_entrances_v11.json')
    ents = json.load(open(reg, encoding='utf-8'))['entrances'] if os.path.exists(reg) else []
    check(report,'V6 court levels are physical geometry; V11 entrance registry and Academic upper-level objects exist',
          bool(zs and max(zs)-min(zs)>.85 and len(ents)>=6 and bpy.data.objects.get('Academic_V11_Balustrades')
               and bpy.data.objects.get('Academic_V11_GateA_Fascia')),
          {'terrace_z_range':[min(zs),max(zs)] if zs else None,'entrances':[e['id'] for e in ents]})
    # ---- V7 source checks
    sys.path.insert(0, os.path.join(ROOT, 'src'))
    import math as _m
    pav=bpy.data.objects.get('Plaza_Paving')
    check(report,'V7 paving edge restraint is a separate flush material region',
          bool(pav and any(m and m.name=='M_V7_Paving_Edge_Restraint' for m in pav.data.materials)),None)
    mk=bpy.data.objects.get('Road_Markings_M_Road_Marking_White');rd=bpy.data.objects.get('Road_Network_External')
    if mk and rd:
        from utilities.ground_system import datum as _datum
        offs=[(mk.matrix_world@v.co).z-_datum((mk.matrix_world@v.co).x,(mk.matrix_world@v.co).y) for v in mk.data.vertices[:500]]
        check(report,'V7 road markings 12 mm above asphalt (V6 4 mm)',all(abs(o-.072)<.002 for o in offs),{'marking_minus_datum':[min(offs),max(offs)]})
    plot=bpy.data.objects.get('Ground_Campus_Plot')
    if plot:
        from utilities.ground_system import datum as _datum
        lifted=sum(1 for v in plot.data.vertices if v.co.z-_datum(v.co.x,v.co.y)>.05)
        check(report,'V7 graded soil shoulders at raised edges',lifted>100,{'lifted_vertices':lifted,'vertices':len(plot.data.vertices)})
    if terrace:
        pts=[terrace.matrix_world@v.co for v in terrace.data.vertices]
        far=max(_m.hypot(q.x,q.y+249.) for q in pts if not 8.9<q.x<12.1)
        ramp_foot=min(q.y for q in pts if 8.9<q.x<12.1)
        check(report,'V7 court tiers concentric with inner glazing (outer radius ~62.5 m incl. tread; ramp foot outside)',
              61.5<far<63. and ramp_foot<-311.,{'max_tier_radius_m':round(far,3),'ramp_foot_y':round(ramp_foot,3)})
    res=bpy.data.objects.get('AB_East_Residential_Pair_Estimated')
    if res:
        zs=[(res.matrix_world@v.co).z for v in res.data.vertices]
        det=bpy.data.objects.get('AB_East_Residential_Pair_Estimated_Details')
        dz=max((det.matrix_world@v.co).z for v in det.data.vertices) if det else 0
        check(report,'V7 dormitory candidate six storeys (roof 21.4 m, cores above roof)',abs(max(zs)-21.4)<.05 and dz>24.5,
              {'roof_z':max(zs),'core_top_z':dz,'identity':res.get('zc_identity')})
    kinds={}
    for o in objs:
        if o.type=='LIGHT' and o.get('zc_night_energy'):
            kinds[o.get('zc_light_kind','bollard')]=kinds.get(o.get('zc_light_kind','bollard'),0)+1
    check(report,'V7 evening luminaires generated (off in daylight source)',kinds.get('bollard')==32 and kinds.get('street',0)>0 and kinds.get('court_pole',0)>0 and kinds.get('entrance',0)>0
          and all(o.data.energy==0 for o in objs if o.type=='LIGHT' and o.get('zc_night_energy')),kinds)
    check(report,'V7 architectural showcase camera path present',bool(bpy.data.objects.get('CIN_V7_Architectural_Showcase')),None)
    kit=Path(ROOT)/'Zewail_V6_Reference_Kit'
    photo_manifest=json.loads((kit/'source_manifest.json').read_text())
    photos=photo_manifest['photos']
    unchanged=len(photos)==16 and all(hashlib.sha256((kit/'owner_photos'/p['filename']).read_bytes()).hexdigest()==p['sha256'] for p in photos)
    check(report,'all 16 owner photo originals retain supplied SHA-256',unchanged,len(photos))

    # bounding box of buildings, and objects that float / sink
    heights = {}
    for coll_name in ("Main_Buildings", "Secondary_Buildings"):
        for o in bpy.data.collections[coll_name].objects:
            zs = [(o.matrix_world @ v.co).z for v in o.data.vertices]
            heights[o.name] = (round(min(zs), 2), round(max(zs), 2))
    report["building_z_ranges_m"] = heights
    bad = {k: v for k, v in heights.items() if not (-0.5 <= v[0] <= 0.5 and 4 < v[1] < 70)}
    check(report, "building heights plausible (base at ground, 4-70 m tall)", not bad, bad or "ok")
    floating = [o.name for o in objs if o.type == 'MESH' and o.parent is None and o.location.z > 1.0
                and o.users_collection[0].name in ("Palms", "Trees", "Shrubs", "Site_Furniture")]
    check(report, "no floating vegetation/furniture", not floating, floating[:10])

    # survey-anchor consistency (V4): the model still sits where survey.py (OSM / Sentinel-2 /
    # photogrammetry) says it should. Self-consistency checks, NOT a measure of accuracy.
    sys.path.insert(0, os.path.join(ROOT, "src"))
    from utilities import survey as SV

    def world_bbox(names):
        xs, ys = [], []
        for n in names:
            o = bpy.data.objects.get(n)
            if not o:
                continue
            for c in o.bound_box:
                w = o.matrix_world @ __import__('mathutils').Vector(c)
                xs.append(w.x)
                ys.append(w.y)
        return (min(xs), min(ys), max(xs), max(ys)) if xs else None

    adm = "AB_Administration_Cultural_Building"
    bb = world_bbox([adm, adm + "_Details", adm + "_Glass"])
    anchors = {}
    if bb:
        anchors["admin_bbox"] = [round(v, 1) for v in bb]
        anchors["admin_axis_offset_m"] = round((bb[0] + bb[2]) / 2, 2)
        anchors["admin_width_m"] = round(bb[2] - bb[0], 1)
    for key, name, spec in (("helmy", "AB_Helmy_Institute_Medical_Sciences", SV.HELMY),
                            ("nano", "AB_East_Research_Institute_Nano", SV.EAST_INSTITUTE)):
        b = world_bbox([name])
        if b:
            c = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
            anchors[key + "_centre_error_m"] = round(((c[0] - spec['center'][0]) ** 2 +
                                                      (c[1] - spec['center'][1]) ** 2) ** 0.5, 2)
    acb = world_bbox(["AB_Academic_Building"])
    if acb:
        anchors["academic_bbox"] = [round(v, 1) for v in acb]
    report["plan_anchor_consistency"] = anchors
    roof=world_bbox(['Academic_Roof'])
    check(report,'Academic roof stays over the Academic footprint after separation',
          bool(roof and acb and roof[0]>=acb[0]-2 and roof[2]<=acb[2]+2 and roof[1]>=acb[1]-2 and roof[3]<=acb[3]+4),
          {'roof_bbox':roof,'academic_bbox':acb})
    ok = (bb and abs(anchors["admin_axis_offset_m"]) < 1.0 and 155 < anchors["admin_width_m"] < 175
          and anchors.get("helmy_centre_error_m", 99) < 3 and anchors.get("nano_centre_error_m", 99) < 3
          and acb and abs((acb[0] + acb[2]) / 2) < 2
          and abs(acb[1] - (SV.ACADEMIC['curve_c'][1] - SV.ACADEMIC['r_out'])) < 3
          and abs(acb[3] - SV.ACADEMIC['prong_front_y']) < 3)
    check(report, "survey-anchor consistency (admin on axis, institute & academic positions)", ok, anchors)
    # V4 main gate: portal frame on the axis at the OSM gate line, photogrammetric height
    gb = world_bbox(["AB_Main_Gate_Complex"])
    g = bpy.data.objects.get("AB_Main_Gate_Complex")
    gz = max((g.matrix_world @ v.co).z for v in g.data.vertices) if g else 0.0
    gate = {"bbox": [round(v, 1) for v in gb] if gb else None, "max_z_m": round(gz, 2), "gate_y": SV.GATE_Y}
    report["main_gate"] = gate
    check(report, "main gate complex on the axis at the gate line, frame ~18.7 m high",
          bool(gb and abs((gb[0] + gb[2]) / 2) < 1.0 and gb[1] < SV.GATE_Y < gb[3] and abs(gz - 18.7) < 0.3), gate)

    pc = bpy.data.collections.get("Unverified_Masterplan_Proposals")
    lc = scene.view_layers[0].layer_collection.children.get("Unverified_Masterplan_Proposals") if pc else None
    check(report, "unverified proposals kept separate (excluded from view layer and renders)",
          bool(pc and len(pc.objects) and pc.hide_render and lc and lc.exclude),
          f"{len(pc.objects) if pc else 0} blockouts")

    missing_files = [i.filepath for i in bpy.data.images if i.source == 'FILE' and i.filepath
                     and not os.path.exists(bpy.path.abspath(i.filepath))]
    missing_libs = [l.filepath for l in bpy.data.libraries if not os.path.exists(bpy.path.abspath(l.filepath))]
    check(report, "no missing external resources", not missing_files and not missing_libs, missing_files + missing_libs)

    stats = {}
    for f in PREVIEWS:
        p = os.path.join(ROOT, "output", "previews", f)
        if not os.path.exists(p):
            stats[f] = "missing"
            continue
        img = bpy.data.images.load(p)
        px = np.array(img.pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]
        stats[f] = {"size": list(img.size), "mean": round(float(px.mean()), 3), "std": round(float(px.std()), 3)}
        bpy.data.images.remove(img)
    report["previews"] = stats
    ok = all(isinstance(v, dict) and v["std"] > 0.03 and 0.05 < v["mean"] < 0.95 for v in stats.values())
    check(report, "preview renders exist and are not blank", ok, stats)

    if os.path.exists(GLB):
        before = set(bpy.data.objects)
        tmp = bpy.data.scenes.new("GLB_Import_Test")
        with bpy.context.temp_override(scene=tmp, view_layer=tmp.view_layers[0]):
            bpy.ops.import_scene.gltf(filepath=GLB)
        new = [o for o in bpy.data.objects if o not in before]
        n_mesh = sum(1 for o in new if o.type == 'MESH')
        report["glb"] = {"path": GLB, "size_mb": round(os.path.getsize(GLB) / 1e6, 1), "imported_objects": len(new),
                         "imported_meshes": n_mesh, "imported_cameras": sum(1 for o in new if o.type == 'CAMERA')}
        check(report, "GLB re-imports with geometry", n_mesh > 100, report["glb"])
        leaked = [o.name for o in new if o.name.startswith("Plan_Bldg")]
        check(report, "GLB excludes unverified proposal blockouts", not leaked, leaked[:5])
    else:
        check(report, "GLB re-imports with geometry", False, "GLB file missing")

    report["all_pass"] = all(c["pass"] for c in report["checks"])
    report['source_blend_sha256']=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()
    out = os.path.join(ROOT, "output", "validation", "v11", "source_verification.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    for c in report["checks"]:
        print(f"[verify] {'PASS' if c['pass'] else 'FAIL'}  {c['check']}")
    print(f"[verify] report: {out}")
    sys.exit(0 if report["all_pass"] else 1)


if __name__ == "__main__":
    main()
