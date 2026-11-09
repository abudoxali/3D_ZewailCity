"""P03/P05 institute-plaza context; form visible, placement/metric sizes estimated."""
import math,bpy
from mathutils import Vector
from . import survey as SV
from .geometry import MeshBuilder,parent_keep,get_collection

def build(M,C):
    spec=SV.HELMY;a=math.radians(spec['angle_deg']);cx,cy=spec['center']
    def world(x,y):return (cx+x*math.cos(a)-y*math.sin(a),cy+x*math.sin(a)+y*math.cos(a))
    # Separate context hypothesis: do not move P03's pergola into P13's inner court.
    x,y=world(24.,29.)
    mb=MeshBuilder()
    for lx in [-9.,-4.5,0.,4.5,9.]:
        for ly in [-2.5,2.5]:
            u,v=world(24.+lx,29.+ly)
            mb.obox(M['wood'],(u,v,1.99),(.24,.24,3.56),a)
    for ly in [-2.5,2.5]:
        u,v=world(24.,29.+ly);mb.obox(M['wood'],(u,v,3.8),(19.,.25,.35),a)
    for i in range(39):
        u,v=world(14.5+i*.5,29.);mb.obox(M['wood'],(u,v,4.0),(.09,6.,.16),a)
    coll=get_collection('Photo_Institute_Context_Estimated')
    o=mb.to_object('Institute_Photo_Pergola_Details',coll)
    bpy.context.view_layer.update();parent_keep(o,bpy.data.objects['AB_Helmy_Institute_Medical_Sciences'])
    o['zc_collision']=True;o['zc_evidence']='P03/P05 pergola/plaza morphology. Institute-cluster interpretation medium confidence; exact position/size estimated.'
    mb=MeshBuilder()
    poly=[world(24.+dx,29.+dy) for dx,dy in [(-11,-5),(11,-5),(11,5),(-11,5)]]
    mb.prism(M['plaza_grey'],poly,-.1,.21)
    o=mb.to_object('Photo_Context_Paving',coll);o['zc_evidence']='P03/P05 polished plaza context, not a calibrated map trace.'
