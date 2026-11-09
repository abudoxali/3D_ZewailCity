"""Evidence-anchored site coordinates.

Coordinate system
-----------------
All layout coordinates are digitised from the CEGMAN/Aura site-plan drawing in the
2014 architecture brochure (B04, embedded image 6, 2692 x 2386 px), and checked
against the official 2025 campus aerial (A01) and contractor photographs (A02-A05).

* Blender +Y points to the top of that drawing, the main (north) gate and the
  front of the Administration & Cultural building. The drawing's north arrow is
  rotated about 20 degrees clockwise from its top edge, so +Y is roughly
  N 20 deg W (see SUN_AZIMUTH handling in scene_setup).
* Origin = centre of the copper dome (plan pixel 1574, 817).
* Scale = 0.595 m per plan pixel. Derivation: the drawing's dashed plot boundary
  encloses 2,369,158 px^2; the architect (B02) states an 840,000 m^2 land plot.
  sqrt(840000 / 2369158) = 0.5954. Independent check: the dome-drum diameter is
  20.8 m from the plan at this scale and about 20 m from photo A02 (scaled by an
  18 m, three-storey parapet), so the scale is plausible to within ~10 %.

Every anchor below records its plan pixel, the evidence IDs (see
references/REFERENCE_SOURCES.md) and a confidence level.
"""

PLAN_PX_TO_M = 0.595
PLAN_ORIGIN = (1574.0, 817.0)


def P(u, v):
    """Plan pixel -> Blender metres."""
    return ((u - PLAN_ORIGIN[0]) * PLAN_PX_TO_M, -(v - PLAN_ORIGIN[1]) * PLAN_PX_TO_M)


# Dashed plot boundary (plan corners) ---------------------------------- B04
BOUNDARY = [P(1096, 179), P(1906, 179), P(2511, 1993), P(737, 2029)]

# Circular campus road around the core --------------------------- B04 + A01
# Plan: ring top at v~737 in front of the admin, left/right extremes u~1079/2093.
CIRCLE_CENTER = (0.0, P(0, 1255)[1])          # x snapped to the campus axis
CIRCLE_RADIUS = 308.0
# Octagonal road / plaza around the Academic complex ------------------ B04
OCTAGON_APOTHEM = 135.0

# Gates (E markers on the plan) ---------------------------------------- B04
GATE_N = (0.0, P(0, 300)[1])
GATE_W = P(986, 1229)
GATE_E = P(2207, 1229)
GATE_S = (0.0, P(0, 1995)[1])

# Buildings (as built) -----------------------------------------------------
ADMIN = {   # B04 bldg 4; A01-A04 photographs; Hassan Allam: 3 floors + 2 basements, 36,000 m2 BUA
    'front_y': P(0, 781)[1],          # main front face of the central block (21.4 m)
    'portico_front_y': P(0, 767)[1],  # portico protrusion (29.8 m)
    'arm_front_y': P(0, 760)[1],      # lateral arms project toward the gate (33.9 m)
    'rear_y': P(0, 975)[1],           # rear wings 4.a / 4.b (-94 m)
}
ACADEMIC = {  # B04 bldg 7 (C-shaped ring + forward arms); A01 (front blocks), A05 (curved ring)
    'center': (0.0, P(0, 1221)[1]),   # -240.4 m
    'ring_outer': 102.0,
    'ring_depth': 27.0,
    'ring_end_y': P(0, 1158)[1],      # straight ends of the C rise above the centre line
    'arm_front_y': P(0, 1083)[1],     # -158.3 m
    'core_y0': P(0, 1165)[1], 'core_y1': P(0, 1279)[1],
}
HELMY = {   # B04 bldg 5 (west of admin); A05 SIAC aerial; A01 right side. SIAC: 12,200 m2
    'center': P(1356, 920), 'angle_deg': -40.9, 'length': 108.0, 'width': 35.0,
}
NANO = {    # B04 bldg 6 (east of admin); A01 left side; listed as completed (Wikipedia)
    'center': P(1815, 918), 'angle_deg': 40.9, 'length': 96.0, 'width': 33.0,
}

# Parking (P on the plan; cars visible in A01 west side) ----------------- B04/A01
PARKING_WEST = [P(1095, 780), P(1165, 780), P(1165, 1090), P(1095, 1090)]
PARKING_BUS = [P(1185, 640), P(1290, 700), P(1250, 760), P(1150, 700)]
PARKING_EAST = [P(1985, 790), P(2055, 790), P(2055, 1000), P(1985, 1000)]

# Proposed / unverified buildings from the same plan (kept separate) -------- B04
# (label, plan centre u, v, length m, width m, rotation deg, height m)
PROPOSED = [
    ("Plan_Bldg_1", 1340, 508, 55, 95, 0, 20),
    ("Plan_Bldg_2", 1797, 508, 55, 95, 0, 20),
    ("Plan_Bldg_3_Gate", 1864, 696, 25, 25, 0, 6),
    ("Plan_Bldg_8_NW_a", 1257, 969, 62, 40, -45, 16),
    ("Plan_Bldg_8_NW_b", 1351, 1081, 70, 40, -45, 16),
    ("Plan_Bldg_8_NW_c", 1436, 1031, 40, 30, -45, 14),
    ("Plan_Bldg_8_NE_a", 1924, 964, 62, 40, 45, 16),
    ("Plan_Bldg_8_NE_b", 1723, 1031, 40, 30, 45, 14),
    ("Plan_Bldg_8_NE_c", 1811, 1077, 70, 40, 45, 16),
    ("Plan_Bldg_8_SW_a", 1294, 1417, 110, 45, 45, 16),
    ("Plan_Bldg_8_SW_b", 1369, 1493, 90, 40, 45, 16),
    ("Plan_Bldg_8_SE_a", 1844, 1410, 100, 45, -45, 16),
    ("Plan_Bldg_8_SE_b", 1774, 1493, 90, 40, -45, 16),
    ("Plan_Bldg_9", 1029, 1607, 130, 50, -50, 16),
    ("Plan_Bldg_10_Sports", 1222, 1800, 140, 110, -40, 3),
    ("Plan_Bldg_11", 1578, 1582, 75, 70, 0, 16),
    ("Plan_Bldg_12_Housing", 2075, 1736, 300, 160, 55, 14),
    ("Plan_Bldg_13", 940, 1882, 70, 45, -40, 12),
]
