extends "res://tests/v5_ground.gd"
## Complete acceptance journey: one placement outside G1, no later teleport/fly/jump.
func run_validation() -> void:
	main._start_explore()
	var pts: Array = [
		Vector2(-19,-337),Vector2(-19,-310),Vector2(-16.3,-290),Vector2(-16.3,-270),Vector2(-16.3,-110),
		Vector2(-25,-55),Vector2(0,-42),Vector2(0,-25),Vector2(0,-42),Vector2(-25,-55),
		Vector2(-21,-80),Vector2(-40.76,-70.47),Vector2(-63.59,-66.58),Vector2(-86.05,-61),
		Vector2(-115.63,-50.83),Vector2(-144.03,-37.74),Vector2(-170.94,-21.85),Vector2(-196.1,-3.33),
		Vector2(-210.47,23.21),Vector2(-188.08,18.3),Vector2(-169.57,3.32),Vector2(-164.06,.67),
		Vector2(-156.56,.78),Vector2(-151.94,2.03),Vector2(-145.08,7.12),Vector2(-137.23,15.02),
		Vector2(-106.81,45.74),Vector2(-51.23,100.78),Vector2(-41.46,110.11),Vector2(-23.63,117.15),
		Vector2(0,117.88),Vector2(0,155),Vector2(-13,200),Vector2(-13,221.5),
		Vector2(-8,232),Vector2(-9,245),Vector2(-10,262),Vector2(-9,245),Vector2(-8,232),
		Vector2(-13,221.5),Vector2(-13,200),Vector2(13,200),Vector2(13,221.5),
		Vector2(9,245),Vector2(10,262),Vector2(9,245),Vector2(13,221.5),Vector2(13,200),
		Vector2(0,200),Vector2(0,239),Vector2(0,264),Vector2(0,280),Vector2(0,315),
		Vector2(10.5,315),Vector2(10.5,285.5),Vector2(10.5,315),Vector2(0,315),Vector2(0,340),
		Vector2(0,368),Vector2(0,430),Vector2(0,500),Vector2(150,520),Vector2(250,525),Vector2(350,525),Vector2(425,555)]
	var plan = JSON.parse_string(FileAccess.get_file_as_string("res://../../output/validation/v11/dorm_garden_plan.json"))
	for p in plan.walk_paths_godot[0]:
		pts.append(Vector2(p[0],p[1]))
	Input.action_press("sprint")
	await follow_route("outside G1 > approach > Administration landing > Academic A > BOTH stairs/hall/bridge > court ramp > rear > dormitory",pts)
	Input.action_release("sprint")
	check("journey ends with walking physics and collision enabled", player.mode == "walk" and not player.noclip and player.collision_mask == 1 and player.is_on_floor())
	save_json(OUT_VALID + "v11_full_journey.json", {"checks":results,"all_pass":results.all(func(r):return r.pass),
		"method":"One initial floor placement outside G1; continuous real sprint/walk input; no subsequent teleport/fly/jump; existing collision masks"})
