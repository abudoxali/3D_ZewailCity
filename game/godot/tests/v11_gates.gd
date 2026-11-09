extends "res://tests/v5_ground.gd"

## V11 gate checks (owner 02/04/06). Real player movement against closed leaves, ray checks
## of the opening in both states, and the G1 bypass strip. Godot = (x_b, z_b, -y_b).

func _settle_physics() -> void:
	for i in 3:
		await get_tree().physics_frame


func _blocked(a: Vector3, b: Vector3) -> bool:
	return not ray(a, b).is_empty()


func run_validation() -> void:
	main._start_explore()
	var gc = campus.gate_controller
	check("V11 gate controller loaded the sliding leaves", gc != null and gc.leaves.size() >= 12, {"leaves": gc.leaves.size() if gc else 0})
	check("V11 six interactive gates G1-G6", gc != null and gc.gates.size() == 6, {"gates": gc.gates.keys() if gc else []})
	if gc == null:
		save_json(OUT_VALID + "v11_gates_runtime.json", {"checks": results, "all_pass": false})
		return
	# ---- G1 east lane (C02: closed at start) --------------------------------------------
	var gy := 314.6
	var yg := gy + 5.6 + 2.5
	var f = campus.ground_at(9.5, -yg + 2.0)
	var h: float = (f.y if f != null else 0.0) + 1.2
	var a := Vector3(9.5, h, -yg - 3.5)
	var b := Vector3(9.5, h, -yg + 3.5)
	check("G1 east lane starts closed", not gc.is_open("G1") and _blocked(a, b))
	# Real movement: walk at the closed leaf from outside; the player must not pass.
	await place(9.5, -yg - 4.5, Vector3(0, 0, 1))
	await hold("move_forward", 3.0)
	check("G1 closed leaf stops a walking player", player.position.z < -yg - .05, {"z": player.position.z, "leaf_z": -yg})
	gc.set_gate("G1", true, true)
	await _settle_physics()
	check("G1 opened: east lane clear at body height", not _blocked(a, b))
	await place(9.5, -yg - 4.5, Vector3(0, 0, 1))
	await hold("move_forward", 3.0)
	check("G1 open lane lets the player through", player.position.z > -yg + 1.0, {"z": player.position.z})
	gc.set_gate("G1", false, true)
	await _settle_physics()
	check("G1 closed again: both lanes blocked", _blocked(a, b) and _blocked(Vector3(-9.5, h, -yg - 3.5), Vector3(-9.5, h, -yg + 3.5)))
	# Animated (non-instant) operation reaches the open state.
	gc.toggle("G1")
	await get_tree().create_timer(3.0).timeout
	check("G1 animated opening completes", gc.is_open("G1") and not _blocked(a, b))
	# ---- G1 bypass strip (owner 02): lane post -> portal leg return walls -------------
	for sx in [-1.0, 1.0]:
		var yy := gy + 5.0
		check("G1 bypass strip closed by return wall x=" + str(sx), _blocked(Vector3(sx * 14.8, h, -yy), Vector3(sx * 10.2, h, -yy)))
	# ---- G2-G6 (owner 06): G1-family leaves, start open, close for real ----------------
	for g in campus.manifest.get("gates", []).slice(1):
		var gid: String = g.id
		var x: float = g.model_position_blender_m[0]
		var z: float = -g.model_position_blender_m[1]
		var inward := Vector2(g.inward[0], -g.inward[1]).normalized()
		var fl = campus.ground_at(x, z)
		var hh: float = (fl.y if fl != null else 0.0) + 1.2
		var p0 := Vector3(x - inward.x * 4.0, hh, z - inward.y * 4.0)
		var p1 := Vector3(x + inward.x * 4.0, hh, z + inward.y * 4.0)
		check(gid + " starts open with a clear vehicle opening", gc.is_open(gid) and not _blocked(p0, p1))
		gc.set_gate(gid, false, true)
		await _settle_physics()
		check(gid + " closed leaves block the opening", _blocked(p0, p1))
		await place(x - inward.x * 5.0, z - inward.y * 5.0, Vector3(inward.x, 0, inward.y))
		await hold("move_forward", 2.5)
		# inward is an oblique approach vector at G3, not the gate-plane normal.
		# Sliding along a closed leaf must not be mistaken for crossing its plane.
		var wall_u := Vector2(cos(g.wall_angle_radians), -sin(g.wall_angle_radians))
		var normal := Vector2(-wall_u.y, wall_u.x)
		if normal.dot(inward) < 0:
			normal = -normal
		var distance_to_plane := Vector2(player.position.x - x, player.position.z - z).dot(normal) + 1.20
		check(gid + " closed gate stops a walking player", distance_to_plane < -.05,
			{"pos": r3(player.position), "signed_distance_to_leaf_m": distance_to_plane})
		gc.set_gate(gid, true, true)
		await _settle_physics()
		check(gid + " reopened", not _blocked(p0, p1))
	# ---- Real interaction path (Codex review): HUD prompt, E key, flight suppression -----
	var g3 = campus.manifest.get("gates", [])[2]
	var gx: float = g3.model_position_blender_m[0]
	var gz: float = -g3.model_position_blender_m[1]
	var inw := Vector2(g3.inward[0], -g3.inward[1]).normalized()
	await place(gx + inw.x * 4.0, gz + inw.y * 4.0, Vector3(-inw.x, 0, -inw.y))
	await frames(10)
	check("walking near " + g3.id + " shows the gate prompt", gc._prompt_text != "", {"prompt": gc._prompt_text})
	var was_open: bool = gc.is_open(g3.id)
	var ev := InputEventAction.new()
	ev.action = "interact"
	ev.pressed = true
	var up := InputEventAction.new()
	up.action = "interact"
	up.pressed = false
	Input.parse_input_event(ev)
	await frames(3)
	Input.parse_input_event(up)
	await frames(3)
	check("E key toggles the nearest gate " + g3.id, gc.is_open(g3.id) != was_open)
	player.set_mode("fly")
	await frames(6)
	check("gate prompt hidden while flying", gc._prompt_text == "")
	var before: bool = gc.is_open(g3.id)
	Input.parse_input_event(ev)
	await frames(3)
	Input.parse_input_event(up)
	await frames(3)
	check("E while flying does not operate the gate", gc.is_open(g3.id) == before)
	player.set_mode("walk")
	gc.set_gate(g3.id, true, true)
	await frames(10)
	main._open_menu(true)
	await frames(6)
	before = gc.is_open(g3.id)
	await tap("interact")
	check("pause suppresses prompt and E interaction", gc._prompt_text == "" and gc.is_open(g3.id) == before)
	main._start_explore()
	await frames(6)
	check("resume restores gate prompt in place", gc._prompt_text != "")
	main.enter_photo_mode()
	await frames(6)
	await tap("interact")
	check("photo mode suppresses gate interaction", gc._prompt_text == "" and gc.is_open(g3.id) == before)
	main.exit_photo_mode()
	save_json(OUT_VALID + "v11_gates_runtime.json", {"checks": results, "all_pass": results.all(func(r): return r["pass"]),
		"state_report": str(gc.report())})
