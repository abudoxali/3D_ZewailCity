extends "res://tests/v5_ground.gd"
## One initial placement; native player movement throughout all later sections.
func run_validation() -> void:
	# A window-close request must not masquerade as successful route completion.
	get_tree().auto_accept_quit=false
	main._start_explore()
	main.set_process_unhandled_input(false);player.set_process_unhandled_input(false)
	for layer in main.find_children("*","CanvasLayer",true,false):(layer as CanvasLayer).visible=false
	var w=get_tree().root;w.content_scale_size=Vector2i(1920,1080);w.content_scale_mode=Window.CONTENT_SCALE_MODE_VIEWPORT;w.content_scale_aspect=Window.CONTENT_SCALE_ASPECT_KEEP
	w.set_flag(Window.FLAG_NO_FOCUS,true)
	w.position=Vector2i(-2500,-1500)
	await follow_route("V17 uncut G1 approach > Administration entrance > rotunda",[
		Vector2(-19,-337),Vector2(-19,-310),Vector2(-16.3,-270),Vector2(-16.3,-110),
		Vector2(-25,-55),Vector2(0,-42),Vector2(0,-25),Vector2(0,0),Vector2(0,22)])
	await follow_route("V17 uncut BOTH Administration side loops and rear exit",[
		Vector2(0,22),Vector2(-10,30),Vector2(-19,30),Vector2(-26,25),Vector2(-26,-30),
		Vector2(-26,25),Vector2(-19,30),Vector2(19,30),Vector2(26,25),Vector2(26,-30),
		Vector2(26,25),Vector2(19,30),Vector2(-10,30),Vector2(-10,60),Vector2(-11,90),Vector2(-11,103),Vector2(0,112),Vector2(0,145),Vector2(0,176),Vector2(-11,198)],false)
	await follow_route("V17 uncut BOTH major stairs, upper landing and hall",[
		Vector2(-11,198),Vector2(-11,220.5),Vector2(-11,233),Vector2(-11,253),
		Vector2(-11,233),Vector2(-11,220.5),Vector2(11,220.5),Vector2(11,198),
		Vector2(11,220.5),Vector2(11,233),Vector2(11,253),Vector2(11,233),Vector2(11,220.5),Vector2(-11,220.5),Vector2(-11,198)],false)
	await follow_route("V17 uncut lower entrance > courtyard levels > rear exit",[
		Vector2(-11,198),Vector2(-2.3,204),Vector2(-2.3,213),Vector2(-2.3,228),Vector2(-2.3,236),Vector2(-2.3,268),
		Vector2(0,276),Vector2(0,284),Vector2(0,295),Vector2(0,313),Vector2(0,349),Vector2(0,365)],false)
	var gallery:Array=[Vector2(0,365),Vector2(0,348),Vector2(0,330)]
	var visit:Array=load("res://tests/v17_routes.gd").rear_gallery(-1.)
	gallery.append_array(visit.slice(1))
	visit.reverse()
	gallery.append_array(visit.slice(1))
	gallery.append(Vector2(0,348));gallery.append(Vector2(0,365))
	await follow_route("V18 uncut rear opening > Academic gallery > return to rear route",gallery,false)
	Input.action_press("sprint")
	await follow_route("V17 uncut rear ground > housing paths > pergola plaza",[
		Vector2(0,365),Vector2(0,430),Vector2(0,500),Vector2(150,520),Vector2(250,525),Vector2(350,525),Vector2(425,555)],false)
	Input.action_release("sprint")
	await follow_route("V17 uncut curved garden paths and pergola",load("res://tests/v17_routes.gd").garden(),false)
	check("V17 uncut walkthrough ends physically grounded",player.mode=="walk" and not player.noclip and player.collision_mask==1 and player.is_on_floor())
	save_json(OUT_VALID+"v17_walkthrough.json",{"checks":results,"method":"One initial placement outside G1; actual movement actions; no later teleport/fly/jump. Independent route-check verdicts retained."})
