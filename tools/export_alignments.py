"""Blender -b edited.blend --python tools/v17_export_alignments.py -- --out sources.json

Export ALL vehicle + footway + area boundary source splines, including holes,
estimated widths, sidewalk widths and union parameters. Place this snapshot at
src/utilities/data/v17_alignment_overrides.json to rebuild. The original dated
OSM JSON and rollback envelopes are never edited. POLY source splines are native
editable curves; converting one to a different spline type requires conversion
back to POLY before export, avoiding any silently discarded Bezier handles.
"""
import argparse
import json
from pathlib import Path
import sys
import bpy

p=argparse.ArgumentParser();p.add_argument('--out',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
coll=bpy.data.collections['V17_Editable_Transport_Sources']
document=json.loads(coll['zc_document_metadata']);rows=[]
for key in document['parameters']:document['parameters'][key]=float(coll[key])
objects=list(coll.objects)
if all('zc_source_order' in obj for obj in objects):objects.sort(key=lambda o:o['zc_source_order'])
for obj in objects:
    if obj.type!='CURVE':continue
    row=json.loads(obj['zc_source_metadata']);arrays=[]
    for spline in obj.data.splines:
        if spline.type!='POLY':raise ValueError('Convert source spline to POLY before export: '+obj.name)
        pts=[]
        for point in spline.points:
            v=obj.matrix_world@point.co.xyz
            pts.append([float(v.x),float(v.y)])
        if row['geometry']=='area':
            if not spline.use_cyclic_u:raise ValueError('Area boundary must remain closed: '+obj.name)
            pts.append(pts[0])
        arrays.append(pts)
    if row['geometry']=='line':
        if len(arrays)!=1:raise ValueError('Vehicle/footway source must have one axis spline: '+obj.name)
        row['points']=arrays[0];row['width_m']=float(obj['zc_width_m'])
        if 'sidewalk_m' in row:row['sidewalk_m']=float(obj['zc_sidewalk_m'])
    else:row['rings']=arrays
    # Keep the exact double-precision source for unchanged native float32
    # splines. This prevents a save/export cycle from collapsing sub-mm valid
    # kerb-boundary vertices or drifting the dated reference envelope.
    if json.dumps(arrays,separators=(',',':'))==obj.get('zc_native_signature'):
        row.update(json.loads(obj['zc_original_geometry']))
    if 'zc_immutable_source' in obj:
        original=json.loads(obj['zc_immutable_source'])
        prior=original.get('rings',[original.get('points',[])])
        if len(prior)!=len(arrays) or any(len(a)!=len(b) or
                any(abs(x-u)>.001 or abs(y-v)>.001 for (x,y),(u,v) in zip(a,b))
                for a,b in zip(prior,arrays)):
            raise ValueError('External reference geometry is immutable: '+obj.name)
        if abs(float(row.get('width_m',0))-float(original.get('width_m',0)))>.0001:
            raise ValueError('External reference width is immutable: '+obj.name)
        row=original
    rows.append(row)
document['sources']=rows
out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(document,indent=1),encoding='utf-8')
print('Exported',len(rows),'vehicle/pedestrian/area sources to',out)
