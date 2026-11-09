extends Node
## Registers the input map in code so the bindings live in one readable place.
## Autoloaded as `Controls` before the main scene.

const BINDINGS := {
	"move_forward": [KEY_W, KEY_UP],
	"move_back": [KEY_S, KEY_DOWN],
	"move_left": [KEY_A, KEY_LEFT],
	"move_right": [KEY_D, KEY_RIGHT],
	"sprint": [KEY_SHIFT],
	"jump": [KEY_SPACE],
	"fly_up": [KEY_SPACE, KEY_E],
	"fly_down": [KEY_CTRL, KEY_Q],
	"toggle_fly": [KEY_F],
	"toggle_noclip": [KEY_C],
	"reset_spawn": [KEY_R],
	"pause": [KEY_ESCAPE],
	"tour": [KEY_T],
	"tour_pause": [KEY_P],
	"toggle_map": [KEY_M],
	"toggle_help": [KEY_H, KEY_F1],
	"speed_up": [KEY_EQUAL, KEY_KP_ADD],
	"speed_down": [KEY_MINUS, KEY_KP_SUBTRACT],
	"spawn_1": [KEY_1],
	"spawn_2": [KEY_2],
	"spawn_3": [KEY_3],
	"spawn_4": [KEY_4],
	"spawn_5": [KEY_5],
	"spawn_6": [KEY_6],
	"spawn_7": [KEY_7],
	"screenshot": [KEY_F12],
	"photo_mode": [KEY_F9],
	"photo_lighting": [KEY_L],
	"interact": [KEY_E],
}

## Human-readable table shown in the Help panel.
const HELP := [
	["move", "help.move"],
	["mouse", "help.look"],
	["sprint", "help.sprint"],
	["jump", "help.jump"],
	["fly_down", "help.down"],
	["toggle_fly", "help.fly"],
	["toggle_noclip", "help.collision"],
	["speed", "help.speed"],
	["reset_spawn", "help.reset"],
	["locations", "help.locations"],
	["tour", "help.tour"],
	["tour_pause", "help.tour_pause"],
	["toggle_map", "help.map"],
	["toggle_help", "help.help"],
	["photo_mode", "help.photo"],
	["photo_lighting", "help.light"],
	["screenshot", "help.capture"],
	["interact", "help.interact"],
	["pause", "help.pause"],
]


func _ready() -> void:
	for action in BINDINGS:
		if InputMap.has_action(action):
			InputMap.erase_action(action)
		InputMap.add_action(action, 0.2)
		for key in BINDINGS[action]:
			var ev := InputEventKey.new()
			ev.physical_keycode = key
			InputMap.action_add_event(action, ev)
	# Godot desktop defaults contain keyboard events only. Add menu navigation
	# without replacing the built-in keyboard actions or gameplay bindings.
	var menu_buttons := {"ui_accept":JOY_BUTTON_A,"ui_cancel":JOY_BUTTON_B,"ui_up":JOY_BUTTON_DPAD_UP,"ui_down":JOY_BUTTON_DPAD_DOWN,"ui_left":JOY_BUTTON_DPAD_LEFT,"ui_right":JOY_BUTTON_DPAD_RIGHT}
	for action in menu_buttons:
		var button := InputEventJoypadButton.new()
		button.button_index = menu_buttons[action]
		button.device = -1
		InputMap.action_add_event(action, button)


func help_binding(action: String) -> String:
	if action == "mouse": return "Mouse" if L10n.language == "en" else "الفأرة"
	if action == "move": return "W A S D / ↑ ↓ ← →"
	if action == "locations": return "1–7"
	if action == "speed": return help_binding("speed_up") + " / " + help_binding("speed_down")
	var keys: Array[String] = []
	for code in BINDINGS.get(action, []):
		keys.append(OS.get_keycode_string(code))
	return " / ".join(keys)
