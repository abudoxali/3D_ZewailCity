extends "res://tests/v5_ground.gd"

func run_validation() -> void:
	main._start_explore()
	await follow_route("rear natural soil and estimated earth path",[Vector2(0,370),Vector2(0,430),Vector2(0,505)])
	var plan = JSON.parse_string(FileAccess.get_file_as_string("res://../../output/validation/v11/dorm_garden_plan.json"))
	var points: Array = []
	for p in plan.walk_paths_godot[0]: points.append(Vector2(p[0],p[1]))
	await follow_route("dormitory candidate ingress and photo garden path",points)
	var s: Dictionary=campus.spawn_by_id("SPAWN_14_Dormitory_Candidate")
	main._go_to_spawn(s.id,"",false)
	await frames(60)
	check("dormitory approach spawn grounded",player.is_on_floor() and not overlapping(player.position+Vector3(0,.05,0)))
	var l=campus.landmark_at(Vector3(390,1,603))
	check("dormitory identity remains explicitly unconfirmed",not l.is_empty() and not l.verified and String(l.label).contains("unconfirmed"))
	save_json("res://../../output/validation/v11/dormitory_runtime.json",{"checks":results,"all_pass":results.all(func(r):return r["pass"])})
