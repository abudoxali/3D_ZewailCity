"""Building entrances from P12/P14; exact facade coordinates remain hypotheses.

These are explicitly separate from the owner's six boundary gates. P14 dome
sightline supports an east-prong interpretation; it is not a surveyed location.
"""
import math,json
from pathlib import Path
import bpy
from mathutils import Matrix
from .architecture import Parts
from .geometry import Edge,get_collection,parent_keep
from .gate import _text_mesh,FONT_LAT
ENTRIES=[{'id':'B-C','photo':'P12','model_blender':[0,-348.5],'geographic_status':'UNVERIFIED rear-curve hypothesis','visible_label':'Gate (C)'},
         {'id':'B-F','photo':'P14','model_blender':[55.45,-205],'geographic_status':'UNVERIFIED +X-prong hypothesis from dome sightline','visible_label':'Gate (F)'}]

def text(P,M,e,s,z,words,size):
    me=_text_mesh(words,FONT_LAT,size)
    if me:
        p=e.at(s,.36)
        xf=Matrix.Translation((p.x,p.y,z))@Matrix.Rotation(e.angle,4,'Z')@Matrix.Rotation(math.pi/2,4,'X')
        P.det.add_mesh(M['stone_plain'],me,xf)

def write_legacy_registry():
    """V11: the V6 entrance geometry is superseded by v11_academic (owner 10/13). The V6
    register is kept for history with a pointer to the V11 registry."""
    out=Path(__file__).resolve().parents[2]/'references'
    (out/'internal_building_entries_v6.json').write_text(json.dumps({'classification':'BUILDING ENTRANCES; NOT PERIMETER GATES',
       'superseded_by':'references/academic_entrances_v11.json (V11 owner corrections 10/13)','entries':ENTRIES},indent=2))


def build(M,C):
    """V6-V10 entrance geometry (no longer called from V11)."""
    coll=get_collection('Academic_Internal_Entrances')
    root=bpy.data.objects['AB_Academic_Building']
    P=Parts('Academic_Building_Entrances',M)
    # P12: tall recessed dark bay on the curved outside wall. The retained open
    # route is a functional interpretation; the photographed doors' state is unknown.
    e=Edge((-7.,-348.5),(7.,-348.5))
    P.curtain(e,.15,13.85,4.3,7.6,mull=1.4,transom=2.8,off=.12)
    P.det.fbox(M['metal'],e,7.,.04,.3,14.,3.7,4.3)
    text(P,M,e,7.,3.88,'Gate (C)',.55)
    for side in [-1,1]:
        x=side*10.
        P.shell.box(M['stone'],x-2.,-348.6,.21,x+2.,-347.2,.66)
        for k in range(3):P.shell.box(M['stone'],x-2.,-348.6-(3-k)*.42,.16,x+2.,-348.6,.21+(k+1)*.15)
    # P14: UST / Gate F panel on a conservative east-prong hypothesis.
    e=Edge((55.45,-225.),(55.45,-185.))
    P.frame(e,17.,23.,.21,23.4,t=.65,depth=.5)
    P.curtain(e,17.,23.,.7,23.1,mull=3.,transom=5.,off=.2)
    text(P,M,e,20.,12.0,'UST',2.25)
    text(P,M,e,20.,2.2,'Gate (F)',.45)
    for k in range(6):P.shell.fbox(M['stone'],e,20.,0,.5*(6-k),6.,.21,.21+(k+1)*.15)
    P.det.fbox(M['stone'],e,31.,0,2.2,12.,5.,5.6)
    P.curtain(e,25.,37.,5.6,19.,mull=2.4,transom=3.3,off=2.)
    # P14 side ramp is visible; its 1:20 construction here remains estimated.
    verts=[(59.2,-223,.21),(61.6,-223,.21),(61.6,-205,1.11),(59.2,-205,1.11)]
    P.shell.raw(M['plaza_light'],verts,[(0,1,2,3)])
    for mb,suffix in [(P.shell,'Structure'),(P.glass,'Glass'),(P.det,'Details')]:
        if mb.empty():continue
        o=mb.to_object('Academic_Internal_Entries_'+suffix,coll)
        parent_keep(o,root);o['zc_collision']=suffix!='Glass'
        o['zc_evidence']='P12 Gate C / P14 Gate F are building entrances. Visible form; exact mapped facade positions UNVERIFIED.'
    out=Path(__file__).resolve().parents[2]/'references'
    (out/'internal_building_entries_v6.json').write_text(json.dumps({'classification':'BUILDING ENTRANCES; NOT PERIMETER GATES',
       'entries':ENTRIES},indent=2))
