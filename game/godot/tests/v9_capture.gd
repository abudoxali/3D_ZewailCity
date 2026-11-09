extends Node
## Matched eye-height captures (V9: V8/V9 gate; V10: V9/V10 gate + new evidence views).
##
##   godot --path game/godot --resolution 1920x1080 res://tests/V9Capture.tscn -- --tag=v8 --preset=high
##
## The first run resolves each view to an exact camera transform (eye 1.70 m above
## the floor that existed at that run) and stores it in
## output/validation/v11/game_view_poses.json. Every later run reuses those stored
## transforms unchanged, so V8 and V9 images share camera, FOV, resolution, preset,
## time of day and HUD state (hidden). Real rendering, no post-processing.

var OUT := "res://../../output/validation/v11/"
const EYE := 1.70
const VIEWS := [
	["V12_landing_detail",[0.,0.],[0.,0.,1.],false],
	["V12_stair_detail",[0.,0.],[0.,0.,1.],false],
	["V12_masterplan_top",[0.,0.],[0.,0.,1.],false],
	["V12_tree_prototype",[0.,0.],[0.,0.,1.],false],
	["V12_G1_close",[0.,0.],[0.,0.,1.],false],
	["V12_approach_close",[0.,0.],[0.,0.,1.],false],
	["V12_court_close",[0.,0.],[0.,0.,1.],false],
	["V12_dorm_close",[0.,0.],[0.,0.,1.],false],
	["V12_shrub_prototype",[0.,0.],[0.,0.,1.],false],
	["V12_admin_covered",[0.,0.],[0.,0.,1.],false],
	["V12_junction_dropoff_eye",[0.,0.],[0.,0.,1.],false],
	["V12_junction_ring_east_eye",[0.,0.],[0.,0.,1.],false],
	["V12_ring_junction_eye",[0.,0.],[0.,0.,1.],false],
	["V12_G2_junction_eye",[0.,0.],[0.,0.,1.],false],
	["V12_admin_frontage_eye",[0.,0.],[0.,0.,1.],false],
	["V13_sky_sun_azimuth",[0.,0.],[0.,0.,1.],false],
	["V13_approach_aerial",[0.,0.],[0.,0.,1.],false],
	["V14_g1_median_nose",[0.,0.],[0.,0.,1.],false],
	["V14_g1_gate_sand",[0.,0.],[0.,0.,1.],false],
	["V14_g1_forecourt_beds",[0.,0.],[0.,0.,1.],false],
	["V14_junction_admin_close",[0.,0.],[0.,0.,1.],false],
	["V14_ring_sidewalk_step",[0.,0.],[0.,0.,1.],false],

	["PBR_detail",[0.0,0.0],[0.0,0.0,1.0],false],
	# name, [x, z] Godot floor point, look target [x, y_above_floor, z], evening?
	["G1_exterior_eye", [-14.0, -346.0], [0.0, 3.0, -314.6], false],
	["G1_pedestrian_approach", [-21.0, -288.0], [-17.0, 0.6, -312.0], false],
	["main_approach_road", [-12.5, -268.0], [-12.5, 0.0, -150.0], false],
	["ring_road_eye", [290.0, 152.0], [262.0, 0.6, 56.0], false],
	["academic_stair_left", [-13.0, 205.0], [-13.0, 3.5, 222.0], false],
	["academic_court_paving", [18.0, 258.0], [30.0, -0.8, 276.0], false],
	["admin_ramp_landing", [17.5, -54.0], [11.0, 0.4, -36.0], false],
	["dorm_garden_paths", [425.0, 568.0], [419.0, -0.6, 583.0], false],
	["desert_soil_rear", [20.0, 377.0], [0.0, 0.0, 348.0], false],
	["soil_road_edge_west", [-180.0, -60.0], [-150.0, -0.4, -40.0], false],
	["planted_soil_grove", [-62.0, -205.0], [-40.0, -0.3, -175.0], false],
	["external_asphalt", [-40.0, 362.0], [20.0, -0.6, 364.0], false],
	["wall_inside_soil", [-300.0, 40.0], [-330.0, 0.6, 10.0], false],
	["G2_inside", [14.1, 620.1], [6.4, 1.4, 638.7], false],
	["G2_outside", [13.7, 658.2], [6.4, 1.4, 638.7], false],
	["G3_inside", [-261.5, -110.4], [-270.9, 1.4, -132.5], false],
	["G3_outside", [-284.5, -141.5], [-270.9, 1.4, -132.5], false],
	["G4_inside", [-324.7, 245.0], [-342.3, 1.4, 238.0], false],
	["G4_outside", [-362.6, 246.0], [-342.3, 1.4, 238.0], false],
	["G5_inside", [221.4, -68.3], [237.8, 1.4, -76.2], false],
	["G5_outside", [245.9, -97.2], [237.8, 1.4, -76.2], false],
	["G6_inside", [328.5, 227.9], [346.6, 1.4, 236.8], false],
	["G6_outside", [366.5, 230.7], [346.6, 1.4, 236.8], false],
	["drone_overview", [-260.0, -330.0], [40.0, 0.0, 20.0], false, 150.0],
	["G1_inside_evening", [-16.3, -274.6], [-13.0, 1.5, -314.6], true],
	["dorm_garden_evening", [425.0, 568.0], [419.0, -0.6, 583.0], true],
	# V10 evidence views: absolute stored poses only (tools/v10_add_capture_poses.py);
	# the floor point / target here are unused placeholders.
	["P09_forecourt_photo", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["P13_court_photo", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["P15_bridge_photo", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["P16_dorm_photo", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["P12_rear_gateC_photo", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["academic_court_aerial", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["admin_entrance_axis", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["admin_lobby_threshold", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["academic_arcade", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["academic_stair_right", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["academic_central_passage", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["junction_dropoff_ring", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["junction_ring_east", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["academic_court_topdown", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["academic_court_palm_bed", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	# V11 owner-screenshot views: absolute stored poses (tools/v11_add_capture_poses.py).
	["O00_admin_roof_forecourt", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["O02_G1_inside", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["O03_G1_paving_curb", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["O04_G1_wall_side", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["O05_approach_walk", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["O06_G2_portal", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["O07_academic_front", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["O08_terrace_overlook", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["O09_rear_passage", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["O10_gate_c", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["O11_academic_aerial", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["O12_dorm_entry", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["O13_ust_corner", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["O14_stairs_forecourt", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["O15_junction_eye", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["O16_dome_axis_forecourt", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["O16_dome_axis_terrace", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["O12_east_institute_interface", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["O12_helmy_interface", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["O15_ring_junction_candidate", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	# V15 pilot inspection poses (tools/v15_add_poses.py), absolute stored poses only.
	["V15_crossover_bands_eye", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["V15_median_eye", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["V15_verge_bed_close", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["V15_kerb_close", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["V15_ring_junction_kerbs", [0.0, 0.0], [0.0, 0.0, 1.0], false],
	["V15_g1_inside_kerbs", [0.0, 0.0], [0.0, 0.0, 1.0], false],
]

var main: Node3D
var campus: Node3D
var cam: Camera3D
var tag := "v8"
var perf := {}
var only: PackedStringArray = []


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--tag="):
			tag = a.get_slice("=", 1)
		elif a.begins_with("--only="):
			only = a.get_slice("=", 1).split(",")
		elif a.begins_with("--out="):
			OUT = a.get_slice("=", 1).trim_suffix("/") + "/"
	# Uncapped: no vsync / FPS cap, so GPU cost (not the display rate) is measured.
	if "--uncapped" in OS.get_cmdline_user_args():
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
		Engine.max_fps = 0
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT + "game_captures"))
	main = load("res://v11/scenes/Main.tscn" if "--v12-baseline" in OS.get_cmdline_user_args() else "res://scenes/Main.tscn").instantiate()
	add_child(main)
	while not main.ready_done:
		await get_tree().process_frame
	# Windows may shrink a decorated 1080p window while the logical canvas still
	# reports 1920x1080. Render at a fixed real viewport size and verify its pixels.
	var window := get_tree().root
	window.content_scale_size = Vector2i(1920,1080)
	window.content_scale_mode = Window.CONTENT_SCALE_MODE_VIEWPORT
	window.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_KEEP
	# V11 Settings.apply_display runs during Main startup and can restore VSync.
	# Enforce benchmark timing AFTER it, and record the actual native state.
	if "--uncapped" in OS.get_cmdline_user_args():
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
		Engine.max_fps = 0
	campus = main.campus
	main.set_process_unhandled_input(false)
	main.player.set_process_unhandled_input(false)
	main._start_explore()
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--gate-state="):
			for gate in campus.manifest.gates:
				campus.gate_controller.set_gate(gate.id, arg.get_slice("=",1) == "open", true)
	for c in main.find_children("*", "CanvasLayer", true, false):
		(c as CanvasLayer).visible = false
	cam = Camera3D.new()
	cam.near = 0.08
	cam.far = 6000.0
	cam.fov = Settings.fov
	add_child(cam)
	cam.make_current()
	var poses: Dictionary = await _poses()
	perf = {"tag": tag, "vsync": "disabled (uncapped)" if "--uncapped" in OS.get_cmdline_user_args() else "enabled (display cap)", "adapter": RenderingServer.get_video_adapter_name(), "preset": Settings.preset,
		"resolution": [get_viewport().get_visible_rect().size.x, get_viewport().get_visible_rect().size.y],
		"fov": cam.fov, "views": {}, "manifest": campus.manifest, "loading": campus.stats,
		"capture_started_unix": Time.get_unix_time_from_system(),
		"actual_vsync_mode":DisplayServer.window_get_vsync_mode(), "actual_max_fps":Engine.max_fps}
	for v in VIEWS:
		var name: String = v[0]
		var p: Dictionary = poses["external_asphalt"] if name == "PBR_detail" else poses[name]
		if only.size() and not only.has(name):
			continue
		if bool(v[3]) != main.evening_mode:
			main._set_evening(bool(v[3]))
		cam.make_current()
		for c in main.find_children("*", "CanvasLayer", true, false):
			(c as CanvasLayer).visible = false
		cam.global_transform = Transform3D(Basis(Quaternion(p.q[0], p.q[1], p.q[2], p.q[3])), Vector3(p.o[0], p.o[1], p.o[2]))
		await _settle(90)
		var img := get_viewport().get_texture().get_image()
		if img.get_size() != Vector2i(1920,1080):
			push_error("Actual capture pixels are not 1920x1080: " + str(img.get_size()))
			get_tree().quit(3)
			return
		perf["actual_render_resolution"] = [img.get_width(),img.get_height()]
		var path := ProjectSettings.globalize_path(OUT + "game_captures/" + tag + "_" + name + ".png")
		if not "--skip-images" in OS.get_cmdline_user_args():
			img.save_png(path)
		perf.views[name] = await _measure(180)
		perf.views[name]["pose"] = p
		print("[v9-capture] ", path)
	main._set_evening(false)
	var f := FileAccess.open(OUT + "game_capture_perf_" + tag + ".json", FileAccess.WRITE)
	f.store_string(JSON.stringify(perf, "  "))
	f.close()
	get_tree().quit(0)


func _poses() -> Dictionary:
	var path := OUT + "game_view_poses.json"
	# Codex review (V11): the V10/V11 evidence views have placeholder floor points and are
	# only meaningful with stored absolute poses; never resolve them silently.
	if not FileAccess.file_exists(path):
		push_error("stored poses required: " + path + " (run tools/v11_add_capture_poses.py)")
		get_tree().quit(2)
		return {}
	if FileAccess.file_exists(path):
		var d = JSON.parse_string(FileAccess.get_file_as_string(path))
		if d is Dictionary:
			# Stored poses are never recomputed (V9 fix: a size check that counted
			# "__source" once overwrote them). Missing views are a hard error.
			for v in VIEWS:
				if v[0] != "PBR_detail" and not d.has(v[0]):
					push_error("stored pose missing: " + str(v[0]))
					get_tree().quit(2)
			print("[v9-capture] reusing stored poses from ", d.get("__source", "?"))
			return d
	var out := {}
	await _settle(30)
	for v in VIEWS:
		var xz: Array = v[1]
		var g = campus.ground_at(xz[0], xz[1], 12.0)
		var floor_y: float = g.y if g != null else 0.0
		var eye_h: float = v[4] if v.size() > 4 else EYE
		var eye := Vector3(xz[0], floor_y + eye_h, xz[1])
		var tgt: Array = v[2]
		var t := Transform3D(Basis(), eye).looking_at(Vector3(tgt[0], floor_y + tgt[1], tgt[2]), Vector3.UP)
		var q := t.basis.get_rotation_quaternion()
		out[v[0]] = {"o": [eye.x, eye.y, eye.z], "q": [q.x, q.y, q.z, q.w], "floor_y_at_resolve": floor_y,
			"floor_hit": g != null}
	var s := out.duplicate()
	s["__source"] = tag
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(s, "  "))
	f.close()
	return out


func _settle(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _measure(n: int) -> Dictionary:
	var times: Array = []
	var last := Time.get_ticks_usec()
	for i in n:
		await get_tree().process_frame
		var now := Time.get_ticks_usec()
		times.append((now - last) / 1000.0)
		last = now
	times.sort()
	var avg: float = times.reduce(func(a, b): return a + b, 0.0) / times.size()
	return {"frames": n, "avg_ms": snappedf(avg, 0.01), "avg_fps": snappedf(1000.0 / avg, 0.1),
		"p50_ms": snappedf(times[int(times.size() * 0.50)], 0.01),
		"p95_ms": snappedf(times[int(times.size() * 0.95)], 0.01),
		"p99_ms": snappedf(times[int(times.size() * 0.99)], 0.01),
		"rendered_primitives": Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
		"draws": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
		"texture_memory_bytes": Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED)}
