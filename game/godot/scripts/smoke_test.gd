extends Node
## Release smoke test, used only with `-- --smoketest` (V4). It runs inside the exported
## executable, where the tests/ folder is not shipped, and drives the real input actions
## (Input.action_press), the same path the keyboard uses. This is automated input, NOT a
## human play test.
##
##   ZewailCityExplorer.exe -- --smoketest
##
## Prints one JSON line prefixed "[smoketest]", writes user://smoketest.json and quits
## with exit code 0 (all passed) or 1.

var main: Node3D
var results: Array = []
## V13: controlled input. V12.1 runs showed real OS mouse/keyboard input reaching the
## smoke window (heading drift, unrequested spawn jumps) for a known-good build too.
## The window is made non-focusable and every real (non-synthetic) event is consumed;
## counts and focus state are reported so a run documents its own input conditions.
var real_events_blocked := 0
var real_event_kinds := {}
var focused_frames := 0


func _input(event: InputEvent) -> void:
	if event is InputEventAction:
		return
	real_events_blocked += 1
	var k := event.get_class()
	real_event_kinds[k] = int(real_event_kinds.get(k, 0)) + 1
	get_viewport().set_input_as_handled()


func _process(_d: float) -> void:
	if DisplayServer.window_is_focused():
		focused_frames += 1


func _ready() -> void:
	process_priority = -1000
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_NO_FOCUS, true)
	main = get_parent()
	while not main.ready_done:
		await get_tree().process_frame
	await _run()


func _frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func _hold(action: String, seconds: float) -> void:
	Input.action_press(action)
	await _frames(int(seconds * 60.0))
	Input.action_release(action)
	await _frames(2)


func _tap(action: String) -> void:
	for pressed in [true, false]:
		var ev := InputEventAction.new()
		ev.action = action
		ev.pressed = pressed
		Input.parse_input_event(ev)
		await _frames(2)


func _check(name: String, ok: bool, detail := {}) -> void:
	results.append({"name": name, "pass": ok, "detail": detail})
	print("[smoketest] %s  %s  %s" % ["PASS" if ok else "FAIL", name, JSON.stringify(detail)])


func _run() -> void:
	var player: CharacterBody3D = main.player
	var campus: Node3D = main.campus
	_check("campus loaded", campus.stats.static_bodies >= 7 and campus.spawns.size() >= 7, campus.stats)
	_check("main menu shown at startup", main.state == "menu" and main.menu.visible, {"state": main.state})
	_check("Arabic RTL packaged menu", L10n.language == "ar" and main.menu.root.layout_direction == Control.LAYOUT_DIRECTION_RTL)
	await get_tree().process_frame
	await get_tree().process_frame
	if DisplayServer.get_name() != "headless":
		get_viewport().get_texture().get_image().save_png("user://smoketest_arabic_menu.png")
	main._start_explore()
	await _frames(10)
	_check("start exploration from the menu", main.state == "explore", {"state": main.state})
	# walk and sprint on the approach walkway (spawn 5)
	main._go_to_spawn(campus.spawns[4].id, "", false)
	await _frames(40)
	var a: Vector3 = player.global_position
	await _hold("move_forward", 2.0)
	var walk := Vector2(player.global_position.x - a.x, player.global_position.z - a.z).length() / 2.0
	_check("walk (W)", walk > 3.0 and walk < 5.2 and player.is_on_floor(), {"speed_mps": snappedf(walk, 0.01)})
	a = player.global_position
	Input.action_press("sprint")
	await _hold("move_forward", 1.5)
	Input.action_release("sprint")
	var sprint := Vector2(player.global_position.x - a.x, player.global_position.z - a.z).length() / 1.5
	_check("sprint (Shift+W)", sprint > walk * 1.5, {"speed_mps": snappedf(sprint, 0.01)})
	# drone mode
	await _tap("toggle_fly")
	_check("toggle drone mode (F)", player.mode == "fly", {"mode": player.mode})
	var y0: float = player.global_position.y
	await _hold("fly_up", 1.5)
	_check("fly up (Space/E)", player.global_position.y - y0 > 8.0, {"climb_m": snappedf(player.global_position.y - y0, 0.1)})
	await _tap("toggle_fly")
	await _frames(240)
	_check("back to walking, lands", player.mode == "walk" and player.is_on_floor(), {"mode": player.mode})
	# new V4 spawn outside the main gate (key 7), then walk through the pedestrian gate
	await _tap("spawn_7")
	await _frames(30)
	var g0: Vector3 = player.global_position
	# a frame from the running build itself, at the gate (rendering check of the shipped assets)
	await get_tree().process_frame
	await get_tree().process_frame
	if DisplayServer.get_name() != "headless":
		get_viewport().get_texture().get_image().save_png("user://smoketest_gate.png")
	_check("spawn 7 (outside the main gate) is grounded", player.is_on_floor() and player.last_spawn_id == "SPAWN_07_Main_Gate_Exterior",
		{"pos": [snappedf(g0.x, 0.1), snappedf(g0.y, 0.1), snappedf(g0.z, 0.1)]})
	player.face_direction(Vector3(0, 0, 1))
	Input.action_press("move_forward")
	var n := 0
	while player.global_position.z < -298.6 and n < 14 * 60:
		await get_tree().physics_frame
		n += 1
	Input.action_release("move_forward")
	_check("walk through the pedestrian gate into the campus", player.global_position.z >= -298.6,
		{"z": snappedf(player.global_position.z, 0.1)})
	# pause menu (Esc) and resume
	await _tap("pause")
	_check("pause menu (Esc)", main.state == "menu", {"state": main.state})
	await _tap("pause")
	_check("resume from the pause menu (Esc)", main.state == "explore", {"state": main.state})
	# V5 content and public circulation must also work in the packaged executable.
	_check("V15 content shipped",campus.spawns.size()==14 and campus.manifest.get("gates",[]).size()==6 and str(ProjectSettings.get_setting("application/config/version"))=="15.0.0" and str(campus.manifest.get("reconstruction_version",""))=="15.0.0" and int(campus.stats.get("v9_masked_ground_surfaces",0))>0)
	var pbr_ok := FileAccess.file_exists("res://assets/pbr/manifest.json")
	for asset in ["asphalt_01","concrete_pavement_03","sand_01","sparse_grass","beige_wall_001"]:
		for kind in ["diff","nor_gl","rough"]:
			pbr_ok = pbr_ok and ResourceLoader.exists("res://assets/pbr/%s/%s_%s_%s.jpg" % [asset,asset,kind,"2k" if asset=="paving_stones_125a" else "1k"])
	pbr_ok = pbr_ok and ResourceLoader.exists("res://assets/pbr/sky/kloofendal_48d_partly_cloudy_puresky_sunclamped_2k.hdr")
	pbr_ok = pbr_ok and FileAccess.file_exists("res://assets/pbr/tone_targets.json")
	_check("All 15 V14 PBR textures, HDRI sky, tone targets and license manifest packaged",pbr_ok)
	# V8: packaged geometry must permit each LOCAL gate crossing. This deliberately
	# does not test or imply connection to any external public road.
	for gate in campus.manifest.get("gates",[]).slice(1):
		var params: Dictionary = gate.get("parameters_v8",{})
		var angle: float = params.get("orientation",0.)
		var inward := Vector2(gate.inward[0],-gate.inward[1])
		var normal := Vector2(-sin(angle),-cos(angle))
		if normal.dot(inward)<0: normal=-normal
		var center := Vector2(gate.model_position_blender_m[0],-gate.model_position_blender_m[1])
		var start := center-normal*4.
		var floor = campus.ground_at(start.x,start.y)
		if floor!=null:
			player.set_mode("walk")
			player.teleport(floor+Vector3(0,player.half_height()+.05,0),Vector3(normal.x,0,normal.y))
			await _frames(20)
			await _hold("move_forward",2.4)
		var progress := (Vector2(player.position.x,player.position.z)-center).dot(normal)
		_check("V8 packaged local threshold "+gate.id,floor!=null and player.is_on_floor() and progress>2. and gate.status=="PROVISIONAL_MAP_CLUSTER" and not params.is_empty(),{"progress_m":progress,"external_access":gate.get("external_access","")})
	var ground=campus.ground_at(0.,205.)
	player.teleport(ground+Vector3(0,player.half_height()+.05,0),Vector3(0,0,1))
	await _frames(30)
	Input.action_press("sprint")
	await _hold("move_forward",10.)
	Input.action_release("sprint")
	_check("V6 Academic passage to courtyard in Windows build",player.is_on_floor() and player.position.z>280 and player.position.z<315,{"position":[player.position.x,player.position.y,player.position.z]})
	main._go_to_spawn("SPAWN_13_Academic_Courtyard","",false)
	await _frames(45)
	_check("V6 courtyard spawn grounded",player.is_on_floor())
	player.face_direction(Vector3(1,0,-.3))
	await get_tree().process_frame
	if DisplayServer.get_name()!="headless":
		get_viewport().get_texture().get_image().save_png("user://smoketest_v6_courtyard.png")
	main._go_to_spawn("SPAWN_14_Dormitory_Candidate","",false)
	await _frames(45)
	_check("V6 dormitory candidate spawn grounded",player.is_on_floor())
	await get_tree().process_frame
	if DisplayServer.get_name()!="headless":
		get_viewport().get_texture().get_image().save_png("user://smoketest_v6_dormitory.png")
	for x in [-13.,13.]:
		var start = campus.ground_at(x,214.)
		player.teleport(start+Vector3(0,player.half_height()+.05,0),Vector3(0,0,1))
		await _frames(30)
		Input.action_press("move_forward")
		var step_frames := 0
		while player.position.z<229.8 and step_frames<12*60:
			await get_tree().physics_frame
			step_frames+=1
		Input.action_release("move_forward")
		await _frames(3)
		_check("V6 packaged major stair "+str(x),player.is_on_floor() and absf(player.feet_position().y-4.41)<.15,{"position":[player.position.x,player.position.y,player.position.z]})
	# V10: the Administration entrance is a real doorway into a bounded lobby (A02).
	var adm = campus.ground_at(0.,-38.)
	player.teleport(adm+Vector3(0,player.half_height()+.05,0),Vector3(0,0,1))
	await _frames(30)
	Input.action_press("move_forward")
	var adm_frames := 0
	while player.position.z<-15. and adm_frames<10*60:
		await get_tree().physics_frame
		adm_frames+=1
	Input.action_release("move_forward")
	await _frames(3)
	_check("V10 packaged Administration doorway to lobby",player.is_on_floor() and player.position.z>-18.9 and player.position.z<-9.5 and absf(player.feet_position().y-.72)<.1,{"position":[player.position.x,player.position.y,player.position.z]})
	main._set_evening(true)
	var bollards: int = campus.manifest.get("evening_lights",[]).filter(func(l): return String(l.get("kind",""))=="bollard").size()
	_check("V7 packaged evening lights (all modelled luminaires, 32 garden bollards)",main.evening_mode and main.garden_lights.visible and main.garden_lights.get_child_count()==campus.manifest.get("evening_lights",[]).size() and bollards==32,{"lights":main.garden_lights.get_child_count(),"bollards":bollards})
	main._set_evening(false)
	_check("V6 packaged daylight restore",not main.evening_mode and not main.garden_lights.visible)
	_check("V11 Academic entrance registry separate from boundary gates",campus.manifest.get("academic_entrances_v11",{}).get("entrances",[]).size()>=6 and campus.manifest.gates.size()==6 and campus.manifest.get("gate_leaves",[]).size()==19)
	# Fresh packaged G3 operation through E, then real movement on both gate states.
	var gate = campus.manifest.gates[2]
	var center := Vector2(gate.model_position_blender_m[0], -gate.model_position_blender_m[1])
	var tangent := Vector2(cos(gate.wall_angle_radians), -sin(gate.wall_angle_radians))
	var normal := Vector2(-tangent.y,tangent.x)
	if normal.dot(Vector2(gate.inward[0],-gate.inward[1])) < 0:
		normal = -normal
	var start := center + normal * 3.0
	var floor = campus.ground_at(start.x,start.y)
	player.teleport(floor + Vector3(0,player.half_height()+.05,0),Vector3(-normal.x,0,-normal.y))
	campus.gate_controller.set_gate("G3",true,true)
	await _frames(30)
	await _tap("interact")
	await _frames(170)
	_check("V11 packaged E closes G3 including pedestrian leaf",not campus.gate_controller.is_open("G3"))
	await _hold("move_forward",2.0)
	var distance := (Vector2(player.position.x,player.position.z)-center).dot(normal)+1.2
	_check("V11 packaged closed G3 stops walking",distance>.05 and player.is_on_floor(),{"signed_distance_to_leaf_m":distance})
	await _tap("interact")
	await _frames(170)
	await _hold("move_forward",2.0)
	distance = (Vector2(player.position.x,player.position.z)-center).dot(normal)+1.2
	_check("V11 packaged E opens G3 and walking passage",campus.gate_controller.is_open("G3") and distance < -1.0,{"signed_distance_to_leaf_m":distance})
	# V7 photo mode: enter, move freely, capture at 2x, return to the exact prior state.
	main._go_to_spawn(campus.spawns[1].id,"",false)
	await _frames(30)
	var before: Vector3 = player.global_position
	await _tap("photo_mode")
	_check("V7 photo mode entered (free camera, HUD hidden)",main.state=="photo" and player.mode=="fly" and player.noclip and not main.hud.visible)
	await _hold("move_forward",1.0)
	_check("V7 photo mode camera moves",player.global_position.distance_to(before)>2.0,{"moved_m":snappedf(player.global_position.distance_to(before),0.01)})
	await _tap("photo_lighting")
	_check("V7 photo mode evening preset",main.evening_mode)
	var shot: String = await main.capture_highres(2)
	var img := Image.load_from_file(ProjectSettings.globalize_path(shot))
	_check("V7 photo mode 2x capture",img!=null and img.get_width()>=2*int(main.get_viewport().get_visible_rect().size.x),{"path":ProjectSettings.globalize_path(shot),"size":[img.get_width() if img else 0,img.get_height() if img else 0]})
	await _tap("photo_mode")
	await _frames(10)
	_check("V7 photo mode returns to exact prior state",main.state=="explore" and player.mode=="walk" and not main.evening_mode and main.hud.visible and player.global_position.distance_to(before)<.05,{"offset_m":snappedf(player.global_position.distance_to(before),0.001)})
	# A real 5-second rendered sample from this exported executable. Keep all
	# other GPU jobs stopped when running the packaged verification script.
	await _frames(60)
	var frame_times: Array[float] = []
	var begun := Time.get_ticks_usec()
	var previous := begun
	while Time.get_ticks_usec()-begun<5000000:
		await get_tree().process_frame
		var now := Time.get_ticks_usec()
		frame_times.append((now-previous)/1000.)
		previous=now
	frame_times.sort()
	var elapsed: float = (previous-begun)/1000000.
	var fps: float = frame_times.size()/elapsed
	_check("Exported 1080p High sample at least 60 FPS",fps>=60 and int(main.get_viewport().get_visible_rect().size.x)==1920 and int(main.get_viewport().get_visible_rect().size.y)==1080,
		{"duration_s":elapsed,"frames":frame_times.size(),"avg_fps":fps,"p99_ms":frame_times[int(frame_times.size()*.99)],"max_ms":frame_times[-1]})
	var ok := results.all(func(r): return r.pass)
	var rep := {"passed": results.filter(func(r): return r.pass).size(), "failed": results.filter(func(r): return not r.pass).size(),
		"results": results, "adapter": RenderingServer.get_video_adapter_name(),
		"input_control": {"window_no_focus_flag": DisplayServer.window_get_flag(DisplayServer.WINDOW_FLAG_NO_FOCUS), "real_events_blocked": real_events_blocked, "real_event_kinds": real_event_kinds, "frames_with_os_focus": focused_frames},
		"version": ProjectSettings.get_setting("application/config/version"),"source_blend_sha256":campus.manifest.get("source_blend_sha256",""),
		"packaged_manifest_glb_sha256":campus.manifest.get("game_glb_sha256","")}
	var fh := FileAccess.open("user://smoketest.json", FileAccess.WRITE)
	if fh:
		fh.store_string(JSON.stringify(rep, "  "))
	print("[smoketest] SUMMARY " + JSON.stringify({"passed": rep.passed, "failed": rep.failed,
		"report": ProjectSettings.globalize_path("user://smoketest.json")}))
	get_tree().quit(0 if ok else 1)
