"""Build the Zewail City campus scene and save output/Zewail_City_3D.blend.

Usage (from the project root):
    blender -b --python src/build_scene.py
"""
import os
import sys
import time

import bpy

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SRC)
sys.path.insert(0, SRC)

from utilities import academic_public, buildings, cinematics, dormitory, gate, gate_inventory, ground_system, materials, proposals, scene_setup, site, vegetation, v5_cameras, v6_photo_cameras  # noqa: E402
from utilities.geometry import get_collection  # noqa: E402

BLEND_PATH = os.environ.get("ZC_BLEND_OUT") or os.path.join(ROOT, "output", "Zewail_City_3D.blend")


def make_collections():
    top = {name: get_collection(name) for name in (
        "Campus_Ground", "Main_Buildings", "Secondary_Buildings", "Architectural_Details",
        "Windows_And_Glass", "Roads_And_Pathways", "Vegetation", "Site_Furniture", "Lighting", "Cameras",
        "Main_Gate_Complex", "Provisional_Campus_Gates", "Unverified_Masterplan_Proposals")}
    veg = top["Vegetation"]
    return {
        'ground': top["Campus_Ground"], 'main': top["Main_Buildings"], 'secondary': top["Secondary_Buildings"],
        'details': top["Architectural_Details"], 'glass': top["Windows_And_Glass"],
        'roads': top["Roads_And_Pathways"], 'furniture': top["Site_Furniture"],
        'lighting': top["Lighting"], 'cameras': top["Cameras"],
        'proposals': top["Unverified_Masterplan_Proposals"], 'gate': top["Main_Gate_Complex"],
        'provisional_gates':top['Provisional_Campus_Gates'],
        'academic_facades':get_collection('Academic_Facades'), 'academic_stairs':get_collection('Academic_Stairs'),
        'academic_roof':get_collection('Academic_Roof'), 'academic_entry':get_collection('Academic_Entrance'),
        'academic_court':get_collection('Academic_Courtyard'),
        'veg_palms': get_collection("Palms", veg), 'veg_trees': get_collection("Trees", veg),
        'veg_shrubs': get_collection("Shrubs", veg), 'veg_lawns': get_collection("Planters_And_Hedges", veg),
        # V10: optional, disabled by default (excluded from view layer, renders and the game)
        'vehicles': get_collection("Optional_Vehicles_Disabled"),
    }


def clear_data():
    """Empty the current file without resetting preferences (keeps user extensions untouched)."""
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras,
                 bpy.data.curves, bpy.data.images, bpy.data.worlds, bpy.data.node_groups, bpy.data.actions):
        for block in list(coll):
            coll.remove(block)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for s in list(bpy.data.scenes)[1:]:
        bpy.data.scenes.remove(s)


def main():
    t0 = time.time()
    clear_data()
    scene = bpy.context.scene
    scene.name = "Zewail_City_Campus"
    scene_setup.setup_units(scene)
    scene_setup.setup_render(scene)
    device = scene_setup.enable_gpu(scene)

    C = make_collections()
    M = materials.build_materials()
    A = vegetation.build_assets(M)
    print('[build] materials and assets ready',flush=True)

    site.build_ground(M, C)
    site.build_roads(M, C)
    site.build_landscape(M, C)
    buildings.build_all(M, C)
    gate.build_gate(M, C)
    gate.build_perimeter_wall(M, C)
    gate_inventory.build_provisional(M,C)
    proposals.build_proposals(M, C)
    veg = site.build_vegetation(M, C, A)
    furn = site.build_furniture(M, C, A)
    academic_public.build_spaces(M,C,A)
    dormitory.build(M,C,A)
    from utilities import v6_context
    v6_context.build(M,C)
    print('[build] V4 survey layout ready; rebuilding V5 ground topology',flush=True)
    ground_system.rebuild(M, C)
    # V7: evening sources for modelled luminaires (off in the daylight source scene).
    from utilities import v7_lighting
    lamp_counts = v7_lighting.street_lamps()
    entrance_lights = v7_lighting.entrances(M, C)
    print('[build] V7 evening lights', lamp_counts, 'entrance', entrance_lights, flush=True)

    # late-afternoon sun from the WNW: real bearing ~300 deg; V4 survey: +Y is N36.5W, so 300 + 36.5
    sun = scene_setup.setup_world(scene, sun_elev=32.0, sun_azimuth=336.5)
    C['lighting'].objects.link(sun)
    scene_setup.build_cameras(scene, C['cameras'])
    shots = cinematics.build(scene, C['cameras'])
    v5_cameras.build(scene,C['cameras'])
    v6_photo_cameras.build(scene,C['cameras'])

    # V10: vehicles stay editable but are excluded from the realistic reconstruction.
    veh = C['vehicles']
    veh.hide_render = True
    veh['zc_evidence'] = 'No photograph shows parked/moving cars; kept only for future gameplay.'
    for vl in scene.view_layers:
        lc = vl.layer_collection.children.get(veh.name)
        if lc:
            lc.exclude = True

    from utilities import v12_realism
    v12_realism.apply(os.environ.get('ZC_V12_VEG_STAGE','v13'))
    # V15 pilot: ice-plant groundcover rows in the kerbed approach verge beds (C02).
    from utilities import v15_corridor
    v15_corridor.plant_groundcover()
    v15_corridor.write_log()
    # Editable V12 scene carries its verified texture inputs with it.
    bpy.ops.file.pack_all()
    os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
    if os.path.exists(BLEND_PATH):  # replace rather than leave a .blend1 backup
        os.remove(BLEND_PATH)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH, compress=True, relative_remap=True)
    print(f"[build] device={device} objects={len(bpy.data.objects)} meshes={len(bpy.data.meshes)} "
          f"materials={len(bpy.data.materials)} vegetation={veg} furniture={furn} shots={len(shots)}")
    print(f"[build] saved {BLEND_PATH} in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
