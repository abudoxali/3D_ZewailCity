"""Photo13/4 supported lit Gate A recesses; fixture count/positions estimated.

No temporary event strings, invented offices, or luminous opaque window panels.
Permanent ceiling strips and bounded lights illuminate real surfaces behind glass.
"""
import bpy
from .geometry import MeshBuilder,parent_keep
from .v7_lighting import add_lights

def add(M,C,root,A):
    for o in list(bpy.data.objects):
        if o.name.startswith('V7_V18_Academic_'):bpy.data.objects.remove(o,do_unlink=True)
    mb=MeshBuilder();neutral=[];warm=[]
    # Front lower vestibule, upper public hall and recessed side colonnades.
    for x in (-4.5,0.,4.5):
        for y in (-221.5,-225.5):
            z=3.58
            mb.box(M['lamp_neutral'],x-.8,y-.07,z,x+.8,y+.07,z+.025)
            neutral.append((x,y,z-.12))
    for x in (-12.,-6.,0.,6.,12.):
        for y in (-244.5,-247.):
            z=8.72
            mb.box(M['lamp_neutral'],x-.85,y-.07,z,x+.85,y+.07,z+.025)
            neutral.append((x,y,z-.12))
    # Photo13 has a small warm illuminated patch at the upper left, with the
    # remaining upper facade dark. It does not justify lighting every window.
    for x in (11.,7.):
        z=23.58;y=-246.
        mb.box(M['lamp_warm'],x-.9,y-.09,z,x+.9,y+.09,z+.025)
        warm.append((x,y,z-.15))
    for sx in (-1,1):
        for y in (-210.,-219.,-230.):
            z=8.12;x=sx*18.2
            mb.box(M['lamp_neutral'],x-.15,y-.15,z,x+.15,y+.15,z+.03)
            neutral.append((x,y,z-.15))
    o=mb.to_object('Academic_V18_Permanent_Luminaires',C['details']);parent_keep(o,root)
    o['zc_evidence']='photo13/4: lit entrances and arcade; fixture layout/brightness estimated; event strings excluded'
    for points,kind in ((neutral,'lobby_neutral'),(warm,'lobby_warm')):
        for light in add_lights('V18_Academic_'+kind,points,kind,80.,o['zc_evidence']):parent_keep(light,root)
