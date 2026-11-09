extends Control
## Top-down orientation map. The background is rendered once from an
## orthographic camera at startup (no per-frame cost); the player arrow,
## spawn numbers and landmark dots are drawn on top. Clicking a landmark
## dot asks main.gd to teleport to that landmark's spawn.

signal landmark_clicked(landmark: Dictionary)

## Map window in Godot world coordinates (x, z): centred between the gate and the academic ring.
var centre := Vector2(0, 180)
var extent := 1200.0
var texture: Texture2D
var player: Node3D
var landmarks: Array = []
var spawns: Array = []
var expanded := false

func _ready() -> void:
	layout_direction = L10n.direction()
	L10n.language_changed.connect(func(): layout_direction = L10n.direction(); queue_redraw())


func render_background(world_parent: Node) -> void:
	if DisplayServer.get_name() == "headless":
		return   # no renderer: frame_post_draw never fires
	var vp := SubViewport.new()
	vp.size = Vector2i(768, 768)
	vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	vp.msaa_3d = Viewport.MSAA_4X
	var cam := Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = extent
	cam.near = 1.0
	cam.far = 2000.0
	cam.position = Vector3(centre.x, 900.0, centre.y)
	cam.rotation_degrees = Vector3(-90, 0, 0)
	vp.add_child(cam)
	world_parent.add_child(vp)
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var img := vp.get_texture().get_image()
	texture = ImageTexture.create_from_image(img)
	vp.queue_free()
	queue_redraw()


func world_to_map(p: Vector3) -> Vector2:
	var u := (p.x - (centre.x - extent * 0.5)) / extent
	var v := (p.z - (centre.y - extent * 0.5)) / extent
	return Vector2(u, v) * size


func _process(_dt: float) -> void:
	if visible:
		queue_redraw()


func _draw() -> void:
	var r := Rect2(Vector2.ZERO, size)
	draw_rect(r, Color(0.08, 0.09, 0.1, 0.85))
	if texture:
		draw_texture_rect(texture, r, false, Color(1, 1, 1, 0.95))
	draw_rect(r, Color(1, 1, 1, 0.5), false, 1.5)
	var font := get_theme_default_font()
	for l in landmarks:
		var m := world_to_map(l.position)
		var gate := String(l.id)=="LM_Main_Gate" or String(l.id).begins_with("LM_Gate_")
		var col := Color(1.0, 0.78, 0.25) if l.verified else Color(0.75, 0.75, 0.75)
		if gate:
			col=Color(0.3,0.95,1.0) if l.verified else Color(1.,.65,.15)
			draw_rect(Rect2(m-Vector2(5,5),Vector2(10,10)),col,false,1.5)
			draw_string(font,m+Vector2(7,-5),"G1" if l.id=="LM_Main_Gate" else String(l.id).trim_prefix("LM_Gate_"),HORIZONTAL_ALIGNMENT_LEFT,-1,12,col)
		elif String(l.id).begins_with("LM_Building_"):
			col=Color(.83,.52,1.)
			draw_string(font,m+Vector2(7,-5),"B-"+String(l.id).trim_prefix("LM_Building_"),HORIZONTAL_ALIGNMENT_LEFT,-1,12,col)
		draw_circle(m, 4.5, Color(0, 0, 0, 0.6))
		draw_circle(m, 3.2, col)
		if expanded:
			_draw_shaped(L10n.location(l.id, l.label), m + Vector2(6,4), 14)
	for i in spawns.size():
		if i>=7:
			continue # New gates already have their G identifiers and clickable landmark.
		var m := world_to_map(spawns[i].position)
		draw_string(font, m + Vector2(-4, 5), str(i + 1), HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color(0.6, 0.95, 1.0))
	if player and is_instance_valid(player):
		var p := world_to_map(player.global_position)
		var fwd := -player.global_transform.basis.z
		var ang := atan2(fwd.z, fwd.x)
		var pts := PackedVector2Array([
			p + Vector2(cos(ang), sin(ang)) * 9.0,
			p + Vector2(cos(ang + 2.5), sin(ang + 2.5)) * 6.0,
			p + Vector2(cos(ang - 2.5), sin(ang - 2.5)) * 6.0,
		])
		draw_colored_polygon(pts, Color(1, 0.2, 0.2))
	_draw_shaped(L10n.t("map.gate"), Vector2(8,22), 16)

func _draw_shaped(text: String, pos: Vector2, font_size: int) -> void:
	var line := TextLine.new()
	line.direction = TextServer.DIRECTION_RTL if L10n.language == "ar" else TextServer.DIRECTION_LTR
	line.add_string(text, get_theme_default_font(), font_size)
	line.draw(get_canvas_item(), pos, Color.WHITE)


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var best := {}
		var best_d := 14.0
		for l in landmarks:
			var d := world_to_map(l.position).distance_to(event.position)
			if d < best_d:
				best_d = d
				best = l
		if not best.is_empty():
			landmark_clicked.emit(best)
			accept_event()
