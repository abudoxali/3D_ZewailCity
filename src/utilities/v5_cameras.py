"""Review cameras for evidence-labelled V5 features, regenerated with the scene."""
from .scene_setup import _camera
from .gate_inventory import RECORDS

def build(scene,coll):
    views={
        'Ground_And_Roads':((0,-206.1,1500),(0,-206.1,0),24.,1200.),
        'Main_Gate_Outside':((-30,360,1.8),(0,314.6,8),24.,None),
        'Main_Gate_Inside':((-18,276,1.8),(0,314.6,8),24.,None),
        'Academic_Entrance':((0,-205,1.83),(0,-239,3),24.,None),
        'Academic_Left_Stair':((-13,-213,1.83),(-13,-231,4.5),24.,None),
        'Academic_Right_Stair':((13,-213,1.83),(13,-231,4.5),24.,None),
        'Academic_Courtyard':((0,-225,75),(0,-285,0),24.,None),
        'Academic_Passage':((0,-239,1.83),(0,-270,1.83),24.,None),
        'Rear_Soil':((0,-380,1.83),(0,-450,1),24.,None),
        'Dormitory_Candidate':((455,-555,55),(390,-603,0),24.,None)}
    for g in RECORDS[1:]:
        x,y=g['model_position_blender_m']
        dx,dy=g['inward']
        views[g['id']+'_Provisional_Gate']=((x-dx*18,y-dy*18,2.),(x,y,1.5),24.,None)
    for name,(loc,target,lens,ortho) in views.items():
        cam=_camera('CAM_V5_'+name,coll,loc,target,lens,ortho)
        cam.data.clip_start=.1
        cam['resolution']=[1120,1200] if name=='Ground_And_Roads' else [1280,720]
