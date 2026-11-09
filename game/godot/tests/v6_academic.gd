extends "res://tests/v5_academic.gd"

func run_validation() -> void:
	await super.run_validation()
	await follow_route("V6 three stepped semicircular court levels",[Vector2(46,272),Vector2(43,272),Vector2(40,272),Vector2(30,272),Vector2(20,272)])
	check("terraced court has real elevated collision",absf(player.feet_position().y-1.11)<.15,{"feet_y":player.feet_position().y})
	await follow_route("V6 estimated accessible terrace ramp",[Vector2(10.5,317),Vector2(10.5,314),Vector2(10.5,300),Vector2(10.5,285.5)])
	check("ramp reaches upper court",player.feet_position().y>1.0 and player.is_on_floor(),{"feet_y":player.feet_position().y})
	player.face_direction(Vector3(0,0,1))
	await hold("move_forward",8.)
	check("ramp descends continuously to main paving",player.is_on_floor() and player.position.z>315 and player.feet_position().y<.5,{"position":r3(player.position)})
	save_json("res://../../output/validation/v11/academic_runtime.json",{"checks":results,"all_pass":results.all(func(r):return r["pass"])})
