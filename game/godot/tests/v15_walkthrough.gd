extends Node
## V15 pilot walkthrough: a scripted eye-level camera (1.65 m above the actual floor) from outside
## Gate G1, through the gate lane, down the main approach past the kerbs, verge beds, crossover
## bands and palm median, to the Administration forecourt. Record with Godot Movie Maker:
##   godot --path game/godot --resolution 1920x1080 --fixed-fps 30 --write-movie out.avi res://tests/V15Walkthrough.tscn
## Blender (x, y) waypoints; Godot = (x, floor + eye, -y).
const PATH := [Vector2(-15.0, 356.0), Vector2(-11.0, 336.0), Vector2(-9.45, 318.0), Vector2(-8.6, 300.0),
	Vector2(-7.2, 282.0), Vector2(-6.4, 262.0), Vector2(-7.6, 236.0), Vector2(-8.2, 205.0), Vector2(-7.8, 175.0),
	Vector2(-6.5, 145.0), Vector2(-5.5, 118.0), Vector2(-3.0, 96.0), Vector2(0.0, 74.0), Vector2(0.0, 52.0)]
const SECONDS := 52.0
const FPS := 30.0
const EYE := 1.65
var main: Node3D
var cam: Camera3D
var pts: Array[Vector3] = []

func _ready() -> void:
	main = load("res://scenes/Main.tscn").instantiate()
	add_child(main)
	while not main.ready_done:
		await get_tree().process_frame
	main.set_process_unhandled_input(false)
	main.player.set_process_unhandled_input(false)
	main._start_explore()
	for c in main.find_children("*", "CanvasLayer", true, false):
		(c as CanvasLayer).visible = false
	cam = Camera3D.new()
	cam.near = 0.08
	cam.far = 6000.0
	cam.fov = Settings.fov
	add_child(cam)
	cam.make_current()
	for p in PATH:
		var g = main.campus.ground_at(p.x, -p.y, 12.0)
		pts.append(Vector3(p.x, (g.y if g != null else 0.1) + EYE, -p.y))
	var curve := Curve3D.new()
	for i in pts.size():
		var a: Vector3 = pts[max(i - 1, 0)]
		var b: Vector3 = pts[min(i + 1, pts.size() - 1)]
		var tan := (b - a) * 0.25
		curve.add_point(pts[i], -tan, tan)
	curve.bake_interval = 0.2
	var length := curve.get_baked_length()
	var frames := int(SECONDS * FPS)
	for i in 20:
		await get_tree().process_frame
	for f in frames:
		var t := float(f) / float(frames - 1)
		var e := t * t * (3.0 - 2.0 * t) * 0.35 + t * 0.65   # gentle ease in/out
		var d := e * length
		var pos := curve.sample_baked(d)
		var ahead := curve.sample_baked(min(d + 14.0, length))
		var look := Vector3(ahead.x, pos.y - 0.9, ahead.z)
		if look.distance_to(pos) < 0.5:
			look = pos + Vector3(0, -0.3, -1)
		cam.make_current()
		cam.global_transform = Transform3D(Basis(), pos).looking_at(look, Vector3.UP)
		await get_tree().process_frame
	get_tree().quit(0)
