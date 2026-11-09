extends "res://tests/v5_ground.gd"
## Continuous integration route. Sprint input uses the existing walking physics;
## no intermediate teleport, fly, jump or no-clip is used.
func run_validation() -> void:
	main._start_explore()
	Input.action_press("sprint")
	await follow_route("continuous main exterior gate > west mapped footways > Academic passage > rear",[
		Vector2(-19,-327),Vector2(-19,-310),Vector2(-16.3,-290),Vector2(-16.3,-270),Vector2(-16.3,-110),
		Vector2(-21,-80),Vector2(-40.76,-70.47),Vector2(-63.59,-66.58),Vector2(-86.05,-61),
		Vector2(-115.63,-50.83),Vector2(-144.03,-37.74),Vector2(-170.94,-21.85),Vector2(-196.1,-3.33),
		Vector2(-210.47,23.21),Vector2(-188.08,18.3),Vector2(-169.57,3.32),Vector2(-164.06,.67),
		Vector2(-156.56,.78),Vector2(-151.94,2.03),Vector2(-145.08,7.12),Vector2(-137.23,15.02),
		Vector2(-106.81,45.74),Vector2(-51.23,100.78),Vector2(-41.46,110.11),Vector2(-23.63,117.15),
		Vector2(0,117.88),Vector2(0,155),Vector2(0,205),Vector2(0,235),Vector2(0,280),
		Vector2(0,320),Vector2(0,352),Vector2(0,368)])
	Input.action_release("sprint")
	save_json("res://../../output/validation/v11/journey_runtime.json",{"checks":results,"all_pass":results.all(func(r):return r["pass"]),"method":"scripted sprint through existing walk controller; one initial placement, continuous movement"})
