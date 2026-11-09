"""V15 fixed eye-level/close inspection poses for the G1 -> Administration pilot (Blender eye/target,
stored in Godot coordinates). Existing poses are never modified."""
import json, sys, math
import numpy as np
def look_q(f):
    f=np.array(f,float);f/=np.linalg.norm(f);z=-f;x=np.cross([0,1,0],z);x/=np.linalg.norm(x);y=np.cross(z,x)
    m=np.array([x,y,z]).T;t=m.trace()
    if t>0:s=math.sqrt(t+1)*2;return [(m[2,1]-m[1,2])/s,(m[0,2]-m[2,0])/s,(m[1,0]-m[0,1])/s,s/4]
    i=int(np.argmax(np.diag(m)));j,k=(i+1)%3,(i+2)%3;s=math.sqrt(1+m[i,i]-m[j,j]-m[k,k])*2
    q=[0,0,0,0];q[i]=s/4;q[j]=(m[j,i]+m[i,j])/s;q[k]=(m[k,i]+m[i,k])/s;q[3]=(m[k,j]-m[j,k])/s;return q  # copied from tools/v12_add_road_poses.py
U = 260.4  # survey.APPROACH_U_TURN_Y
POSES = {
    'V15_crossover_bands_eye': ((-6.0, U + 15.5, 1.7), (-6.0, U - 2.0, 0.0), 'Crossover transverse bands (C02), inbound carriageway'),
    'V15_median_eye': ((-3.0, 232.0, 1.7), (0.0, 205.0, 0.35), 'Palm median from pedestrian eye level at the carriageway edge'),
    'V15_verge_bed_close': ((-16.3, 200.0, 1.7), (-11.6, 191.0, 0.15), 'Kerbed verge bed with groundcover from the walkway (C02)'),
    'V15_kerb_close': ((-6.5, 150.0, 1.5), (-9.7, 156.0, 0.2), 'Precast kerb units at the verge edge, close'),
    'V15_ring_junction_kerbs': ((-15.0, 121.0, 1.7), (-8.0, 100.0, 0.2), 'Approach end / kerb returns toward the ring junction'),
    'V15_g1_inside_kerbs': ((-15.5, 300.0, 1.7), (-6.0, 312.0, 0.2), 'Inside G1: lane kerbs and median nose'),
}
def g(v):
    return [v[0], v[2], -v[1]]
for path in sys.argv[1:]:
    d = json.load(open(path)); added = []
    for name, (eye, tgt, note) in POSES.items():
        if name in d:
            continue
        e, t = np.array(g(eye), float), np.array(g(tgt), float)
        d[name] = {'o': e.round(3).tolist(), 'q': look_q(t - e), 'fixed_v15_pose': True, 'note': note,
                   'blender_eye': list(eye), 'blender_target': list(tgt)}
        added.append(name)
    json.dump(d, open(path, 'w'), indent=2); print(path, added)
