extends RefCounted
## V12 licensed PBR integration (Poly Haven CC0, see res://assets/pbr/manifest.json).
## Ground surfaces keep the V11 ground shader and its layers (macro tone, anti-tiling,
## Blender drift/relief/contact masks); this script only adds provider maps to it.
## Natural sand, graded soil, compacted earth and planted sparse soil keep their V11
## procedural surfaces (mode 2): as whole surfaces, provider sand_01 read as grey cracked
## crust and sparse_grass lost V11's green-brown variation (independent QA).
## Provider surfaces (mode 1) are tinted to the approved V11 mean colour
## (res://assets/pbr/tone_targets.json, tools/v12_tone_targets.py), so a surface keeps its
## identity and gains physical-scale detail. Jointed V11 paving and lawn keep their own
## albedo/joints and receive fine detail only (mode 2). Road paint is mode 3.
## V13 QA: ambientCG PavingStones125A (photographed running bond) was tried and REJECTED
## (stone grain smeared into streaks at grazing angles; joints vanished beyond ~15 m).
## Campus paver roads and dormitory paths kept the V11 0.22 x 0.11 m running bond
## (D02 photo: rectangular grey pavers, low-contrast joints; the provider concrete_pavers
## zig-zag was the wrong unit) with fine concrete_pavement_03 detail. Asphalt roughness
## floor 0.93: the 0.86 floor gave a demonstrable mid-distance specular sheen band.
const SHADER=preload("res://shaders/pbr_world.gdshader")
## key: [asset, tile metres, normal strength, mode, anti-tiling rotation, roughness floor, contrast]
const GROUND={
	"Asphalt":["asphalt_01",2.1,0.5,1,true,0.93,1.0],
	"Paver_Road_Grey":["concrete_pavement_03",2.1,0.12,2,false,0.76],
	"Garden_Pavers":["concrete_pavement_03",2.1,0.12,2,false,0.76],
	"Desert_Sand":["sand_01",1.5,0.3,2,false,0.8],
	"Graded_Campus_Soil":["sand_01",1.5,0.3,2,false,0.8],
	"Compacted_Earth":["sand_01",1.5,0.28,2,false,0.8],
	"Planted_Soil_Sparse":["sparse_grass",2.0,0.3,2,true,0.8],
	"Plaza_Grey":["concrete_pavement_03",2.1,0.22,2,false,0.72],
	"Plaza_Light":["concrete_pavement_03",2.1,0.22,2,false,0.72],
	"Paving_Limestone":["concrete_pavement_03",2.1,0.22,2,false,0.72],
	"Paving_Light":["concrete_pavement_03",2.1,0.22,2,false,0.72],
	"Concrete_Curb":["concrete_pavement_03",2.1,0.2,2,false,0.74],
	"Paving_Edge_Restraint":["concrete_pavement_03",2.1,0.2,2,false,0.74],
	"Grass_Lawn":["sparse_grass",2.0,0.25,2,true,0.8],
	## V15: raised kerbed verge beds of brown soil (C02); Poly Haven `dirt` (CC0) at its 2.0 m
	## physical tile is also the baked Blender source, so detail mode keeps it calibrated.
	"V15_Planted_Bed_Soil":["dirt",2.0,0.35,2,true,0.82],
}
## Provider map resolution per asset (default 1k).
const RES={"paving_stones_125a":"2k","dirt":"2k"}
var cache={}
var tones={}

func _init() -> void:
	if FileAccess.file_exists("res://assets/pbr/tone_targets.json"):
		var d=JSON.parse_string(FileAccess.get_file_as_string("res://assets/pbr/tone_targets.json"))
		if d is Dictionary: tones=d

func _maps(sm:ShaderMaterial,asset:String) -> void:
	for m in ["diff","nor_gl","rough"]:
		sm.set_shader_parameter({"diff":"pbr_albedo","nor_gl":"pbr_normal","rough":"pbr_rough"}[m],load("res://assets/pbr/%s/%s_%s_%s.jpg" % [asset,asset,m,RES.get(asset,"1k")]))

## Adds provider maps to a V11 ground ShaderMaterial (res://shaders/ground_surface.gdshader).
## Returns true when the surface is a V12 PBR surface.
func configure(sm:ShaderMaterial,n:String) -> bool:
	for key in GROUND:
		if not n.contains(key): continue
		var a:Array=GROUND[key]
		_maps(sm,a[0])
		sm.set_shader_parameter("pbr_mode",a[3])
		sm.set_shader_parameter("pbr_tile_m",a[1])
		sm.set_shader_parameter("pbr_normal_strength",a[2])
		sm.set_shader_parameter("pbr_rotate",a[4])
		sm.set_shader_parameter("pbr_rough_floor",a[5])
		if a[3]==1:
			var t:Dictionary=tones.get(key,{})
			var tint:Array=t.get("tint",[1.0,1.0,1.0])
			sm.set_shader_parameter("pbr_tint",Vector3(tint[0],tint[1],tint[2]))
			sm.set_shader_parameter("pbr_saturation",float(t.get("saturation",1.0)))
			sm.set_shader_parameter("pbr_contrast",a[6])
			sm.set_shader_parameter("pbr_highpass",0.0)
			sm.set_shader_parameter("pbr_albedo_bias",0.0)
			sm.set_shader_parameter("pbr_aggregate",1.0 if key=="Asphalt" else 0.0)
			# Provider paver shapes differ from the V11 brick grid: no per-brick tone.
			sm.set_shader_parameter("unit_variation",0.0)
		else:
			sm.set_shader_parameter("pbr_detail_amount",0.22 if key=="Grass_Lawn" else 0.12 if key in ["Paver_Road_Grey","Garden_Pavers"] else 0.18)
		sm.resource_name="V12_"+key
		return true
	return false

## Road paint (flat V11 material) becomes worn paint over the actual asphalt maps.
func paint(src:StandardMaterial3D,ground_shader:Shader) -> ShaderMaterial:
	var key="paint_"+src.resource_name
	if cache.has(key): return cache[key]
	var sm=ShaderMaterial.new()
	sm.shader=ground_shader
	sm.resource_name="V12_"+src.resource_name
	_maps(sm,"asphalt_01")
	var t:Dictionary=tones.get("Asphalt",{})
	var tint:Array=t.get("tint",[1.0,1.0,1.0])
	sm.set_shader_parameter("pbr_mode",3)
	sm.set_shader_parameter("pbr_tile_m",2.1)
	sm.set_shader_parameter("pbr_normal_strength",0.45)
	sm.set_shader_parameter("pbr_rough_floor",0.93)
	sm.set_shader_parameter("pbr_tint",Vector3(tint[0],tint[1],tint[2]))
	sm.set_shader_parameter("pbr_saturation",float(t.get("saturation",0.2)))
	sm.set_shader_parameter("pbr_highpass",0.0)
	sm.set_shader_parameter("pbr_albedo_bias",0.0)
	sm.set_shader_parameter("pbr_rotate",true)
	# Slightly off-white / ochre retroreflective paint, not pure display white.
	var c:Color=src.albedo_color
	sm.set_shader_parameter("paint_color",Vector3(c.r,c.g,c.b)*0.92)
	sm.set_shader_parameter("has_albedo",false)
	cache[key]=sm
	return sm

## Facades/stairs: V11 stone/stucco albedo and joints plus fine beige_wall_001 response.
func architecture(src:StandardMaterial3D) -> ShaderMaterial:
	var n=src.resource_name
	if not (n.contains("Stone") or n.contains("Stucco")) or src.albedo_texture==null: return null
	var key="arch_"+n
	if cache.has(key): return cache[key]
	var sm=ShaderMaterial.new()
	sm.shader=SHADER
	sm.resource_name="V12_"+n
	for m in ["diff","nor_gl","rough"]:
		sm.set_shader_parameter({"diff":"albedo_tex","nor_gl":"normal_tex","rough":"rough_tex"}[m],load("res://assets/pbr/beige_wall_001/beige_wall_001_%s_1k.jpg" % m))
	sm.set_shader_parameter("detail_only",true)
	sm.set_shader_parameter("base_tex",src.albedo_texture)
	sm.set_shader_parameter("base_color",src.albedo_color)
	sm.set_shader_parameter("tile_m",3.0)
	sm.set_shader_parameter("normal_strength",0.22)
	sm.set_shader_parameter("roughness_floor",0.78)
	cache[key]=sm
	return sm
