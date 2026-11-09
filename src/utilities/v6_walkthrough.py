"""Continuous camera walk: both stairs, court levels, rear soil and photo garden.
Recorded tour is scripted, never a human playtest. Outdoor connection accelerated.
"""
import math
from .ground_system import datum
from . import dormitory

def shot():
    frame=1;cams=[(1,(-10.1,-203.,1.91))];targets=[(1,(-10.1,-219.,5.))]
    labels=[(1,'V6 photo-grounded walkthrough | scripted camera, estimated dimensions')]
    def move(x,y,foot=.21,speed=4.5,label=None):
        nonlocal frame
        p=(x,y,foot+1.7);old=cams[-1][1]
        dist=math.dist(p,old);frame+=max(12,math.ceil(dist/speed*30))
        dx,dy=x-old[0],y-old[1];n=max(.001,math.hypot(dx,dy))
        cams.append((frame,p));targets.append((frame,(x+dx/n*12,y+dy/n*12,p[2]+.10)))
        if label:labels.append((frame,label))
    def hold(target,seconds=2.):
        nonlocal frame
        frame+=round(seconds*30);cams.append((frame,cams[-1][1]));targets.append((frame,target))
    # V11: great stairs from the forecourt (y -208.9) to the 4.41 m terrace (y -219); the walk goes
    # round void A (|x| < 5.8, y -229.5..-221.5) to the cross band and back. Cameras at |x| 10.1,
    # clear of the mid-flight rail at |x| 13.25.
    move(-10.1,-208.9,label='V11: left great stair to the upper terrace')
    move(-10.1,-219.,4.41,speed=2.4);move(-10.1,-221.5,4.41)
    move(-8,-226.,4.41);move(-8,-232.,4.41);move(0,-232.,4.41,label='Upper terrace between the two railed voids')
    hold((0,-70,14),3.)
    move(-8,-232.,4.41);move(-8,-221.,4.41);move(-10.1,-219.4,4.41);move(-10.1,-208.9,speed=2.4)
    move(-10.1,-203.);move(10.1,-203.,label='V11: right great stair')
    move(10.1,-208.9);move(10.1,-219.,4.41,speed=2.4)
    hold((0,-246,10),1.5)
    move(10.1,-208.9,speed=2.4);move(10.1,-203.);move(0,-203.)
    move(0,-239.,label='P15: deep stone portal and public passage')
    move(0,-264.);move(0,-280.,label='P13: projecting glazed bays, recessed balconies and stepped court')
    hold((59,-302,13),3.)
    move(0,-315.);move(10.5,-315.)
    move(10.5,-285.,1.11,label='Estimated terrace ramp; three physical court levels')
    hold((-45,-302,13),2.)
    move(10.5,-315.);move(0,-315.);move(0,-340.)
    move(0,-368.,datum(0,-368)+.012,label='Rear passage to the rear open area (owner 09) | rear sandy ground')
    for x,y in [(0,-430),(0,-500),(150,-520),(250,-525),(350,-525),dormitory.INGRESS]:
        move(x,y,datum(x,y)+.012,speed=14.,label='Accelerated continuous outdoor connection; estimated earth walking line' if y==-430 else None)
    labels.append((frame,'P04/P16: photo-supported dormitory candidate; geographic identity UNVERIFIED'))
    line=dormitory.LINES[0]
    for distance in list(range(5,int(line.length),5))+[line.length]:
        p=line.interpolate(distance);move(p.x,p.y,dormitory.height(p.x,p.y),speed=3.6)
    hold((401,-632,12),3.)
    return (25.,cams,targets,labels)
