extends Node
## Automated checks for the explorer. Runs the real Main scene and drives the
## player through simulated input actions (Input.action_press), so it exercises
## the same code paths as the keyboard, but it is NOT a human play test.
##
## Validation (headless OK):
##   godot --headless --path game/godot res://tests/Validate.tscn
## Screenshots + performance (needs a window / GPU):
##   godot --path game/godot --resolution 1920x1080 res://tests/Validate.tscn -- --capture
##
## Reports: output/validation/godot_validation.json, output/validation/godot_performance.json,
## screenshots: output/previews/godot/*.png

## --outdir selects a separate evidence directory; current default is V8.
var OUT_VALID := "res://../../output/validation/v11/"
var OUT_SHOTS := "res://../../output/validation/v11/game_captures/"
## V4 main gate line in Godot coordinates (Blender y = 314.6 -> Godot z = -314.6).
const GATE_Z := -314.6

var main: Node3D
var player: CharacterBody3D
var campus: Node3D
var results: Array = []
var capture_mode := false


func _ready() -> void:
	capture_mode = "--capture" in OS.get_cmdline_user_args()
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--outdir="):
			OUT_VALID = "res://../../output/validation/" + a.get_slice("=", 1).trim_suffix("/") + "/"
			OUT_SHOTS = OUT_VALID + "game_captures/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT_VALID))
	# V7: --uncapped removes vsync / FPS cap so GPU cost differences are measurable.
	if "--uncapped" in OS.get_cmdline_user_args():
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
		Engine.max_fps = 0
	main = load("res://scenes/Main.tscn").instantiate()
	add_child(main)
	while not main.ready_done:
		await get_tree().process_frame
	player = main.player
	campus = main.campus
	if capture_mode:
		await run_capture()
	else:
		await run_validation()
	get_tree().quit(0 if results.all(func(r): return r["pass"]) else 1)


# ------------------------------------------------------------------ helpers
func check(name: String, ok: bool, detail: Dictionary = {}) -> void:
	results.append({"name": name, "pass": ok, "detail": detail})
	print(("[PASS] " if ok else "[FAIL] ") + name + "  " + JSON.stringify(detail))


func frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func hold(action: String, seconds: float) -> void:
	Input.action_press(action)
	await frames(int(seconds * 60.0))
	Input.action_release(action)
	await frames(2)


func walk_until(cond: Callable, timeout: float) -> void:
	Input.action_press("move_forward")
	var n := 0
	while not cond.call() and n < int(timeout * 60.0):
		await get_tree().physics_frame
		n += 1
	Input.action_release("move_forward")
	await frames(2)


## Sends a real InputEventAction, so _unhandled_input handlers see it like a key press.
func tap(action: String) -> void:
	for pressed in [true, false]:
		var ev := InputEventAction.new()
		ev.action = action
		ev.pressed = pressed
		Input.parse_input_event(ev)
		await frames(2)


func space() -> PhysicsDirectSpaceState3D:
	return player.get_world_3d().direct_space_state


func ray(from: Vector3, to: Vector3, mask := 1) -> Dictionary:
	var q := PhysicsRayQueryParameters3D.create(from, to, mask)
	q.exclude = [player.get_rid()]
	return space().intersect_ray(q)


func overlapping(pos: Vector3) -> bool:
	var q := PhysicsShapeQueryParameters3D.new()
	q.shape = player.shape
	q.transform = Transform3D(Basis(), pos)
	q.collision_mask = 1
	q.exclude = [player.get_rid()]
	return not space().intersect_shape(q, 1).is_empty()


func goto_spawn(i: int) -> Dictionary:
	var s: Dictionary = campus.spawns[i]
	main._go_to_spawn(s.id, "", false)
	await frames(45)
	return s


func r3(v: Vector3) -> Array:
	return [snappedf(v.x, 0.01), snappedf(v.y, 0.01), snappedf(v.z, 0.01)]


func save_json(path: String, data) -> void:
	path = OUT_VALID + path.get_file()
	if data is Dictionary and is_instance_valid(campus):
		data["source_blend_sha256"]=campus.manifest.get("source_blend_sha256","")
		data["asset_sha256"]=FileAccess.get_sha256("res://assets/campus/campus_full.glb")
	var apath := ProjectSettings.globalize_path(path)
	DirAccess.make_dir_recursive_absolute(apath.get_base_dir())
	var f := FileAccess.open(apath, FileAccess.WRITE)
	f.store_string(JSON.stringify(data, "  "))
	f.close()
	print("[validate] wrote " + apath)


# ------------------------------------------------------------------ validation
func run_validation() -> void:
	main._start_explore()
	var st: Dictionary = campus.stats
	check("campus loaded with collision and batched instances",
		st.static_bodies >= 7 and st.veg_batches > 0 and st.spawns >= 5, st)

	# 1. every spawn is grounded, settled and not inside geometry
	for i in campus.spawns.size():
		var s := await goto_spawn(i)
		var p0 := player.global_position
		await frames(60)
		var p1 := player.global_position
		var g := ray(p1 + Vector3(0, 2, 0), p1 + Vector3(0, -50, 0))
		var feet: float = player.feet_position().y
		var ok := player.is_on_floor() and p0.distance_to(p1) < 0.3 and not overlapping(p1 + Vector3(0, 0.05, 0)) \
			and not g.is_empty() and absf(feet - g.position.y) < 0.15
		check("spawn grounded: " + s.id, ok, {"feet_y": snappedf(feet, 0.01), "ground_y": snappedf(g.position.y if not g.is_empty() else -999.0, 0.01),
			"settle_move_m": snappedf(p0.distance_to(p1), 0.001), "on_floor": player.is_on_floor(), "pos": r3(p1)})

	# 2. walking speed and sprint speed on open ground (approach lawn)
	await goto_spawn(4)
	var a := player.global_position
	await hold("move_forward", 2.0)
	var walk_speed := Vector2(player.global_position.x - a.x, player.global_position.z - a.z).length() / 2.0
	check("walk moves the player (W)", walk_speed > 3.0 and walk_speed < 5.2, {"avg_speed_mps": snappedf(walk_speed, 0.01)})
	a = player.global_position
	Input.action_press("sprint")
	await hold("move_forward", 2.0)
	Input.action_release("sprint")
	var sprint_speed := Vector2(player.global_position.x - a.x, player.global_position.z - a.z).length() / 2.0
	check("sprint is faster (Shift+W)", sprint_speed > walk_speed * 1.5, {"avg_speed_mps": snappedf(sprint_speed, 0.01)})
	a = player.global_position
	await hold("move_left", 1.0)
	await hold("move_right", 1.0)
	await hold("move_back", 1.0)
	check("strafe and back-pedal (A, D, S)", player.global_position.distance_to(a) > 2.0 and player.is_on_floor(),
		{"moved_m": snappedf(player.global_position.distance_to(a), 0.01)})

	# 3. jump
	await goto_spawn(1)
	var y0 := player.global_position.y
	var ymax := y0
	Input.action_press("jump")
	for k in 70:
		await get_tree().physics_frame
		ymax = maxf(ymax, player.global_position.y)
		if k == 3:
			Input.action_release("jump")
	await frames(30)
	check("jump rises and lands (Space)", ymax - y0 > 0.7 and ymax - y0 < 1.6 and player.is_on_floor(),
		{"apex_m": snappedf(ymax - y0, 0.01)})

	# 4. gravity: drop from 25 m, must land on the floor and not fall through
	var s5: Dictionary = campus.spawns[4]
	player.teleport(s5.position + Vector3(3, 25, 0))
	await frames(240)
	var g2 := ray(player.global_position + Vector3(0, 1, 0), player.global_position + Vector3(0, -50, 0))
	check("gravity: falls 25 m and lands on the ground", player.is_on_floor() and not g2.is_empty()
		and absf(player.feet_position().y - g2.position.y) < 0.15, {"feet_y": snappedf(player.feet_position().y, 0.01)})

	# 5. solid buildings: walk straight at each facade, must stop at the first solid surface
	var wall_tests := [[1, "Administration (front, up the portico steps)"], [2, "Academic Building (courtyard wing beside public route)"],
		[3, "Helmy Institute"], [5, "East research institute"]]
	for wt in wall_tests:
		var s := await goto_spawn(wt[0])
		if wt[0] == 1:   # walk between two portico columns (x = 0 and 4.8 m) up the steps to the glazed front
			player.global_position.x += 2.4
			await frames(20)
		if wt[0] == 2: # V6 open core: face a real side-wing wall from a clear courtyard position.
			# Inner walkway at x=17 clears the planted strip (x=11.3..15.7).
			player.teleport(campus.ground_at(17.,200.)+Vector3(0,player.half_height()+.05,0),Vector3(1,0,0))
			await frames(20)
		var dir: Vector3 = Vector3(s.facing.x, 0, s.facing.z).normalized()
		if wt[0]==2:dir=Vector3(1,0,0)
		var start := player.global_position
		var hit := ray(start + Vector3(0, 0.6, 0), start + Vector3(0, 0.6, 0) + dir * 200.0)
		if hit.is_empty():
			check("wall collision: " + wt[1], false, {"error": "no wall found ahead"})
			continue
		var d := Vector3(hit.position.x - start.x, 0, hit.position.z - start.z).length()
		Input.action_press("sprint")
		await hold("move_forward", d / 9.0 + 3.0)
		Input.action_release("sprint")
		var moved := (player.global_position - start).dot(dir)
		var ok := moved <= d - 0.2 and moved >= d - 2.5
		check("wall collision: " + wt[1], ok, {"wall_distance_m": snappedf(d, 0.01), "moved_m": snappedf(moved, 0.01),
			"stopped_short_by_m": snappedf(d - moved, 0.01), "hit": String(hit.collider.name)})

	# 6. curb: step down from the sidewalk to the road and back up (spawn 1 is on the sidewalk)
	await goto_spawn(0)
	var side_y: float = player.feet_position().y
	var side_x := player.global_position.x
	player.set_view(PI / 2.0)          # face -X (toward the carriageway)
	await walk_until(func(): return player.global_position.x <= side_x - 4.5, 3.0)
	var road_y: float = player.feet_position().y
	player.set_view(-PI / 2.0)         # face +X (back to the sidewalk)
	await walk_until(func(): return player.global_position.x >= side_x - 0.3, 4.0)
	await frames(20)
	var back_y: float = player.feet_position().y
	check("curb: steps down to the road and back up onto the sidewalk", side_y - road_y > 0.08
		and absf(back_y - side_y) < 0.05 and player.global_position.x >= side_x - 0.5,
		{"sidewalk_y": snappedf(side_y, 0.01), "road_y": snappedf(road_y, 0.01), "back_y": snappedf(back_y, 0.01)})

	# 6b. V4 main gate. Walk from the exterior spawn (spawn 7) straight through the west
	# pedestrian gate and across the inner plaza into the campus.
	var sg := await goto_spawn(6)
	var g0 := player.global_position
	player.face_direction(Vector3(0, 0, 1))          # Blender -Y = Godot +Z: into the campus
	await walk_until(func(): return player.global_position.z >= GATE_Z + 16.0, 14.0)
	var g1 := player.global_position
	check("gate: walk from the exterior spawn through the pedestrian gate into the campus",
		g1.z >= GATE_Z + 16.0 and player.is_on_floor(),
		{"spawn": sg.id, "start": r3(g0), "end": r3(g1), "gate_line_z": GATE_Z})
	# the portal frame leg and the closed lane gate are solid
	for blk in [[Vector3(14.3, 0, GATE_Z - 8.0), "gate: portal frame leg is solid"],
			[Vector3(9.45, 0, GATE_Z - 16.0), "gate: closed steel lane gate is solid"]]:
		var bp: Vector3 = blk[0]
		var gnd = campus.ground_at(bp.x, bp.z)
		player.teleport((gnd if gnd != null else bp) + Vector3(0, player.half_height() + 0.05, 0), Vector3(0, 0, 1))
		await frames(20)
		var bstart := player.global_position
		# a fan of five rays at hip height: one ray can slip between the 4 cm gate bars,
		# the player capsule cannot
		var bf: Vector3 = player.feet_position() + Vector3(0, 1.0, 0)
		var bh := {}
		for dx in [-0.08, -0.04, 0.0, 0.04, 0.08]:
			var hh := ray(bf + Vector3(dx, 0, 0), bf + Vector3(dx, 0, 40))
			if not hh.is_empty() and (bh.is_empty() or hh.position.z < bh.position.z):
				bh = hh
		if bh.is_empty():
			check(blk[1], false, {"error": "nothing ahead"})
			continue
		var bd: float = bh.position.z - bstart.z
		await hold("move_forward", bd / 4.0 + 2.0)
		var bmoved := player.global_position.z - bstart.z
		check(blk[1], bmoved <= bd - 0.2 and bmoved >= bd - 2.5,
			{"obstacle_m": snappedf(bd, 0.01), "moved_m": snappedf(bmoved, 0.01), "hit": String(bh.collider.name)})

	# 7. fly mode: ascend, move, collide, no-clip, glide back to walking
	await goto_spawn(1)
	player.set_mode("fly")
	await frames(10)
	var fy := player.global_position.y
	await hold("fly_up", 2.0)
	check("fly: ascend (Space/E)", player.global_position.y - fy > 15.0, {"climb_m": snappedf(player.global_position.y - fy, 0.1)})
	var fp := player.global_position
	await hold("move_forward", 1.5)
	check("fly: move forward", player.global_position.distance_to(fp) > 20.0, {"moved_m": snappedf(player.global_position.distance_to(fp), 0.1)})
	await hold("fly_down", 1.0)
	check("fly: descend (Ctrl/Q)", player.global_position.y < fp.y, {"y": snappedf(player.global_position.y, 0.1)})
	# fly into the admin facade at 6 m with collision on, then with no-clip
	var s2: Dictionary = campus.spawns[1]
	player.teleport(s2.position + Vector3(5, 13, 0), s2.facing)   # aim at the broad upper facade, above the portico
	player.set_mode("fly")
	player.fly_speed = 10.0
	await frames(5)
	var fdir: Vector3 = Vector3(s2.facing.x, 0, s2.facing.z).normalized()
	var fstart := player.global_position
	var fh := ray(fstart, fstart + fdir * 100.0)
	var fd := Vector3(fh.position.x - fstart.x, 0, fh.position.z - fstart.z).length() if not fh.is_empty() else 0.0
	await hold("move_forward", fd / 10.0 + 2.0)
	var fmoved := (player.global_position - fstart).dot(fdir)
	# V10 (final geometry review): require the stop to be AT the facade (capsule radius
	# ~0.36 m) and at altitude, not merely "short of it", so an early unrelated stop or a
	# glide to the ground cannot pass.
	var fstop := fd - fmoved
	check("fly with collision is blocked by the facade", fd > 0 and fstop >= 0.2 and fstop <= 0.6 and absf(player.global_position.y - fstart.y) < 1.5,
		{"wall_m": snappedf(fd, 0.01), "moved_m": snappedf(fmoved, 0.01), "alt_change_m": snappedf(player.global_position.y - fstart.y, 0.01)})
	player.set_noclip(true)
	await hold("move_forward", 3.0)
	fmoved = (player.global_position - fstart).dot(fdir)
	check("fly no-clip passes through (C)", player.noclip and fmoved > fd + 3.0, {"moved_m": snappedf(fmoved, 0.01)})
	player.set_noclip(false)
	main._go_to_spawn(campus.spawns[4].id, "", false)
	await frames(10)
	player.set_mode("fly")
	await hold("fly_up", 2.0)
	player.set_mode("walk")
	await frames(150)
	check("fly -> walk glides down and lands", player.mode == "walk" and player.is_on_floor(), {"feet_y": snappedf(player.feet_position().y, 0.01)})

	# 8. reset (R) returns to the last spawn
	player.teleport(Vector3(300, 5, 300))
	await frames(10)
	await tap("reset_spawn")
	await frames(30)
	var last: Dictionary = campus.spawn_by_id(player.last_spawn_id)
	check("reset (R) returns to the last spawn", Vector2(player.global_position.x - last.position.x, player.global_position.z - last.position.z).length() < 8.0,
		{"spawn": player.last_spawn_id})

	# 9. landmark identification
	await goto_spawn(1)
	var lm: Dictionary = campus.landmark_at(player.global_position)
	check("HUD location at the admin forecourt", lm.get("id", "") == "LM_Administration", {"landmark": lm.get("label", "")})
	await goto_spawn(5)
	lm = campus.landmark_at(player.global_position)
	check("unconfirmed identity is flagged", lm.get("id", "") == "LM_East_Institute" and not lm.verified, {"landmark": lm.get("label", "")})

	# 10. tour paths: clearance against the RENDER geometry (not just collision proxies)
	_build_render_colliders()
	await frames(3)
	var tour_report := {}
	for path_name in main.tour.available():
		main.tour.load_path(path_name)
		var bad: Array = []
		var cuts := 0
		var n: int = main.tour.samples.size()
		var minclear := INF
		for i in n:
			var smp: Array = main.tour.samples[i]
			var p := Vector3(smp[1], smp[2], smp[3])
			if _sphere_hits(p, 0.75):
				bad.append([snappedf(smp[0], 0.01), r3(p)])
			if i > 0:
				var q: Array = main.tour.samples[i - 1]
				var qp := Vector3(q[1], q[2], q[3])
				# V7: a jump > 6 m in one frame (180 m/s) is an editorial hard cut between
				# shots, not camera motion; its endpoints are still sphere-checked above.
				if qp.distance_to(p) > 6.0:
					cuts += 1
				else:
					var h := ray(qp, p, 1 << 7)
					if not h.is_empty():
						bad.append([snappedf(smp[0], 0.01), r3(p), "segment"])
			if i % 15 == 0:
				minclear = minf(minclear, _clearance(p))
		tour_report[path_name] = {"samples": n, "duration_s": main.tour.duration, "clipping_samples": bad.size(), "hard_cuts": cuts,
			"first_clips": bad.slice(0, 5), "min_clearance_m": snappedf(minclear, 0.01)}
		check("tour path clear of geometry: " + path_name, bad.is_empty(), tour_report[path_name])

	# 11. tour playback state machine (start, pause, resume, exit)
	main.start_tour("TOUR_Guided")
	await frames(30)
	var t1: float = main.tour.t
	main.tour.toggle_pause()
	await frames(30)
	var t2: float = main.tour.t
	main.tour.toggle_pause()
	await frames(30)
	var t3: float = main.tour.t
	check("tour plays, pauses (P) and resumes", main.state == "tour" and t1 > 0.0 and is_equal_approx(t1, t2) and t3 > t2,
		{"t": [snappedf(t1, 0.01), snappedf(t2, 0.01), snappedf(t3, 0.01)]})
	var ev := InputEventAction.new()
	ev.action = "pause"
	ev.pressed = true
	Input.parse_input_event(ev)
	await frames(5)
	check("tour exits with Esc", main.state == "explore" and not main.tour.playing, {"state": main.state})

	var fails := results.filter(func(r): return not r["pass"]).size()
	save_json(OUT_VALID + "godot_validation.json", {
		"generated": Time.get_datetime_string_from_system(), "renderer": RenderingServer.get_video_adapter_name(),
		"headless": DisplayServer.get_name() == "headless", "passed": results.size() - fails, "failed": fails,
		"note": "Input is simulated with Input.action_press on the real player script; not a human play test.",
		"results": results, "tours": tour_report, "campus_stats": campus.stats})
	print("[validate] %d passed, %d failed" % [results.size() - fails, fails])


var _render_space_ready := false


func _build_render_colliders() -> void:
	if _render_space_ready:
		return
	var body := StaticBody3D.new()
	body.collision_layer = 1 << 7       # layer 8: validation only
	body.collision_mask = 0
	add_child(body)
	var shapes := {}
	for n in campus.campus_root.find_children("*", "GeometryInstance3D", true, false):
		var mesh: Mesh = null
		var xforms: Array = []
		if n is MeshInstance3D:
			mesh = n.mesh
			xforms = [n.global_transform]
		elif n is MultiMeshInstance3D:
			mesh = n.multimesh.mesh
			for i in n.multimesh.instance_count:
				xforms.append(n.global_transform * n.multimesh.get_instance_transform(i))
		if mesh == null:
			continue
		var key := mesh.get_instance_id()
		if not shapes.has(key):
			shapes[key] = mesh.create_trimesh_shape()
		for xf in xforms:
			var cs := CollisionShape3D.new()
			cs.shape = shapes[key]
			cs.transform = xf
			body.add_child(cs)
	_render_space_ready = true


func _sphere_hits(p: Vector3, r: float) -> bool:
	var q := PhysicsShapeQueryParameters3D.new()
	var sp := SphereShape3D.new()
	sp.radius = r
	q.shape = sp
	q.transform = Transform3D(Basis(), p)
	q.collision_mask = 1 << 7
	return not space().intersect_shape(q, 1).is_empty()


func _clearance(p: Vector3) -> float:
	for r in [1.0, 2.0, 4.0, 8.0, 16.0]:
		if _sphere_hits(p, r):
			return r
	return 32.0


# ------------------------------------------------------------------ capture + performance
func run_capture() -> void:
	# Automated capture: ignore stray keyboard/mouse input reaching the window.
	main.set_process_unhandled_input(false)
	player.set_process_unhandled_input(false)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT_SHOTS))
	var perf := {"adapter": RenderingServer.get_video_adapter_name(), "api": RenderingServer.get_video_adapter_api_version(),
		"resolution": [get_viewport().get_visible_rect().size.x, get_viewport().get_visible_rect().size.y],
		"preset": Settings.preset, "views": {}, "campus_stats": campus.stats}
	# main menu as shown at startup
	main._open_menu(false)
	await _settle(40)
	_shot("ui_main_menu")
	main._start_explore()
	await _view("ground_level_approach", 0, Vector3.ZERO, 0.0, perf)
	await _view("admin_forecourt", 1, Vector3(0, 0, -6), deg_to_rad(10), perf)
	await _view("academic_plaza", 2, Vector3.ZERO, deg_to_rad(6), perf)
	await _view("helmy_institute", 3, Vector3.ZERO, deg_to_rad(8), perf)
	await _view("east_institute", 5, Vector3.ZERO, deg_to_rad(8), perf)
	await _view("academic_inner_courtyard_v6",12,Vector3.ZERO,deg_to_rad(3),perf)
	await _view("dormitory_candidate_v6",13,Vector3.ZERO,deg_to_rad(5),perf)
	await _view_at("academic_left_stair_v6",Vector3(-13,.21,214),Vector3(0,0,1),deg_to_rad(12),perf)
	await _view_at("academic_right_stair_v6",Vector3(13,.21,214),Vector3(0,0,1),deg_to_rad(12),perf)
	await _view_at("academic_central_passage_v6",Vector3(0,.21,237),Vector3(0,0,1),0.,perf)
	await _view_at("academic_terraces_v6",Vector3(46,.21,272),Vector3(-1,0,.2),deg_to_rad(8),perf)
	await _view_at("building_gate_c_hypothesis",Vector3(25,.21,380),Vector3(-.4,0,-1),deg_to_rad(12),perf)
	await _view_at("building_gate_f_hypothesis",Vector3(90,.21,194),Vector3(-1,0,.2),deg_to_rad(14),perf)
	# V7 comparison views: identical transforms are used for the V6 baseline and V7.
	await _view_at("dorm_garden_day_v7",Vector3(425,.21,568),Vector3(-.4,0,1),deg_to_rad(3),perf)
	await _view_at("dorm_facade_ground_v7",Vector3(398,.21,592),Vector3(-.55,0,.83),deg_to_rad(14),perf)
	await _view_at("road_external_asphalt_v7",Vector3(-40,.2,-362),Vector3(1,0,0),deg_to_rad(-4),perf)
	await _view_at("road_internal_ring_v7",Vector3(290,.2,152),Vector3(-.28,0,-.96),deg_to_rad(-3),perf)
	await _view_at("academic_court_eye_v7",Vector3(18,.21,262),Vector3(.55,0,.83),deg_to_rad(6),perf)
	await _view_at("academic_court_day_compare_v7",Vector3(46,.21,272),Vector3(-1,0,.2),deg_to_rad(8),perf)
	for gate in campus.manifest.get("gates",[]).slice(1):
		var a: float = gate.parameters_v8.orientation
		var inward := Vector2(gate.inward[0],-gate.inward[1])
		var v := Vector2(-sin(a),-cos(a))
		if v.dot(inward)<0: v=-v
		var u := Vector2(cos(a),-sin(a))
		var p := Vector2(gate.model_position_blender_m[0],-gate.model_position_blender_m[1])
		var q := p-v*17.+u*9.
		await _view_at("v8_gate_"+gate.id,Vector3(q.x,0,q.y),Vector3(p.x-q.x,0,p.y-q.y),deg_to_rad(5),perf)
	main._set_evening(true)
	await _view_at("dorm_garden_evening_v6",Vector3(425,.21,568),Vector3(-.4,0,1),deg_to_rad(3),perf)
	await _view_at("academic_court_evening_v7",Vector3(46,.21,272),Vector3(-1,0,.2),deg_to_rad(8),perf)
	await _view_at("main_gate_inside_evening_v7",Vector3(-16.3,0.2,GATE_Z+40.0),Vector3(0.25,0,-1),deg_to_rad(10),perf)
	main._set_evening(false)
	# V4: main gate from the exterior spawn, from inside, and the pedestrian route
	await _view("main_gate_exterior", 6, Vector3.ZERO, deg_to_rad(12), perf)
	await _view_at("main_gate_landmark", Vector3(-30, 0.2, GATE_Z - 46.0), Vector3(0.6, 0, 1), deg_to_rad(14), perf)
	await _view_at("main_gate_inside", Vector3(-16.3, 0.2, GATE_Z + 40.0), Vector3(0.25, 0, -1), deg_to_rad(10), perf)
	await _view_at("pedestrian_route_walkway", Vector3(-16.3, 0.2, -230.0), Vector3(0, 0, 1), deg_to_rad(3), perf)
	await _view_at("academic_gate_a_court", Vector3(0, 0.2, 152.0), Vector3(0, 0, 1), deg_to_rad(9), perf)
	# close-range: standing beside the portico
	await _view_at("admin_close_range", Vector3(9, 0.2, -31.5), Vector3(-0.35, 0, 1), deg_to_rad(22), perf)
	# drone view
	player.set_mode("fly")
	player.teleport(Vector3(-260, 150, -330))
	player.set_mode("fly")
	player.face_direction(Vector3(260, 0, 350))
	player.set_view(player.yaw, deg_to_rad(-22))
	await _settle(60)
	_shot("drone_aerial")
	perf.views["drone_aerial"] = await _measure(180)
	player.set_mode("walk")
	await _settle(120)
	# guided tour camera at several moments, then measure a whole minute of tour playback
	for tt in [6.0, 14.0, 18.0, 30.0, 42.0, 50.0, 62.0, 70.0, 80.0, 94.0]:
		main.start_tour("TOUR_Guided")
		main.tour.t = tt
		main.tour.paused = true
		main.tour._apply(tt)
		await _settle(45)
		_shot("tour_t%03d" % int(tt))
	main.tour.paused = false
	main.tour.t = 0.0
	perf.views["guided_tour_first_60s"] = await _measure(0, 60.0)
	main.start_tour("CIN_V6_Photo_Walkthrough")
	await _settle(60)
	perf.views["v6_stair_walkthrough_10s"] = await _measure(0,10.0)
	main.tour.stop(false)
	main._start_explore()
	main._go_to_spawn(campus.spawns[1].id, "", false)
	await _settle(60)
	_shot("hud_explore")
	for p in ["Low", "Medium", "High"]:
		Settings.set_preset(p)
		await _settle(60)
		perf.views["admin_forecourt_" + p] = await _measure(240)
	Settings.set_preset("High")
	perf["vsync"] = "disabled (uncapped)" if "--uncapped" in OS.get_cmdline_user_args() else "enabled (display cap)"
	save_json(OUT_VALID + "godot_performance.json", perf)


func _settle(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _shot(name: String) -> void:
	var img := get_viewport().get_texture().get_image()
	var path := ProjectSettings.globalize_path(OUT_SHOTS + name + ".png")
	img.save_png(path)
	print("[capture] " + path)


func _measure(n: int, duration_seconds := 0.0) -> Dictionary:
	var times: Array = []
	var draws := 0.0
	var prims := 0.0
	var last := Time.get_ticks_usec()
	var started := last
	while times.size() < n or (duration_seconds > 0.0 and (Time.get_ticks_usec() - started) / 1000000.0 < duration_seconds):
		await get_tree().process_frame
		var now := Time.get_ticks_usec()
		times.append((now - last) / 1000.0)
		last = now
		draws += Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
		prims += Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
	times.sort()
	var avg: float = times.reduce(func(a, b): return a + b, 0.0) / times.size()
	return {"frames": times.size(), "preset":Settings.preset, "lighting":"Evening" if main.evening_mode else "Day", "duration_s": snappedf((Time.get_ticks_usec()-started)/1000000.0,0.001), "avg_ms": snappedf(avg, 0.01), "avg_fps": snappedf(1000.0 / avg, 0.1),
		"p95_ms": snappedf(times[int(times.size() * 0.95)], 0.01), "p99_ms": snappedf(times[int(times.size() * 0.99)], 0.01),
		"max_ms": snappedf(times[-1], 0.01), "avg_draw_calls": int(draws / times.size()), "avg_primitives": int(prims / times.size()),
		"vram_mb": snappedf(Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0, 0.1)}


func _view(name: String, spawn_i: int, offset: Vector3, pitch: float, perf: Dictionary) -> void:
	main._go_to_spawn(campus.spawns[spawn_i].id, "", false)
	player.global_position += offset
	player.set_view(player.yaw, pitch)
	await _settle(60)
	_shot(name)
	perf.views[name] = await _measure(240)


func _view_at(name: String, pos: Vector3, facing: Vector3, pitch: float, perf: Dictionary) -> void:
	var g = campus.ground_at(pos.x, pos.z)
	player.teleport((g if g != null else pos) + Vector3(0, player.half_height() + 0.05, 0), facing)
	player.set_view(player.yaw, pitch)
	await _settle(60)
	_shot(name)
	perf.views[name] = await _measure(240)
