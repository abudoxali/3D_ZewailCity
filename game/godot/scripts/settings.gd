extends Node
## Graphics presets and user preferences. Autoloaded as `Settings`.
## Saved to user://settings.cfg. Command line (after `--`): --preset=low|medium|high

signal changed

const PRESETS := {
	"Low": {
		"scale_3d": 0.77, "msaa": Viewport.MSAA_DISABLED, "fxaa": true, "shadow_size": 2048,
		"shadow_distance": 220.0, "ssao": false, "ssr": false, "glow": false, "sdfgi": false,
		"veg_range": 260.0, "prop_range": 180.0, "lod_threshold": 4.0, "fog": true,
	},
	"Medium": {
		"scale_3d": 1.0, "msaa": Viewport.MSAA_2X, "fxaa": false, "shadow_size": 4096,
		"shadow_distance": 400.0, "ssao": true, "ssr": false, "glow": true, "sdfgi": false,
		"veg_range": 600.0, "prop_range": 350.0, "lod_threshold": 1.5, "fog": true,
	},
	"High": {
		"scale_3d": 1.0, "msaa": Viewport.MSAA_4X, "fxaa": false, "shadow_size": 8192,
		"shadow_distance": 650.0, "ssao": true, "ssil": true, "ssr": true, "glow": true, "sdfgi": false,
		"veg_range": 1400.0, "prop_range": 800.0, "lod_threshold": 1.0, "fog": true,
	},
	# V10: optional architectural-quality preset. SDFGI adds real multi-bounce sky and
	# sun bounce into arcades, courts and the Administration lobby; TAA settles thin
	# mullions and rails. High is unchanged and remains the performance target.
	"Ultra": {
		"scale_3d": 1.0, "msaa": Viewport.MSAA_4X, "fxaa": false, "taa": true, "shadow_size": 8192,
		"shadow_distance": 800.0, "ssao": true, "ssil": true, "ssr": true, "glow": true, "sdfgi": true,
		"veg_range": 1800.0, "prop_range": 1000.0, "lod_threshold": 0.6, "fog": true,
	},
}

var preset := "High"
var mouse_sensitivity := 0.0022
var fov := 75.0
var invert_y := false
var show_fps := true
var resolution := Vector2i(1600, 900)
var display_mode := 0
var vsync := 1
var fps_limit := 0
var shadow_quality := "Preset"
var move_speed := 1.0
var language := "ar"
var _display_applied := false
const FIELDS := {
	"preset":"graphics", "shadow_quality":"graphics",
	"mouse_sensitivity":"input", "invert_y":"input", "move_speed":"input",
	"fov":"view", "show_fps":"view", "language":"view",
	"resolution":"display", "display_mode":"display", "vsync":"display", "fps_limit":"display",
}

const PATH := "user://settings.cfg"


func _ready() -> void:
	load_settings()
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--preset="):
			var p := arg.get_slice("=", 1).capitalize()
			if PRESETS.has(p):
				preset = p
	if not PRESETS.has(preset):
		preset = "High"
	L10n.set_language(language)

func load_settings(path := PATH) -> Error:
	var cfg := ConfigFile.new()
	var err := cfg.load(path)
	if err == OK:
		for field in FIELDS:
			var value = cfg.get_value(FIELDS[field], field, get(field))
			if typeof(value) == typeof(get(field)):
				set(field, value)
	_sanitize()
	return err

func _sanitize() -> void:
	if not PRESETS.has(preset): preset = "High"
	if shadow_quality not in ["Preset","Low","Medium","High"]: shadow_quality = "Preset"
	if language not in ["ar","en"]: language = "ar"
	mouse_sensitivity = clampf(mouse_sensitivity, 0.0005, 0.006)
	fov = clampf(fov, 60, 100)
	move_speed = clampf(move_speed, 0.25, 3.0)
	display_mode = clampi(display_mode, 0, 2)
	vsync = clampi(vsync, 0, 2)
	if fps_limit not in [0,30,60,120,144,240]: fps_limit = 0
	if resolution.x < 640 or resolution.y < 360: resolution = Vector2i(1600,900)

func update(field: String, value) -> void:
	if not FIELDS.has(field): return
	set(field, value)
	_sanitize()
	save()
	if field == "language": L10n.set_language(language)
	apply_display(field in ["resolution", "display_mode"])
	changed.emit()

func apply_display(force := false) -> void:
	Engine.max_fps = fps_limit
	if DisplayServer.get_name() == "headless": return
	DisplayServer.window_set_vsync_mode([DisplayServer.VSYNC_DISABLED, DisplayServer.VSYNC_ENABLED, DisplayServer.VSYNC_ADAPTIVE][vsync])
	var cmd := OS.get_cmdline_args()
	if not force and (cmd.has("--resolution") or cmd.has("--write-movie") or "--capture" in OS.get_cmdline_user_args()): return
	if _display_applied and not force: return
	_display_applied = true
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_BORDERLESS, display_mode == 1)
	if display_mode == 0:
		DisplayServer.window_set_size(resolution)
	elif display_mode == 1:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	else:
		DisplayServer.window_set_size(resolution)
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN)

func shadow_values() -> Dictionary:
	var v: Dictionary = PRESETS[preset]
	if shadow_quality == "Preset": return v
	return PRESETS[shadow_quality]


func values() -> Dictionary:
	return PRESETS[preset]


func set_preset(p: String) -> void:
	if PRESETS.has(p):
		preset = p
		save()
		changed.emit()


func save(path := PATH) -> Error:
	var cfg := ConfigFile.new()
	for field in FIELDS:
		cfg.set_value(FIELDS[field], field, get(field))
	return cfg.save(path)
