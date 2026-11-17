extends "res://tests/v5_ground.gd"
## Actual exported collision and player routes; no injected floor/teleport repair.

func run_validation() -> void:
	main._start_explore()
	main.set_process_unhandled_input(false)
	player.set_process_unhandled_input(false)
	for layer in main.find_children("*","CanvasLayer",true,false):(layer as CanvasLayer).visible=false
	var transport=JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/final_partition_segment_audit.json"))
	var holes:Array=[]
	var samples:int=0
	for row in transport.samples:
		var p:Vector2=Vector2(row.xy[0],-row.xy[1])
		var hit=ray(Vector3(p.x,8.,p.y),Vector3(p.x,-6.,p.y))
		samples+=1
		if hit.is_empty():holes.append([p.x,p.y])
	check("V17 every source segment has actual exported collision",holes.is_empty(),{"samples":samples,"hole_count":holes.size(),"examples":holes.slice(0,20)})
	var admin=ray(Vector3(0,4,-40),Vector3(0,-5,-40))
	var academic=ray(Vector3(0,2,180),Vector3(0,-5,180))
	check("V17 Administration to Academic relative descent exists in real meshes",not admin.is_empty() and not academic.is_empty() and admin.position.y-academic.position.y>2.,{"admin":r3(admin.position) if not admin.is_empty() else [],"academic":r3(academic.position) if not academic.is_empty() else [],"dimensions":"ESTIMATED; only descent direction owner-supported"})
	# Rotunda axis must be an actual tall void, while gallery roof remains solid.
	check("V17 Administration rotunda open to window drum",ray(Vector3(0,3,0),Vector3(0,27.,0)).is_empty())
	check("V17 Administration fixed rear glazing blocks",not ray(Vector3(0,3.3,92),Vector3(0,3.3,98)).is_empty())
	check("V17 Academic fixed lower glazing blocks",not ray(Vector3(0,.6,217),Vector3(0,.6,224)).is_empty())
	check("V17 Academic lower doorway is a real opening",ray(Vector3(-2.3,.6,217),Vector3(-2.3,.6,224)).is_empty())
	# One placement for the entire architectural traversal below. Subsequent
	# follow_route(start=false) calls retain actual player position and velocity.
	await follow_route("V17 front entrance > rotunda > rear route > graded campus > Academic forecourt",[
		Vector2(0,-42),Vector2(0,-26),Vector2(0,-17),Vector2(0,0),Vector2(0,22),
		Vector2(-10,35),Vector2(-10,60),Vector2(-11,90),Vector2(-11,103),Vector2(0,112),Vector2(0,145),Vector2(0,176),Vector2(-11,198)])
	await follow_route("V17 exact left treads > upper landing > exact right treads",[
		Vector2(-11,198),Vector2(-11,215),Vector2(-11,220.5),Vector2(-11,222),
		Vector2(-11,220.5),Vector2(11,220.5),Vector2(11,215),Vector2(11,198)],false)
	await follow_route("V17 right stair ascent > upper hall > left descent",[
		Vector2(11,198),Vector2(11,220.5),Vector2(11,233),Vector2(11,253),
		Vector2(11,233),Vector2(11,220.5),Vector2(-11,220.5),Vector2(-11,198)],false)
	await follow_route("V17 lower Gate A > open court platforms > rear passage",[
		Vector2(-11,198),Vector2(-2.3,204),Vector2(-2.3,213),Vector2(-2.3,228),Vector2(-2.3,236),
		Vector2(-2.3,268),Vector2(0,276),Vector2(0,284),Vector2(0,295),
		Vector2(0,313),Vector2(0,327),Vector2(0,349),Vector2(0,365)],false)
	check("V17 continuous architecture route ends with physical collision",player.mode=="walk" and not player.noclip and player.collision_mask==1 and player.is_on_floor())
	# Separate representative roads and garden routes have their own initial
	# placements; they are not misrepresented as part of the uncut route above.
	await follow_route("V17 east ring junction",[Vector2(301,250),Vector2(301,240),Vector2(300,225),Vector2(297,195)])
	await follow_route("V17 west ring junction",[Vector2(-301,240),Vector2(-300,225),Vector2(-297,205)])
	await follow_route("V17 housing garden and pergola plaza",load("res://tests/v17_routes.gd").garden())
	# Reproduce the court coping stall at several lateral capsule contacts.
	# These are separate focused placements, not part of the uncut route above.
	for x in [-.12,-.06,0.,.06,.12]:
		await follow_route("V18 court coping ascent lateral "+str(x),[Vector2(x,277.67),Vector2(x,284.)])
		await follow_route("V18 court coping descent lateral "+str(x),[Vector2(x,284.),Vector2(x,270.)],false)
	save_json(OUT_VALID+"v17_reconstruction.json",{"checks":results,"all_pass":results.all(func(r):return r["pass"]),"method":"Real input; one initial placement across connected architectural sections; separate placements for road/garden checks"})
