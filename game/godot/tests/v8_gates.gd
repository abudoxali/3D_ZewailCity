extends "res://tests/v5_ground.gd"

func run_validation() -> void:
	main._start_explore()
	var gates: Array = campus.manifest.get("gates", [])
	check("V8 six gates and stable provisional evidence", gates.size()==6 and gates.slice(1).all(func(g):return g.status=="PROVISIONAL_MAP_CLUSTER" and g.has("parameters_v8")))
	for g in gates.slice(1):
		var c: Dictionary = g.parameters_v8
		var x: float = g.model_position_blender_m[0]
		var z: float = -g.model_position_blender_m[1]
		var a: float = c.orientation
		var u := Vector2(cos(a),-sin(a))
		var inward := Vector2(g.inward[0],-g.inward[1])
		var v := Vector2(-sin(a),-cos(a))
		if v.dot(inward)<0: v=-v
		var p := Vector2(x,z)
		await follow_route("V8 local vehicle threshold inward "+g.id,[p-v*7,p,p+v*7])
		await follow_route("V8 local vehicle threshold outward "+g.id,[p+v*7,p,p-v*7])
		var ped: Vector2 = p+u*(float(c.opening_width)*.5-float(c.pedestrian_width)*.5)
		await follow_route("V8 pedestrian bay "+g.id,[ped-v*2.4,ped,ped+v*2.4])
		var support: Vector2 = p-u*(float(c.opening_width)*.5+.325)
		var floor = campus.ground_at(x,z)
		var y: float = floor.y+1.4 if floor!=null else 1.4
		check("V8 masonry support blocks capsule-height ray "+g.id,not ray(Vector3(support.x-v.x*2,y,support.y-v.y*2),Vector3(support.x+v.x*2,y,support.y+v.y*2)).is_empty())
		check("V8 open vehicle route has head clearance "+g.id,ray(Vector3(x-v.x*2,y,z-v.y*2),Vector3(x+v.x*2,y,z+v.y*2)).is_empty())
	check("G2 unresolved external sand gap remains explicit",gates[1].external_access=="UNRESOLVED_SAND_GAP_25M")
	save_json(OUT_VALID+"v8_gates_runtime.json",{"checks":results,"all_pass":results.all(func(r):return r["pass"])})
