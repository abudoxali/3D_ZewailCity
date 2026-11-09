extends CanvasLayer
signal explore_requested
signal tour_requested(path_name: String)
signal mode_requested(mode: String)
signal spawn_requested(spawn_id: String)
signal quit_requested
signal lighting_requested
signal main_menu_requested
const Style := preload("res://ui/style.gd")
const Drawing := preload("res://ui/campus_drawing.gd")
var spawns: Array = []
var landmarks: Array = []
var tours: Array = []
var paused_game := false
var current_page := "main"
var root: Control
var _page_box: VBoxContainer
var _title: Label
var _subtitle: Label
var _panel: PanelContainer
var _scroll: ScrollContainer
var _hero: Control
var _footer: HBoxContainer
var _focus: Array[Control] = []

func _ready() -> void:
	layer = 10
	process_mode = Node.PROCESS_MODE_ALWAYS
	root = Control.new()
	root.name = "MenuRoot"
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.theme = Style.theme()
	add_child(root)
	var bg := ColorRect.new()
	bg.color = Style.PAPER
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(bg)
	_hero = Drawing.new()
	_hero.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_hero.anchor_right = 0.54
	_hero.offset_left = 60
	_hero.offset_top = 100
	_hero.offset_bottom = -90
	root.add_child(_hero)
	_panel = PanelContainer.new()
	_panel.add_theme_stylebox_override("panel", Style.box(Color.TRANSPARENT))
	_panel.anchor_left = 0.57
	_panel.anchor_right = 0.94
	_panel.anchor_top = 0.09
	_panel.anchor_bottom = 0.86
	root.add_child(_panel)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	_panel.add_child(v)
	_title = Label.new()
	_title.add_theme_font_size_override("font_size", 48)
	v.add_child(_title)
	_subtitle = Label.new()
	_subtitle.add_theme_font_size_override("font_size", 24)
	_subtitle.add_theme_color_override("font_color", Style.MUTED)
	_subtitle.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(_subtitle)
	_scroll = ScrollContainer.new()
	_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.follow_focus = true
	v.add_child(_scroll)
	_page_box = VBoxContainer.new()
	_page_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_page_box.add_theme_constant_override("separation", 10)
	_scroll.add_child(_page_box)
	_footer = HBoxContainer.new()
	_footer.anchor_left = 0.57
	_footer.anchor_right = 0.94
	_footer.anchor_top = 0.89
	_footer.anchor_bottom = 0.96
	_footer.add_theme_constant_override("separation", 18)
	root.add_child(_footer)
	var tag := Label.new()
	tag.text = "v" + str(ProjectSettings.get_setting("application/config/version", ""))
	tag.add_theme_font_size_override("font_size", 14)
	tag.add_theme_color_override("font_color", Style.MUTED)
	root.add_child(tag)
	tag.anchor_top = 1
	tag.anchor_bottom = 1
	tag.offset_left = 84
	tag.offset_right = 240
	tag.offset_top = -48
	tag.offset_bottom = -2
	L10n.language_changed.connect(func(): show_page(current_page))
	show_page("main")

func open(as_pause: bool) -> void:
	paused_game = as_pause
	visible = true
	show_page("main")

func close() -> void:
	visible = false

func _clear() -> void:
	_focus.clear()
	for parent in [_page_box, _footer]:
		for child in parent.get_children():
			parent.remove_child(child)
			child.queue_free()

func _button(key: String, cb: Callable, primary := false, node_name := "") -> Button:
	var b := Button.new()
	b.text = L10n.t(key)
	if not node_name.is_empty():
		b.name = node_name
		b.icon = Style.icon(node_name, primary)
		b.icon_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		b.add_theme_constant_override("h_separation", 18)
	b.custom_minimum_size.y = 78 if primary else 62
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.add_theme_font_size_override("font_size", 27 if primary else 24)
	if primary:
		b.add_theme_stylebox_override("normal", Style.box(Style.BLUE))
		b.add_theme_stylebox_override("hover", Style.box(Color("0a5675")))
		b.add_theme_stylebox_override("pressed", Style.box(Style.INK))
		b.add_theme_stylebox_override("normal_mirrored", Style.box(Style.BLUE))
		b.add_theme_stylebox_override("hover_mirrored", Style.box(Color("0a5675")))
		b.add_theme_stylebox_override("pressed_mirrored", Style.box(Style.INK))
		b.add_theme_stylebox_override("focus", Style.box(Color.TRANSPARENT, 10, Color("8fc5d4")))
		for state in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
			b.add_theme_color_override(state, Color.WHITE)
	b.pressed.connect(cb)
	_page_box.add_child(b)
	_focus.append(b)
	return b

func _text(text: String, font_size := 23) -> Label:
	var l := Label.new()
	l.text = text
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_font_size_override("font_size", font_size)
	_page_box.add_child(l)
	return l

func _footer_button(key: String, cb: Callable) -> void:
	var b := Button.new()
	b.text = L10n.t(key)
	b.flat = true
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.pressed.connect(cb)
	_footer.add_child(b)
	_focus.append(b)

func show_page(page: String) -> void:
	current_page = "graphics" if page == "settings" else page
	_clear()
	root.layout_direction = L10n.direction()
	var main := current_page == "main"
	_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED if main else ScrollContainer.SCROLL_MODE_SHOW_ALWAYS
	_hero.visible = main
	var rtl := L10n.language == "ar"
	_hero.anchor_left = 0.46 if rtl else 0.0
	_hero.anchor_right = 1.0 if rtl else 0.54
	_hero.offset_right = -60
	_panel.anchor_left = (0.06 if rtl else 0.57) if main else 0.17
	_panel.anchor_right = (0.43 if rtl else 0.94) if main else 0.83
	_footer.anchor_left = 0.06 if rtl else 0.57
	_footer.anchor_right = 0.43 if rtl else 0.94
	_title.text = L10n.t("app.title" if main else "menu." + current_page)
	_subtitle.text = ""
	_scroll.scroll_vertical = 0
	match current_page:
		"main":
			_title.text = L10n.t("menu.pause" if paused_game else "app.title")
			_subtitle.text = L10n.t("menu.pause_sub" if paused_game else "app.subtitle")
			if not paused_game:
				_text(L10n.t("app.description"), 22)
			_button("menu.resume" if paused_game else "menu.start", func(): explore_requested.emit(), true, "StartExploration")
			if not paused_game:
				_button("menu.tour", func(): tour_requested.emit("TOUR_Guided"), false, "GuidedTour")
			_button("menu.locations", func(): show_page("locations"), false, "LocationSelection")
			_button("menu.settings", func(): show_page("graphics"), false, "GraphicsSettings")
			if paused_game:
				_button("menu.help", func(): show_page("help"))
				_button("menu.home", func(): main_menu_requested.emit(); open(false))
			_button("menu.exit", func(): quit_requested.emit(), false, "Exit")
			_footer_button("menu.help", func(): show_page("help"))
			_footer_button("menu.more", func(): show_page("more"))
		"graphics":
			_title.text = L10n.t("menu.settings")
			_subtitle.text = L10n.t("settings.subtitle")
			_settings()
		"locations":
			_subtitle.text = L10n.t("locations.subtitle")
			_text(L10n.t("locations.spawns"), 28)
			for s in spawns:
				var id := String(s.id)
				_button("", func(): spawn_requested.emit(id)).text = L10n.location(id, s.label)
			_text(L10n.t("locations.landmarks"), 28)
			for lm in landmarks:
				if String(lm.get("spawn", "")).is_empty():
					continue
				var id := String(lm.spawn)
				_button("", func(): spawn_requested.emit(id)).text = L10n.location(lm.id, lm.label)
		"help":
			_subtitle.text = L10n.t("help.subtitle")
			for row in Controls.HELP:
				var h := HBoxContainer.new()
				h.custom_minimum_size.y = 48
				var desc := Label.new()
				desc.text = L10n.t(row[1])
				desc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
				var key := Label.new()
				key.text = Controls.help_binding(row[0])
				key.layout_direction = Control.LAYOUT_DIRECTION_LTR
				key.text_direction = Control.TEXT_DIRECTION_LTR
				key.add_theme_color_override("font_color", Style.BLUE)
				h.add_child(desc)
				h.add_child(key)
				_page_box.add_child(h)
		"more":
			for entry in [["camera","menu.camera"],["tours","menu.cinematics"],["help","menu.help"],["about","menu.about"]]:
				var target: String = entry[0]
				_button(entry[1], func(): show_page(target))
			_button("menu.evening", func(): lighting_requested.emit())
		"camera":
			_button("hud.walk", func(): mode_requested.emit("walk"))
			_button("hud.fly_mode", func(): mode_requested.emit("fly"))
		"tours":
			_title.text = L10n.t("menu.cinematics")
			_subtitle.text = L10n.t("hud.tour_hints")
			for tour in tours:
				var id := String(tour)
				_button("", func(): tour_requested.emit(id)).text = L10n.tour_name(id)
		"about":
			_text(L10n.t("menu.about_text"))
	if not main:
		_footer_button("menu.back", func(): show_page("main"))
	_footer_button("menu.navigation", func(): pass)
	_footer.get_child(_footer.get_child_count() - 1).focus_mode = Control.FOCUS_NONE
	_focus.pop_back()
	_wire_focus.call_deferred()

func _wire_focus() -> void:
	_page_box.queue_sort()
	_scroll.queue_sort()
	if _focus.is_empty():
		return
	for i in _focus.size():
		var c := _focus[i]
		c.focus_neighbor_top = c.get_path_to(_focus[posmod(i - 1, _focus.size())])
		c.focus_neighbor_bottom = c.get_path_to(_focus[(i + 1) % _focus.size()])
		c.focus_previous = c.focus_neighbor_top
		c.focus_next = c.focus_neighbor_bottom
	_focus[0].grab_focus()

func _input(event: InputEvent) -> void:
	if not visible: return
	if event.is_action_pressed("pause") or event.is_action_pressed("ui_cancel"):
		if current_page != "main":
			show_page("main")
			get_viewport().set_input_as_handled()
		elif paused_game:
			explore_requested.emit()
			get_viewport().set_input_as_handled()
	elif current_page == "help" and (event.is_action_pressed("ui_down") or event.is_action_pressed("ui_up")):
		_scroll.scroll_vertical += 60 if event.is_action_pressed("ui_down") else -60
		get_viewport().set_input_as_handled()
	elif event is InputEventKey and event.pressed and event.keycode in [KEY_PAGEDOWN,KEY_PAGEUP,KEY_HOME,KEY_END]:
		match event.keycode:
			KEY_PAGEDOWN: _scroll.scroll_vertical += 500
			KEY_PAGEUP: _scroll.scroll_vertical -= 500
			KEY_HOME: _scroll.scroll_vertical = 0
			KEY_END: _scroll.scroll_vertical = 100000
		get_viewport().set_input_as_handled()

func _row(key: String, control: Control) -> void:
	var h := HBoxContainer.new()
	h.custom_minimum_size.y = 62
	h.add_theme_constant_override("separation", 28)
	var label := Label.new()
	label.text = L10n.t(key)
	label.custom_minimum_size.x = 380
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(label)
	control.custom_minimum_size.x = 410
	h.add_child(control)
	_page_box.add_child(h)
	_focus.append(control)

func _option(key: String, labels: Array, values: Array, selected, cb: Callable) -> void:
	var o := OptionButton.new()
	if key in ["settings.resolution","settings.fps_limit"]:
		o.text_direction = Control.TEXT_DIRECTION_LTR
	for label in labels:
		o.add_item(str(label))
	o.select(maxi(values.find(selected), 0))
	o.item_selected.connect(func(i): cb.call(values[i]))
	_row(key, o)

func _slider(key: String, lo: float, hi: float, step: float, value: float, field: String, multiplier := 1.0) -> void:
	var h := HBoxContainer.new()
	var slider := HSlider.new()
	slider.min_value = lo
	slider.max_value = hi
	slider.step = step
	slider.value = value
	slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var number := Label.new()
	number.custom_minimum_size.x = 80
	number.layout_direction = Control.LAYOUT_DIRECTION_LTR
	number.text_direction = Control.TEXT_DIRECTION_LTR
	number.text = "%.2f" % value
	h.add_child(slider)
	h.add_child(number)
	slider.value_changed.connect(func(v): number.text = "%.2f" % v; Settings.update(field, v * multiplier))
	_row(key, h)
	_focus.pop_back()
	_focus.append(slider)

func _check(key: String, field: String) -> void:
	var cb := CheckBox.new()
	cb.text = L10n.t(key)
	cb.button_pressed = bool(Settings.get(field))
	cb.custom_minimum_size.y = 62
	cb.toggled.connect(func(v): Settings.update(field, v))
	_page_box.add_child(cb)
	_focus.append(cb)

func _settings() -> void:
	_text(L10n.t("settings.display"), 28)
	var resolutions: Array = [Vector2i(1280,720),Vector2i(1600,900),Vector2i(1920,1080),Vector2i(2560,1440)]
	for res in [Settings.resolution, DisplayServer.window_get_size()]:
		if res.x > 0 and res not in resolutions:
			resolutions.append(res)
	var names: Array = []
	for res in resolutions:
		names.append("%d × %d" % [res.x,res.y])
	_option("settings.resolution", names, resolutions, Settings.resolution, func(v): Settings.update("resolution",v))
	_option("settings.display_mode", [L10n.t("settings.windowed"),L10n.t("settings.borderless"),L10n.t("settings.exclusive")], [0,1,2], Settings.display_mode, func(v): Settings.update("display_mode",v))
	_option("settings.vsync", [L10n.t("settings.off"),L10n.t("settings.on"),L10n.t("settings.adaptive")], [0,1,2], Settings.vsync, func(v): Settings.update("vsync",v))
	_option("settings.fps_limit", [L10n.t("settings.off"),"30","60","120","144","240"], [0,30,60,120,144,240], Settings.fps_limit, func(v): Settings.update("fps_limit",v))
	_text(L10n.t("settings.graphics"), 28)
	var qualities: Array = ["Low","Medium","High","Ultra"]
	var labels: Array = []
	for q in qualities:
		labels.append(L10n.t("quality."+q))
	_option("settings.preset", labels, qualities, Settings.preset, func(v): Settings.set_preset(v))
	_option("settings.shadow", [L10n.t("settings.preset_shadow")]+labels.slice(0,3), ["Preset","Low","Medium","High"], Settings.shadow_quality, func(v): Settings.update("shadow_quality",v))
	_text(L10n.t("settings.input"), 28)
	_slider("settings.sensitivity",0.5,6.0,0.1,Settings.mouse_sensitivity*1000,"mouse_sensitivity",0.001)
	_slider("settings.speed",0.25,3.0,0.05,Settings.move_speed,"move_speed")
	_slider("settings.fov",60,100,1,Settings.fov,"fov")
	_check("settings.invert","invert_y")
	_check("settings.performance","show_fps")
	_option("settings.language",["عربي","English"],["ar","en"],Settings.language,func(v): Settings.update("language",v))
