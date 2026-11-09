"""Export output/Zewail_City_3D.blend to output/exports/Zewail_City_3D.glb.

glTF cannot store procedural node textures, so before exporting (in memory only,
the .blend is not re-saved) every procedurally driven Base Color / Roughness is
replaced by the flat fallback stored in material["gltf_base_color"].

Usage (from the project root):
    blender -b output/Zewail_City_3D.blend --python src/export_glb.py
"""
import os

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLB_PATH = os.path.join(ROOT, "output", "exports", "Zewail_City_3D.glb")


def flatten_materials():
    for m in bpy.data.materials:
        if not m.node_tree:
            continue
        # V12 foliage is already native glTF PBR; retain its actual leaf UVs/maps.
        if m.get('zc_v12_foliage'):
            continue
        bsdf = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf is None:
            continue
        if m.get('zc_v12_asset'):
            import sys
            sys.path.insert(0,os.path.join(ROOT,'src'))
            from utilities.v12_realism import image
            nt=m.node_tree
            for kind,sock in [('diff','Base Color'),('rough','Roughness'),('nor_gl','Normal')]:
                for link in list(bsdf.inputs[sock].links):nt.links.remove(link)
                tex=nt.nodes.new('ShaderNodeTexImage');tex.image=image(m['zc_v12_asset'],kind)
                if kind=='nor_gl':
                    nm=nt.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.35
                    nt.links.new(tex.outputs[0],nm.inputs['Color']);nt.links.new(nm.outputs[0],bsdf.inputs[sock])
                else:nt.links.new(tex.outputs[0],bsdf.inputs[sock])
            bsdf.inputs['Base Color'].default_value=(1.,1.,1.,1.)
            continue
        for name in ('Base Color', 'Roughness', 'Normal'):
            sock = bsdf.inputs[name]
            for link in list(sock.links):
                m.node_tree.links.remove(link)
        if "gltf_base_color" in m:
            bsdf.inputs['Base Color'].default_value = (*m["gltf_base_color"], 1.0)
        bsdf.inputs['Roughness'].default_value = m.roughness


def drop_unverified():
    """Unverified masterplan blockouts stay in the .blend only (in memory removal).

    V10 (Codex review): the disabled vehicle collection is removed too; the glTF
    exporter does not filter excluded/hidden collections by default."""
    for name in ("Unverified_Masterplan_Proposals", "Optional_Vehicles_Disabled"):
        coll = bpy.data.collections.get(name)
        if coll:
            for o in list(coll.all_objects):
                bpy.data.objects.remove(o)
    # V10: collision-only proxies (hidden from render) are game data, not architecture
    for o in [o for o in bpy.data.objects if o.name.endswith('_Collision_Proxy')]:
        bpy.data.objects.remove(o)


def main():
    drop_unverified()
    flatten_materials()
    os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=GLB_PATH,
        export_format='GLB',
        export_apply=True,          # bake bevel modifiers into the meshes
        export_cameras=True,
        export_lights=True,
        export_yup=True,
    )
    print(f"[export] wrote {GLB_PATH} ({os.path.getsize(GLB_PATH) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
