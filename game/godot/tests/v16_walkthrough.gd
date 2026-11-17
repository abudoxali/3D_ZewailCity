extends "res://tests/v5_ground.gd"
## A single real player route, without teleport/fly/jump after initial placement.
func run_validation() -> void:
	main._start_explore()
	main.set_process_unhandled_input(false)
	player.set_process_unhandled_input(false)
	var window=get_tree().root
	window.content_scale_size=Vector2i(1920,1080)
	window.content_scale_mode=Window.CONTENT_SCALE_MODE_VIEWPORT
	window.content_scale_aspect=Window.CONTENT_SCALE_ASPECT_KEEP
	for layer in main.find_children("*","CanvasLayer",true,false):(layer as CanvasLayer).visible=false
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	var points:Array=[Vector2(0,-42),Vector2(0,-33),Vector2(0,-25),Vector2(0,-17),
		Vector2(0,0),Vector2(0,22),Vector2(-10,30),Vector2(-19,30),Vector2(-26,25),
		Vector2(-26,0),Vector2(-26,-20),Vector2(-26,-30),Vector2(-26,-35),
		Vector2(-26,-28),Vector2(-26,-20),Vector2(-26,0),Vector2(-26,25),
		Vector2(-19,30),Vector2(-10,30),Vector2(10,30),Vector2(19,30),Vector2(26,25),
		Vector2(26,0),Vector2(26,-20),Vector2(26,-30),Vector2(26,-35),
		Vector2(26,-28),Vector2(26,-20),Vector2(26,0),Vector2(26,25),
		Vector2(19,30),Vector2(10,30),Vector2(-10,30),Vector2(-10,50),Vector2(-10,75),
		Vector2(-11,90),Vector2(-11,103),Vector2(0,112),Vector2(0,117.88),
		Vector2(-23.63,117.15),Vector2(-41.46,110.11),Vector2(-51.23,100.78),
		Vector2(-106.81,45.74),Vector2(-137.23,15.02),Vector2(-145.08,7.12),
		Vector2(-151.94,2.03),Vector2(-156.56,.78),Vector2(-164.06,.67),
		Vector2(-169.57,3.32),Vector2(-188.08,18.3)]
	await follow_route("V16 uncut front > central > BOTH side loops > roofed plaza > rear exit > campus-road traversal",points)
	check("V16 uncut route ends on floor in walk mode with collision",player.mode=="walk" and not player.noclip and player.collision_mask==1 and player.is_on_floor())
	save_json(OUT_VALID+"v16_walkthrough.json",{"checks":results,"method":"One initial placement; real movement actions throughout, no teleport/fly/jump"})
