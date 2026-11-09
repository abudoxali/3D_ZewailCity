extends "res://tests/validate.gd"
## Real physics/input tests of exported GLB, separate from plan-topology assertions.

func place(x: float, z: float, direction: Vector3) -> void:
	player.set_mode("walk")
	var g = campus.ground_at(x,z)
	if g == null:
		check("route has a start floor",false,{"x":x,"z":z})
		return
	player.teleport(g+Vector3(0,player.HEIGHT*.5+.05,0))
	player.face_direction(direction)
	await frames(40)

## V11: start=false continues from the player's real position (elevated routes: place()
## only finds floors below 3 m, which would drop the player under an upper deck).
func follow_route(name: String, points: Array, start := true) -> void:
	if start:
		await place(points[0].x,points[0].y,Vector3(points[1].x-points[0].x,0,points[1].y-points[0].y))
	var failures := []
	var airborne := 0
	var floor_losses := 0
	var max_floor_gap := 0.
	var max_gap_at := {}
	for target: Vector2 in points.slice(1):
		var distance := Vector2(player.position.x,player.position.z).distance_to(target)
		var budget := int((distance / 3. + 4.)*60.)
		Input.action_press("move_forward")
		for i in budget:
			var offset := target-Vector2(player.position.x,player.position.z)
			if offset.length() < .65:
				break
			player.face_direction(Vector3(offset.x,0,offset.y))
			await get_tree().physics_frame
			if not player.is_on_floor():
				airborne += 1
			var feet: float=player.feet_position().y
			var floor=campus.ground_at(player.position.x,player.position.z,feet+.5)
			if floor==null:
				for d in [Vector2(.02,0),Vector2(-.02,0),Vector2(0,.02),Vector2(0,-.02)]:
					floor=campus.ground_at(player.position.x+d.x,player.position.z+d.y,feet+.5)
					if floor!=null:
						break
			if floor==null:
				floor_losses+=1
			else:
				var gap: float=absf(feet-floor.y)
				if gap>max_floor_gap:
					max_floor_gap=gap
					max_gap_at={"player":r3(player.position),"velocity":r3(player.velocity),"on_floor":player.is_on_floor(),"feet_y":feet,"floor":r3(floor),"target":[target.x,target.y]}
		Input.action_release("move_forward")
		await frames(4)
		if Vector2(player.position.x,player.position.z).distance_to(target) > 1.:
			failures.append({"target":[target.x,target.y],"actual":r3(player.position)})
	check(name,failures.is_empty() and player.is_on_floor() and floor_losses==0 and max_floor_gap<.55,
		{"failures":failures,"airborne_frames":airborne,"floor_losses":floor_losses,"max_floor_gap_m":max_floor_gap,"max_gap_at":max_gap_at,"final":r3(player.position)})

func run_validation() -> void:
	main._start_explore()
	var data = JSON.parse_string(FileAccess.get_file_as_string("res://../../output/validation/v11/road_floor_samples.json"))
	var gaps := []
	var max_error := 0.
	var edge_recoveries := 0
	var height_errors := []
	var floor_excludes: Array[RID] = [player.get_rid()]
	for body in campus.campus_root.find_children("*","StaticBody3D",true,false):
		if not String(body.name).contains("COL_Ground"):
			floor_excludes.append(body.get_rid())
	for sample in data:
		var p := Vector3(sample.godot[0],sample.godot[1],sample.godot[2])
		var query := PhysicsRayQueryParameters3D.create(p+Vector3(0,.4,0),p-Vector3(0,.4,0),1)
		query.exclude=floor_excludes
		var hit := space().intersect_ray(query)
		if hit.is_empty() or absf(hit.position.y-p.y)>.04:
			var best_error: float=absf(hit.position.y-p.y) if not hit.is_empty() else INF
			for offset in [Vector3(.02,0,0),Vector3(-.02,0,0),Vector3(0,0,.02),Vector3(0,0,-.02)]:
				query.from=p+offset+Vector3(0,.4,0)
				query.to=p+offset-Vector3(0,.4,0)
				var probe=space().intersect_ray(query)
				if not probe.is_empty() and absf(probe.position.y-p.y)<best_error:
					hit=probe
					best_error=absf(probe.position.y-p.y)
			if not hit.is_empty() and best_error<.04:
				edge_recoveries+=1
		if hit.is_empty():
			gaps.append(sample)
		else:
			max_error=maxf(max_error,absf(hit.position.y-p.y))
			if absf(hit.position.y-p.y)>.04:
				height_errors.append({"sample":sample,"hit":r3(hit.position)})
	check("all road centrelines have collision at source elevation",gaps.is_empty() and max_error < .04,
		{"samples":data.size(),"gaps":gaps,"height_errors":height_errors,"max_error_m":max_error,"edge_recoveries_at_2cm":edge_recoveries})
	if "--floors-only" in OS.get_cmdline_user_args():
		save_json("res://../../output/validation/v11/ground_floor_probe.json",{"checks":results})
		return
	await follow_route("gate walkway and perimeter-loop transition",[Vector2(-19,-327),Vector2(-19,-310),Vector2(-16.3,-290),Vector2(-16.3,-270)])
	await follow_route("approach paving",[Vector2(16.3,-220),Vector2(16.3,-200),Vector2(16.3,-180)])
	await follow_route("academic connector",[Vector2(0,121),Vector2(0,145),Vector2(0,160)])
	await follow_route("ring road grade",[Vector2(300.7,250),Vector2(301.2,240),Vector2(300.7,225)])
	save_json("res://../../output/validation/v11/ground_runtime.json",{"checks":results,"all_pass":results.all(func(r):return r["pass"])})
