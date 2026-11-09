extends "res://tests/v5_dormitory.gd"

func run_validation() -> void:
	await super.run_validation()
	var plan = JSON.parse_string(FileAccess.get_file_as_string("res://../../output/validation/v11/dorm_garden_plan.json"))
	for i in plan.walk_paths_godot.size():
		var points: Array = []
		for p in plan.walk_paths_godot[i]: points.append(Vector2(p[0],p[1]))
		await follow_route("V6 photo garden branch "+str(i+1),points)
	main._set_evening(true)
	await frames(2)
	# V7: all modelled luminaires light in the evening; the garden keeps its 32 bollards.
	var lights: Array = campus.manifest.get("evening_lights",[])
	var bollards: int = lights.filter(func(l): return String(l.get("kind",""))=="bollard").size()
	var bounded := true
	for l in main.garden_lights.get_children():
		var r: float = (l as OmniLight3D).omni_range if l is OmniLight3D else (l as SpotLight3D).spot_range
		bounded = bounded and not (l as Light3D).shadow_enabled and r <= 20.0 and (l as Light3D).distance_fade_enabled
	check("evening has bounded garden bollards and luminaire lights",main.evening_mode and main.garden_lights.visible and bollards==32 and main.garden_lights.get_child_count()==lights.size() and bounded,{"lights":main.garden_lights.get_child_count(),"bollards":bollards,"bounded_shadowless":bounded})
	main._set_evening(false)
	check("daylight restored without reloading geometry",not main.evening_mode and not main.garden_lights.visible and main.sun.light_energy>1.0)
	save_json("res://../../output/validation/v11/dormitory_runtime.json",{"checks":results,"all_pass":results.all(func(r):return r["pass"])})
