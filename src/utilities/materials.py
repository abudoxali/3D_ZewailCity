"""Procedural, node-based materials for the campus.

Every material stores a flat fallback colour in m["gltf_base_color"]; the GLB
exporter script uses it because glTF cannot carry procedural node textures.
"""
import bpy


def _reset(name):
    old = bpy.data.materials.get(name)
    if old:
        bpy.data.materials.remove(old)
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    out.location = (700, 0)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.location = (400, 0)
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    return m, nt, b


def _finish(m, color, rough=0.5, metal=0.0):
    m.diffuse_color = (*color, 1.0)
    m.roughness = rough
    m.metallic = metal
    m["gltf_base_color"] = list(color)
    return m


def _world_pos(nt):
    return nt.nodes.new('ShaderNodeNewGeometry').outputs['Position']


def _object_pos(nt):
    return nt.nodes.new('ShaderNodeTexCoord').outputs['Object']


def _noise(nt, vec, scale, detail=6.0, rough=0.55):
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    nt.links.new(vec, n.inputs['Vector'])
    return n.outputs['Fac']


def _ramp(nt, fac, c0, c1, p0=0.3, p1=0.7):
    r = nt.nodes.new('ShaderNodeValToRGB')
    e = r.color_ramp.elements
    e[0].position, e[0].color = p0, (*c0, 1.0)
    e[1].position, e[1].color = p1, (*c1, 1.0)
    nt.links.new(fac, r.inputs['Fac'])
    return r.outputs['Color']


def _ramp_value(nt, fac, v0, v1, p0=0.3, p1=0.7):
    return _ramp(nt, fac, (v0, v0, v0), (v1, v1, v1), p0, p1)


def _bump(nt, height, strength, distance=0.1, normal=None):
    b = nt.nodes.new('ShaderNodeBump')
    b.inputs['Strength'].default_value = strength
    b.inputs['Distance'].default_value = distance
    nt.links.new(height, b.inputs['Height'])
    if normal is not None:
        nt.links.new(normal, b.inputs['Normal'])
    return b.outputs['Normal']


def noisy(name, c0, c1, scale=0.4, rough=0.6, metal=0.0, bump=0.05, bump_scale=8.0,
          coords='world', rough_var=None):
    """Generic material: colour variation from noise plus a fine bump."""
    m, nt, b = _reset(name)
    vec = _world_pos(nt) if coords == 'world' else _object_pos(nt)
    nt.links.new(_ramp(nt, _noise(nt, vec, scale), c0, c1), b.inputs['Base Color'])
    b.inputs['Metallic'].default_value = metal
    if rough_var:
        nt.links.new(_ramp_value(nt, _noise(nt, vec, scale * 3.0), rough_var[0], rough_var[1]), b.inputs['Roughness'])
    else:
        b.inputs['Roughness'].default_value = rough
    if bump:
        nt.links.new(_bump(nt, _noise(nt, vec, bump_scale, detail=4), bump), b.inputs['Normal'])
    mid = tuple((a + c) / 2 for a, c in zip(c0, c1))
    return _finish(m, mid, rough, metal)


def flat(name, color, rough=0.5, metal=0.0, coat=0.0, emission=None, strength=0.0, spec=0.5):
    m, nt, b = _reset(name)
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['Specular IOR Level'].default_value = spec
    if emission:
        b.inputs['Emission Color'].default_value = (*emission, 1.0)
        b.inputs['Emission Strength'].default_value = strength
    return _finish(m, color, rough, metal)


def _mul(nt, a, b):
    m = nt.nodes.new('ShaderNodeMix')
    m.data_type = 'RGBA'
    m.blend_type = 'MULTIPLY'
    m.inputs['Factor'].default_value = 1.0
    nt.links.new(a, m.inputs['A'])
    nt.links.new(b, m.inputs['B'])
    return m.outputs['Result']


def _mix(nt, fac, a, b):
    m = nt.nodes.new('ShaderNodeMix')
    m.data_type = 'RGBA'
    nt.links.new(fac, m.inputs['Factor'])
    for sock, v in (('A', a), ('B', b)):
        if isinstance(v, tuple):
            m.inputs[sock].default_value = (*v, 1.0)
        else:
            nt.links.new(v, m.inputs[sock])
    return m.outputs['Result']


def paving(name, c0, c1, mortar, brick_w=0.9, row_h=0.45, rough=0.7, grain=0.10, grain_scale=9.0,
           joint_rough=0.92, bias=0.0):
    """V7: scale-correct unit paving. Factor is the MORTAR mask (Blender manual:
    1 = mortar), so joints are now recessed (the V6 bump raised them). Each unit
    keeps Blender's per-brick colour variation, plus fine stone/concrete grain and
    a rougher joint; no wear, stains or cracks are invented."""
    m, nt, b = _reset(name)
    pos = _world_pos(nt)
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Brick Width'].default_value = brick_w
    br.inputs['Row Height'].default_value = row_h
    br.inputs['Mortar Size'].default_value = 0.012 if brick_w > 0.5 else 0.006
    br.inputs['Mortar Smooth'].default_value = 0.25
    br.inputs['Bias'].default_value = bias
    br.inputs['Color1'].default_value = (*c0, 1.0)
    br.inputs['Color2'].default_value = (*c1, 1.0)
    br.inputs['Mortar'].default_value = (*mortar, 1.0)
    br.offset = 0.5
    nt.links.new(pos, br.inputs['Vector'])
    g = _ramp_value(nt, _noise(nt, pos, grain_scale, detail=8, rough=0.65), 1.0 - grain, 1.0 + grain * 0.6, 0.25, 0.75)
    nt.links.new(_mul(nt, br.outputs['Color'], g), b.inputs['Base Color'])
    rv = _ramp_value(nt, _noise(nt, pos, grain_scale * 0.5, detail=3), rough - 0.05, rough + 0.05, 0.3, 0.7)
    nt.links.new(_mix(nt, br.outputs['Fac'], rv, (joint_rough,) * 3), b.inputs['Roughness'])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.invert = True
    bump.inputs['Strength'].default_value = 0.35
    bump.inputs['Distance'].default_value = 0.004
    nt.links.new(br.outputs['Fac'], bump.inputs['Height'])
    b2 = _bump(nt, _noise(nt, pos, grain_scale * 4.0, detail=4), 0.04, 0.002, bump.outputs['Normal'])
    nt.links.new(b2, b.inputs['Normal'])
    return _finish(m, tuple((a + c) / 2 for a, c in zip(c0, c1)), rough)


def aggregate(name, c_dark, c_light, fleck, fleck_amount=0.35, macro=0.06, fine=55.0, rough=(0.80, 0.94),
              bump=0.18, bump_scale=70.0, fleck_cut=0.64):
    """V7 aggregate surfaces (asphalt, concrete, earth, sand): low-frequency tone
    from macro noise, aggregate/grit flecks at real scale, roughness variation and
    fine relief. Sun-faded asphalt albedo ~0.09-0.14 (V6's 0.03-0.07 read as
    black plastic in the engine)."""
    m, nt, b = _reset(name)
    pos = _world_pos(nt)
    base = _ramp(nt, _noise(nt, pos, macro, detail=5, rough=0.6), c_dark, c_light, 0.3, 0.7)
    mid = _ramp_value(nt, _noise(nt, pos, macro * 18.0, detail=4), 0.9, 1.08, 0.3, 0.7)
    base = _mul(nt, base, mid)
    fn = nt.nodes.new('ShaderNodeTexNoise')
    fn.inputs['Scale'].default_value = fine
    fn.inputs['Detail'].default_value = 2.0
    fn.inputs['Roughness'].default_value = 0.5
    nt.links.new(pos, fn.inputs['Vector'])
    mask = nt.nodes.new('ShaderNodeMapRange')
    mask.inputs['From Min'].default_value = fleck_cut
    mask.inputs['From Max'].default_value = fleck_cut + 0.05
    nt.links.new(fn.outputs['Fac'], mask.inputs['Value'])
    amt = nt.nodes.new('ShaderNodeMath')
    amt.operation = 'MULTIPLY'
    amt.inputs[1].default_value = fleck_amount
    nt.links.new(mask.outputs['Result'], amt.inputs[0])
    nt.links.new(_mix(nt, amt.outputs[0], base, fleck), b.inputs['Base Color'])
    nt.links.new(_ramp_value(nt, _noise(nt, pos, macro * 25.0, detail=3), rough[0], rough[1]), b.inputs['Roughness'])
    nt.links.new(_bump(nt, fn.outputs['Fac'], bump, 0.003,
                       _bump(nt, _noise(nt, pos, bump_scale * 0.08, detail=5), bump * 0.6, 0.02)), b.inputs['Normal'])
    mid_c = tuple((a + c) / 2 for a, c in zip(c_dark, c_light))
    return _finish(m, mid_c, sum(rough) / 2)


def palm_trunk(name):
    m, nt, b = _reset(name)
    vec = _object_pos(nt)
    w = nt.nodes.new('ShaderNodeTexWave')
    w.wave_type = 'BANDS'
    w.bands_direction = 'Z'
    w.inputs['Scale'].default_value = 4.0
    w.inputs['Distortion'].default_value = 2.0
    w.inputs['Detail'].default_value = 3.0
    nt.links.new(vec, w.inputs['Vector'])
    nt.links.new(_ramp(nt, w.outputs['Fac'], (0.13, 0.09, 0.055), (0.30, 0.23, 0.15)), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.85
    nt.links.new(_bump(nt, w.outputs['Fac'], 0.6, 0.05), b.inputs['Normal'])
    return _finish(m, (0.24, 0.18, 0.12), 0.85)


def glass(name, color=(0.012, 0.018, 0.026), rough=0.03):
    """Dark tinted architectural glazing (opaque, highly reflective; cheap to render)."""
    m, nt, b = _reset(name)
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = 0.15
    b.inputs['Specular IOR Level'].default_value = 0.8
    b.inputs['IOR'].default_value = 1.52
    b.inputs['Coat Weight'].default_value = 0.4
    b.inputs['Coat Roughness'].default_value = 0.02
    return _finish(m, color, rough, 0.15)


def solar(name):
    m, nt, b = _reset(name)
    pos = _world_pos(nt)
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Brick Width'].default_value = 1.0
    br.inputs['Row Height'].default_value = 1.65
    br.inputs['Mortar Size'].default_value = 0.03
    br.offset = 0.0
    br.inputs['Color1'].default_value = (0.02, 0.035, 0.09, 1)
    br.inputs['Color2'].default_value = (0.025, 0.04, 0.1, 1)
    br.inputs['Mortar'].default_value = (0.6, 0.6, 0.62, 1)
    nt.links.new(pos, br.inputs['Vector'])
    nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.15
    b.inputs['Metallic'].default_value = 0.3
    return _finish(m, (0.03, 0.04, 0.1), 0.15, 0.3)


def stone_panels(name, c0, c1, joint, panel_w=1.2, panel_h=0.6, rough=0.55):
    """Stone cladding with a stack-bond panel grid (photos A02/A03 show large
    light marble/limestone panels). Panels are projected on (x + y, z) so walls of
    any orientation get joints; roofs carry a separate membrane material."""
    m, nt, b = _reset(name)
    pos = _world_pos(nt)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(pos, sep.inputs[0])
    add = nt.nodes.new('ShaderNodeMath')
    add.operation = 'ADD'
    nt.links.new(sep.outputs['X'], add.inputs[0])
    nt.links.new(sep.outputs['Y'], add.inputs[1])
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(add.outputs[0], comb.inputs['X'])
    nt.links.new(sep.outputs['Z'], comb.inputs['Y'])
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.offset = 0.0
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Brick Width'].default_value = panel_w
    br.inputs['Row Height'].default_value = panel_h
    br.inputs['Mortar Size'].default_value = 0.008
    br.inputs['Color1'].default_value = (*c0, 1.0)
    br.inputs['Color2'].default_value = (*c1, 1.0)
    br.inputs['Mortar'].default_value = (*joint, 1.0)
    nt.links.new(comb.outputs[0], br.inputs['Vector'])
    # V7: subtle natural-stone grain within each panel and a rougher joint; the panel
    # joint is now RECESSED (Factor = mortar mask; V6 raised every joint).
    br.inputs['Mortar Smooth'].default_value = 0.2
    g = _ramp_value(nt, _noise(nt, comb.outputs[0], 7.0, detail=8, rough=0.6), 0.93, 1.05, 0.25, 0.75)
    nt.links.new(_mul(nt, br.outputs['Color'], g), b.inputs['Base Color'])
    rv = _ramp_value(nt, _noise(nt, comb.outputs[0], 2.5, detail=3), rough - 0.05, rough + 0.05, 0.3, 0.7)
    nt.links.new(_mix(nt, br.outputs['Fac'], rv, (min(1.0, rough + 0.2),) * 3), b.inputs['Roughness'])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.invert = True
    bump.inputs['Strength'].default_value = 0.3
    bump.inputs['Distance'].default_value = 0.004
    nt.links.new(br.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return _finish(m, tuple((a + c) / 2 for a, c in zip(c0, c1)), rough)


def build_materials():
    M = {}
    # architecture -------------------------------------------------------
    # light grey-white marble cladding with joints (A02, A03)
    M['stone'] = stone_panels("M_Stone_Cladding", (0.70, 0.69, 0.65), (0.66, 0.65, 0.61), (0.40, 0.40, 0.38))
    M['stone_plain'] = noisy("M_Stone_White", (0.63, 0.60, 0.54), (0.72, 0.69, 0.63), scale=0.25,
                             rough=0.6, bump=0.04, bump_scale=6.0)
    # V7: warmer sandy beige, as in P16 and the official dorms image.
    M['res_stone']=stone_panels('M_V6_Residential_Stone',(.62,.53,.39),(.69,.60,.45),(.40,.36,.29),rough=.57)
    # V7 (P16 zoom): lighter sky-reflective residential glass, grey stone plinth and
    # three neutral interior curtain colours seen behind the panes.
    M['res_glass']=glass('M_V7_Residential_Glass',color=(.055,.07,.085),rough=.08)
    M['res_plinth']=noisy('M_V7_Residential_Plinth',(.36,.35,.33),(.43,.42,.40),scale=2.,rough=.6,bump=.03,bump_scale=20.)
    M['res_curtain_a']=flat('M_V7_Curtain_Offwhite',(.62,.60,.55),rough=.9)
    M['res_curtain_b']=flat('M_V7_Curtain_Beige',(.48,.40,.30),rough=.9)
    M['res_curtain_c']=flat('M_V7_Curtain_Greyblue',(.30,.33,.36),rough=.9)
    M['res_lit']=flat('M_V6_Residential_Window_Lit',(.08,.12,.17),rough=.22,emission=(.28,.39,.55),strength=.35)
    # dark grey horizontal granite bands at floor / parapet lines (A02, A03)
    M['band'] = noisy("M_Granite_Band", (0.075, 0.075, 0.08), (0.12, 0.12, 0.125), scale=4.0, rough=0.35, bump=0.0)
    # copper-clad drum and dome (A02: light copper drum; A01/A03: banded, darker dome)
    M['copper'] = noisy("M_Copper_Drum", (0.60, 0.31, 0.15), (0.70, 0.38, 0.20), scale=0.6, metal=1.0,
                        rough=0.4, bump=0.0, rough_var=(0.34, 0.48))
    M['copper_dome'] = noisy("M_Copper_Dome", (0.52, 0.27, 0.13), (0.62, 0.34, 0.18), scale=0.5, metal=1.0,
                             rough=0.42, bump=0.0, rough_var=(0.36, 0.5))
    M['copper_dark'] = noisy("M_Copper_Dome_Band", (0.36, 0.17, 0.08), (0.42, 0.21, 0.10), scale=0.5,
                             metal=1.0, rough=0.45, bump=0.0)
    M['stone_warm'] = noisy("M_Stone_Beige", (0.62, 0.53, 0.41), (0.72, 0.63, 0.50), scale=0.3,
                            rough=0.65, bump=0.06, bump_scale=5.0)
    M['roof'] = noisy("M_Roof_Membrane", (0.40, 0.40, 0.39), (0.50, 0.49, 0.47), scale=0.15,
                      rough=0.85, bump=0.03)
    M['glass'] = glass("M_Glass_Dark")
    M['glass_blue'] = glass("M_Glass_Blue_Tint", color=(0.02, 0.04, 0.06), rough=0.05)
    M['metal'] = flat("M_Metal_Mullion", (0.10, 0.10, 0.11), rough=0.35, metal=0.9)
    M['metal_light'] = flat("M_Metal_Aluminium", (0.55, 0.56, 0.58), rough=0.3, metal=1.0)
    M['solar'] = solar("M_Solar_Panel")
    M['proposal'] = flat("M_Unverified_Proposal_Blockout", (0.45, 0.25, 0.75), rough=0.8)
    M['wood'] = noisy("M_Wood_Pergola", (0.14, 0.065, 0.03), (0.22, 0.11, 0.05), scale=3.0,
                      rough=0.55, bump=0.1, bump_scale=30.0)
    # ground / roads --------------------------------------------------------
    # V7: sun-faded asphalt with light limestone aggregate (C01/C02/D02 road photos).
    M['asphalt'] = aggregate("M_Asphalt", (0.085, 0.084, 0.082), (0.135, 0.13, 0.124), (0.36, 0.34, 0.31),
                             fleck_amount=0.45, macro=0.05, fine=60.0, rough=(0.80, 0.93), bump=0.22)
    # V7 concrete edge restraint strip between unit paving and soil/planting (ESTIMATED detail).
    M['edge'] = aggregate("M_V7_Paving_Edge_Restraint", (0.55, 0.535, 0.50), (0.63, 0.615, 0.58), (0.74, 0.72, 0.68),
                          fleck_amount=0.2, macro=0.5, fine=95.0, rough=(0.76, 0.88), bump=0.06)
    M['marking'] = flat("M_Road_Marking_White", (0.82, 0.82, 0.80), rough=0.55)
    M['marking_y'] = flat("M_Road_Marking_Yellow", (0.80, 0.55, 0.04), rough=0.55)
    M['curb'] = aggregate("M_Concrete_Curb", (0.50, 0.49, 0.46), (0.60, 0.585, 0.55), (0.70, 0.68, 0.64),
                          fleck_amount=0.25, macro=0.6, fine=90.0, rough=(0.74, 0.88), bump=0.08)
    M['curb_paint'] = flat("M_Curb_Paint_Black", (0.03, 0.03, 0.03), rough=0.6)
    M['paving'] = paving("M_Paving_Limestone", (0.69, 0.63, 0.53), (0.62, 0.56, 0.47), (0.40, 0.37, 0.32),
                         rough=0.68, grain=0.09)
    M['paving_light'] = paving("M_Paving_Light", (0.66, 0.63, 0.58), (0.60, 0.57, 0.52), (0.40, 0.38, 0.35),
                               brick_w=1.2, row_h=0.6, rough=0.62, grain=0.08)
    M['granite'] = noisy("M_Granite_Dark", (0.10, 0.10, 0.105), (0.18, 0.18, 0.19), scale=6.0,
                         rough=0.25, bump=0.0)
    # P05/P09/P13: large-format slabs and real dark stone inlays; no photo textures.
    # V7 (P09/P13 re-read at full size): light grey-beige honed granite slabs; V6's
    # 0.22-0.28 albedo with 0.32 roughness mirrored the blue sky in the engine.
    M['plaza_grey']=paving('M_V6_Plaza_Grey',(.44,.43,.40),(.50,.49,.46),(.20,.20,.19),brick_w=1.2,row_h=.6,rough=.46,grain=.14,grain_scale=14.)
    M['plaza_light']=paving('M_V6_Plaza_Light',(.55,.52,.47),(.61,.58,.53),(.27,.26,.24),brick_w=1.2,row_h=.6,rough=.50,grain=.12,grain_scale=14.)
    M['plaza_inlay']=noisy('M_V6_Plaza_Inlay',(.055,.06,.062),(.10,.11,.115),scale=8.,rough=.24,bump=0.)
    # P11: grey-beige concrete brick pavers in running bond, visibly varied per unit.
    M['garden_paver']=paving('M_V6_Garden_Pavers',(.38,.36,.32),(.47,.44,.39),(.20,.19,.17),brick_w=.22,row_h=.11,rough=.72,grain=.12,grain_scale=25.,bias=.1)
    # V10 (P13): the court curtain wall is very dark, strongly reflective glass.
    M['court_glass']=glass('M_V6_Court_Glass',color=(.016,.021,.026),rough=.08)
    # V10: clear entrance-screen glazing of the Administration lobby (see-through in the game).
    M['lobby_glass']=glass('M_V10_Lobby_Glass',color=(.05,.06,.065),rough=.04)
    # V10: matte light plaster for the lobby ceiling (aluminium mirrored the probe).
    M['plaster']=flat('M_V10_Ceiling_Plaster',(.78,.77,.74),rough=.85)
    M['grass'] = noisy("M_Grass_Lawn", (0.05, 0.12, 0.03), (0.11, 0.20, 0.055), scale=0.12,
                       rough=0.95, bump=0.35, bump_scale=90.0)
    # V7: P07/P12/P14 earth: warm sandy loam with small pale grit and darker clods.
    M['sand'] = aggregate("M_Desert_Sand", (0.42, 0.29, 0.17), (0.55, 0.41, 0.25), (0.66, 0.56, 0.42),
                          fleck_amount=0.3, macro=0.012, fine=70.0, rough=(0.90, 0.98), bump=0.25, bump_scale=8.0)
    M['soil_light'] = aggregate("M_Graded_Campus_Soil", (0.45, 0.33, 0.21), (0.57, 0.44, 0.29), (0.68, 0.58, 0.45),
                                fleck_amount=0.35, macro=0.03, fine=65.0, rough=(0.86, 0.98), bump=0.25, bump_scale=10.0)
    M['compacted']=aggregate('M_Compacted_Earth',(0.40,.31,.21),(.50,.40,.28),(.62,.55,.45),
                             fleck_amount=.45,macro=.05,fine=80.,rough=(.82,.95),bump=.18,bump_scale=14.)
    M['pebbles'] = noisy("M_White_Pebbles", (0.72, 0.71, 0.68), (0.85, 0.84, 0.81), scale=40.0, rough=0.6,
                         bump=0.6, bump_scale=45.0)
    M['gravel'] = noisy("M_Dark_Gravel", (0.05, 0.05, 0.055), (0.12, 0.12, 0.13), scale=40.0, rough=0.8,
                        bump=0.5, bump_scale=60.0)
    M['palm_fan'] = noisy("M_Fan_Palm_Leaf", (0.10, 0.17, 0.06), (0.20, 0.27, 0.10), scale=0.5, rough=0.6, bump=0.0)
    M['palm_skirt'] = noisy("M_Fan_Palm_Dead_Skirt", (0.22, 0.15, 0.08), (0.32, 0.23, 0.13), scale=2.0, rough=0.9,
                            bump=0.4, bump_scale=12.0)
    M['soil'] = noisy("M_Planter_Soil", (0.20, 0.13, 0.08), (0.30, 0.20, 0.12), scale=3.0, rough=0.95)
    M['water'] = flat("M_Water_Pool", (0.02, 0.06, 0.07), rough=0.02, coat=1.0, spec=1.0)
    # vegetation -------------------------------------------------------------
    M['palm_trunk'] = palm_trunk("M_Palm_Trunk")
    M['palm_leaf'] = noisy("M_Palm_Frond", (0.05, 0.13, 0.025), (0.13, 0.24, 0.05), scale=0.35,
                           rough=0.55, bump=0.0)
    M['foliage'] = noisy("M_Tree_Foliage", (0.035, 0.11, 0.025), (0.10, 0.21, 0.045), scale=0.6,
                         rough=0.8, bump=0.4, bump_scale=4.0)
    M['cypress'] = noisy("M_Cypress_Foliage", (0.025, 0.07, 0.025), (0.05, 0.13, 0.04), scale=0.8,
                         rough=0.8, bump=0.4, bump_scale=5.0)
    M['bark'] = noisy("M_Tree_Bark", (0.10, 0.075, 0.055), (0.20, 0.155, 0.11), scale=6.0, rough=0.9,
                      bump=0.5, bump_scale=25.0)
    M['foliage_dark'] = noisy("M_V7_Tree_Foliage_Shade", (0.025, 0.07, 0.02), (0.06, 0.13, 0.035), scale=0.8,
                              rough=0.85, bump=0.4, bump_scale=5.0)
    M['shrub'] = noisy("M_Shrub_Green", (0.04, 0.14, 0.03), (0.10, 0.25, 0.05), scale=1.0, rough=0.85,
                       bump=0.4, bump_scale=6.0)
    M['shrub_red'] = noisy("M_Shrub_Bougainvillea", (0.38, 0.03, 0.06), (0.62, 0.08, 0.14), scale=1.4,
                           rough=0.8, bump=0.4, bump_scale=6.0)
    M['shrub_orange'] = noisy("M_Shrub_Orange", (0.55, 0.20, 0.03), (0.75, 0.38, 0.06), scale=1.4,
                              rough=0.8, bump=0.4, bump_scale=6.0)
    M['shrub_golden'] = noisy("M_V7_Shrub_Golden_Green", (0.30, 0.36, 0.05), (0.45, 0.50, 0.10), scale=1.4,
                              rough=0.8, bump=0.4, bump_scale=6.0)
    M['hedge'] = noisy("M_Hedge", (0.03, 0.10, 0.025), (0.07, 0.18, 0.04), scale=0.8, rough=0.85,
                       bump=0.5, bump_scale=8.0)
    # site furniture / vehicles ---------------------------------------------
    M['pole'] = flat("M_Lamp_Pole", (0.16, 0.17, 0.18), rough=0.4, metal=0.8)
    M['lamp'] = flat("M_Lamp_Lens", (0.9, 0.85, 0.7), rough=0.2, emission=(1.0, 0.82, 0.55), strength=2.0)
    M['tire'] = flat("M_Car_Tire", (0.02, 0.02, 0.02), rough=0.9)
    M['car_glass'] = glass("M_Car_Glass", color=(0.01, 0.012, 0.015), rough=0.05)
    for key, col in (('red', (0.45, 0.015, 0.02)), ('white', (0.80, 0.80, 0.79)), ('silver', (0.42, 0.43, 0.45)),
                     ('black', (0.015, 0.015, 0.018)), ('yellow', (0.80, 0.52, 0.02)), ('blue', (0.03, 0.08, 0.30))):
        M['car_' + key] = flat("M_Car_Paint_" + key.title(), col, rough=0.25, metal=0.5, coat=1.0)

    # ---- V4: main gate complex and site surfaces (photos C01, C02, D02, D03) ----------
    # V8 C01/C02/D02: cream-beige stone, not saturated orange. Linear albedo;
    # retain scale-correct recessed 8 mm panel joints and baked normals.
    M['gate_stone'] = stone_panels("M_Gate_Sandstone_Tiles", (0.64, 0.595, 0.50), (0.72, 0.675, 0.58),
                                   (0.43, 0.405, 0.35), panel_w=0.8, panel_h=0.6, rough=0.70)
    # Dark split-face ledgestone: portal inlay band, pedestrian-gate flanks, pavilion panel (C01).
    M["ledgestone"] = stone_panels("M_Ledgestone_Dark", (0.050, 0.040, 0.034), (0.11, 0.085, 0.065),
                                   (0.025, 0.02, 0.018), panel_w=0.4, panel_h=0.08, rough=0.8)
    # Ochre plaster of the single-storey gate buildings and the perimeter wall (C01, C02).
    M['stucco'] = noisy("M_Stucco_Ochre", (0.56, 0.49, 0.38), (0.64, 0.57, 0.46), scale=0.5, rough=0.85,
                        bump=0.02, bump_scale=30.0)
    # Grey interlocking concrete pavers of the campus roads and gate forecourt (C02 2017, D02 2021).
    M['paver_road'] = paving("M_Paver_Road_Grey", (0.30, 0.30, 0.29), (0.26, 0.26, 0.25), (0.16, 0.16, 0.15),
                             brick_w=0.22, row_h=0.11, rough=0.8)
    M['mulch'] = noisy("M_Red_Mulch", (0.15, 0.035, 0.02), (0.24, 0.065, 0.035), scale=25.0, rough=0.95,
                       bump=0.2, bump_scale=60.0)
    M['steel_dark'] = flat("M_Steel_Gate_Dark", (0.03, 0.03, 0.035), rough=0.45, metal=0.8)
    M['logo_metal'] = flat("M_Logo_Brushed_Bronze", (0.50, 0.38, 0.20), rough=0.35, metal=0.9)
    # Drought-tolerant planting seen in the gate beds (C01): agave, barrel cactus, euphorbia, cycad.
    M['agave'] = noisy("M_Agave_Leaf", (0.20, 0.30, 0.16), (0.42, 0.45, 0.20), scale=3.0, rough=0.55, bump=0.0)
    M['cactus'] = noisy("M_Barrel_Cactus", (0.20, 0.28, 0.04), (0.38, 0.40, 0.06), scale=6.0, rough=0.6,
                        bump=0.1, bump_scale=40.0)
    M['euphorbia'] = noisy("M_Euphorbia_Red", (0.20, 0.03, 0.02), (0.10, 0.16, 0.04), scale=2.0, rough=0.6, bump=0.0)
    M['cycad'] = noisy("M_Cycad_Frond", (0.02, 0.07, 0.015), (0.05, 0.13, 0.03), scale=1.5, rough=0.6, bump=0.0)
    M['groundcover'] = noisy("M_Groundcover_Planted", (0.035, 0.09, 0.02), (0.09, 0.15, 0.04), scale=1.5,
                             rough=0.9, bump=0.12, bump_scale=12.0)
    # sparse planting on soil (Sentinel-2: the approach parcels read brown with tree canopy, not lawn)
    M['planted_soil'] = noisy("M_Planted_Soil_Sparse", (0.17, 0.115, 0.06), (0.09, 0.12, 0.045), scale=0.35,
                              rough=0.95, bump=0.1, bump_scale=10.0)
    # V9: bake-correct natural ground, asphalt and lawn (see v9_ground_materials).
    from .v9_ground_materials import override
    override(M)
    return M
