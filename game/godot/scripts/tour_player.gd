extends Node3D
## Plays a camera path exported from Blender by src/export_camera_paths.py
## (res://assets/tours/<NAME>.json). Samples are per frame at the path's fps;
## positions and view vectors are interpolated between samples.
##
## Edit a path in Blender, run export_camera_paths.py, restart the explorer:
## the campus itself does not need rebuilding or re-importing.

signal label_changed(text: String)
signal finished(name: String)
signal paused_changed(paused: bool)

const TOUR_DIR := "res://assets/tours/"

var camera: Camera3D
var data: Dictionary = {}
var samples: Array = []
var labels: Array = []
var fps := 30.0
var duration := 0.0
var t := 0.0
var playing := false
var paused := false
var speed := 1.0
var current_name := ""
var _label := ""


func _ready() -> void:
	camera = Camera3D.new()
	camera.name = "TourCamera"
	camera.near = 0.1
	camera.far = 6000.0
	add_child(camera)


static func available() -> Array:
	var out: Array = []
	var idx := TOUR_DIR + "index.json"
	if FileAccess.file_exists(idx):
		var d = JSON.parse_string(FileAccess.get_file_as_string(idx))
		if d is Array:
			for e in d:
				out.append(String(e.name))
	return out


func load_path(path_name: String) -> bool:
	var p := TOUR_DIR + path_name + ".json"
	if not FileAccess.file_exists(p):
		push_error(L10n.t("error.tour_missing", [p]))
		return false
	var d = JSON.parse_string(FileAccess.get_file_as_string(p))
	if not (d is Dictionary) or not d.has("samples"):
		push_error(L10n.t("error.tour_invalid", [p]))
		return false
	data = d
	samples = d.samples
	labels = d.get("labels", [])
	fps = float(d.get("fps", 30))
	duration = float(samples[-1][0])
	camera.fov = float(d.get("fov_v_deg", 50.0))
	current_name = path_name
	return true


func start(path_name: String) -> bool:
	if not load_path(path_name):
		return false
	t = 0.0
	playing = true
	paused = false
	_label = ""
	camera.make_current()
	_apply(0.0)
	return true


func stop(emit := true) -> void:
	if not playing:
		return
	playing = false
	camera.clear_current(false)
	if emit:
		finished.emit(current_name)


func toggle_pause() -> void:
	if playing:
		paused = not paused
		paused_changed.emit(paused)


func _process(delta: float) -> void:
	if not playing or paused:
		return
	t += delta * speed
	if t >= duration:
		_apply(duration)
		stop(true)
		return
	_apply(t)


func transform_at(time: float) -> Transform3D:
	var f: float = clamp(time * fps, 0.0, samples.size() - 1.0)
	var i := int(floor(f))
	var j: int = min(i + 1, samples.size() - 1)
	var a := f - i
	var s0: Array = samples[i]
	var s1: Array = samples[j]
	var p := Vector3(s0[1], s0[2], s0[3]).lerp(Vector3(s1[1], s1[2], s1[3]), a)
	var fw := Vector3(s0[4], s0[5], s0[6]).lerp(Vector3(s1[4], s1[5], s1[6]), a).normalized()
	var up := Vector3(s0[7], s0[8], s0[9]).lerp(Vector3(s1[7], s1[8], s1[9]), a).normalized()
	return Transform3D(Basis.looking_at(fw, up), p)


func label_at(time: float) -> String:
	var text := ""
	for l in labels:
		if float(l[0]) <= time + 0.0001:
			text = String(l[1])
	return L10n.source(text)


func _apply(time: float) -> void:
	camera.global_transform = transform_at(time)
	var text := label_at(time)
	if text != _label:
		_label = text
		label_changed.emit(text)
