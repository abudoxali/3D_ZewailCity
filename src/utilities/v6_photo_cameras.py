"""Fixed reference-review poses. Approximate perspective fits, never surveyed cameras."""
import json,math
from pathlib import Path
import bpy
from mathutils import Vector
PHOTOS={
 'P09':('photo_2026-11-07_15-14-14.jpg',(0,-224.1,6.11),(0,-45,12),30,(1280,1086),'Academic upper landing looking +Y; dome/admin sightline anchors yaw; FOV/height estimated.'),
 'P13':('photo_2026-11-07_15-14-31.jpg',(61,-269,1.95),(35,-333,10),24,(960,1280),'Academic inner arc; ground-eye height, tangent view, curvature and projecting bays fitted approximately.'),
 'P15':('photo_2026-11-07_15-14-36.jpg',(26,-285,2.55),(-1,-249,11),25,(960,1280),'Inner court toward central bridge; portal/terrace correspondence is a spatial hypothesis.'),
 'P16':('photo_2026-11-07_15-14-46.jpg',(424,-566,9.2),(385,-623,9),26,(1031,1280),'Southern OSM candidate court; facade rhythm / garden design only, geographic identity UNVERIFIED.'),
 'P04':('photo_2026-11-07_15-13-59.jpg',(425,-568,10.5),(385,-621,9),25,(1280,1065),'Dusk reference of same garden-design cluster; candidate block location unconfirmed.'),
 'P12':('photo_2026-11-07_15-14-26.jpg',(25,-389,1.9),(0,-348,11),25,(960,1280),'Outer curved Academic rear-bay hypothesis; Gate C angle/location not independently established.'),
 'P14':('photo_2026-11-07_15-14-34.jpg',(112,-249,1.9),(52,-193,13),24,(960,1280),'East-prong hypothesis: admin dome lies to image right; Gate F exact wing/position UNVERIFIED.'),
 'Court_Overview':('',(115,-375,70),(0,-278,3),32,(1280,720),'Overview, NOT CAMERA-ALIGNED to an owner photograph.'),
}
def build(scene,coll):
    for key,(_,loc,tgt,lens,size,note) in PHOTOS.items():
        cam=bpy.data.objects.get('REF_V6_'+key)
        if cam:cd=cam.data
        else:
            cd=bpy.data.cameras.new('REF_V6_'+key)
            cam=bpy.data.objects.new('REF_V6_'+key,cd);coll.objects.link(cam)
        cam.location=loc;cam.rotation_euler=(Vector(tgt)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
        cd.lens=lens;cd.sensor_fit='HORIZONTAL';cd.sensor_width=36.;cd.clip_start=.1;cd.clip_end=5000
        cam['zc_photo_id']=key;cam['zc_camera_fit']='APPROXIMATE / NOT CALIBRATED';cam['zc_assumptions']=note
    out=Path(__file__).resolve().parents[2]/'output/validation/v11'
    out.mkdir(parents=True,exist_ok=True)
    (out/'reference_cameras.json').write_text(json.dumps({k:{'filename':v[0],'location':v[1],'target':v[2],'lens_mm':v[3],'resolution':v[4],'fit':'APPROXIMATE, NOT A CALIBRATED PHOTO MATCH','assumptions':v[5]} for k,v in PHOTOS.items()},indent=2))
