"""Remove only zero-area float32 collapses from emitted surfaces, with an audit."""
from pathlib import Path
import json
import bpy,bmesh

def clean_surfaces():
    rows=[]
    for name in ('Road_Network_Internal','Road_Network_External','Road_Curb_Edges','Kerb_Box_Collision_Proxy','Plaza_Paving','Plaza_Academic_Courtyard','Ground_Campus_Plot','Ground_Desert_Sand','Lawns'):
        o=bpy.data.objects.get(name)
        if not o:continue
        count=0;area=0.;passes=0
        for attempt in range(8):
            bad=[f for f in o.data.polygons if f.area<1e-12]
            if not bad:break
            area+=sum(f.area for f in bad);count+=len(bad);passes+=1
            ids={f.index for f in bad}
            bm=bmesh.new();bm.from_mesh(o.data);bm.faces.ensure_lookup_table()
            bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.index in ids],context='FACES_ONLY')
            bm.to_mesh(o.data);bm.free();o.data.update()
        if any(f.area<1e-12 for f in o.data.polygons):raise RuntimeError('Numerical face cleanup did not converge: '+name)
        if count:rows.append({'object':name,'removed_collapsed_faces':count,'total_removed_area_m2':area,'passes':passes})
    p=Path(__file__).resolve().parents[2]/'output/build_metadata/v17/float32_cleanup.json'
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps({'threshold_m2':1e-12,'changes':rows,'policy':'Only collapsed numerical faces; no hole-sized geometry deletion'},indent=1))
    print('[V17 float32 cleanup]',rows,flush=True)
