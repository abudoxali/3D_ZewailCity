extends "res://tests/v5_ground.gd"

func run_validation() -> void:
	main._start_explore()
	var gates: Array=campus.manifest.get("gates",[])
	check("six distinct gates with explicit evidence states",gates.size()==6 and gates[0].status=="PHOTO_AND_MAP" and gates.slice(1).all(func(g):return g.status=="PROVISIONAL_MAP_CLUSTER"))
	check("original seven spawn indices preserved",campus.spawns[0].id=="SPAWN_01_Main_Entrance" and campus.spawns[6].id=="SPAWN_07_Main_Gate_Exterior")
	for g in gates.slice(1):
		var s: Dictionary=campus.spawn_by_id(g.spawn)
		check("gate spawn present "+g.id,not s.is_empty())
		var x: float=g.model_position_blender_m[0]
		var z: float=-g.model_position_blender_m[1]
		var inward:=Vector2(g.inward[0],-g.inward[1])
		await follow_route("walk through provisional opening "+g.id,[Vector2(x,z)+inward*8,Vector2(x,z),Vector2(x,z)-inward*8])
	save_json("res://../../output/validation/v11/gates_runtime.json",{"checks":results,"all_pass":results.all(func(r):return r["pass"])})
