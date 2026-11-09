extends Node
## Isolated contract and rendered UI verification. No campus or bridge dependency.
@export var capture_only := false
const Menu := preload("res://scripts/ui/menu.gd")
const Hud := preload("res://scripts/ui/hud.gd")
const Style := preload("res://ui/style.gd")
var results: Array = []
var evidence := "res://../../output/validation/v11/final/ui/"
var _changed_count := 0

func check(label: String, passed: bool) -> void:
	results.append({"name":label, "pass":passed})
	print(("[PASS] " if passed else "[FAIL] ") + label)

func settle() -> void:
	for i in 5:
		await get_tree().process_frame

func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(evidence))
	L10n.set_language("ar")
	if capture_only:
		if DisplayServer.get_name() == "headless":
			push_error("Rendered captures require a windowed renderer.")
			get_tree().quit(1)
			return
		await captures()
	else:
		await contracts()
	var failed := results.filter(func(r): return not r["pass"]).size()
	var report := {"passed":results.size()-failed,"failed":failed,"results":results,"renderer":RenderingServer.get_video_adapter_name(),"headless":DisplayServer.get_name()=="headless"}
	var output := FileAccess.open(evidence + ("capture_summary.json" if capture_only else "v11_ui.json"), FileAccess.WRITE)
	output.store_string(JSON.stringify(report,"  "))
	output.close()
	print("[v11_ui] " + JSON.stringify(report))
	get_tree().quit(0 if failed == 0 else 1)

func fixture(menu: CanvasLayer) -> void:
	var manifest = JSON.parse_string(FileAccess.get_file_as_string("res://assets/campus/campus_manifest.json"))
	menu.spawns = manifest.spawn_points
	menu.landmarks = manifest.landmarks
	menu.tours = preload("res://scripts/tour_player.gd").available()

func _signal_changed() -> void:
	_changed_count += 1

func contracts() -> void:
	get_tree().root.size = Vector2i(1920,1080)
	get_tree().root.content_scale_size = Vector2i(1920,1080)
	get_tree().root.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	await settle()
	var menu := Menu.new()
	add_child(menu)
	fixture(menu)
	await settle()
	check("menu builds and defaults to RTL", menu.root.layout_direction == Control.LAYOUT_DIRECTION_RTL)
	for name in ["StartExploration","GuidedTour","LocationSelection","GraphicsSettings","Exit"]:
		var button := menu._page_box.get_node_or_null(name) as Button
		check("main action focusable: " + name, button != null and button.focus_mode == Control.FOCUS_ALL)
	check("exactly five main actions", menu._page_box.find_children("*","Button",true,false).size()==5)
	check("first action receives focus", menu._page_box.get_node("StartExploration").has_focus())
	var next := InputEventAction.new()
	next.action = "ui_down"
	next.pressed = true
	Input.parse_input_event(next)
	await settle()
	check("keyboard down moves focus", menu._page_box.get_node("GuidedTour").has_focus())
	var release := InputEventAction.new()
	release.action = "ui_down"
	release.pressed = false
	Input.parse_input_event(release)
	var tour_selected: Array = []
	menu.tour_requested.connect(func(id): tour_selected.append(id))
	var accept := InputEventKey.new()
	accept.keycode = KEY_ENTER
	accept.physical_keycode = KEY_ENTER
	accept.pressed = true
	Input.parse_input_event(accept)
	await settle()
	accept = InputEventKey.new()
	accept.keycode = KEY_ENTER
	accept.physical_keycode = KEY_ENTER
	accept.pressed = false
	Input.parse_input_event(accept)
	await settle()
	check("Enter activates focused tour action", tour_selected == ["TOUR_Guided"])
	var explored: Array = []
	menu.explore_requested.connect(func(): explored.append(true))
	var click_position: Vector2 = menu._page_box.get_node("StartExploration").get_global_rect().get_center()
	for pressed in [true,false]:
		var mouse := InputEventMouseButton.new()
		mouse.button_index=MOUSE_BUTTON_LEFT
		mouse.position=click_position
		mouse.global_position=click_position
		mouse.pressed=pressed
		Input.parse_input_event(mouse)
		await settle()
	check("mouse click activates exploration", explored == [true])
	var glyphs_ok := true
	var catalog_ok := true
	for key in L10n.TEXT:
		var pair: Array = L10n.TEXT[key]
		catalog_ok = catalog_ok and pair.size()==2 and not str(pair[0]).is_empty() and not str(pair[1]).is_empty()
		for i in str(pair[0]).length():
			var code := str(pair[0]).unicode_at(i)
			if code >= 0x0600 and code <= 0x06ff:
				glyphs_ok = glyphs_ok and Style.FONT.has_char(code)
	check("every catalog entry has Arabic and English", catalog_ok)
	check("Noto Arabic font has all Arabic catalog glyphs", glyphs_ok)
	var assets_localized := true
	for item in menu.spawns + menu.landmarks:
		assets_localized = assets_localized and L10n.TEXT.has("location." + String(item.id))
	for id in menu.tours:
		assets_localized = assets_localized and L10n.TEXT.has("tour." + String(id))
		var data = JSON.parse_string(FileAccess.get_file_as_string("res://assets/tours/" + String(id) + ".json"))
		for caption in data.get("labels",[]):
			if not String(caption[1]).is_empty():
				assets_localized = assets_localized and L10n.TEXT.has("source." + String(caption[1]))
	check("all current asset names and tour captions localized", assets_localized)
	check("gate formatting contract", L10n.t("gate.prompt_open",[L10n.t("gate.name",["G1"])])=="اضغط E لفتح البوابة G1")
	check("interact is E", InputMap.has_action("interact") and Controls.BINDINGS.interact == [KEY_E])
	for page in ["graphics","help","locations","camera","tours","more","about"]:
		menu.show_page(page)
		await settle()
		check("page builds and has focus: " + page, not menu._focus.is_empty() and menu._focus[0].has_focus())
	menu.show_page("help")
	await settle()
	var scroll_event := InputEventAction.new()
	scroll_event.action = "ui_down"
	scroll_event.pressed = true
	Input.parse_input_event(scroll_event)
	await settle()
	check("help scrolls with keyboard/controller navigation", menu._scroll.scroll_vertical > 0)
	var cancel := InputEventAction.new()
	cancel.action = "pause"
	cancel.pressed = true
	Input.parse_input_event(cancel)
	await settle()
	check("Esc returns from submenu", menu.current_page == "main")
	L10n.set_language("en")
	await settle()
	check("English changes layout and action text", menu.root.layout_direction==Control.LAYOUT_DIRECTION_LTR and menu._page_box.get_node("StartExploration").text=="Start exploration")
	L10n.set_language("ar")
	menu.open(true)
	await settle()
	check("pause exposes resume and home", menu._page_box.get_node("StartExploration").text==L10n.t("menu.resume") and menu._page_box.find_children("*","Button",true,false).size()==6)
	var resumed: Array = []
	menu.explore_requested.connect(func(): resumed.append(true))
	var pad := InputEventJoypadButton.new()
	pad.button_index = JOY_BUTTON_B
	pad.pressed = true
	Input.parse_input_event(pad)
	await settle()
	check("gamepad cancel resumes from pause", not resumed.is_empty())
	var hud := Hud.new()
	add_child(hud)
	hud.set_interaction_prompt(L10n.t("gate.prompt_open",[L10n.t("gate.pedestrian")]))
	check("HUD group and prompt API", hud.is_in_group("hud") and hud._prompt_panel.visible and hud.interaction_prompt.text.contains("E"))
	hud.clear_interaction_prompt()
	check("prompt clears", not hud._prompt_panel.visible and hud.interaction_prompt.text.is_empty())
	hud.set_interaction_prompt("")
	check("empty prompt stays hidden", not hud._prompt_panel.visible)
	hud.show_loading()
	check("localized loading indicator visible", hud._loading.visible and hud._loading.text==L10n.t("loading"))
	hud.hide_loading()
	check("loading indicator clears", not hud._loading.visible)
	var snapshot := {}
	for field in Settings.FIELDS: snapshot[field] = Settings.get(field)
	var existed := FileAccess.file_exists(Settings.PATH)
	var original := FileAccess.get_file_as_bytes(Settings.PATH) if existed else PackedByteArray()
	Settings.changed.connect(_signal_changed)
	var boot_preset := Settings.preset
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--preset="):
			check("command line preset wins", boot_preset==arg.get_slice("=",1).capitalize())
	for preset in Settings.PRESETS:
		Settings.set_preset(preset)
	check("all four presets emit changed", _changed_count == 4 and Settings.preset == "Ultra")
	Settings.resolution=Vector2i(1280,720)
	Settings.display_mode=2
	Settings.vsync=2
	Settings.fps_limit=144
	Settings.shadow_quality="Low"
	Settings.mouse_sensitivity=0.004
	Settings.move_speed=1.75
	Settings.invert_y=true
	Settings.fov=92.0
	Settings.show_fps=false
	Settings.language="en"
	var expected := {}
	for field in Settings.FIELDS: expected[field]=Settings.get(field)
	var test_path := "user://v11-roundtrip-test.cfg"
	check("settings save succeeds", Settings.save(test_path)==OK)
	for field in snapshot: Settings.set(field,snapshot[field])
	check("settings load succeeds", Settings.load_settings(test_path)==OK)
	var equal := true
	for field in expected: equal = equal and Settings.get(field)==expected[field]
	check("all settings round-trip", equal)
	check("shadow override maps atlas and distance", Settings.shadow_values().shadow_size==2048 and Settings.shadow_values().shadow_distance==220.0)
	Settings.apply_display()
	check("FPS limit applies to Engine", Engine.max_fps==144)
	menu.open(false)
	menu.show_page("graphics")
	await settle()
	var options := menu._page_box.find_children("*", "OptionButton",true,false)
	var preset_option := options[4] as OptionButton
	preset_option.item_selected.emit(1)
	check("preset UI applies real setting", Settings.preset=="Medium")
	var bad := ConfigFile.new()
	bad.set_value("graphics","preset","invalid")
	bad.set_value("input","mouse_sensitivity",-1.0)
	bad.set_value("view","fov",500.0)
	bad.set_value("view","language","invalid")
	bad.save(test_path)
	Settings.load_settings(test_path)
	check("invalid persisted settings sanitized", Settings.preset=="High" and Settings.mouse_sensitivity==0.0005 and Settings.fov==100 and Settings.language=="ar")
	for field in snapshot: Settings.set(field,snapshot[field])
	Settings.changed.disconnect(_signal_changed)
	Engine.max_fps=Settings.fps_limit
	if existed:
		var file := FileAccess.open(Settings.PATH,FileAccess.WRITE)
		file.store_buffer(original)
		file.close()
	else:
		DirAccess.remove_absolute(Settings.PATH)
	DirAccess.remove_absolute(test_path)
	L10n.set_language(snapshot.language)
	menu.queue_free()
	hud.queue_free()
	await settle()

func shot(vp: SubViewport, filename: String) -> void:
	await settle()
	await RenderingServer.frame_post_draw
	var img := vp.get_texture().get_image()
	check("capture " + filename, img.save_png(evidence+filename+".png")==OK)
	print("[capture] " + filename + " %dx%d" % [img.get_width(),img.get_height()])

func captures() -> void:
	# Fixed offscreen GPU viewport avoids Windows reducing a 1080p decorated window.
	# canvas_items logical layout matches project 1920x1080 at both physical sizes.
	for resolution in [Vector2i(1920,1080),Vector2i(1280,720),Vector2i(1366,768),Vector2i(2560,1440)]:
		var vp := SubViewport.new()
		vp.size=resolution
		vp.size_2d_override=Vector2i(1920,1080)
		vp.size_2d_override_stretch=true
		vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS
		add_child(vp)
		var preview := TextureRect.new()
		preview.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		preview.texture=vp.get_texture()
		preview.expand_mode=TextureRect.EXPAND_IGNORE_SIZE
		add_child(preview)
		var menu := Menu.new()
		vp.add_child(menu)
		fixture(menu)
		var prefix := "%dx%d_" % [resolution.x,resolution.y]
		for page in ["main","graphics","help","locations"]:
			menu.show_page(page)
			await shot(vp,prefix+page)
			if page != "main":
				menu._scroll.scroll_vertical=10000
				await shot(vp,prefix+page+"_bottom")
				print("[scroll] %s %s content=%s min=%s area=%s max=%s offset=%d" % [prefix,page,menu._page_box.size,menu._page_box.get_combined_minimum_size(),menu._scroll.size,menu._scroll.get_v_scroll_bar().max_value,menu._scroll.scroll_vertical])
				check("bottom scroll reachable " + prefix + page, menu._scroll.scroll_vertical>0)
		menu.open(true)
		await shot(vp,prefix+"pause")
		menu.close()
		var hud := Hud.new()
		vp.add_child(hud)
		hud.set_location(L10n.location("LM_Main_Gate"), L10n.t("entrance.label",["G1"]))
		hud.set_mode(L10n.t("hud.walk"))
		hud.set_hints(L10n.t("hud.walk_hints"))
		hud.set_interaction_prompt(L10n.t("gate.prompt_open",[L10n.t("gate.pedestrian")]))
		await shot(vp,prefix+"hud_prompt")
		preview.queue_free()
		vp.queue_free()
		await settle()
	await display_checks()

func display_checks() -> void:
	# Exercise the native APIs without writing the user's saved display choices.
	var old_mode := Settings.display_mode
	var old_resolution := Settings.resolution
	var old_vsync := Settings.vsync
	var old_limit := Settings.fps_limit
	var window_size := DisplayServer.window_get_size()
	var window_mode := DisplayServer.window_get_mode()
	var borderless := DisplayServer.window_get_flag(DisplayServer.WINDOW_FLAG_BORDERLESS)
	var vsync_mode := DisplayServer.window_get_vsync_mode()
	Settings.resolution=Vector2i(1280,720)
	Settings.display_mode=0
	Settings.apply_display(true)
	await settle()
	check("native window resolution applies", DisplayServer.window_get_size()==Vector2i(1280,720))
	check("native windowed mode applies", DisplayServer.window_get_mode()==DisplayServer.WINDOW_MODE_WINDOWED)
	Settings.display_mode=1
	Settings.apply_display(true)
	await settle()
	check("native borderless fullscreen applies", DisplayServer.window_get_mode()==DisplayServer.WINDOW_MODE_FULLSCREEN and DisplayServer.window_get_flag(DisplayServer.WINDOW_FLAG_BORDERLESS))
	Settings.display_mode=2
	Settings.apply_display(true)
	await settle()
	check("native exclusive fullscreen applies", DisplayServer.window_get_mode()==DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN)
	for mode in [0,1,2]:
		Settings.vsync=mode
		Settings.apply_display()
		await settle()
		check("native VSync mode %d applies" % mode, DisplayServer.window_get_vsync_mode()==mode)
	Settings.fps_limit=120
	Settings.apply_display()
	check("native FPS limit applies", Engine.max_fps==120)
	Settings.display_mode=old_mode
	Settings.resolution=old_resolution
	Settings.vsync=old_vsync
	Settings.fps_limit=old_limit
	Engine.max_fps=old_limit
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_BORDERLESS,borderless)
	DisplayServer.window_set_size(window_size)
	DisplayServer.window_set_mode(window_mode)
	DisplayServer.window_set_vsync_mode(vsync_mode)
