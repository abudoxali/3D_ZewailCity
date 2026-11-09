"""Spawn points and landmarks for the game-ready campus (Blender coordinates).

This is the single source for both. `build_game_assets.py` turns these entries
into empties in the Game_Spawn_Points / Game_Landmarks collections and writes
them to output/game_ready/campus_manifest.json, which the Godot explorer reads.

Coordinates are Blender metres: origin = dome centre, +Y = toward the main gate
along the campus axis, Z up. `facing` is a 2D direction in the XY plane.

Spawn heights are not stored. The Godot loader drops each spawn onto the
collision floor with a downward ray, so spawns stay grounded if the site
geometry changes.

V4: positions follow the survey layout (utilities/survey.py). The order of the
first six spawns is kept (keys 1-6 and the automated tests rely on it); the
exterior gate spawn is appended as spawn 7.

Landmark labels use only identities supported by references/SOURCE_EVIDENCE.md.
The east institute's identity is unconfirmed, and its label says so.
"""
import math

from . import survey as SV

GY = SV.GATE_Y


def _local_to_world(spec, lx, ly):
    a = math.radians(spec['angle_deg'])
    cx, cy = spec['center']
    return (cx + lx * math.cos(a) - ly * math.sin(a), cy + lx * math.sin(a) + ly * math.cos(a))


def _local_dir(spec, dx, dy):
    a = math.radians(spec['angle_deg'])
    return (dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a))


def _unit(dx, dy):
    n = math.hypot(dx, dy)
    return (dx / n, dy / n)


_helmy_front = _local_to_world(SV.HELMY, 0.0, SV.HELMY['width'] / 2 + 14.0)
_nano_front = _local_to_world(SV.EAST_INSTITUTE, -10.0, SV.EAST_INSTITUTE['width'] / 2 + 14.0)

# id, label, (x, y), facing (dx, dy), note
SPAWN_POINTS = [
    ("SPAWN_01_Main_Entrance", "Main gate, inside (east walkway)", (15.0, GY - 6.6), (0.0, -1.0),
     "Paved plaza just inside the portal frame, beside the outbound lane (C02, D02, OSM gate nodes)."),
    ("SPAWN_02_Administration", "Administration & Cultural Building forecourt", (0.0, 35.0), (0.0, -1.0),
     "Forecourt paving between the portico steps and the drop-off loop (A01, A02, OSM 912696912)."),
    ("SPAWN_03_Academic", "Academic Building, Gate (A) courtyard", (0.0, -176.0), (0.0, -1.0),
     "Courtyard between the two forward prongs, facing the Gate (A) front (D05, OSM 540106547)."),
    ("SPAWN_04_Institutes", "Helmy Institute forecourt", _helmy_front, _local_dir(SV.HELMY, 0.0, -1.0),
     "In front of the Helmy Institute's long facade (A05, OSM 540106545)."),
    ("SPAWN_05_Central_Overview", "Approach walkway (east), facing the admin", (16.3, 205.0), (0.0, -1.0),
     "East walkway of the approach between the planted strip and the outer bed (C02, OSM approach)."),
    ("SPAWN_06_East_Institute", "East research institute forecourt", _nano_front,
     _local_dir(SV.EAST_INSTITUTE, 0.0, -1.0),
     "In front of the east institute (OSM 540106546; A01). Identity unconfirmed."),
    ("SPAWN_07_Main_Gate_Exterior", "Main gate, outside (Ahmed Zewail Road side)", (-19.0, GY + 12.5),
     _unit(0.2, -1.0),
     "Exterior apron in front of the west gate building, facing the portal and the pedestrian gate (C01, D03)."),
]

# id, label, (x, y, z) focus point, radius m (for "you are near" HUD), verified, evidence, spawn id
# (selecting a landmark in the explorer teleports to its spawn)
LANDMARKS = [
    ("LM_Main_Gate", "Main gate (portal frame and gatehouse)", (0.0, GY, 9.0), 45.0, True,
     "Commons C01/C02 (2017-11-18), official D02/D03; OSM gate nodes 5225739523/5225739528.",
     "SPAWN_07_Main_Gate_Exterior"),
    ("LM_Approach_Road", "Approach road", (0.0, 200.0, 1.0), 45.0, True,
     "OSM 685373372 / 912696914; C02 (2017), A04.", "SPAWN_05_Central_Overview"),
    ("LM_Flower_Bed", "Circular flower bed", (0.0, 82.0, 0.5), 18.0, True,
     "A01, A02, C02 (white pebbles, dark gravel, marigold rings). Position estimated.", "SPAWN_02_Administration"),
    ("LM_Administration", "Administration & Cultural Building", (0.0, 0.0, 12.0), 95.0, True,
     "A01-A04 photographs; OSM 540106548; Hassan Allam project page.", "SPAWN_02_Administration"),
    ("LM_Copper_Dome", "Copper dome", (0.0, 0.0, 30.0), 30.0, True,
     "A01-A03 photographs (copper drum, banded shallow dome, mast).", "SPAWN_02_Administration"),
    ("LM_Academic_Gate_A", "Academic Building, Gate (A)", (0.0, SV.ACADEMIC['core_front_y'], 4.0), 28.0, True,
     "Official zewailcity.edu.eg image 'Academic Building Gate A' (D05); OSM 540106547.", "SPAWN_03_Academic"),
    ("LM_Academic", "Academic Building", (0.0, -230.0, 14.0), 115.0, True,
     "OSM 540106547; A01 front blocks; D05.", "SPAWN_03_Academic"),
    ("LM_Helmy_Institute", "Helmy Institute for Medical Sciences",
     (SV.HELMY['center'][0], SV.HELMY['center'][1], 10.0), 70.0, True,
     "SIAC project page and A05 aerial; OSM 540106545.", "SPAWN_04_Institutes"),
    ("LM_East_Institute", "East research institute (identity unconfirmed)",
     (SV.EAST_INSTITUTE['center'][0], SV.EAST_INSTITUTE['center'][1], 10.0), 60.0, False,
     "OSM 540106546; A01. Presumed NBE Nanosciences, not confirmed.", "SPAWN_06_East_Institute"),
]

SPAWN_FRONTS = {"helmy": _helmy_front, "nano": _nano_front}

# Append all new locations; the original seven indices stay stable.
from .gate_inventory import RECORDS as GATES
for r in GATES[1:]:
    x,y=r['model_position_blender_m']
    dx,dy=r['inward']
    SPAWN_POINTS.append((r['spawn'],r['id']+' '+r['label']+' (provisional)',(x+dx*8,y+dy*8),(-dx,-dy),
                         'OSM gate-node cluster; boundary opening and architecture estimated. Current access unconfirmed.'))
    LANDMARKS.append(('LM_Gate_'+r['id'],r['id']+' '+r['label']+' (provisional)',(x,y,2.),25.,False,
                      'OSM '+','.join(str(n) for n in r['osm_nodes'])+'; owner reports six gates. No gate photograph.',r['spawn']))

SPAWN_POINTS.extend([
    ('SPAWN_13_Academic_Courtyard','Academic inner courtyard',(0.,-280.),(0.,-1.),
     'Owner-described courtyard and central route; dimensions and landscaping estimated.'),
    ('SPAWN_14_Dormitory_Candidate','Dormitory candidate / garden approach',(425.,-555.),(-.4,-1.),
     'Five-storey pair fits owner left/rear description; identity and garden layout remain unconfirmed.')])
LANDMARKS.extend([
    ('LM_Academic_Courtyard','Academic inner courtyard',(0.,-280.,1.),58.,False,
     'Owner confirms courtyard, palms, seating and through-route. Geometry/layout estimated; cafeteria is in basement per official dining page.',
     'SPAWN_13_Academic_Courtyard'),
    ('LM_Dormitory_Candidate','Student dormitory candidate (identity unconfirmed)',(390.,-603.,1.),85.,False,
     'OSM 540106540/541 five storeys; owner left/rear location and central garden; D01 photo does not geolocate the building.',
     'SPAWN_14_Dormitory_Candidate')])
import math as _m
_A = SV.ACADEMIC
_gc = (_A['curve_c'][0] + (_A['r_out'] + 3.) * _m.cos(_m.radians(225.)), _A['curve_c'][1] + (_A['r_out'] + 3.) * _m.sin(_m.radians(225.)))
LANDMARKS.extend([
    # V11: labels sit only on real reachable entrances (owner 10/13). Positions follow
    # references/academic_entrances_v11.json (owner X marks; lettering hypothesis).
    ('LM_Building_C','Academic Building, Gate (C) (position estimated)',(_gc[0],_gc[1],3.),16.,False,
     'P12 shows Gate (C) on the curved stone face. Placed at the owner X mark at 225 deg (sequential-lettering hypothesis); not a boundary gate.',
     'SPAWN_13_Academic_Courtyard'),
    ('LM_Building_F','UST / Gate (F) (corner position estimated)',(_A['r_out']+4.,-223.,3.),20.,False,
     'P14 shows the UST panel and Gate (F); owner 13 places it at the corner. +X side-wing corner estimated; not a boundary gate.','SPAWN_03_Academic'),
    ('LM_Academic_Rear_Passage','Academic rear passage',(0.,_A['curve_c'][1]-_A['r_out']-2.,2.),18.,False,
     'Owner 09: the court connects to the rear open area through the rear passage (ring aperture 266-274 deg). Width/height estimated.',
     'SPAWN_13_Academic_Courtyard'),
    ('LM_Academic_Upper_Terrace','Academic upper terrace',(0.,-226.,5.4),20.,False,
     'Owner: two great stairs reach an open upper terrace with railed openings overlooking the ground floor (14, P09). Dimensions estimated.',
     'SPAWN_03_Academic')])
