// V12: one provider PBR set, physical world-space projection, no inherited dust.
// Diffuse alone is sRGB. Roughness and OpenGL normals remain linear data.
shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rough_tex : filter_linear_mipmap_anisotropic, repeat_enable;
uniform float tile_m = 2.1;
uniform float normal_strength = 0.4;
uniform float saturation = 1.0;
uniform float brightness = 1.0;
uniform float roughness_floor = 0.72;
uniform float albedo_contrast = 1.0;
uniform bool detail_only = false;
uniform sampler2D base_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec4 base_color : source_color = vec4(1.0);
uniform bool local_trial = false;
varying vec3 wp;
varying vec3 wn;
void vertex() {
    wp = (MODEL_MATRIX * vec4(VERTEX,1.0)).xyz;
    wn = normalize(MODEL_NORMAL_MATRIX * NORMAL);
}
void fragment() {
    vec3 an = abs(wn);
    vec2 uv = wp.xy / tile_m;
    if (an.y >= an.x && an.y >= an.z) { uv = vec2(wp.x,-wp.z) / tile_m; }
    else if (an.x >= an.z) { uv = wp.zy / tile_m; }
    vec3 c = texture(albedo_tex,uv).rgb;
    c = mix(vec3(dot(c,vec3(0.2126,0.7152,0.0722))),c,saturation)*brightness;
    c=mix(vec3(0.32),c,albedo_contrast);
    if (detail_only) { c=texture(base_tex,UV).rgb*base_color.rgb*mix(vec3(1.0),clamp(c/0.45,vec3(0.7),vec3(1.3)),0.18); }
    vec3 nt = texture(normal_tex,uv).rgb*2.0-1.0;
    // Godot may encode imported normals as RGTC/BC5: reconstruct OpenGL +Z from XY.
    nt.z=sqrt(max(1.0-dot(nt.xy,nt.xy),0.001));
    // Derivative cotangent frame follows this projection, independent of GLB UV/tangents.
    vec3 dp1=dFdx(wp), dp2=dFdy(wp);
    vec2 du1=dFdx(uv), du2=dFdy(uv);
    float det=du1.x*du2.y-du1.y*du2.x;
    vec3 nw=normalize((INV_VIEW_MATRIX*vec4(NORMAL,0.0)).xyz);
    vec3 tw=normalize((dp1*du2.y-dp2*du1.y)*sign(det));
    tw=normalize(tw-nw*dot(tw,nw));
    vec3 bw=normalize((-dp1*du2.x+dp2*du1.x)*sign(det));
    bw=normalize(bw-nw*dot(bw,nw));
    vec3 nn=normalize(tw*nt.x*normal_strength+bw*nt.y*normal_strength+nw*max(nt.z,0.15));
    NORMAL=normalize((VIEW_MATRIX*vec4(nn,0.0)).xyz);
    ALBEDO=c;
    ROUGHNESS=clamp(texture(rough_tex,uv).r,roughness_floor,1.0);
    METALLIC=0.0;
}
