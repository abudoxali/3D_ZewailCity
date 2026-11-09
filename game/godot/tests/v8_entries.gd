extends "res://tests/v5_ground.gd"

func run_validation() -> void:
	main._start_explore()
	await follow_route("Administration steps reach a supported landing",[Vector2(2.3,-33),Vector2(2.3,-30),Vector2(2.3,-25)])
	check("Administration landing matches top stair 0.72 m",player.is_on_floor() and absf(player.feet_position().y-.72)<.09,{"feet_y":player.feet_position().y})
	var road = campus.ground_at(11.,-40.3)
	var toe = campus.ground_at(11.,-39.90)
	check("Administration ramp toe meets road within 2 cm",road!=null and toe!=null and absf(road.y-toe.y)<.02,{"road_y":road.y if road!=null else -99,"toe_y":toe.y if toe!=null else -99})
	await follow_route("Administration provisional 6.5% ramp ascent",[Vector2(11,-41.5),Vector2(11,-35),Vector2(11,-29),Vector2(11,-25)])
	check("Administration ramp reaches landing",player.is_on_floor() and absf(player.feet_position().y-.72)<.09,{"feet_y":player.feet_position().y})
	await follow_route("Administration ramp descent",[Vector2(11,-25),Vector2(11,-32),Vector2(11,-38),Vector2(11,-42)])
	# Off-route: closed facade remains solid, ramp rail is not removed for traversal.
	# V10: the axis bay is now a real recessed entrance (doorways at x -1.1..1.1 and
	# 1.9..4.1), so the V8 ray at x=2.3 correctly passes. The envelope check moves to
	# the solid facade either side of the entrance bay (Codex integration note).
	for fx in [-16.,16.]:
		check("Administration facade retained x="+str(fx),not ray(Vector3(fx,1.8,-25),Vector3(fx,1.8,-15)).is_empty())
	check("Administration ramp side rail solid",not ray(Vector3(10.5,1.40,-35),Vector3(9.8,1.40,-35)).is_empty())
	save_json(OUT_VALID+"v8_entries_runtime.json",{"checks":results,"all_pass":results.all(func(r):return r["pass"])})
