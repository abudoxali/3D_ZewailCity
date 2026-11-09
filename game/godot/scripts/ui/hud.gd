extends CanvasLayer
## In-game overlay: location name, movement mode, compact hints, FPS,
## tour caption, toast messages and the minimap.

const MiniMap := preload("res://scripts/ui/minimap.gd")

var location_label: Label
var location_sub: Label
var mode_label: Label
var hint_label: Label
var fps_label: Label
var tour_caption: Label
var toast: Label
var crosshair: Control
var minimap: Control
var _toast_time := 0.0
var interaction_prompt: Label
var _prompt_panel: PanelContainer
var _loading: Label
var _location_text := ""
var _location_note := ""


func _ready() -> void:
	layer = 5
	add_to_group("hud")
	var root := Control.new()
	root.name = "HudRoot"
	root.layout_direction = L10n.direction()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)

	var box := PanelContainer.new()
	_place(box, Vector4(1,0,1,0), Vector4(-560,24,-24,200))
	box.add_theme_stylebox_override("panel", _panel_style(0.55))
	root.add_child(box)
	var v := VBoxContainer.new()
	box.add_child(v)
	location_label = _label(28, Color.WHITE)
	location_sub = _label(19, Color(0.85, 0.85, 0.85))
	mode_label = _label(20, Color(0.6, 0.95, 1.0))
	v.add_child(location_label)
	v.add_child(location_sub)
	v.add_child(mode_label)

	hint_label = _label(22, Color(1, 1, 1, 0.95))
	_place(hint_label, Vector4(0.1, 1, 0.9, 1), Vector4(0, -80, 0, -18))
	hint_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	root.add_child(hint_label)

	tour_caption = _label(30, Color.WHITE)
	_place(tour_caption, Vector4(0.5, 1, 0.5, 1), Vector4(-800, -140, 800, -84))
	tour_caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tour_caption.add_theme_constant_override("outline_size", 8)
	tour_caption.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.75))
	root.add_child(tour_caption)

	toast = _label(18, Color(1, 0.95, 0.7))
	_place(toast, Vector4(0.5, 0, 0.5, 0), Vector4(-600, 30, 600, 60))
	toast.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	toast.add_theme_constant_override("outline_size", 6)
	toast.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	root.add_child(toast)

	minimap = MiniMap.new()
	_place(minimap, Vector4(0,0,0,0), Vector4(24,24,284,284))
	root.add_child(minimap)

	fps_label = _label(19, Color(0.9, 1, 0.9))
	_place(fps_label, Vector4(0,0,0,0), Vector4(24,290,530,334))
	fps_label.add_theme_constant_override("outline_size", 5)
	fps_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	hint_label.add_theme_constant_override("outline_size", 5)
	hint_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	fps_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	root.add_child(fps_label)

	crosshair = Control.new()
	_place(crosshair, Vector4(0.5, 0.5, 0.5, 0.5), Vector4.ZERO)
	crosshair.mouse_filter = Control.MOUSE_FILTER_IGNORE
	crosshair.draw.connect(func(): crosshair.draw_circle(Vector2.ZERO, 2.5, Color(1, 1, 1, 0.7)))
	root.add_child(crosshair)
	_prompt_panel = PanelContainer.new()
	_prompt_panel.name = "InteractionPrompt"
	_place(_prompt_panel, Vector4(0.5,1,0.5,1), Vector4(-380,-235,380,-165))
	_prompt_panel.add_theme_stylebox_override("panel", _panel_style(0.94))
	_prompt_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	interaction_prompt = _label(27, Color.WHITE)
	interaction_prompt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	interaction_prompt.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_prompt_panel.add_child(interaction_prompt)
	root.add_child(_prompt_panel)
	_prompt_panel.hide()
	_loading = _label(30, Color.WHITE)
	_place(_loading, Vector4(0.2,0.4,0.8,0.6), Vector4.ZERO)
	_loading.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	root.add_child(_loading)
	_loading.hide()
	L10n.language_changed.connect(func():
		root.layout_direction = L10n.direction()
		set_location(_location_text, _location_note)
		_loading.text = L10n.t("loading"))

func set_interaction_prompt(text: String) -> void:
	interaction_prompt.text = text
	_prompt_panel.visible = not text.is_empty()

func clear_interaction_prompt() -> void:
	interaction_prompt.text = ""
	_prompt_panel.hide()

func show_loading() -> void:
	visible = true
	for child in get_node("HudRoot").get_children():
		child.hide()
	_loading.text = L10n.t("loading")
	_loading.show()

func hide_loading() -> void:
	for child in get_node("HudRoot").get_children():
		child.show()
	_loading.hide()
	_prompt_panel.hide()


static func _place(c: Control, anchors: Vector4, offsets: Vector4) -> void:
	c.anchor_left = anchors.x
	c.anchor_top = anchors.y
	c.anchor_right = anchors.z
	c.anchor_bottom = anchors.w
	c.offset_left = offsets.x
	c.offset_top = offsets.y
	c.offset_right = offsets.z
	c.offset_bottom = offsets.w


func _label(sz: int, col: Color) -> Label:
	var l := Label.new()
	l.add_theme_font_size_override("font_size", sz)
	l.add_theme_color_override("font_color", col)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


static func _panel_style(alpha: float) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = Color(0.05, 0.06, 0.08, alpha)
	s.set_corner_radius_all(6)
	s.content_margin_left = 14
	s.content_margin_right = 14
	s.content_margin_top = 8
	s.content_margin_bottom = 8
	return s


func set_location(text: String, sub := "") -> void:
	_location_text = text
	_location_note = sub
	location_label.text = L10n.source(text)
	location_sub.text = L10n.source(sub)
	location_sub.visible = sub != ""


func set_mode(text: String) -> void:
	mode_label.text = text


func set_hints(text: String) -> void:
	hint_label.text = text


func set_tour_caption(text: String) -> void:
	tour_caption.text = text


func show_toast(text: String, seconds := 2.5) -> void:
	toast.text = text
	toast.modulate.a = 1.0
	_toast_time = seconds


func set_exploring(on: bool) -> void:
	crosshair.visible = on
	minimap.visible = on and minimap.get_meta("user_visible", true)
	if not on:
		clear_interaction_prompt()


func _process(delta: float) -> void:
	if _toast_time > 0.0:
		_toast_time -= delta
		toast.modulate.a = clamp(_toast_time / 0.6, 0.0, 1.0)
	if Settings.show_fps:
		fps_label.visible = true
		var fps := Engine.get_frames_per_second()
		fps_label.text = L10n.t("hud.performance", [str(int(fps)), "%.1f" % (delta * 1000.0)])
	else:
		fps_label.visible = false
