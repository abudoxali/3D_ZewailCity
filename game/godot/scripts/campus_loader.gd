extends Node3D
## Loads the Blender-exported campus (res://assets/campus/campus_full.glb) and
## prepares it for real-time use. The GLB is never edited here; everything is
## done on the instanced copy, so re-exporting from Blender just works.
##
##  * VEG_* / PROP_* instances that share a mesh become spatially chunked
##    MultiMeshInstance3D nodes (one draw per mesh per 160 m cell) with
##    visibility ranges.
##  * COL_*-colonly proxies were imported as StaticBody3D. They go on physics
##    layer 1 (world_static).
##  * Spawn points and landmarks come from campus_manifest.json, which
##    build_game_assets.py writes from src/utilities/game_points.py.

signal loaded

const CAMPUS_PATH := "res://assets/campus/campus_full.glb"
const MANIFEST_PATH := "res://assets/campus/campus_manifest.json"
const CHUNK := 160.0
const WORLD_LAYER := 1

var manifest: Dictionary = {}
var spawns: Array = []        # [{id, label, position: Vector3, facing: Vector3, note}]
var landmarks: Array = []     # [{id, label, position, radius, verified, evidence, spawn}]
var campus_root: Node3D
var stats := {}
var _batches: Array[MultiMeshInstance3D] = []
var gate_controller: Node


func load_campus() -> void:
	var t0 := Time.get_ticks_msec()
	manifest = _read_json(MANIFEST_PATH)
	var packed: PackedScene = load(CAMPUS_PATH)
	if packed == null:
		push_error("Campus GLB missing or not imported: " + CAMPUS_PATH)
		return
	campus_root = packed.instantiate()
	campus_root.name = "Campus"
	add_child(campus_root)
	var t_inst := Time.get_ticks_msec()
	var bodies := _setup_collision(campus_root)
	var ground_mats := _upgrade_ground_materials()
	var veg := _batch_group("Game_Vegetation", true)
	var props := _batch_group("Game_Props", false)
	_read_points()
	apply_settings()
	# V11: interactive perimeter gate leaves (G1-G6) with real colliders.
	gate_controller = load("res://scripts/gate_controller.gd").new()
	gate_controller.name = "Gates"
	add_child(gate_controller)
	var gate_leaves: int = gate_controller.setup(campus_root)
	stats = {
		"gate_leaves": gate_leaves,
		"load_ms": t_inst - t0, "prepare_ms": Time.get_ticks_msec() - t_inst,
		"static_bodies": bodies, "veg_batches": veg, "prop_batches": props,
		"spawns": spawns.size(), "landmarks": landmarks.size(), "v7_ground_shader_materials": ground_mats, "v9_masked_ground_surfaces": masked_surfaces,
	}
	print("[campus] loaded in %d ms (+%d ms prepare): %s" % [stats.load_ms, stats.prepare_ms, str(stats)])
	await get_tree().physics_frame
	await get_tree().physics_frame
	loaded.emit()


## V7: ground/road/sidewalk materials keep their baked Blender textures but use
## res://shaders/ground_surface.gdshader for large-scale tone variation and, on
## non-jointed aggregates, an anti-tiling second sample. Returns materials converted.
const GROUND_SHADER := preload("res://shaders/ground_surface.gdshader")
const STOCHASTIC_KEYS := ["Asphalt", "Sand", "Soil", "Earth", "Grass", "Groundcover", "Planted", "Mulch", "Pebbles", "Gravel"]
var _ground_cache := {}
var v12_pbr = preload("res://scripts/pbr_materials.gd").new()
var emissive_materials: Array[StandardMaterial3D] = []

func _upgrade_ground_materials() -> int:
	for group_name in ["Game_Terrain", "Game_Roads", "Game_Sidewalks"]:
		var group := campus_root.find_child(group_name, true, false)
		if group == null:
			continue
		for mi in group.find_children("*", "MeshInstance3D", true, false):
			var m := mi as MeshInstance3D
			if m.mesh == null:
				continue
			for i in m.mesh.get_surface_count():
				var src := m.mesh.surface_get_material(i) as StandardMaterial3D
				# V12: flat road paint becomes worn paint over the asphalt maps.
				if src != null and src.resource_name.contains("Road_Marking"):
					m.set_surface_override_material(i, v12_pbr.paint(src, GROUND_SHADER))
					continue
				if src == null or src.albedo_texture == null:
					continue
				# V9: Blender's per-vertex ground mask arrives as COLOR_0.
				var masked: bool = (m.mesh.surface_get_format(i) & Mesh.ARRAY_FORMAT_COLOR) != 0
				m.set_surface_override_material(i, _ground_material(src, masked))
				if masked:
					masked_surfaces += 1
	# Lamp lenses / lit windows: emission is scaled by the day/evening profile.
	for mi in campus_root.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = (mi as MeshInstance3D).mesh
		if mesh == null:
			continue
		for i in mesh.get_surface_count():
			var sm := mesh.surface_get_material(i) as StandardMaterial3D
			if sm and sm.emission_enabled and not emissive_materials.has(sm):
				emissive_materials.append(sm)
			# V10: the Administration entrance screen is see-through clear glazing (A02
			# shows the recessed lobby behind it); all other campus glass stays opaque
			# reflective, as in V5-V9.
			if sm and sm.resource_name.contains("Lobby_Glass") and sm.transparency == BaseMaterial3D.TRANSPARENCY_DISABLED:
				sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
				sm.albedo_color.a = 0.22
				sm.metallic = 0.1
				sm.roughness = 0.04
				sm.cull_mode = BaseMaterial3D.CULL_DISABLED
			_v11_material_tuning(sm)
			if sm:
				var detail=v12_pbr.architecture(sm)
				if detail != null:
					(mi as MeshInstance3D).set_surface_override_material(i,detail)
	return _ground_cache.size()


## V11 realism pass (owner: avoid opaque-looking glass and washed-out white facades).
## Opaque campus glass gets a low-roughness, partly metallic response so it mirrors the sky
## (SSR on High/Ultra, reflection probes) instead of reading as dark paint; light stone and
## plaster are a touch less bright and less glossy under the strong Egyptian sun.
var _v11_tuned := {}
func _v11_material_tuning(sm: StandardMaterial3D) -> void:
	if sm == null or _v11_tuned.has(sm):
		return
	_v11_tuned[sm] = true
	var n := sm.resource_name
	if n.contains("Glass") and not n.contains("Lobby_Glass") and sm.transparency == BaseMaterial3D.TRANSPARENCY_DISABLED:
		sm.metallic = 0.6
		sm.roughness = 0.03
		sm.metallic_specular = 0.75
		sm.albedo_color = sm.albedo_color.lerp(Color(0.10, 0.14, 0.18), 0.35)
	elif n.contains("Stone") or n.contains("Stucco") or n.contains("Plaster"):
		# Wave 5 review: P09/P12/P14/P15 stone is warm sand/ochre, not grey-white.
		sm.albedo_color = sm.albedo_color * Color(0.96, 0.89, 0.77, 1.0)
		sm.roughness = maxf(sm.roughness, 0.78)


## V9 jointed unit paving: Blender brick sizes (materials.paving) for per-unit tone.
const BRICKS := {"Paving_Limestone": Vector2(0.9, 0.45), "Paving_Light": Vector2(1.2, 0.6), "Plaza_Grey": Vector2(1.2, 0.6),
	"Plaza_Light": Vector2(1.2, 0.6), "Garden_Pavers": Vector2(0.22, 0.11), "Paver_Road_Grey": Vector2(0.22, 0.11)}
var masked_surfaces := 0

func _ground_material(src: StandardMaterial3D, masked := false) -> ShaderMaterial:
	var key := [src, masked]
	if _ground_cache.has(key):
		return _ground_cache[key]
	var n := String(src.resource_name)
	var sm := ShaderMaterial.new()
	sm.shader = GROUND_SHADER
	sm.resource_name = "V7_" + n
	sm.set_shader_parameter("albedo_tex", src.albedo_texture)
	sm.set_shader_parameter("albedo_color", src.albedo_color)
	sm.set_shader_parameter("has_normal", src.normal_enabled and src.normal_texture != null)
	if src.normal_texture:
		sm.set_shader_parameter("normal_tex", src.normal_texture)
	sm.set_shader_parameter("normal_strength", src.normal_scale)
	sm.set_shader_parameter("has_rough", src.roughness_texture != null)
	if src.roughness_texture:
		sm.set_shader_parameter("rough_tex", src.roughness_texture)
		var ch := [Vector4(1, 0, 0, 0), Vector4(0, 1, 0, 0), Vector4(0, 0, 1, 0), Vector4(0, 0, 0, 1), Vector4(0.299, 0.587, 0.114, 0)]
		sm.set_shader_parameter("rough_channel", ch[int(src.roughness_texture_channel)])
	sm.set_shader_parameter("roughness_mul", src.roughness)
	sm.set_shader_parameter("metallic_value", src.metallic)
	var stochastic := false
	for k in STOCHASTIC_KEYS:
		if n.contains(k):
			stochastic = true
	sm.set_shader_parameter("stochastic", stochastic)
	var amount := 0.05
	if n.contains("Asphalt"):
		amount = 0.10
	elif stochastic:
		amount = 0.14
	sm.set_shader_parameter("macro_amount", amount)
	# V9 surface kinds and mask response (values mirror the Blender source layers).
	var kind := 0
	if n.contains("Sand") or n.contains("Soil") or n.contains("Earth"):
		kind = 1
	elif n.contains("Asphalt"):
		kind = 2
	elif n.contains("Grass") or n.contains("Groundcover"):
		kind = 4
	for b in BRICKS:
		if n.contains(b):
			kind = 3
			sm.set_shader_parameter("brick_size", BRICKS[b])
			sm.set_shader_parameter("unit_variation", 0.10)
	sm.set_shader_parameter("kind", kind)
	sm.set_shader_parameter("has_masks", masked)
	if kind == 1:
		sm.set_shader_parameter("macro_amount", 0.15)
		# Desert sand carries low wind ripples; a lower boost keeps them subtle.
		sm.set_shader_parameter("normal_boost", 1.2 if n.contains("Desert_Sand") else 1.6)
		sm.set_shader_parameter("macro_scale", 0.03)
		sm.set_shader_parameter("drift_color", Color(0.80, 0.69, 0.53))
		sm.set_shader_parameter("drift_amount", 0.35 if n.contains("Planted") else 0.6)
		sm.set_shader_parameter("relief_tone", 0.12)
		sm.set_shader_parameter("contact_ao", 0.35)
		sm.set_shader_parameter("patch_tint", Color(0.88, 0.91, 0.98))
	elif kind == 2:
		sm.set_shader_parameter("macro_amount", 0.09)
		sm.set_shader_parameter("normal_boost", 1.3)
		sm.set_shader_parameter("drift_color", Color(0.72, 0.62, 0.48))
		sm.set_shader_parameter("drift_amount", 0.75)
	elif kind == 4:
		sm.set_shader_parameter("macro_amount", 0.14)
		sm.set_shader_parameter("patch_tint", Color(1.08, 1.0, 0.72))
	elif n.contains("Paver_Road"):
		sm.set_shader_parameter("drift_color", Color(0.72, 0.62, 0.48))
		sm.set_shader_parameter("drift_amount", 0.65)
	# V15: feathered natural-surface boundaries in the G1 corridor (COLOR_0.a, see shader).
	if kind == 1 or kind == 4:
		sm.set_shader_parameter("feather_amount", 0.5 if kind == 1 else 0.2)
		sm.set_shader_parameter("feather_color", Color(0.62, 0.53, 0.40))
	# V15 raised verge beds and worn median: kerb-side sand drift (C02).
	if n.contains("V15_Planted_Bed") or n.contains("V15_Median"):
		sm.set_shader_parameter("drift_color", Color(0.74, 0.63, 0.47))
		sm.set_shader_parameter("drift_amount", 0.55)
	v12_pbr.configure(sm, n)
	_ground_cache[key] = sm
	return sm


func _read_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_warning("Missing " + path)
		return {}
	var d = JSON.parse_string(FileAccess.get_file_as_string(path))
	return d if d is Dictionary else {}


func _setup_collision(root: Node) -> int:
	var n := 0
	for body in root.find_children("*", "StaticBody3D", true, false):
		var sb := body as StaticBody3D
		sb.collision_layer = 1 << (WORLD_LAYER - 1)
		sb.collision_mask = 0
		n += 1
	return n


func _batch_group(group_name: String, is_veg: bool) -> int:
	var group := campus_root.find_child(group_name, true, false) as Node3D
	if group == null:
		return 0
	var inv := group.global_transform.affine_inverse()
	var buckets := {}
	for child in group.get_children():
		var mi := child as MeshInstance3D
		if mi == null or mi.mesh == null:
			continue
		var key := "%d" % mi.mesh.get_instance_id()
		if not buckets.has(key):
			buckets[key] = {"mesh": mi.mesh, "nodes": []}
		buckets[key].nodes.append(mi)
	var made := 0
	for key in buckets:
		var b: Dictionary = buckets[key]
		if b.nodes.size() < 2:
			continue   # unique pieces (flower beds, pergola) stay ordinary meshes
		var cells := {}
		for mi: MeshInstance3D in b.nodes:
			var xf: Transform3D = inv * mi.global_transform
			var cell := Vector2i(floori(xf.origin.x / CHUNK), floori(xf.origin.z / CHUNK))
			if not cells.has(cell):
				cells[cell] = []
			cells[cell].append(xf)
		var mesh_name := String(b.nodes[0].name).rsplit("_", true, 1)[0]   # VEG_ASSET_Tree_0
		for cell in cells:
			var xforms: Array = cells[cell]
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.mesh = b.mesh
			mm.instance_count = xforms.size()
			for i in xforms.size():
				mm.set_instance_transform(i, xforms[i])
			var mmi := MultiMeshInstance3D.new()
			mmi.multimesh = mm
			mmi.name = "MM_%s_%d_%d" % [mesh_name, cell.x, cell.y]
			var lower := String(b.nodes[0].name).to_lower()
			mmi.set_meta("is_veg", is_veg)
			mmi.set_meta("small", lower.contains("shrub"))
			# V15: ground-hugging groundcover clumps (8-10 cm): no shadows, short draw range.
			mmi.set_meta("groundcover", lower.contains("groundcover"))
			if lower.contains("groundcover"):
				mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			if lower.contains("shrub"):
				mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				# V13: leaf-geometry shrubs sit in full sun on open beds; their shared
				# Pachira leaf material reads too dark there (independent QA).
				if lower.contains("leafy"):
					for si in b.mesh.get_surface_count():
						var lm := b.mesh.surface_get_material(si) as StandardMaterial3D
						if lm:
							var bright := lm.duplicate() as StandardMaterial3D
							bright.albedo_color = lm.albedo_color * Color(1.35, 1.4, 1.25, 1.0)
							mmi.set_surface_override_material(si, bright)
			group.add_child(mmi)
			_batches.append(mmi)
			made += 1
		for mi: MeshInstance3D in b.nodes:
			mi.queue_free()
	return made


func _read_points() -> void:
	spawns.clear()
	landmarks.clear()
	for s in manifest.get("spawn_points", []):
		spawns.append({
			"id": s.id, "label": s.label, "note": s.get("note", ""),
			"position": _v3(s.godot), "facing": _v3(s.facing_godot),
		})
	for l in manifest.get("landmarks", []):
		landmarks.append({
			"id": l.id, "label": l.label, "position": _v3(l.godot), "radius": float(l.radius),
			"verified": bool(l.verified), "evidence": l.get("evidence", ""), "spawn": l.get("spawn", ""),
		})
	if spawns.is_empty():   # fall back to the empties in the GLB
		for n in campus_root.find_children("SPAWN_*", "Node3D", true, false):
			spawns.append({"id": n.name, "label": n.name, "note": "", "position": n.global_position,
				"facing": Vector3(0, 0, 1)})


func _v3(a) -> Vector3:
	return Vector3(float(a[0]), float(a[1]), float(a[2]))


func apply_settings() -> void:
	var v: Dictionary = Settings.values()
	for mmi in _batches:
		if not is_instance_valid(mmi):
			continue
		var r: float = v.veg_range if mmi.get_meta("is_veg", false) else v.prop_range
		if mmi.get_meta("small", false):
			r *= 0.5
		if mmi.get_meta("groundcover", false):
			r = minf(r * 0.12, 150.0)
		mmi.visibility_range_end = r + CHUNK * 0.7
		mmi.visibility_range_end_margin = 40.0
		mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF


func spawn_by_id(id: String) -> Dictionary:
	for s in spawns:
		if s.id == id:
			return s
	return {}


## Highest walkable surface under (x, z) that is below `max_h` (so roofs and
## canopies are ignored when the spawn is next to a building). Returns null if none.
func ground_at(x: float, z: float, max_h := 3.0) -> Variant:
	var space := get_world_3d().direct_space_state
	var from := Vector3(x, max_h, z)
	var q := PhysicsRayQueryParameters3D.create(from, Vector3(x, -60.0, z), 1 << (WORLD_LAYER - 1))
	var hit := space.intersect_ray(q)
	if hit.is_empty():
		return null
	return hit.position


## A collision-free body-centre position for a capsule standing at spawn `s`.
func safe_spawn_position(s: Dictionary, capsule: Shape3D, half_height: float, exclude: Array = []) -> Vector3:
	var ex: Array[RID] = []
	ex.assign(exclude)
	var base: Vector3 = s.position
	var offsets: Array[Vector2] = [Vector2.ZERO]
	for ring in range(1, 7):
		for k in 8:
			var a := TAU * k / 8.0
			offsets.append(Vector2(cos(a), sin(a)) * ring * 1.0)
	var space := get_world_3d().direct_space_state
	for o in offsets:
		var g = ground_at(base.x + o.x, base.z + o.y)
		if g == null:
			continue
		var centre: Vector3 = g + Vector3(0, half_height + 0.05, 0)
		var q := PhysicsShapeQueryParameters3D.new()
		q.shape = capsule
		q.transform = Transform3D(Basis(), centre)
		q.collision_mask = 1 << (WORLD_LAYER - 1)
		q.exclude = ex
		if space.intersect_shape(q, 1).is_empty():
			return centre
	return base + Vector3(0, half_height + 2.0, 0)


## Nearest landmark whose radius contains `pos` (2D). Smaller radii win, so the
## dome beats the building that contains it.
func landmark_at(pos: Vector3) -> Dictionary:
	var best := {}
	var best_r := INF
	for l in landmarks:
		var d := Vector2(pos.x - l.position.x, pos.z - l.position.z).length()
		if d <= l.radius and l.radius < best_r:
			best = l
			best_r = l.radius
	return best
