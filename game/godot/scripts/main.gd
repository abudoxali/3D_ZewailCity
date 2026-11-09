extends Node3D
## Zewail City Campus Explorer: scene orchestration.
##
## States: "menu" (main or pause menu), "explore" (walk / fly), "tour".
##
## Command-line options (after `--`):
##   --autotour=NAME     skip the menu and play a tour path (e.g. TOUR_Guided)
##   --quit-at-end       quit when that tour ends (used with --write-movie)
##   --explore           skip the menu and start exploring at spawn 1
##   --preset=low|medium|high
##   --smoketest         V4: automated input smoke test (menu, walk, sprint, fly, gate spawn), then quit
## Movie Maker (offline cinematic render):
##   godot --path game/godot --write-movie out.avi --fixed-fps 30 -- --autotour=TOUR_Guided --quit-at-end

const CampusLoader := preload("res://scripts/campus_loader.gd")
const Player := preload("res://scripts/player.gd")
const TourPlayer := preload("res://scripts/tour_player.gd")
const Hud := preload("res://scripts/ui/hud.gd")
const Menu := preload("res://scripts/ui/menu.gd")

var campus: Node3D
var player: CharacterBody3D
var tour: Node3D
var hud: CanvasLayer
var menu: CanvasLayer
var env: Environment
var sun: DirectionalLight3D
var state := "menu"
var ready_done := false
var args := {}
var _loc_timer := 0.0
var _boot_ms := 0
var evening_mode := false
var garden_lights: Node3D
## V7 Photo Mode: saved exploration state restored on exit.
var photo_saved := {}
var photo_hint: CanvasLayer


func _ready() -> void:
	_boot_ms = Time.get_ticks_msec()
	_fit_window()
	_parse_args()
	_build_environment()
	campus = CampusLoader.new()
	campus.name = "CampusLoader"
	add_child(campus)
	player = Player.new()
	player.name = "Player"
	add_child(player)
	tour = TourPlayer.new()
	tour.name = "Tour"
	add_child(tour)
	hud = Hud.new()
	add_child(hud)
	menu = Menu.new()
	add_child(menu)
	menu.visible = false
	hud.visible = false
	player.input_enabled = false
	hud.show_loading()
	await campus.load_campus()
	_after_load()


## V4: the 1600x900 window used to be a project-setting override
## (display/window/size/window_*_override). Godot 4.6 Movie Maker records at the window size and
## that override took precedence over --resolution, so the V3 tour was written at 1600x900.
## The override is gone; plain interactive windowed runs are sized here instead, while
## Movie Maker, --resolution and headless runs keep the size they were given (1920x1080 default).
func _fit_window() -> void:
	if "--capture" in OS.get_cmdline_user_args():
		# Render at exactly 1080p even if Windows shrinks the decorated window.
		var window := get_tree().root
		window.content_scale_size = Vector2i(1920, 1080)
		window.content_scale_mode = Window.CONTENT_SCALE_MODE_VIEWPORT
		window.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_KEEP
		return
	var cmd := OS.get_cmdline_args()
	if DisplayServer.get_name() == "headless" or cmd.has("--write-movie") or cmd.has("--resolution") 			or DisplayServer.window_get_mode() != DisplayServer.WINDOW_MODE_WINDOWED:
		return
	var scr := DisplayServer.screen_get_usable_rect()
	var size := Vector2i(1600, 900)
	if scr.size.x > 0:
		size = Vector2i(mini(size.x, scr.size.x - 40), mini(size.y, scr.size.y - 60))
	DisplayServer.window_set_size(size)
	DisplayServer.window_set_position(scr.position + (scr.size - size) / 2)


func _parse_args() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and a.contains("="):
			args[a.get_slice("=", 0).trim_prefix("--")] = a.get_slice("=", 1)
		elif a.begins_with("--"):
			args[a.trim_prefix("--")] = true


func _after_load() -> void:
	hud.hide_loading()
	hud.minimap.player = player
	hud.minimap.landmarks = campus.landmarks
	hud.minimap.spawns = campus.spawns
	hud.minimap.landmark_clicked.connect(func(l): _go_to_spawn(String(l.spawn), l.label))
	menu.spawns = campus.spawns
	menu.landmarks = campus.landmarks
	menu.tours = TourPlayer.available()
	menu.explore_requested.connect(_start_explore)
	menu.tour_requested.connect(start_tour)
	menu.mode_requested.connect(func(m):
		_start_explore()
		player.set_mode(m))
	menu.spawn_requested.connect(func(id):
		_start_explore()
		_go_to_spawn(id))
	menu.quit_requested.connect(func(): get_tree().quit())
	menu.lighting_requested.connect(func(): _set_evening(not evening_mode))
	menu.main_menu_requested.connect(func(): _open_menu(false))
	L10n.language_changed.connect(_update_mode_label)
	player.mode_changed.connect(func(_m): _update_mode_label())
	player.fly_speed_changed.connect(func(s):
		_update_mode_label()
		hud.show_toast(L10n.t("toast.speed", [str(int(s * Settings.move_speed))]), 1.2))
	tour.label_changed.connect(func(t): hud.set_tour_caption(t))
	tour.finished.connect(_on_tour_finished)
	tour.paused_changed.connect(func(p): hud.show_toast(L10n.t("toast.tour_paused" if p else "toast.tour_resumed"), 1.5))
	Settings.changed.connect(_apply_settings)
	_apply_settings()
	_add_reflection_probes()
	_set_evening(args.has("evening"))
	_go_to_spawn(campus.spawns[0].id if campus.spawns.size() else "", "", false)
	await hud.minimap.render_background(self)
	ready_done = true
	print("[main] ready in %d ms (campus %s)" % [Time.get_ticks_msec() - _boot_ms, str(campus.stats)])
	if args.has("smoketest"):      # V4: automated input smoke test of the exported build
		var st: Node = load("res://scripts/smoke_test.gd").new()
		st.name = "SmokeTest"
		_open_menu(false)
		add_child(st)
		return
	if args.has("autotour"):
		start_tour(String(args.autotour))
	elif args.has("explore"):
		_start_explore()
	else:
		_open_menu(false)


# ------------------------------------------------------------------ environment
const HDRI_PATH := "res://assets/pbr/sky/kloofendal_48d_partly_cloudy_puresky_sunclamped_2k.hdr"
const HDRI_ENERGY := 0.6
const HDRI_BACKGROUND_ENERGY := 1.25
## Yaw that puts the HDRI's own sun azimuth on the DirectionalLight azimuth (calibrated
## from a capture aimed at the game sun; see output/validation/v13/sky_calibration).
const HDRI_YAW_DEG := -93.0
var proc_sky_mat: ProceduralSkyMaterial
var hdri_sky_mat: PanoramaSkyMaterial


func _build_environment() -> void:
	env = Environment.new()
	env.background_mode = Environment.BG_SKY
	var sky_mat := ProceduralSkyMaterial.new()
	# V11 realism: a deeper clear desert sky with a warm, slightly hazy horizon (the
	# default procedural sky is pale and flattens the cream stone against it).
	sky_mat.sky_top_color = Color(0.22, 0.42, 0.72)
	sky_mat.sky_horizon_color = Color(0.70, 0.74, 0.76)
	sky_mat.ground_horizon_color = Color(0.70, 0.66, 0.60)
	sky_mat.ground_bottom_color = Color(0.36, 0.31, 0.26)
	sky_mat.sun_angle_max = 20.0
	var sky := Sky.new()
	sky.sky_material = sky_mat
	env.sky = sky
	proc_sky_mat = sky_mat
	# V13: daytime sky from a real captured HDRI (Poly Haven kloofendal_48d_partly_cloudy_puresky,
	# CC0) with its sun clamped (the DirectionalLight is the sun; an unclamped HDRI sun
	# would light the scene twice). Evening keeps the procedural blue-hour sky.
	if ResourceLoader.exists(HDRI_PATH) and not ("--v12-baseline" in OS.get_cmdline_user_args() or "--v12-legacy-daylight" in OS.get_cmdline_user_args() or "--v13-procedural-sky" in OS.get_cmdline_user_args()):
		hdri_sky_mat = PanoramaSkyMaterial.new()
		hdri_sky_mat.panorama = load(HDRI_PATH)
		hdri_sky_mat.energy_multiplier = HDRI_ENERGY
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	# V7: AgX keeps bright stone and sunlit sand readable without ACES' hue shifts.
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.tonemap_white = 6.0
	# V11: slightly lower exposure so sunlit cream facades keep their joint and band detail.
	env.tonemap_exposure = 0.92
	env.fog_light_color = Color(0.80, 0.82, 0.84)
	env.fog_density = 0.00045
	env.fog_aerial_perspective = 0.55
	env.fog_sky_affect = 0.15
	env.glow_intensity = 0.35
	env.glow_bloom = 0.03
	env.ssao_radius = 1.0
	env.ssao_intensity = 1.2
	env.ssao_detail = 0.6
	env.ssao_light_affect = 0.15
	# V7 (High only): screen-space indirect light gives sunlit paving/sand a warm
	# bounce into shaded facades and courts instead of pure blue sky ambient.
	env.ssil_radius = 6.0
	env.ssil_intensity = 0.9
	env.ssil_normal_rejection = 1.0
	# V10 (Ultra only, sdfgi toggled by the preset): campus-scale cascades with
	# occlusion so arcades and the lobby darken correctly; bounce kept modest so the
	# cream stone does not wash out.
	env.sdfgi_use_occlusion = true
	env.sdfgi_cascades = 6
	env.sdfgi_min_cell_size = 0.25
	env.sdfgi_bounce_feedback = 0.45
	env.sdfgi_energy = 0.9
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.0
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	# Late-afternoon sun from the WNW at 32 deg elevation, matching the Blender scene
	# (plan +Y is about N20W, so WNW is ~47 deg from +Y toward -X).
	sun = DirectionalLight3D.new()
	sun.name = "Sun"
	sun.rotation_degrees = Vector3(-32.0, -132.5, 0.0)
	sun.light_energy = 1.45
	sun.light_color = Color(1.0, 0.95, 0.87)
	sun.light_angular_distance = 0.5
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_blend_splits = true
	# V12: 0.04 left directional shadow acne (diagonal stripes) on flat asphalt; 0.1 removes
	# it without detaching the stair-nosing contact shadows (matched captures).
	sun.shadow_bias = 0.1
	sun.shadow_normal_bias = 1.2
	# V7: denser near cascades (about 30 / 95 / 260 m at 650 m) for contact shadows at
	# stair nosings, benches and facade reveals.
	sun.directional_shadow_split_1 = 0.045
	sun.directional_shadow_split_2 = 0.145
	sun.directional_shadow_split_3 = 0.40
	sun.shadow_blur = 1.2
	add_child(sun)


func _set_evening(enabled: bool) -> void:
	evening_mode = enabled
	if garden_lights == null:
		garden_lights = Node3D.new()
		garden_lights.name = "EveningLighting"
		add_child(garden_lights)
		# V7: every modelled luminaire exported from Blender (street lamps, Academic court
		# poles, garden bollards, covered entrances). Shadowless and distance-faded.
		for point in campus.manifest.get("evening_lights", []):
			var lamp: Light3D
			if bool(point.get("spot", false)):
				var spot := SpotLight3D.new()
				spot.spot_range = float(point.range_m)
				spot.spot_angle = 58.0
				spot.spot_attenuation = 0.8
				spot.rotation_degrees = Vector3(-90.0, 0.0, 0.0)
				lamp = spot
			else:
				var omni := OmniLight3D.new()
				omni.omni_range = float(point.range_m)
				omni.omni_attenuation = 1.2
				lamp = omni
			garden_lights.add_child(lamp)
			lamp.position = Vector3(point.godot[0], point.godot[1], point.godot[2])
			var c: Array = point.get("color", [1.0, 0.70, 0.38])
			lamp.light_color = Color(c[0], c[1], c[2])
			lamp.light_energy = float(point.energy)
			lamp.light_specular = 0.35
			lamp.shadow_enabled = false
			lamp.distance_fade_enabled = true
			lamp.distance_fade_begin = 170.0
			lamp.distance_fade_length = 40.0
	garden_lights.visible = enabled
	var sky_mat := proc_sky_mat
	env.sky.sky_material = proc_sky_mat
	env.background_energy_multiplier = 1.0
	env.fog_sky_affect = 0.15
	env.sky_rotation = Vector3.ZERO
	if enabled:
		# Blue-hour dusk: readable architecture, warm artificial light, no night-black.
		sky_mat.sky_top_color = Color(0.035, 0.055, 0.13)
		sky_mat.sky_horizon_color = Color(0.30, 0.22, 0.24)
		sky_mat.ground_bottom_color = Color(0.05, 0.045, 0.04)
		sky_mat.ground_horizon_color = Color(0.20, 0.16, 0.15)
		sky_mat.sky_energy_multiplier = 1.0
		env.ambient_light_color = Color(0.42, 0.46, 0.62)
		env.ambient_light_sky_contribution = 0.6
		env.ambient_light_energy = 0.55
		env.tonemap_exposure = 1.35
		env.glow_intensity = 0.55
		env.glow_bloom = 0.04
		env.fog_light_color = Color(0.20, 0.20, 0.26)
		sun.light_energy = 0.06
		sun.light_color = Color(0.70, 0.62, 0.72)
		sun.rotation_degrees.x = -4.0
	else:
		sky_mat.sky_top_color = Color(0.33, 0.50, 0.74)
		sky_mat.sky_horizon_color = Color(0.74, 0.78, 0.82)
		sky_mat.sky_curve = 0.12
		sky_mat.ground_bottom_color = Color(0.46, 0.39, 0.31)
		sky_mat.ground_horizon_color = Color(0.72, 0.68, 0.61)
		sky_mat.sun_angle_max = 25.0
		sky_mat.sky_energy_multiplier = 1.0
		# V7: sky-only ambient tinted every shadow saturated blue (V6 captures); mix in a
		# warm sand/stone bounce colour instead.
		env.ambient_light_color = Color(0.86, 0.80, 0.71)
		env.ambient_light_sky_contribution = 0.55
		env.ambient_light_energy = 0.9
		env.tonemap_exposure = 0.96
		env.glow_intensity = 0.0
		env.glow_bloom = 0.0
		env.fog_light_color = Color(0.80, 0.82, 0.84)
		sun.light_energy = 1.55
		sun.light_color = Color(1.0, 0.95, 0.87)
		sun.rotation_degrees.x = -32.0
	if not enabled and hdri_sky_mat != null:
		env.sky.sky_material = hdri_sky_mat
		env.sky_rotation = Vector3(0.0, deg_to_rad(HDRI_YAW_DEG), 0.0)
		# Visible sky only: ambient/reflection radiance stays at HDRI_ENERGY.
		env.background_energy_multiplier = HDRI_BACKGROUND_ENERGY
		# Blend the desert haze into the photographed horizon (QA: hard band in aerials).
		env.fog_sky_affect = 0.45
	# Controlled material QA uses the recorded V11 daylight verbatim.
	if not enabled and "--v12-legacy-daylight" in OS.get_cmdline_user_args():
		sky_mat.sky_top_color = Color(0.33,0.50,0.74)
		env.ambient_light_color = Color(0.86,0.80,0.71)
		env.ambient_light_energy = 1.0
		env.tonemap_exposure = 1.0
		env.glow_intensity = 0.35
		env.glow_bloom = 0.03
		env.adjustment_saturation = 1.06
		env.ssao_intensity = 1.8
		sun.light_color = Color(1.0,0.95,0.87)
		sun.shadow_normal_bias = 1.2
		sun.shadow_blur = 1.2
	# Probes are captured once in daylight; dim them for the evening profile.
	for probe in find_children("Probe_*", "ReflectionProbe", false, false):
		(probe as ReflectionProbe).intensity = 0.18 if enabled else 0.9
	for m in campus.emissive_materials:
		if not m.has_meta("v7_day_energy"):
			m.set_meta("v7_day_energy", m.emission_energy_multiplier)
		m.emission_energy_multiplier = float(m.get_meta("v7_day_energy")) * (2.5 if enabled else 0.12)
	if ready_done:
		hud.show_toast(L10n.t("toast.evening" if enabled else "toast.day"),2.0)


## V7: two box-projected probes, rendered once at load, so the curved Academic
## glazing and polished court stone reflect the surrounding facades instead of only
## the sky, and the residential glass reflects its courtyard. Shadows off.
func _add_reflection_probes() -> void:
	for spec in [["Probe_Admin_Entry", Vector3(0, 8, -25), Vector3(65, 18, 55)],
			["Probe_Academic_Court", Vector3(0, 12, 285), Vector3(160, 30, 130)],
			["Probe_Dormitory_Garden", Vector3(390, 11, 600), Vector3(130, 30, 110)]]:
		if spec[0]=="Probe_Admin_Entry" and "--v12-legacy-daylight" in OS.get_cmdline_user_args():
			continue
		var probe := ReflectionProbe.new()
		probe.name = spec[0]
		probe.position = spec[1]
		probe.size = spec[2]
		probe.box_projection = true
		probe.update_mode = ReflectionProbe.UPDATE_ONCE
		probe.max_distance = 400.0
		probe.enable_shadows = false
		probe.ambient_mode = ReflectionProbe.AMBIENT_DISABLED
		probe.intensity = 0.9
		add_child(probe)


func _apply_settings() -> void:
	Settings.apply_display()
	var v: Dictionary = Settings.values()
	var vp := get_viewport()
	vp.msaa_3d = v.msaa
	vp.screen_space_aa = Viewport.SCREEN_SPACE_AA_FXAA if v.fxaa else Viewport.SCREEN_SPACE_AA_DISABLED
	vp.scaling_3d_scale = v.scale_3d
	vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_FSR2 if v.scale_3d < 1.0 else Viewport.SCALING_3D_MODE_BILINEAR
	vp.mesh_lod_threshold = v.lod_threshold
	var shadows: Dictionary = Settings.shadow_values()
	RenderingServer.directional_shadow_atlas_set_size(int(shadows.shadow_size), true)
	RenderingServer.viewport_set_positional_shadow_atlas_size(vp.get_viewport_rid(), int(shadows.shadow_size), true)
	sun.directional_shadow_max_distance = shadows.shadow_distance
	env.ssao_enabled = v.ssao
	env.ssil_enabled = v.get("ssil", false)
	env.ssr_enabled = v.ssr
	env.glow_enabled = v.glow
	env.sdfgi_enabled = v.sdfgi
	vp.use_taa = v.get("taa", false)
	env.fog_enabled = v.fog
	if player and player.camera:
		player.camera.fov = Settings.fov
	if campus:
		campus.apply_settings()
	if ready_done and state == "explore":
		_update_mode_label()


# ------------------------------------------------------------------ states
func _open_menu(as_pause: bool) -> void:
	state = "menu"
	player.input_enabled = false
	hud.visible = as_pause
	hud.set_exploring(false)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	menu.open(as_pause)


func _start_explore() -> void:
	if tour.playing:
		tour.stop(false)
		hud.set_tour_caption("")
	state = "explore"
	menu.close()
	hud.visible = true
	hud.set_exploring(true)
	player.camera.make_current()
	player.input_enabled = true
	if DisplayServer.get_name() != "headless":
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	_update_mode_label()


func start_tour(path_name: String) -> void:
	menu.close()
	if not tour.start(path_name):
		hud.show_toast(L10n.t("error.tour_missing", [L10n.tour_name(path_name)]))
		_open_menu(false)
		return
	state = "tour"
	player.input_enabled = false
	hud.visible = true
	hud.set_exploring(false)
	hud.set_location(L10n.tour_name(path_name), "")
	hud.set_mode(L10n.t("hud.tour_camera" if path_name == "TOUR_Guided" else "hud.cinematic"))
	hud.set_hints(L10n.t("hud.tour_hints"))
	Input.mouse_mode = Input.MOUSE_MODE_HIDDEN if DisplayServer.get_name() != "headless" else Input.MOUSE_MODE_VISIBLE


func _on_tour_finished(_name: String) -> void:
	hud.set_tour_caption("")
	if args.has("quit-at-end"):
		get_tree().quit()
		return
	_start_explore()
	hud.show_toast(L10n.t("toast.tour_finished"))


func _go_to_spawn(id: String, label := "", toast := true) -> void:
	var s: Dictionary = campus.spawn_by_id(id)
	if s.is_empty():
		return
	var pos: Vector3 = campus.safe_spawn_position(s, player.shape, player.half_height(), [player.get_rid()])
	player.teleport(pos, s.facing)
	player.last_spawn_id = id
	if toast:
		hud.show_toast(L10n.t("toast.teleport", [L10n.location(id, label if label != "" else s.label)]))


func _update_mode_label() -> void:
	if state == "tour":
		hud.set_location(L10n.tour_name(tour.current_name), "")
		hud.set_mode(L10n.t("hud.tour_camera" if tour.current_name == "TOUR_Guided" else "hud.cinematic"))
		hud.set_hints(L10n.t("hud.tour_hints"))
		return
	if player.mode == "walk":
		hud.set_mode(L10n.t("hud.walk"))
		hud.set_hints(L10n.t("hud.walk_hints"))
	else:
		hud.set_mode(L10n.t("hud.fly", [str(int(player.fly_speed * Settings.move_speed)), L10n.t("hud.noclip") if player.noclip else ""]))
		hud.set_hints(L10n.t("hud.fly_hints"))


# ------------------------------------------------------------------ input / update
func _unhandled_input(event: InputEvent) -> void:
	if not ready_done:
		return
	if state == "photo":
		_photo_input(event)
		return
	if event.is_action_pressed("photo_mode") and state == "explore":
		enter_photo_mode()
		return
	if event.is_action_pressed("pause"):
		match state:
			"tour":
				tour.stop(false)
				hud.set_tour_caption("")
				_start_explore()
			"explore":
				_open_menu(true)
			"menu":
				if menu.paused_game:
					_start_explore()
		return
	if event.is_action_pressed("screenshot"):
		_save_screenshot()
	if state == "tour":
		if event.is_action_pressed("tour_pause"):
			tour.toggle_pause()
		return
	if state != "explore":
		return
	if event.is_action_pressed("toggle_fly"):
		player.toggle_mode()
	elif event.is_action_pressed("toggle_noclip") and player.mode == "fly":
		player.set_noclip(not player.noclip)
		hud.show_toast(L10n.t("toast.collision_off" if player.noclip else "toast.collision_on"), 1.2)
	elif event.is_action_pressed("reset_spawn"):
		_go_to_spawn(player.last_spawn_id if player.last_spawn_id != "" else campus.spawns[0].id)
	elif event.is_action_pressed("tour"):
		start_tour("TOUR_Guided")
	elif event.is_action_pressed("toggle_map"):
		var vis: bool = not hud.minimap.get_meta("user_visible", true)
		hud.minimap.set_meta("user_visible", vis)
		hud.minimap.visible = vis
	elif event.is_action_pressed("toggle_help"):
		_open_menu(true)
		menu.show_page("help")
	else:
		for i in 7:
			if event.is_action_pressed("spawn_%d" % (i + 1)) and i < campus.spawns.size():
				_go_to_spawn(campus.spawns[i].id)
	if event is InputEventMouseButton and event.pressed and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


func _process(delta: float) -> void:
	if not ready_done or state != "explore":
		return
	_loc_timer -= delta
	if _loc_timer <= 0.0:
		_loc_timer = 0.25
		var l: Dictionary = campus.landmark_at(player.global_position)
		if l.is_empty():
			hud.set_location(L10n.t("hud.grounds"), "")
		else:
			var note := ""
			if not l.verified:
				if l.id=="LM_Academic_Courtyard":
					note=L10n.t("note.estimated")
				elif String(l.id).begins_with("LM_Gate_"):
					note=L10n.t("note.gate")
				else:
					note=L10n.t("note.identity")
			hud.set_location(l.label,note)


# ------------------------------------------------------------------ V7 photo mode
## Free camera (drone fly, collision off), HUD hidden. Wheel / + / - change speed,
## L toggles the existing daylight / evening presets, F12 saves a 2x capture,
## F9 or Esc restores the exact previous position, view, mode and HUD.
func enter_photo_mode() -> void:
	if state != "explore":
		return
	photo_saved = {"position": player.global_position, "yaw": player.yaw, "pitch": player.pitch,
		"mode": player.mode, "noclip": player.noclip, "fly_speed": player.fly_speed,
		"hud": hud.visible, "evening": evening_mode, "last_spawn": player.last_spawn_id}
	state = "photo"
	player.set_mode("fly")
	player.set_noclip(true)
	player.fly_speed = minf(player.fly_speed, 8.0)
	player.velocity = Vector3.ZERO
	hud.visible = false
	if photo_hint == null:
		photo_hint = CanvasLayer.new()
		photo_hint.layer = 20
		var lbl := Label.new()
		lbl.name = "Hint"
		lbl.text = L10n.t("photo.hints")
		lbl.layout_direction = L10n.direction()
		lbl.add_theme_font_size_override("font_size", 22)
		lbl.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
		lbl.add_theme_constant_override("outline_size", 4)
		lbl.position = Vector2(24, 18)
		photo_hint.add_child(lbl)
		add_child(photo_hint)
	photo_hint.visible = true
	var tw := create_tween()
	(photo_hint.get_node("Hint") as Label).modulate.a = 1.0
	tw.tween_interval(3.0)
	tw.tween_property(photo_hint.get_node("Hint"), "modulate:a", 0.0, 1.0)


func exit_photo_mode() -> void:
	if state != "photo":
		return
	if evening_mode != bool(photo_saved.evening):
		_set_evening(bool(photo_saved.evening))
	player.set_noclip(bool(photo_saved.noclip))
	player.fly_speed = float(photo_saved.fly_speed)
	player.mode = String(photo_saved.mode)
	player.set_mode(String(photo_saved.mode))
	player.global_position = photo_saved.position
	player.velocity = Vector3.ZERO
	player.set_view(float(photo_saved.yaw), float(photo_saved.pitch))
	player.last_spawn_id = String(photo_saved.last_spawn)
	if photo_hint:
		photo_hint.visible = false
	state = "explore"
	hud.visible = bool(photo_saved.hud)
	_update_mode_label()


func _photo_input(event: InputEvent) -> void:
	if event.is_action_pressed("photo_mode") or event.is_action_pressed("pause"):
		exit_photo_mode()
	elif event.is_action_pressed("photo_lighting"):
		_set_evening(not evening_mode)
	elif event.is_action_pressed("screenshot"):
		capture_highres()


## Renders the current view once into an offscreen viewport at `scale` x the window
## size, sharing this World3D / environment, and saves a PNG. Returns the path.
func capture_highres(scale := 2) -> String:
	var src_cam := get_viewport().get_camera_3d()
	var size := Vector2i(get_viewport().get_visible_rect().size) * scale
	var sv := SubViewport.new()
	sv.size = size
	sv.msaa_3d = get_viewport().msaa_3d
	sv.screen_space_aa = get_viewport().screen_space_aa
	sv.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	var cam := Camera3D.new()
	sv.add_child(cam)
	add_child(sv)
	cam.global_transform = src_cam.global_transform
	cam.fov = src_cam.fov
	cam.near = src_cam.near
	cam.far = src_cam.far
	cam.current = true
	for i in 4:
		await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute("user://screenshots")
	var path := "user://screenshots/zewail_photo_%s.png" % Time.get_datetime_string_from_system().replace(":", "-")
	var img := sv.get_texture().get_image()
	img.save_png(path)
	sv.queue_free()
	print("[photo] saved %s (%dx%d)" % [ProjectSettings.globalize_path(path), img.get_width(), img.get_height()])
	return path


func _save_screenshot() -> void:
	DirAccess.make_dir_recursive_absolute("user://screenshots")
	var path := "user://screenshots/zewail_%s.png" % Time.get_datetime_string_from_system().replace(":", "-")
	get_viewport().get_texture().get_image().save_png(path)
	hud.show_toast(L10n.t("toast.saved", [ProjectSettings.globalize_path(path)]))
