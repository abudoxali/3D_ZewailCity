// V9 ground surfaces. Uses the baked albedo / normal / roughness tiles that Blender
// exported (world-scale box UVs; V9 natural-ground tiles are natively periodic) and adds:
//  * multi-octave world-space tone variation per surface kind, so no tile repeats
//    identically across hundreds of metres (V7 had one weak octave);
//  * for non-jointed aggregates a second rotated, rescaled sample (anti-tiling);
//  * for jointed paving a per-unit (brick-grid exact) tone variation;
//  * the V9 per-vertex ground mask exported from Blender (COLOR_0, only when
//    has_masks): R = fine-sand drift at road/paving/wall edges, G = estimated relief
//    (crests a little darker / gravellier), B = contact occlusion at walls/buildings.
// The same layers exist in the Blender source materials; nothing here is post-processing.
// V12: optional licensed CC0 PBR maps (Poly Haven) at physical world scale feed the SAME
// layers instead of replacing them: pbr_mode 1 = provider surface (mean colour matched to
// the approved V11 surface via pbr_tint), 2 = fine detail on V11 jointed paving/lawn,
// 3 = worn road paint over the asphalt maps.
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rough_tex : hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec4 albedo_color : source_color = vec4(1.0);
uniform bool has_albedo = true;
uniform bool has_normal = false;
uniform bool has_rough = false;
uniform vec4 rough_channel = vec4(0.0, 1.0, 0.0, 0.0);
uniform float roughness_mul = 1.0;
uniform float normal_strength = 1.0;
uniform float metallic_value = 0.0;
uniform bool stochastic = false;
uniform float macro_amount = 0.08;
uniform float macro_scale = 0.035;
// 0 generic, 1 natural soil/sand, 2 asphalt, 3 jointed unit paving, 4 lawn/planting
uniform int kind = 0;
uniform vec2 brick_size = vec2(0.0);
uniform float unit_variation = 0.0;
uniform bool has_masks = false;
uniform vec3 drift_color : source_color = vec3(0.70, 0.60, 0.45);
uniform float drift_amount = 0.0;
uniform float relief_tone = 0.0;
uniform float contact_ao = 0.0;
uniform vec3 patch_tint = vec3(0.94, 0.95, 0.99);
uniform float normal_boost = 1.0;
// V15: COLOR_0.a < 1 marks natural-surface boundaries (Blender v15_corridor.feather_fn); both
// sides blend toward one shared dusty transition tone with world-noise breakup, so soil, planted
// soil and lawn grade into each other instead of meeting at a hard patch edge.
uniform vec3 feather_color : source_color = vec3(0.62, 0.53, 0.40);
uniform float feather_amount = 0.0;

uniform int pbr_mode = 0;
uniform sampler2D pbr_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D pbr_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D pbr_rough : hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float pbr_tile_m = 2.1;
uniform float pbr_saturation = 1.0;
uniform float pbr_contrast = 1.0;
// Removes the provider's within-tile blotches (they repeat every tile and read as a grid);
// large-scale tone then comes only from the non-repeating world-space macro layers.
uniform float pbr_highpass = 0.0;
// Mip bias on the provider albedo only: suppresses JPEG 8x8 block moire at grazing angles.
uniform float pbr_albedo_bias = 0.0;
// Asphalt aggregate: cavity shading from the provider normal plus sparse light stone
// chips (1.2 cm world cells) that fade out before they could alias.
uniform float pbr_aggregate = 0.0;
uniform vec3 pbr_tint = vec3(1.0);
uniform float pbr_normal_strength = 0.3;
uniform float pbr_detail_amount = 0.18;
uniform float pbr_rough_floor = 0.7;
uniform bool pbr_rotate = false;
uniform vec3 paint_color : source_color = vec3(0.78, 0.78, 0.75);

varying vec3 wpos;
varying vec3 wnrm;
varying vec4 vmask;

float hash12(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash12(i), hash12(i + vec2(1.0, 0.0)), u.x),
			mix(hash12(i + vec2(0.0, 1.0)), hash12(i + vec2(1.0, 1.0)), u.x), u.y);
}

float fbm3(vec2 p) {
	return vnoise(p) * 0.55 + vnoise(p * 2.31 + 7.1) * 0.3 + vnoise(p * 5.17 + 3.3) * 0.15;
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	vmask = COLOR;
	wnrm = normalize(MODEL_NORMAL_MATRIX * NORMAL);
}

float luma(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }

void fragment() {
	vec2 uv = UV;
	bool own = pbr_mode != 1 && pbr_mode != 3;
	vec4 a = (has_albedo && own) ? texture(albedo_tex, uv) : vec4(1.0);
	vec3 n = own ? texture(normal_tex, uv).rgb : vec3(0.5, 0.5, 1.0);
	float r = (has_rough && own) ? dot(texture(rough_tex, uv), rough_channel) : 1.0;
	if (stochastic && own) {
		const float ang = 0.83;
		mat2 rot = mat2(vec2(cos(ang), sin(ang)), vec2(-sin(ang), cos(ang)));
		vec2 uv2 = rot * uv * 0.61 + vec2(0.37, 0.71);
		float m = smoothstep(0.32, 0.68, vnoise(wpos.xz * 0.043 + 11.0));
		if (has_albedo) {
			a = mix(a, texture(albedo_tex, uv2), m);
		}
		vec3 n2 = texture(normal_tex, uv2).rgb * 2.0 - 1.0;
		n2.xy = transpose(rot) * n2.xy;
		n = mix(n, n2 * 0.5 + 0.5, m);
		if (has_rough) {
			r = mix(r, dot(texture(rough_tex, uv2), rough_channel), m);
		}
	}
	vec3 col = a.rgb * albedo_color.rgb;
	// ---- V12 provider maps, world projection on the dominant axis (metres / tile).
	vec3 pn = vec3(0.0, 0.0, 1.0);
	vec2 puv = vec2(0.0);
	if (pbr_mode > 0) {
		vec3 an = abs(wnrm);
		puv = vec2(wpos.x, -wpos.z) / pbr_tile_m;
		if (an.x > an.y && an.x >= an.z) { puv = wpos.zy / pbr_tile_m; }
		else if (an.z > an.y && an.z > an.x) { puv = wpos.xy / pbr_tile_m; }
		vec3 pc = texture(pbr_albedo, puv, pbr_albedo_bias).rgb;
		vec3 pnt = texture(pbr_normal, puv).rgb * 2.0 - 1.0;
		float pr = texture(pbr_rough, puv).r;
		vec3 lp = textureLod(pbr_albedo, puv, 7.0).rgb;
		if (pbr_rotate) {
			// Anti-tiling: a rotated, 0.77x second sample under ~25 m world noise; the
			// normal XY is rotated back so lighting stays consistent.
			const float ang = 1.13;
			mat2 rot = mat2(vec2(cos(ang), sin(ang)), vec2(-sin(ang), cos(ang)));
			vec2 puv2 = rot * puv * 0.77 + vec2(0.41, 0.17);
			// Always mixed (35-65 %): a single sample anywhere shows the tile lattice at grazing angles.
			float m = 0.35 + 0.3 * vnoise(wpos.xz * 0.11 + 3.0);
			pc = mix(pc, texture(pbr_albedo, puv2, pbr_albedo_bias).rgb, m);
			lp = mix(lp, textureLod(pbr_albedo, puv2, 7.0).rgb, m);
			vec3 pn2 = texture(pbr_normal, puv2).rgb * 2.0 - 1.0;
			pn2.xy = transpose(rot) * pn2.xy;
			pnt = mix(pnt, pn2, m);
			pr = mix(pr, texture(pbr_rough, puv2).r, m);
		}
		// BC5/RGTC import keeps XY only: rebuild OpenGL +Z.
		pnt.z = sqrt(max(1.0 - dot(pnt.xy, pnt.xy), 0.001));
		pn = pnt;
		float pl = luma(pc);
		vec3 pm = textureLod(pbr_albedo, puv, 11.0).rgb;
		pc = mix(pc, max(pc - lp + pm, vec3(0.0)), pbr_highpass);
		float pmean = max(luma(pm), 0.01);
		if (pbr_mode == 1) {
			// Mean-preserving contrast about the provider's own mean (tint stays calibrated).
			vec3 pmd = mix(vec3(pmean), pm, pbr_saturation);
			col = mix(pmd, mix(vec3(pl), pc, pbr_saturation), pbr_contrast) * pbr_tint;
			if (pbr_aggregate > 0.0) {
				float cav = smoothstep(0.72, 0.985, pn.z);
				col *= mix(1.0, mix(0.86, 1.07, cav), pbr_aggregate);
				vec2 cell = floor(wpos.xz / 0.012);
				float chip = step(0.955, hash12(cell + 17.0)) * (0.6 + 0.4 * hash12(cell + 3.1));
				float fade = 1.0 - smoothstep(0.004, 0.011, length(fwidth(wpos.xz)));
				col = mix(col, col * 1.75 + vec3(0.025, 0.024, 0.022), chip * fade * 0.5 * pbr_aggregate);
			}
			r = max(pr, pbr_rough_floor);
		} else if (pbr_mode == 2) {
			col *= mix(1.0, clamp(pl / pmean, 0.65, 1.35), pbr_detail_amount);
			r = max(mix(r, pr, 0.35), pbr_rough_floor);
		} else {
			// Worn paint: slight aggregate show-through and patchy wear toward the asphalt.
			vec3 asph = mix(vec3(pl), pc, pbr_saturation) * pbr_tint;
			float wear = smoothstep(0.55, 0.85, vnoise(wpos.xz * 1.9 + 7.0)) * 0.28 + smoothstep(0.8, 0.45, pl / pmean) * 0.22;
			col = mix(paint_color * (0.94 + 0.08 * vnoise(wpos.xz * 6.0)), asph, wear);
			r = mix(0.62, max(pr, pbr_rough_floor), wear);
		}
	}
	// Large (~30 m) and medium (~8 m) world-space tone; V7 used one octave.
	float macro = fbm3(wpos.xz * macro_scale);
	float mid = fbm3(wpos.xz * macro_scale * 3.7 + 19.0);
	float tone = (macro - 0.5) * 2.0 * macro_amount + (mid - 0.5) * macro_amount * (kind == 1 || kind == 4 ? 1.1 : 0.5);
	col *= 1.0 + tone;
	if (kind == 1 || kind == 4) {
		// Patches of greyer lag gravel / drier planting (multiplicative tint only).
		float p = smoothstep(0.45, 0.72, fbm3(wpos.xz * 0.09 + 41.0));
		col *= mix(vec3(1.0), patch_tint, p);
	}
	if (kind == 3 && brick_size.x > 0.0) {
		// Exact Blender brick grid (Scale 1, offset 0.5 on even rows): per-unit tone.
		vec2 bp = vec2(wpos.x, -wpos.z);
		float row = floor(bp.y / brick_size.y);
		float off = (mod(row, 2.0) == 0.0) ? brick_size.x * 0.5 : 0.0;
		float col_i = floor((bp.x + off) / brick_size.x);
		float h = hash12(vec2(col_i, row) + 0.37);
		float h2 = hash12(vec2(row, col_i) + 5.11);
		col *= (1.0 + (h - 0.5) * 2.0 * unit_variation) * mix(vec3(1.0), vec3(1.03, 1.0, 0.96), (h2 - 0.5) * 2.0);
	}
	float ao = 1.0;
	if (has_masks) {
		float drift = pow(clamp(vmask.r, 0.0, 1.0), 1.4) * drift_amount * (0.45 + 0.55 * vnoise(wpos.xz * 1.3 + 5.0));
		col = mix(col, drift_color * (0.92 + 0.16 * vnoise(wpos.xz * 9.0)), drift);
		r = mix(r, 1.0, drift * 0.6);
		col *= 1.0 - relief_tone * (vmask.g - 0.5) * 2.0;
		ao = 1.0 - contact_ao * clamp(vmask.b, 0.0, 1.0);
		float fw = 1.0 - clamp(vmask.a, 0.0, 1.0);
		if (feather_amount > 0.0 && fw > 0.001) {
			float fn = fbm3(wpos.xz * 0.21 + 23.0) * 2.0 - 1.0;
			float e = clamp((fw - 0.55 * (1.0 - fw) * fn) * 1.12, 0.0, 1.0);
			e = e * e * (3.0 - 2.0 * e);
			vec3 fc = feather_color * (0.9 + 0.2 * vnoise(wpos.xz * 1.7 + 2.0));
			col = mix(col, fc, e * feather_amount);
			r = mix(r, 0.97, e * feather_amount * 0.5);
		}
	}
	ALBEDO = col;
	ROUGHNESS = clamp(r * roughness_mul + (macro - 0.5) * 0.08, 0.03, 1.0);
	METALLIC = metallic_value;
	AO = ao;
	AO_LIGHT_AFFECT = 0.2;
	if (pbr_mode > 0) {
		// Derivative cotangent frame of the world projection (independent of GLB tangents).
		vec3 dp1 = dFdx(wpos), dp2 = dFdy(wpos);
		vec2 du1 = dFdx(puv), du2 = dFdy(puv);
		float det = du1.x * du2.y - du1.y * du2.x;
		vec3 nw = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
		vec3 tw = (dp1 * du2.y - dp2 * du1.y) * sign(det);
		vec3 bw = (-dp1 * du2.x + dp2 * du1.x) * sign(det);
		tw = normalize(tw - nw * dot(tw, nw) + vec3(1e-6));
		bw = normalize(bw - nw * dot(bw, nw) + vec3(1e-6));
		float k = pbr_normal_strength * (pbr_mode == 3 ? 0.5 : 1.0);
		vec3 nn = normalize(tw * pn.x * k + bw * pn.y * k + nw * max(pn.z, 0.2));
		NORMAL = normalize((VIEW_MATRIX * vec4(nn, 0.0)).xyz);
	}
	if (has_normal && pbr_mode != 1 && pbr_mode != 3) {
		NORMAL_MAP = n;
		NORMAL_MAP_DEPTH = normal_strength * normal_boost;
	}
}
