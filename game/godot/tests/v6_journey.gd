extends "res://tests/v5_ground.gd"
## One initial placement, real sprint/walk physics. No intermediate teleport/fly/jump.
func run_validation() -> void:
	main._start_explore()
	Input.action_press("sprint")
	# V11: great stairs run from the forecourt (z 208.9) up to the 4.41 m terrace (z 219);
	# the terrace cross band between the two voids is at z 229.5..235.
	# Around void A (|x| < 5.8, z 221.5..229.5): its railing correctly blocks a straight line.
	var pts: Array=[Vector2(-13,200),Vector2(-13,212),Vector2(-13,221.5),Vector2(-8,226),Vector2(-8,232),
		Vector2(0,232),Vector2(-8,232),Vector2(-8,220.3),Vector2(0,220.3),Vector2(-8,220.3),Vector2(-13,221.5),Vector2(-13,200),
		Vector2(13,200),Vector2(13,221.5),Vector2(13,200),Vector2(0,200),Vector2(0,214),
		Vector2(0,239),Vector2(0,264),Vector2(0,280),Vector2(0,315),Vector2(10.5,315),
		Vector2(10.5,285.5),Vector2(10.5,315),Vector2(0,315),Vector2(0,340),Vector2(0,368),
		Vector2(0,430),Vector2(0,500),Vector2(150,520),Vector2(250,525),Vector2(350,525),Vector2(425,555)]
	var plan = JSON.parse_string(FileAccess.get_file_as_string("res://../../output/validation/v11/dorm_garden_plan.json"))
	var stairs_probe := "--stairs-only" in OS.get_cmdline_user_args()
	if stairs_probe:pts=pts.slice(0,17)
	else:
		for p in plan.walk_paths_godot[0]:pts.append(Vector2(p[0],p[1]))
	await follow_route("continuous two stairs > portal > stepped court ramp > rear soil > dormitory garden",pts)
	Input.action_release("sprint")
	var out := "complete_journey_stairs_probe.json" if stairs_probe else "complete_journey_runtime.json"
	save_json("res://../../output/validation/v11/"+out,{"checks":results,"all_pass":results.all(func(r):return r["pass"]),"method":"scripted existing player physics; one initial placement; no intermediate teleport/fly/jump/no-clip"})
