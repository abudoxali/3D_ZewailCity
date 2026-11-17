extends "res://tests/v5_ground.gd"
func run_validation() -> void:
	main._start_explore()
	for side in [-1.,1.]:
		var points=load("res://tests/v17_routes.gd").rear_gallery(side)
		await follow_route("V18 rear opening > continuous Academic glass gallery "+str(side),points)
		points.reverse()
		await follow_route("V18 gallery returns through the same physical opening "+str(side),points,false)
	var local_floor:float=.21+datum_at(-37.8,314.5)
	check("V18 gallery has real lower floor",not ray(Vector3(-37.8,local_floor+.5,314.5),Vector3(-37.8,local_floor-.5,314.5)).is_empty())
	check("V18 gallery plaster soffit is real",not ray(Vector3(-37.8,local_floor+2.0,314.5),Vector3(-37.8,local_floor+4.,314.5)).is_empty())
	save_json(OUT_VALID+"v18_gallery.json",{"checks":results,"note":"Photo-supported corridor vocabulary; exact plan/level/dimensions remain an estimated interpretation"})
