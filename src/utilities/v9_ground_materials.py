"""V9 natural ground and asphalt materials (procedural, bake-correct).

Defect found in V8: the baked 6 m ground tiles were almost uniform (desert-sand
albedo standard deviation 0.6 %, normal map 0.5 %). The V7 graph put its tone
variation at 20-80 m (constant inside one tile), its grit at a narrow threshold
and its relief at a 3 mm bump, and the half-offset seamless blend then halved
what remained. At eye height the ground read as a flat tan plane.

V9 rebuilds these materials with tile-scale structure that survives baking:
  * all tile-scale fields are sampled on a flat torus in 4D (Clifford torus,
    radius T/2pi, locally isometric), so every bake is natively seamless and the
    variance-halving blend is no longer needed;
  * coarse gravel, fine grit and (sand/soil only) low wind ripples, with colours
    taken from the existing photo-derived palette (flint-brown and pale limestone
    lag gravel on sandy loam -- P07/P12/P14 earth, C01/C02/D02 surroundings);
  * relief in the baked normal map at real scale (5 mm-3 cm);
  * non-tiled macro tone and the per-vertex ground mask (drift, relief tone)
    are gated by the node 'ZC_Bake_Macro' so the bake contains only the tile.
No stains, cracks, tyre marks or vegetation are invented.
"""
import math
from .materials import _reset, _finish

TAU = 2 * math.pi
MASK_ATTR = 'ZC_Ground_Mask'


class Graph:
    def __init__(self, nt):
        self.nt = nt

    def node(self, kind, **props):
        n = self.nt.nodes.new(kind)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def link(self, a, b):
        self.nt.links.new(a, b)

    def _in(self, sock, v):
        if isinstance(v, (int, float)):
            sock.default_value = v
        elif isinstance(v, tuple):
            sock.default_value = (*v, 1.0) if len(v) == 3 else v
        else:
            self.link(v, sock)

    def math(self, op, a, b=None, clamp=False):
        n = self.node('ShaderNodeMath', operation=op)
        n.use_clamp = clamp
        self._in(n.inputs[0], a)
        if b is not None:
            self._in(n.inputs[1], b)
        return n.outputs[0]

    def maprange(self, v, a, b, c, d, clamp=True):
        n = self.node('ShaderNodeMapRange')
        n.clamp = clamp
        for sock, val in zip(('Value', 'From Min', 'From Max', 'To Min', 'To Max'), (v, a, b, c, d)):
            self._in(n.inputs[sock], val)
        return n.outputs['Result']

    def mix(self, fac, a, b, blend='MIX'):
        n = self.node('ShaderNodeMix', data_type='RGBA', blend_type=blend)
        self._in(n.inputs['Factor'], fac)
        self._in(n.inputs['A'], a)
        self._in(n.inputs['B'], b)
        return n.outputs['Result']

    def ramp(self, fac, stops):
        r = self.node('ShaderNodeValToRGB')
        e = r.color_ramp.elements
        while len(e) < len(stops):
            e.new(0.5)
        for el, (p, c) in zip(e, stops):
            el.position = p
            el.color = (*c, 1.0) if len(c) == 3 else c
        self.link(fac, r.inputs['Fac'])
        return r.outputs['Color']

    def sep(self, col):
        n = self.node('ShaderNodeSeparateColor')
        self.link(col, n.inputs[0])
        return n.outputs


def torus(g, T):
    """World XY -> Clifford-torus coordinates: periodic over T, locally isometric."""
    pos = g.node('ShaderNodeNewGeometry').outputs['Position']
    s = g.node('ShaderNodeSeparateXYZ')
    g.link(pos, s.inputs[0])
    R = T / TAU
    ax = g.math('MULTIPLY', s.outputs['X'], TAU / T)
    ay = g.math('MULTIPLY', s.outputs['Y'], TAU / T)
    c = g.node('ShaderNodeCombineXYZ')
    g.link(g.math('MULTIPLY', g.math('COSINE', ax), R), c.inputs['X'])
    g.link(g.math('MULTIPLY', g.math('SINE', ax), R), c.inputs['Y'])
    g.link(g.math('MULTIPLY', g.math('COSINE', ay), R), c.inputs['Z'])
    w = g.math('MULTIPLY', g.math('SINE', ay), R)
    return {'vec': c.outputs[0], 'w': w, 'x': s.outputs['X'], 'y': s.outputs['Y'], 'pos': pos, 'T': T}


def pnoise(g, t, scale, detail=4.0, rough=0.55, offset=0.0):
    n = g.node('ShaderNodeTexNoise', noise_dimensions='4D')
    g.link(t['vec'], n.inputs['Vector'])
    g.link(g.math('ADD', t['w'], offset) if offset else t['w'], n.inputs['W'])
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    return n.outputs['Fac']


def stones(g, t, scale, cut, rmax, offset, density=None):
    """Periodic stone field: returns (mask, dome height, per-stone tone)."""
    v = g.node('ShaderNodeTexVoronoi', voronoi_dimensions='4D', feature='F1', distance='EUCLIDEAN')
    # Irregular (not disc) outlines: periodic domain distortion of ~0.28 cell.
    dn = g.node('ShaderNodeTexNoise', noise_dimensions='4D')
    g.link(t['vec'], dn.inputs['Vector'])
    g.link(g.math('ADD', t['w'], offset + 0.5), dn.inputs['W'])
    dn.inputs['Scale'].default_value = scale * 1.7
    dn.inputs['Detail'].default_value = 2.0
    off = g.node('ShaderNodeVectorMath', operation='MULTIPLY_ADD')
    g.link(dn.outputs['Color'], off.inputs[0])
    off.inputs[1].default_value = (0.56 / scale,) * 3
    off.inputs[2].default_value = (-0.28 / scale,) * 3
    dv = g.node('ShaderNodeVectorMath', operation='ADD')
    g.link(t['vec'], dv.inputs[0])
    g.link(off.outputs[0], dv.inputs[1])
    g.link(dv.outputs[0], v.inputs['Vector'])
    g.link(g.math('ADD', t['w'], offset), v.inputs['W'])
    v.inputs['Scale'].default_value = scale
    v.inputs['Randomness'].default_value = 1.0
    rnd = g.sep(v.outputs['Color'])
    rad = g.maprange(rnd[0], cut, 1.0, rmax * 0.6, rmax)
    rad = g.math('MULTIPLY', rad, g.math('GREATER_THAN', rnd[0], cut))
    if density is not None:
        rad = g.math('MULTIPLY', rad, density)
    sub = g.math('SUBTRACT', rad, v.outputs['Distance'])
    mask = g.math('DIVIDE', sub, g.math('ADD', g.math('MULTIPLY', rad, 0.3), 0.004), clamp=True)
    dome = g.math('DIVIDE', sub, g.math('ADD', rad, 0.002), clamp=True)
    return mask, g.math('POWER', dome, 0.6), rnd[1]


def bake_switch(g):
    """1 in the scene, set to 0 by the game-asset baker (tile-only bake)."""
    n = g.node('ShaderNodeValue')
    n.name = n.label = 'ZC_Bake_Macro'
    n.outputs[0].default_value = 1.0
    return n.outputs[0]


def ground_mask(g, switch):
    """Per-vertex ground mask written by ground_system (R drift, G relief tone, B contact).
    Alpha is 1 only on meshes that carry the mask."""
    a = g.node('ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name=MASK_ATTR)
    gate = g.math('MULTIPLY', a.outputs['Alpha'], switch)
    ch = g.sep(a.outputs['Color'])
    return gate, ch


def _scene_layers(g, t, col, switch, macro_scale, macro_amt, drift_col, drift_amt, relief_tone):
    """Non-tiled additions for the authoritative scene only (gated for baking)."""
    m1 = g.node('ShaderNodeTexNoise')
    g.link(t['pos'], m1.inputs['Vector'])
    m1.inputs['Scale'].default_value = macro_scale
    m1.inputs['Detail'].default_value = 3.0
    m2 = g.node('ShaderNodeTexNoise')
    g.link(t['pos'], m2.inputs['Vector'])
    m2.inputs['Scale'].default_value = macro_scale * 4.7
    m2.inputs['Detail'].default_value = 2.0
    f = g.maprange(g.math('ADD', g.math('MULTIPLY', m1.outputs['Fac'], 0.65), g.math('MULTIPLY', m2.outputs['Fac'], 0.35)),
                   0.3, 0.7, 1.0 - macro_amt, 1.0 + macro_amt)
    comb = g.node('ShaderNodeCombineXYZ')
    for k in ('X', 'Y', 'Z'):
        g.link(f, comb.inputs[k])
    macro = g.mix(1.0, col, comb.outputs[0], 'MULTIPLY')
    out = g.mix(switch, col, macro)
    gate, ch = ground_mask(g, switch)
    if drift_amt:
        brk = g.node('ShaderNodeTexNoise')
        g.link(t['pos'], brk.inputs['Vector'])
        brk.inputs['Scale'].default_value = 1.3
        brk.inputs['Detail'].default_value = 4.0
        d = g.math('MULTIPLY', g.math('POWER', ch[0], 1.4), g.maprange(brk.outputs['Fac'], 0.3, 0.7, 0.45, 1.0))
        out = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', d, drift_amt), gate), out, drift_col)
    if relief_tone:
        tone = g.math('MULTIPLY', g.math('SUBTRACT', ch[1], 0.5), -2.0 * relief_tone)
        fac = g.math('ADD', 1.0, g.math('MULTIPLY', tone, gate))
        tc = g.node('ShaderNodeCombineXYZ')
        for k in ('X', 'Y', 'Z'):
            g.link(fac, tc.inputs[k])
        out = g.mix(1.0, out, tc.outputs[0], 'MULTIPLY')
    return out


def natural_ground(name, T, base_lo, base_hi, peb_dark, peb_mid, peb_light, *,
                   gravel=(10.0, 0.66, 0.30), grit=(36.0, 0.50, 0.30), ripple=0.0, mottle=0.09,
                   grain=0.06, rough=(0.86, 0.97), peb_rough=0.64, bump=1.0, tufts=None,
                   macro_scale=0.02, macro_amt=0.10, drift_col=(0.60, 0.48, 0.33), drift_amt=0.35,
                   relief_tone=0.06, res=1024):
    m, nt, b = _reset(name)
    g = Graph(nt)
    t = torus(g, T)
    patch = pnoise(g, t, 0.24, 3.0, 0.5, 3.1)
    mott = pnoise(g, t, 0.95, 5.0, 0.6, 7.7)
    fine = pnoise(g, t, 150.0, 2.0, 0.5, 11.3)
    # Blender noise Fac clusters in ~0.38-0.62; ramps use that band.
    base = g.ramp(patch, [(0.40, base_lo), (0.60, base_hi)])
    base = g.mix(1.0, base, g.ramp(mott, [(0.40, (1 - mottle,) * 3), (0.60, (1 + mottle,) * 3)]), 'MULTIPLY')
    base = g.mix(1.0, base, g.ramp(fine, [(0.40, (1 - grain,) * 3), (0.60, (1 + grain,) * 3)]), 'MULTIPLY')
    dens = g.maprange(patch, 0.40, 0.60, 0.75, 1.15)
    gm, gh, gt = stones(g, t, gravel[0], gravel[1], gravel[2], 19.0, dens)
    fm, fh, ft = stones(g, t, grit[0], grit[1], grit[2], 41.0, dens)
    pal = [(0.0, peb_dark), (0.5, peb_mid), (1.0, peb_light)]
    col = g.mix(gm, base, g.ramp(gt, pal))
    col = g.mix(g.math('MULTIPLY', fm, 0.85), col, g.ramp(ft, pal))
    height = g.math('ADD', g.math('MULTIPLY', gh, 0.9), g.math('MULTIPLY', fh, 0.35))
    height = g.math('ADD', height, g.math('MULTIPLY', mott, 0.35))
    height = g.math('ADD', height, g.math('MULTIPLY', fine, 0.10))
    hard = g.math('ADD', gm, fm, clamp=True)
    if tufts:
        # Irregular low groundcover clumps (noise threshold, not discs).
        tn = pnoise(g, t, tufts['scale'], 6.0, 0.72, 57.0)
        tm = g.maprange(tn, tufts['cut'], tufts['cut'] + 0.035, 0.0, tufts.get('cover', 0.85))
        tt = pnoise(g, t, tufts['scale'] * 6.0, 3.0, 0.6, 61.0)
        col = g.mix(tm, col, g.ramp(tt, [(0.4, tufts['dark']), (0.6, tufts['light'])]))
        height = g.math('ADD', height, g.math('MULTIPLY', g.math('MULTIPLY', tm, tt), 1.4))
    if ripple:
        kx, ky = 47, 13  # integer wavenumbers per tile: periodic; ~12.3 cm crest spacing at T=6
        ph = g.math('ADD', g.math('MULTIPLY', t['x'], TAU * kx / T), g.math('MULTIPLY', t['y'], TAU * ky / T))
        ph = g.math('ADD', ph, g.math('MULTIPLY', pnoise(g, t, 0.7, 3.0, 0.5, 23.0), 9.0))
        wave = g.math('POWER', g.math('ADD', g.math('MULTIPLY', g.math('SINE', ph), 0.5), 0.5), 1.6)
        rmask = g.math('MULTIPLY', g.maprange(pnoise(g, t, 0.35, 2.0, 0.5, 31.0), 0.46, 0.56, 0.0, ripple),
                       g.math('SUBTRACT', 1.0, hard, clamp=True))
        height = g.math('ADD', height, g.math('MULTIPLY', wave, rmask))
        col = g.mix(g.math('MULTIPLY', rmask, 0.06), col,
                    g.mix(1.0, col, g.ramp(wave, [(0.0, (0.9,) * 3), (1.0, (1.08,) * 3)]), 'MULTIPLY'))
    switch = bake_switch(g)
    col = _scene_layers(g, t, col, switch, macro_scale, macro_amt, drift_col, drift_amt, relief_tone)
    g.link(col, b.inputs['Base Color'])
    rv = g.maprange(fine, 0.4, 0.6, rough[0], rough[1])
    g.link(g.mix(hard, rv, (peb_rough,) * 3), b.inputs['Roughness'])
    bn = g.node('ShaderNodeBump')
    bn.inputs['Strength'].default_value = bump
    bn.inputs['Distance'].default_value = 0.006
    g.link(height, bn.inputs['Height'])
    g.link(bn.outputs['Normal'], b.inputs['Normal'])
    mid = tuple((a + c) / 2 for a, c in zip(base_lo, base_hi))
    m['zc_tile_m'] = T
    m['zc_periodic'] = True
    m['zc_bake_res'] = res
    m['zc_v9_ground'] = 'natural'
    return _finish(m, mid, sum(rough) / 2)


def asphalt(name, T=4.0):
    """Sun-faded dense asphalt: dark binder, exposed light limestone aggregate (C01/C02/D02)."""
    m, nt, b = _reset(name)
    g = Graph(nt)
    t = torus(g, T)
    patch = pnoise(g, t, 0.35, 3.0, 0.5, 2.0)
    mott = pnoise(g, t, 1.6, 4.0, 0.55, 5.0)
    fine = pnoise(g, t, 260.0, 2.0, 0.5, 9.0)
    binder = g.ramp(patch, [(0.4, (0.070, 0.069, 0.067)), (0.6, (0.100, 0.098, 0.094))])
    binder = g.mix(1.0, binder, g.ramp(mott, [(0.4, (0.92,) * 3), (0.6, (1.08,) * 3)]), 'MULTIPLY')
    binder = g.mix(1.0, binder, g.ramp(fine, [(0.4, (0.88,) * 3), (0.6, (1.12,) * 3)]), 'MULTIPLY')
    am, ah, at = stones(g, t, 95.0, 0.15, 0.56, 13.0)
    sm, sh, st = stones(g, t, 240.0, 0.35, 0.50, 29.0)
    pal = [(0.0, (0.15, 0.145, 0.138)), (0.6, (0.26, 0.25, 0.23)), (1.0, (0.40, 0.38, 0.345))]
    col = g.mix(g.math('MULTIPLY', am, 0.9), binder, g.ramp(at, pal))
    col = g.mix(g.math('MULTIPLY', sm, 0.6), col, g.ramp(st, pal))
    switch = bake_switch(g)
    col = _scene_layers(g, t, col, switch, 0.03, 0.07, (0.46, 0.37, 0.25), 0.55, 0.0)
    g.link(col, b.inputs['Base Color'])
    hard = g.math('ADD', am, sm, clamp=True)
    g.link(g.mix(hard, g.maprange(fine, 0.4, 0.6, 0.88, 0.96), (0.74,) * 3), b.inputs['Roughness'])
    height = g.math('ADD', g.math('MULTIPLY', ah, 0.8), g.math('MULTIPLY', sh, 0.3))
    height = g.math('ADD', height, g.math('MULTIPLY', mott, 0.25))
    bn = g.node('ShaderNodeBump')
    bn.inputs['Strength'].default_value = 0.9
    bn.inputs['Distance'].default_value = 0.0035
    g.link(height, bn.inputs['Height'])
    g.link(bn.outputs['Normal'], b.inputs['Normal'])
    m['zc_tile_m'] = T
    m['zc_periodic'] = True
    m['zc_bake_res'] = 2048
    m['zc_v9_ground'] = 'asphalt'
    return _finish(m, (0.115, 0.112, 0.107), 0.88)


def lawn(name, T=3.0):
    """Irrigated lawn: blade-scale tone, clumping and occasional sun-dried patches."""
    m, nt, b = _reset(name)
    g = Graph(nt)
    t = torus(g, T)
    blade = pnoise(g, t, 230.0, 2.0, 0.6, 3.0)
    blade2 = pnoise(g, t, 90.0, 3.0, 0.6, 8.0)
    clump = pnoise(g, t, 2.6, 4.0, 0.6, 13.0)
    dry = pnoise(g, t, 0.55, 3.0, 0.55, 17.0)
    col = g.ramp(clump, [(0.42, (0.058, 0.128, 0.033)), (0.58, (0.095, 0.185, 0.048))])
    col = g.mix(1.0, col, g.ramp(blade, [(0.4, (0.70,) * 3), (0.6, (1.28,) * 3)]), 'MULTIPLY')
    col = g.mix(1.0, col, g.ramp(blade2, [(0.4, (0.86,) * 3), (0.6, (1.12,) * 3)]), 'MULTIPLY')
    col = g.mix(g.maprange(dry, 0.55, 0.62, 0.0, 0.45), col, (0.21, 0.20, 0.085))
    switch = bake_switch(g)
    col = _scene_layers(g, t, col, switch, 0.04, 0.08, (0.4, 0.33, 0.2), 0.0, 0.0)
    g.link(col, b.inputs['Base Color'])
    g.link(g.maprange(blade, 0.4, 0.6, 0.88, 0.98), b.inputs['Roughness'])
    height = g.math('ADD', g.math('MULTIPLY', blade, 0.7), g.math('MULTIPLY', blade2, 0.4))
    height = g.math('ADD', height, g.math('MULTIPLY', clump, 0.5))
    bn = g.node('ShaderNodeBump')
    bn.inputs['Strength'].default_value = 1.0
    bn.inputs['Distance'].default_value = 0.008
    g.link(height, bn.inputs['Height'])
    g.link(bn.outputs['Normal'], b.inputs['Normal'])
    m['zc_tile_m'] = T
    m['zc_periodic'] = True
    m['zc_bake_res'] = 1024
    m['zc_v9_ground'] = 'lawn'
    return _finish(m, (0.075, 0.15, 0.04), 0.93)


def override(M):
    """Replace the V7 ground materials in place (same names, same keys)."""
    flint, tan, lime = (0.16, 0.12, 0.085), (0.34, 0.26, 0.175), (0.62, 0.56, 0.46)
    M['sand'] = natural_ground('M_Desert_Sand', 6.0, (0.42, 0.295, 0.175), (0.56, 0.42, 0.26), flint, tan, lime,
                               gravel=(20.0, 0.62, 0.50), grit=(64.0, 0.45, 0.50), ripple=0.9, mottle=0.12,
                               grain=0.07, rough=(0.90, 0.98), macro_scale=0.012, macro_amt=0.12)
    M['soil_light'] = natural_ground('M_Graded_Campus_Soil', 6.0, (0.45, 0.33, 0.21), (0.58, 0.45, 0.30), flint, tan, lime,
                                     gravel=(17.0, 0.45, 0.52), grit=(58.0, 0.32, 0.50), ripple=0.45, mottle=0.12,
                                     grain=0.07, rough=(0.86, 0.97), macro_scale=0.03, macro_amt=0.10)
    M['compacted'] = natural_ground('M_Compacted_Earth', 6.0, (0.40, 0.31, 0.21), (0.50, 0.40, 0.28), flint, tan, lime,
                                    gravel=(22.0, 0.40, 0.50), grit=(70.0, 0.28, 0.50), ripple=0.0, mottle=0.09,
                                    rough=(0.82, 0.94), peb_rough=0.6, bump=0.8, macro_scale=0.05, macro_amt=0.08)
    M['planted_soil'] = natural_ground('M_Planted_Soil_Sparse', 6.0, (0.15, 0.11, 0.058), (0.22, 0.165, 0.09),
                                       (0.10, 0.08, 0.055), (0.24, 0.19, 0.12), (0.40, 0.35, 0.27),
                                       gravel=(18.0, 0.70, 0.48), grit=(60.0, 0.55, 0.48), ripple=0.0, mottle=0.13,
                                       rough=(0.90, 0.98), macro_scale=0.035, macro_amt=0.10, drift_amt=0.2,
                                       tufts={'scale': 0.9, 'cut': 0.53, 'cover': 0.8,
                                              'dark': (0.055, 0.085, 0.028), 'light': (0.15, 0.16, 0.065)})
    M['asphalt'] = asphalt('M_Asphalt')
    M['grass'] = lawn('M_Grass_Lawn')
    return M
