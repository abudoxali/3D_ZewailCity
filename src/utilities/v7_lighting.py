"""V7 evening light sources, generated with the permanent scene.

Every light is OFF in the authoritative daylight scene (energy 0) and stores its
evening energy in zc_night_energy, as V6 did for the dormitory bollards. The game
export writes them to campus_manifest.json["evening_lights"] with a kind, so the
explorer can create bounded, shadowless real-time lights.

Positions follow modelled luminaires only (street lamps, plaza lamps, Academic
court poles, garden bollards, covered entrances). Brightness, colour temperature
and the luminaire function of the P13 court poles are ESTIMATES.
"""
import math
import bpy

# kind: (godot energy, range m, colour, spot?)  -- used by build_game_assets
KINDS = {
    'street': (2.2, 18.0, (1.0, 0.86, 0.66), False),
    'plaza': (1.6, 11.0, (1.0, 0.84, 0.62), False),
    'court_pole': (1.5, 11.0, (1.0, 0.86, 0.68), False),
    'bollard': (1.3, 7.0, (1.0, 0.70, 0.38), False),
    'entrance': (3.0, 9.0, (1.0, 0.88, 0.72), True),
}


def _coll():
    c = bpy.data.collections.get('Lighting')
    return c if c else bpy.context.scene.collection


def add_lights(prefix, points, kind, energy, evidence, color=None):
    """points: iterable of (x, y, z) in Blender metres."""
    coll = _coll()
    col = color or KINDS[kind][2]
    made = []
    for i, (x, y, z) in enumerate(points):
        ld = bpy.data.lights.new(f'V7_{prefix}_{i + 1}', 'SPOT' if KINDS[kind][3] else 'POINT')
        ld.energy = 0.0
        ld.color = col
        ld.shadow_soft_size = 0.25
        if ld.type == 'SPOT':
            ld.spot_size = math.radians(110)
            ld.spot_blend = 0.6
        o = bpy.data.objects.new(ld.name, ld)
        coll.objects.link(o)
        o.location = (x, y, z)
        o['zc_night_energy'] = float(energy)
        o['zc_light_kind'] = kind
        o['zc_evidence'] = evidence
        made.append(o)
    return made


def street_lamps():
    """Evening sources at the heads of the existing lamp assets (site furniture)."""
    pts = {'street': [], 'plaza': []}
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.data is None:
            continue
        n = o.data.name
        mw = o.matrix_world
        s = o.scale.z
        if n.startswith('ASSET_Street_Lamp_Double'):
            for d in (1, -1):
                p = mw @ __import__('mathutils').Vector((d * 1.7, 0.0, 10.0 - 0.32))
                pts['street'].append(tuple(p))
        elif n.startswith('ASSET_Street_Lamp'):
            p = mw @ __import__('mathutils').Vector((1.7, 0.0, 9.0 - 0.32))
            pts['street'].append(tuple(p))
        elif n.startswith('ASSET_Plaza_Lamp'):
            p = mw @ __import__('mathutils').Vector((0.0, 0.0, 3.75))
            pts['plaza'].append(tuple(p))
    add_lights('Street_Lamp', pts['street'], 'street', 120.0, 'Modelled street lamp head; brightness ESTIMATED')
    add_lights('Plaza_Lamp', pts['plaza'], 'plaza', 70.0, 'Modelled plaza lamp head; brightness ESTIMATED')
    return {k: len(v) for k, v in pts.items()}


def entrances(M, C):
    """Recessed downlights in the P15 portal soffit, the Gate (A) canopy and the
    P12/P14 entrance-hypothesis canopies. Fixtures are visible geometry; their
    count/spacing is ESTIMATED (no soffit photograph shows the fixtures)."""
    from .geometry import MeshBuilder, parent_keep
    root = bpy.data.objects['AB_Academic_Building']
    pts = [(x, y, 7.17) for x in (-3.5, 3.5) for y in (-246.0, -240.0, -234.0)]      # P15 portal soffit (7.2 m)
    pts += [(x, -226.8, 7.17) for x in (-5.0, 0.0, 5.0)]                              # Gate (A) canopy (7.2 m)
    pts += [(x, -349.25, 3.66) for x in (-4.0, 0.0, 4.0)]                              # P12 Gate (C) band (3.7 m)
    mb = MeshBuilder()
    for x, y, z in pts:
        mb.box(M['metal'], x - 0.22, y - 0.22, z, x + 0.22, y + 0.22, z + 0.03)
        mb.box(M['lamp'], x - 0.16, y - 0.16, z - 0.01, x + 0.16, y + 0.16, z)
    o = mb.to_object('Academic_Entrance_Downlights', C['academic_entry'])
    parent_keep(o, root)
    o['zc_evidence'] = 'V7 recessed fixtures; positions ESTIMATED'
    add_lights('Entrance_Downlight', [(x, y, z - 0.05) for x, y, z in pts], 'entrance', 90.0,
               'Covered entrance/passage downlight; fixture spacing and brightness ESTIMATED')
    add_lights('Gate_F_Wall', [(56.2, -205.0, 3.4)], 'entrance', 70.0, 'P14 entrance hypothesis; ESTIMATED')
    return len(pts) + 1
