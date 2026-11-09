"""Photo-supported Academic public spaces; dimensions and spatial fits estimated.

Footprint: OSM 540106547. Two stairs / court / seating / through-route: owner
first-hand description. V10 owner correction: no trees or palms in the inner court. D05 composition only (possibly enhanced photo).
Official dining page places cafeteria in the basement: no invented outdoor cafe.
"""
import math
import bmesh
import bpy
from mathutils import Matrix
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/vendor'))
from shapely.geometry import Polygon, box
from .geometry import MeshBuilder, get_collection, instance, parent_keep

def public_ground_mask():
    # Inner half-disc of the measured C-shaped footprint, central passage, rear axis.
    arc=[(72.*math.cos(math.radians(a)),-249.+72.*math.sin(math.radians(a))) for a in range(180,361,3)]
    m=Polygon(arc).union(box(-5.5,-365.,5.5,-228.)).union(box(-17.8,-249.,17.8,-228.))
    # V10: paved floor under both stair flights (V9 left the right flight standing on
    # graded soil where the OSM footprint is asymmetric) and under the new P09
    # forecourt arcades, which are set back ARC_D into the prong footprints.
    from .buildings import ARC_D, ARC_Y0
    from . import survey as SV
    px0,ypf=SV.ACADEMIC['prong_x'][0],SV.ACADEMIC['prong_front_y']
    m=m.union(box(-px0+.02,-232.,px0-.02,-218.))
    for sx in (-1,1):
        # V10 final audit: the OSM prong footprint runs ~1.3 m beyond the modelled
        # facade line, so the partition left graded soil in front of the arcade (V9's
        # protruding piers hid it). Pave from 2.5 m outside the facade line.
        lo,hi=sorted((sx*(px0-2.5),sx*(px0+ARC_D)))
        m=m.union(box(lo,ARC_Y0,hi,ypf))
    return m

def build_stairs(M,C,root):
    """P09 supports paired substantial stairs and metal rails. Width 10.5 m.
    Rise/riser count remain functional estimates, not recovered measurements.
    """
    for side in (-1,1):
        mb=MeshBuilder()
        lo,hi=sorted((side*8.5,side*19.0))
        front=-229.+28*.36
        for k in range(28):
            mb.box(M['stone'],lo,front-(k+1)*.36,-.15,hi,front-k*.36,.21+(k+1)*.15)
        from .v6_academic import rail_stairs
        rail_stairs(mb,M,lo,hi,front,-229.,4.41)
        mb.box(M['stone'],lo,-232.,4.2,hi,-229.,4.41)
        # V8: continue the slender rail over the exposed 3 m upper landing edge;
        # the V7 rail stopped at the last nosing, leaving the landing unguarded.
        # The inner edge joins the existing upper public walkway; keep it open.
        for x in ((lo+.13,) if side<0 else (hi-.13,)):
            for y in (-230.4,-231.8):
                mb.cylinder(M['metal_light'],(x,y),4.41,5.43,.027,segs=8)
            for z in (4.97,5.43):
                mb.box(M['metal_light'],x-.025,-231.95,z-.025,x+.025,-229.,z+.025)
        obj=mb.to_object('Academic_Stair_'+('Left' if side<0 else 'Right'),C['academic_stairs'])
        parent_keep(obj,root)
        obj['zc_collision']=True
        obj['zc_risers']=28
        obj['zc_riser_height_m']=.15
        obj['zc_tread_m']=.36
        obj['zc_width_m']=10.5
        obj['zc_evidence']='P09 shows substantial stairs/metal rails; owner confirms two flights; all metric dimensions estimated.'

def organize(C,root):
    # Retain independently editable facade, roof, stairs, entrance and courtyard layers.
    # Parts.finish has just parented details; refresh before copying world transforms.
    bpy.context.view_layer.update()
    for child in root.children:
        if child.name.endswith(('_Glass','_Details')):
            C['academic_facades'].objects.link(child)
    detail=bpy.data.objects.get(root.name+'_Details')
    if detail:
        bm=bmesh.new()
        bm.from_mesh(detail.data)
        roof_indices={i for i,m in enumerate(detail.data.materials) if m and m.name=='M_Roof_Membrane'}
        roof=bm.copy()
        bmesh.ops.delete(roof,geom=[f for f in roof.faces if f.material_index not in roof_indices],context='FACES')
        bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index in roof_indices],context='FACES')
        me=bpy.data.meshes.new('Academic_Roof')
        roof.to_mesh(me)
        for m in detail.data.materials:
            me.materials.append(m)
        obj=bpy.data.objects.new('Academic_Roof',me)
        C['academic_roof'].objects.link(obj)
        obj.matrix_world=detail.matrix_world.copy()
        parent_keep(obj,root)
        bm.to_mesh(detail.data)
        bm.free()
        roof.free()

def build_spaces(M,C,A):
    mask=public_ground_mask()
    mb=MeshBuilder()
    # The source surface pass later cuts planters and foundations out of this paving.
    from .v6_academic import paving_regions,polygon_prism,terrace_geometry
    for mat,g in paving_regions(mask,M):polygon_prism(mb,mat,g,-.1,.21)
    mb.to_object('Academic_Public_Paving',C['academic_court'])
    # V10 owner correction: the inner Academic courtyard has NO trees. The V5-V9
    # palm beds at (+-59.5, -253.5) and the four benches beside them (no photographic
    # support) are removed. P13/P15 show open hardscape, dark granite tiers, slender
    # poles and low black seat blocks only (kept in terrace_geometry).
    court_lights=terrace_geometry(M,C,bpy.data.objects['AB_Academic_Building'])
    from .v7_lighting import add_lights
    add_lights('Academic_Court_Pole',court_lights,kind='court_pole',energy=60.,evidence='P13 pole luminaires; brightness ESTIMATED')
    # V11: the V7-V10 passage ceiling slab (z 7.2-7.4) is gone. The upper floor plate of the
    # rebuilt core (v11_academic.core) now covers the lower passage, with two railed voids.
    # V11: the V6 Gate C box at the rear aperture and the UST panel on the +X prong are
    # replaced by the V11 entrance registry (v11_academic: ring/side-wing entrances).
    from .v6_building_entries import write_legacy_registry
    write_legacy_registry()
