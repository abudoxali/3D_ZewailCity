"""V7 architectural showcase: short, eased ground-level shots joined by hard cuts.

Replaces long empty-terrain transits with cuts between the improved areas:
approach road + main gate, approach walkway, admin forecourt, Academic Gate (A)
and stairs, the P15 portal into the stepped court, the court walkway and ramp,
the dormitory candidate garden and facade. Scripted camera, estimated geometry;
every frame is clearance-checked against the render geometry in Godot.
"""
import math
from .ground_system import datum

FPS = 30
KEY_STEP = 6     # frames between keys; LINEAR keys this dense read as smooth motion


def _ease(t):
    return t * t * (3 - 2 * t)


def _lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def _foot(x, y, paved=True):
    return datum(x, y) + (0.21 if paved else 0.012)


SEGMENTS = [
    # (camera start, camera end, target start, target end, seconds, caption)
    ((-118., 366., None), (-46., 362., None), (0., 322., 7.), (0., 318., 7.5), 9.,
     'V7 showcase | approach road surface and main gate (V4 photo-based gate retained)'),
    # V7 review: the first cut passed 2 m from a portal leg (wall filled half the frame);
    # the shot now dollies in on the gate centre line, >= 9 m from every leg.
    ((-3., 358., None), (-2., 338., None), (0., 316., 8.5), (0., 296., 5.), 7.,
     'Main gate: stone portal, lane and pedestrian gates, graded apron'),
    ((-16.3, 296., None), (-16.3, 262., None), (-12., 230., 2.2), (-8., 200., 3.), 8.,
     'Approach walkway: paving joints, edge restraints and planted strips'),
    ((24., 70., None), (12., 54., None), (0., 20., 11.), (0., 18., 10.), 7.,
     'Administration and Cultural Building forecourt'),
    ((2., -168., None), (-1.5, -203., None), (-6., -228., 3.5), (0., -231., 4.6), 9.,
     'Academic Gate (A) forecourt and the paired major stairs (P09)'),
    # V11: the great stair runs from the forecourt (y -208.9) to the 4.41 m terrace (y -219).
    ((-10.1, -203., None), (-10.1, -222., 6.13), (-10.1, -232., 6.4), (-3., -258., 5.0), 8.,
     'V11 great stair to the upper terrace: 28 estimated 150 mm risers, 12.5 m wide, metal rails'),
    ((0., -219., None), (0., -257., None), (0., -262., 3.4), (0., -300., 3.0), 9.,
     'P15: deep stone portal and covered public passage into the court'),
    ((66.7, -270., None), (40., -307., None), (10., -290., 2.5), (-12., -285., 3.0), 11.,
     'P13: court walkway, dark granite risers, platform poles and curved glazing'),
    ((10.5, -317., None), (10.5, -292., 1.11), (-25., -296., 5.), (-45., -282., 8.), 8.,
     'Estimated 3.4% ramp to the upper court level'),
    ('DORM_PATH_A', 'DORM_PATH_B', None, None, 10.,
     'P04/P11/P16 design: paver paths, pebble borders, bed shrubs, bollards | candidate site UNVERIFIED'),
    ((418., -566., 6.0), (406., -575., 6.0), (385., -622., 9.), (388., -624., 10.), 8.,
     'Dormitory candidate facade: window rhythm, cores, plinth | geographic identity UNVERIFIED'),
]


def _resolve(p):
    x, y, z = p
    if z is None:
        z = _foot(x, y) + 1.72
    elif z < 3.0:
        z = z + 1.72          # explicit foot level supplied
    return (x, y, z)


def shot():
    from . import dormitory
    cams, targets, labels = [], [], []
    frame = 1
    line = dormitory.LINES[0]
    for c0, c1, t0, t1, seconds, caption in SEGMENTS:
        if c0 == 'DORM_PATH_A':
            pts = [line.interpolate(d) for d in (6., 32.)]
            c0 = (pts[0].x, pts[0].y, dormitory.height(pts[0].x, pts[0].y) + 1.72)
            c1 = (pts[1].x, pts[1].y, dormitory.height(pts[1].x, pts[1].y) + 1.72)
            ahead = [line.interpolate(d) for d in (24., 46.)]
            t0 = (ahead[0].x, ahead[0].y, 1.4)
            t1 = (ahead[1].x, ahead[1].y, 2.2)
        else:
            c0, c1 = _resolve(c0), _resolve(c1)
        n = max(2, int(seconds * FPS))
        labels.append((frame, caption))
        for k in range(0, n + 1, KEY_STEP):
            t = _ease(min(1.0, k / n))
            cams.append((frame + k, _lerp(c0, c1, t)))
            targets.append((frame + k, _lerp(t0, t1, t)))
        if (n % KEY_STEP) != 0:
            cams.append((frame + n, c1))
            targets.append((frame + n, t1))
        frame += n + 1      # next key on the following frame: a hard cut
    return (24., cams, targets, labels)
