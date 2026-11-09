extends "res://tests/v5_ground.gd"
## Survey along the actual wall tangent/normal, not the often oblique spawn approach.
## Every attempt starts on a verified floor outside collision, then uses real player input.
var samples := []

func run_validation() -> void:
	main._start_explore()
	var gc = campus.gate_controller
	for g in campus.manifest.gates:
		var gid: String = g.id
		var center := Vector2(g.model_position_blender_m[0], -g.model_position_blender_m[1])
		var angle: float = g.wall_angle_radians if gid != "G1" else 0.0
		var u := Vector2(cos(angle), -sin(angle))
		var v := Vector2(-u.y, u.x)
		var inward := Vector2(g.inward[0], -g.inward[1])
		if v.dot(inward) < 0:
			v = -v
		var w: float = g.parameters_v8.opening_width / 2.0 if gid != "G1" else 11.9
		var extent: float = g.parameters_v8.wall_connection_half + 2.0 if gid != "G1" else 64.0
		var plane := -1.20 if gid != "G1" else -8.1
		var walking := []
		if gid == "G1":
			walking = [-19.0, -11.3, -10.3, -9.3, -8.3, -7.7, 7.7, 8.3, 9.3, 10.3, 11.3, 19.0]
		else:
			for k in range(int(ceil(-w + .6)), int(floor(w - .6)) + 1):
				walking.append(float(k))
			walking.append(-w + .45)
			walking.append(w - .45)
			walking.append(2.0 * w + .9 + 1.2 + .85) # pedestrian opening
			walking.append(-w - .5) # leaf/pylon junction bypass attempts
			walking.append(w + .5)
		gc.set_gate(gid, false, true)
		await frames(4)
		var misses := []
		var reference_floor = campus.ground_at(center.x + (9.5 if gid == "G1" else 0.0), center.y - 12.0)
		var h: float = (reference_floor.y if reference_floor != null else 0.0) + 1.1
		for k in range(int(ceil(-extent * 2)), int(floor(extent * 2)) + 1):
			var s := float(k) * .5
			var c: Vector2 = center + u * s
			for sign in [-1.0, 1.0]:
				var a: Vector2 = c + v * (plane - sign * 32.0)
				var b: Vector2 = c + v * (plane + sign * 32.0)
				if ray(Vector3(a.x,h,a.y), Vector3(b.x,h,b.y)).is_empty():
					misses.append({"lateral":s,"direction":sign})
		check(gid + " closed complete frontage rays every 0.5 m, both directions", misses.is_empty(), {"misses":misses})
		for opened in [false, true]:
			gc.set_gate(gid, opened, true)
			await frames(4)
			var failures := []
			for s in walking:
				# Pylons deliberately stay solid in the open state.
				if opened and gid != "G1" and absf(s) > w and s < 2.0*w:
					continue
				for sign in [-1.0, 1.0]:
					var c: Vector2 = center + u * s
					var attempt_plane: float = (0.0 if gid == "G1" else -.45) if absf(s) > (17.0 if gid == "G1" else 2.0*w) else plane
					var a: Vector2 = c + v * (attempt_plane - sign * 4.0)
					await place(a.x, a.y, Vector3(v.x * sign, 0, v.y * sign))
					var initial := player.position
					var valid_start: bool = player.is_on_floor() and not overlapping(initial + Vector3(0,.08,0)) and player.collision_mask == 1 and not player.noclip
					await hold("move_forward", 2.5)
					var progress := (Vector2(player.position.x,player.position.z)-center).dot(v)-attempt_plane
					var crossed: bool = sign * progress > .7
					var ok: bool = valid_start and (crossed if opened else not crossed)
					var row := {"gate":gid,"open":opened,"lateral":s,"direction":sign,"start":r3(initial),"end":r3(player.position),"valid_start":valid_start,"normal_progress":progress,"pass":ok}
					samples.append(row)
					if not ok:
						failures.append(row)
			check(gid + (" open usable passage" if opened else " closed player grid and edge attempts") + " both directions", failures.is_empty(), {"failures":failures})
		gc.set_gate(gid, true, true)
	save_json(OUT_VALID + "v11_gate_coverage.json", {"checks":results,"samples":samples,"all_pass":results.all(func(r):return r.pass)})
