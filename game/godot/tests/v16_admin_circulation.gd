extends "res://tests/v5_ground.gd"
## Exported geometry and actual player movement, not graph reachability alone.

func run_validation() -> void:
	main._start_explore()
	for layer in main.find_children("*", "CanvasLayer", true, false):
		(layer as CanvasLayer).visible = false
	await follow_route("V16 continuous approach > front door > roofed plaza > rear side exit > campus connector", [
		Vector2(0,-42),Vector2(0,-33),Vector2(0,-25),Vector2(0,-17),
		Vector2(0,0),Vector2(0,22),Vector2(10,32),Vector2(10,50),
		Vector2(10,75),Vector2(11,90),Vector2(11,103),Vector2(0,112),Vector2(0,120),Vector2(0,145)])
	for sx in [-1.,1.]:
		await follow_route("V16 side entrance and through gallery sx="+str(sx),[
			Vector2(sx*26,-35),Vector2(sx*26,-28),Vector2(sx*26,-20),
			Vector2(sx*26,0),Vector2(sx*26,25),Vector2(sx*19,30),
			Vector2(sx*10,30),Vector2(sx*10,50),Vector2(sx*10,75),
			Vector2(sx*11,90),Vector2(sx*11,103)])
		for z in [5.,25.,50.,75.,90.]:
			var x:float=sx*10.
			var floor=ray(Vector3(x,2.4,z),Vector3(x,.7,z))
			check("V16 supported floor "+str([x,z]),not floor.is_empty() and absf(floor.position.y-(.72+datum_at(x,z)))<.04)
		check("V16 rear opening clear sx="+str(sx),ray(Vector3(sx*11,2.4,92),Vector3(sx*11,2.4,98)).is_empty())
		check("V16 real roof over gallery sx="+str(sx),not ray(Vector3(sx*10,3.6,60),Vector3(sx*10,7.2,60)).is_empty())
	# Off-happy paths: fixed rear glazing must block; head-clearance must not be
	# confused with an absent roof, and an unsupported axis exit must not be claimed.
	check("V16 retained rear glazing physically blocks central bay",not ray(Vector3(0,3.6,92),Vector3(0,3.6,97)).is_empty())
	check("V16 former vestibule back wall is an actual open passage",ray(Vector3(0,2.4,-10.4),Vector3(0,2.4,8)).is_empty())
	await follow_route("V16 representative reconstructed ring and road junction",[
		Vector2(300.7,250),Vector2(301.2,240),Vector2(300.7,225),Vector2(297,195)])
	# Bounded ground coverage over the whole campus precinct, including corrected
	# ring junctions. Exact building interiors are tested by the player routes.
	var holes:Array=[]
	var samples:int=0
	for x in range(-380,481,4):
		for z in range(-390,701,4):
			samples+=1
			var hit=ray(Vector3(x,3.,z),Vector3(x,-2.,z))
			if hit.is_empty():
				for off in [Vector3(.02,0,0),Vector3(-.02,0,0),Vector3(0,0,.02),Vector3(0,0,-.02)]:
					hit=ray(Vector3(x,3.,z)+off,Vector3(x,-2.,z)+off)
					if not hit.is_empty():break
			if hit.is_empty():holes.append([x,z])
	check("V16 precinct collision has no holes on 4 m grid",holes.is_empty(),{"samples":samples,"hole_count":holes.size(),"examples":holes.slice(0,20)})
	save_json(OUT_VALID+"v16_admin_runtime.json",{"checks":results,"all_pass":results.all(func(r):return r["pass"])})
