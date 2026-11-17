"""Eliminate rejected artificial vegetation without adding speculative species."""
import json
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]


def audit_and_remove():
    removed = []
    reject = ('ASSET_Cypress_', 'ASSET_V6_Garden_Evergreen',
              'ASSET_Shrub_Green_', 'ASSET_V7_Round_Shrub_',
              'ASSET_Cycad_', 'ASSET_Agave_', 'ASSET_Barrel_Cactus', 'ASSET_Euphorbia_')
    for o in list(bpy.data.objects):
        if o.type == 'MESH' and o.data.name.startswith(reject):
            removed.append({'name':o.name,'mesh':o.data.name,
                            'position':list(o.matrix_world.translation)})
            bpy.data.objects.remove(o, do_unlink=True)
    live = [o for o in bpy.data.objects if o.type=='MESH' and
            o.data.name.startswith(('ASSET_V13_Pachira','ASSET_V13_Date_Palm',
                                    'ASSET_V13_Palm_Detailed'))]
    dest=ROOT/'output/build_metadata/v16/vegetation.json'
    prior=json.loads(dest.read_text()).get('removed',[]) if dest.exists() else []
    removed=list({v['name']:v for v in prior+removed}.values())
    report = {'removed':removed, 'licensed_trees_palms_retained':len(live),
              'replacement_policy':'Elimination at unverified species locations; existing licensed trees and palms retained. No new tree geometry.',
              'remaining_procedural':'Clipped dormitory hedge/row masses, low flower borders and lawn surfaces; no species claim.',
              'remaining_rejected_instances':sum(o.type=='MESH' and o.data.name.startswith(reject) for o in bpy.data.objects)}
    p = ROOT/'output/build_metadata/v16/vegetation.json'
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(report,indent=2))
    print('[v16 vegetation]',len(removed),'removed;',len(live),'licensed trees/palms retained',flush=True)
