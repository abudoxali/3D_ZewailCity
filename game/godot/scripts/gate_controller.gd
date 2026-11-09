extends Node
## V11 perimeter gate leaves G1-G6 (owner screenshots 02/06).
##
## build_game_assets.py ships every sliding leaf as a separate mesh named
##   GATELEAF_<gate>_<leaf>_dx<cm>_dy<cm>_s<1 closed | 0 open at start>
## (Blender metres; Godot offset = (dx, 0, -dy)). At load time each leaf is wrapped in an
## AnimatableBody3D with a box collider fitted to its mesh, so a CLOSED leaf physically
## blocks the opening and an OPEN leaf is parked clear of it. The player toggles the
## nearest gate with the "interact" action (E). The HUD prompt API (group "hud":
## set_interaction_prompt / clear_interaction_prompt) and L10n are used when present.

const WORLD_LAYER := 1
const RANGE := 9.0          # m from the nearest leaf (horizontal)
const SLIDE_TIME := 2.4     # s for a full travel
const NAME_RE := "^GATELEAF_(G\\d)_([A-Za-z]+)_dx(-?\\d+)_dy(-?\\d+)_s([01])"

var leaves: Array = []      # [{gate, leaf, body, closed_pos, open_pos, open, t}]
var gates: Dictionary = {}  # gate id -> [leaf dicts]
var _near := ""
var _prompt_text := ""


func setup(root: Node) -> int:
	if not InputMap.has_action("interact"):
		InputMap.add_action("interact")
		var ev := InputEventKey.new()
		ev.physical_keycode = KEY_E
		InputMap.action_add_event("interact", ev)
	var re := RegEx.new()
	re.compile(NAME_RE)
	for n in root.find_children("GATELEAF_*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		var m := re.search(mi.name)
		if m == null:
			continue
		var gid := m.get_string(1)
		var slide := Vector3(float(m.get_string(3)) / 100.0, 0.0, -float(m.get_string(4)) / 100.0)
		var start_closed := m.get_string(5) == "1"
		var parent := mi.get_parent()
		var xf := mi.global_transform
		var aabb := mi.get_aabb()
		var body := AnimatableBody3D.new()
		body.name = "GateBody_" + mi.name.get_slice("_dx", 0)
		# Direct transform updates (sync_to_physics deferred the collider: moved leaves did not block).
		body.sync_to_physics = false
		body.collision_layer = 1 << (WORLD_LAYER - 1)
		body.collision_mask = 0
		parent.add_child(body)
		body.global_transform = xf
		mi.reparent(body, true)
		var cs := CollisionShape3D.new()
		var box := BoxShape3D.new()
		# Solid panel collider: the lattice must block a walker, not just its bars.
		box.size = Vector3(max(aabb.size.x, 0.12), max(aabb.size.y, 0.12), max(aabb.size.z, 0.12))
		cs.shape = box
		cs.position = aabb.get_center()
		body.add_child(cs)
		var start := body.position
		var closed_pos := start if start_closed else start - _local_slide(body, slide)
		var d := {"gate": gid, "leaf": m.get_string(2), "body": body, "closed_pos": closed_pos,
			"open_pos": closed_pos + _local_slide(body, slide), "open": not start_closed, "t": 0.0 if start_closed else 1.0}
		leaves.append(d)
		if not gates.has(gid):
			gates[gid] = []
		gates[gid].append(d)
	return leaves.size()


func _local_slide(body: Node3D, slide_world: Vector3) -> Vector3:
	# Leaf offsets are world-space; convert to the body's parent space.
	var p := body.get_parent() as Node3D
	if p == null:
		return slide_world
	return p.global_transform.basis.inverse() * slide_world


func is_open(gid: String) -> bool:
	for d in gates.get(gid, []):
		if not d.open:
			return false
	return gates.has(gid)


func set_gate(gid: String, open: bool, instant := false) -> void:
	for d in gates.get(gid, []):
		d.open = open
		if instant:
			d.t = 1.0 if open else 0.0
			(d.body as Node3D).position = d.closed_pos.lerp(d.open_pos, d.t)


func toggle(gid: String) -> void:
	set_gate(gid, not is_open(gid))


func gate_centre(gid: String) -> Vector3:
	var c := Vector3.ZERO
	var arr: Array = gates.get(gid, [])
	for d in arr:
		c += (d.body as Node3D).global_position
	return c / max(1, arr.size())


func nearest_gate(pos: Vector3) -> String:
	var best := ""
	var best_d := RANGE
	for d in leaves:
		var b := d.body as Node3D
		var ax: Vector3 = (d.body as Node3D).get_parent().global_transform * d.closed_pos
		var q := Vector2(pos.x - ax.x, pos.z - ax.z).length()
		if q < best_d:
			best_d = q
			best = d.gate
	return best


func _physics_process(delta: float) -> void:
	for d in leaves:
		var target := 1.0 if d.open else 0.0
		if not is_equal_approx(d.t, target):
			d.t = move_toward(d.t, target, delta / SLIDE_TIME)
			var s := smoothstep(0.0, 1.0, d.t)
			(d.body as Node3D).position = d.closed_pos.lerp(d.open_pos, s)


func _process(_delta: float) -> void:
	var cam := get_viewport().get_camera_3d()
	if cam == null:
		return
	var g := "" if _suppressed() else nearest_gate(cam.global_position)
	var text := ""
	if g != "":
		text = _prompt(g)
	if text != _prompt_text:
		_prompt_text = text
		if text == "":
			get_tree().call_group("hud", "clear_interaction_prompt")
		else:
			get_tree().call_group("hud", "set_interaction_prompt", text)
	_near = g


func _unhandled_input(event: InputEvent) -> void:
	# E is also the flight-ascent key: gates respond only while walking.
	if _suppressed():
		return
	if _near != "" and event.is_action_pressed("interact"):
		toggle(_near)
		_prompt_text = ""   # refresh the prompt next frame
		get_viewport().set_input_as_handled()


func _t(key: String, args: Array, fallback: String) -> String:
	var l := get_node_or_null("/root/L10n")
	if l and l.has_method("t"):
		return l.t(key, args)
	return fallback % args if args.size() else fallback


func _prompt(gid: String) -> String:
	var name := _t("gate.name", [gid], "Gate %s")
	if is_open(gid):
		return _t("gate.prompt_close", [name], "Press E to close %s")
	return _t("gate.prompt_open", [name], "Press E to open %s")


func report() -> Dictionary:
	var out := {}
	for gid in gates:
		var arr := []
		for d in gates[gid]:
			arr.append({"leaf": d.leaf, "open": d.open, "pos": (d.body as Node3D).global_position})
		out[gid] = arr
	return out


func _flying() -> bool:
	var pl = get_tree().get_first_node_in_group("player")
	if pl == null:
		var m := get_tree().current_scene
		pl = m.get("player") if m else null
	return pl != null and str(pl.get("mode")) == "fly"


## Codex review (V11): no prompt and no toggling in menus, tours, photo mode, while flying
## or with player input disabled. Clearing the cached prompt also restores it after a pause.
func _suppressed() -> bool:
	var m := get_tree().current_scene
	if m and m.get("state") != null and str(m.get("state")) != "explore":
		return true
	var pl = m.get("player") if m else null
	if pl != null and pl.get("input_enabled") == false:
		return true
	return _flying()
