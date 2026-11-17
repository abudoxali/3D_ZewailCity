"""One explicit, reviewable relative vertical datum shared by mesh and architecture.

The owner establishes the *direction* of descent; its 2.4 m magnitude is a
functional hypothesis. Never substitute DEM context for building survey levels.
"""
import json, math
from functools import lru_cache
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SPEC=json.loads((Path(__file__).parent/'data/v17_elevation.json').read_text())
PROFILE=SPEC['profile_y_z_m']

def smooth(t):
    t=max(0.,min(1.,t));return t*t*(3.-2.*t)

def longitudinal(y):
    for (a,za),(b,zb) in zip(PROFILE[:-1],PROFILE[1:]):
        if a<=y<=b: return za+(zb-za)*smooth((y-a)/(b-a))
    return 0.

@lru_cache(maxsize=400000)
def datum(x,y):
    # Building foundations remain planar; continuous 12 m pad collars carry the
    # difference into the road and terrain functions without a hidden collider.
    from . import survey as SV
    z=longitudinal(y)
    for spec in (SV.HELMY,SV.EAST_INSTITUTE):
        cx,cy=spec['center'];angle=math.radians(spec['angle_deg'])
        dx,dy=x-cx,y-cy
        u=dx*math.cos(angle)+dy*math.sin(angle)
        v=-dx*math.sin(angle)+dy*math.cos(angle)
        d=math.hypot(max(0.,abs(u)-spec['length']/2-3.),max(0.,abs(v)-spec['width']/2-3.))
        if d<12.: z=longitudinal(cy)+(z-longitudinal(cy))*smooth(d/12.)
    # Keep the broad terrain tied to a finite context without changing local
    # entrance/road elevations. No artificial hills or Google elevation claims.
    return z*(1.-smooth((abs(x)-650.)/1000.))

def seat_architecture():
    import bpy
    from mathutils import Vector
    rows=[]
    for o in list(bpy.data.objects):
        if o.parent or not o.name.startswith('AB_') or o.type!='MESH': continue
        if o.name.startswith('AB_Gate_'): continue  # V11 gate builder already uses datum
        points=[o.matrix_world@Vector(p) for p in o.bound_box]
        x=(min(p.x for p in points)+max(p.x for p in points))/2
        y=(min(p.y for p in points)+max(p.y for p in points))/2
        dz=datum(x,y)
        o.location.z+=dz
        o['zc_v17_pad_datum_m']=dz
        o['zc_v17_level_confidence']='ESTIMATED magnitude; owner confirms Administration > Academic direction'
        rows.append({'object':o.name,'center_xy':[x,y],'rigid_offset_m':dz})
    # Dorm garden objects parented to residential shell follow the same datum.
    # Standalone poles/fixtures were already graded by ground_system; light
    # sources and camera eye positions are adjusted separately, once.
    out=ROOT/'output/build_metadata/v17';out.mkdir(parents=True,exist_ok=True)
    report={'specification':SPEC,'rigid_building_offsets':rows,'sections':[]}
    for name,pts in [
        ('G1_Admin_Academic_Rear',[(0.,float(y)) for y in range(330,-551,-2)]),
        ('Academic_cross_section',[(float(x),-274.) for x in range(-130,131,2)]),
        ('Dorm_cross_section',[(float(x),-603.) for x in range(300,481,2)])]:
        samples=[[x,y,datum(x,y)] for x,y in pts]
        grades=[abs(b[2]-a[2])/math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(samples[:-1],samples[1:])]
        report['sections'].append({'name':name,'samples_xyz_m':samples,'max_grade':max(grades)})
    (out/'elevation_audit.json').write_text(json.dumps(report,indent=1))
    print('[V17 elevation]',len(rows),'rigid buildings; 2.4 m relative descent is ESTIMATED',flush=True)

def seat_cameras_and_lights():
    import bpy
    from .cinematics import _fcurves
    for o in bpy.data.objects:
        if o.animation_data and o.animation_data.action and (o.type=='CAMERA' or o.name.endswith('_Target')) and not o.get('zc_v17_animation_keyframes_seated'):
            curves=[f for f in _fcurves(o.animation_data) if f.data_path=='location']
            axes={f.array_index:f for f in curves}
            if all(i in axes for i in (0,1,2)):
                for key in axes[2].keyframe_points:
                    frame=key.co.x;dz=datum(axes[0].evaluate(frame),axes[1].evaluate(frame))
                    key.co.y+=dz;key.handle_left.y+=dz;key.handle_right.y+=dz
                o['zc_v17_animation_keyframes_seated']=True
                o['zc_v17_elevation_seated']=True
        if o.parent or o.type not in ('CAMERA','LIGHT') or o.get('zc_v17_elevation_seated'):continue
        if o.type=='LIGHT' and o.data.type=='SUN':continue
        o.location.z+=datum(o.location.x,o.location.y)
        o['zc_v17_elevation_seated']=True
    bpy.context.scene.frame_set(bpy.context.scene.frame_current)

def source_section_curves():
    import bpy
    from .geometry import get_collection
    c=get_collection('V17_Elevation_Sections_SOURCE_ONLY');c.hide_render=True
    for name,pts in [('Axis',[(0.,float(y)) for y in range(330,-551,-2)]),
                     ('Academic_Transverse',[(float(x),-274.) for x in range(-130,131,2)])]:
        d=bpy.data.curves.new('LEVEL_SECTION_'+name,'CURVE');d.dimensions='3D'
        s=d.splines.new('POLY');s.points.add(len(pts)-1)
        for p,(x,y) in zip(s.points,pts):p.co=(x,y,datum(x,y)+.06,1.)
        o=bpy.data.objects.new(d.name,d);c.objects.link(o)
        o['zc_evidence']=SPEC['classification'];o['zc_vertical_exaggeration']=1.
    for vl in bpy.context.scene.view_layers:
        lc=vl.layer_collection.children.get(c.name)
        if lc:lc.exclude=True
