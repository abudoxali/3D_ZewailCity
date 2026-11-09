extends CharacterBody3D
## First-person walker and free-fly drone in one body.
##
## Walk: gravity, floor snapping, step-up for curbs and stairs (STEP_HEIGHT),
##       sprint, jump. Collides with physics layer 1 (world_static).
## Fly:  free 3D movement relative to the view, vertical ascend / descend,
##       adjustable speed (mouse wheel, + / -), optional no-clip (C).
## Switching fly -> walk glides down to the ground below instead of dropping.

signal mode_changed(mode: String)
signal fly_speed_changed(speed: float)

const RADIUS := 0.35
const HEIGHT := 1.75          # capsule total height (m)
const EYE := 1.62             # eye height above the feet (m)
const WALK_SPEED := 4.6       # m/s; brisk walk with a game feel
const SPRINT_SPEED := 9.5
const JUMP_VELOCITY := 4.6
const ACCEL_GROUND := 12.0
const ACCEL_AIR := 2.5
const STEP_HEIGHT := 0.45     # curbs (~0.2 m), stairs (0.17 m), low planters
const FLY_MIN := 3.0
const FLY_MAX := 300.0
const WORLD_MASK := 1
const BOUNDS := 2400.0        # |x|, |z| limit (the sand plane is 8 km wide)

var mode := "walk"
var noclip := false
var input_enabled := true
var fly_speed := 30.0
var yaw := 0.0
var pitch := 0.0
var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity", 9.81)
var shape: CapsuleShape3D
var head: Node3D
var camera: Camera3D
var _gliding := false
var _glide_tween: Tween
var last_spawn_id := ""


func _ready() -> void:
	collision_layer = 1 << 1          # layer 2: player
	collision_mask = WORLD_MASK
	floor_snap_length = 0.45
	floor_max_angle = deg_to_rad(46.0)
	floor_constant_speed = true
	safe_margin = 0.02
	shape = CapsuleShape3D.new()
	shape.radius = RADIUS
	shape.height = HEIGHT
	var cs := CollisionShape3D.new()
	cs.shape = shape
	cs.name = "Capsule"
	add_child(cs)
	head = Node3D.new()
	head.name = "Head"
	head.position = Vector3(0, EYE - HEIGHT * 0.5, 0)
	add_child(head)
	camera = Camera3D.new()
	camera.name = "Camera"
	camera.near = 0.08
	camera.far = 6000.0
	camera.fov = Settings.fov
	head.add_child(camera)


func half_height() -> float:
	return HEIGHT * 0.5


func feet_position() -> Vector3:
	return global_position - Vector3(0, HEIGHT * 0.5, 0)


func set_view(new_yaw: float, new_pitch := 0.0) -> void:
	yaw = new_yaw
	pitch = clamp(new_pitch, deg_to_rad(-89), deg_to_rad(89))
	rotation = Vector3(0, yaw, 0)
	head.rotation = Vector3(pitch, 0, 0)


func face_direction(dir: Vector3) -> void:
	var flat := Vector3(dir.x, 0, dir.z)
	if flat.length() > 0.001:
		set_view(atan2(-flat.x, -flat.z), 0.0)


func teleport(body_centre: Vector3, facing := Vector3.ZERO) -> void:
	# V10 fix: a teleport is an explicit placement. Previously, teleporting while
	# flying called set_mode("walk"), whose glide-to-ground tween then dragged the
	# player from the NEW position down to the floor (masked in V9 by flush facades).
	if _glide_tween and _glide_tween.is_valid():
		_glide_tween.kill()
	_gliding = false
	global_position = body_centre
	velocity = Vector3.ZERO
	if facing != Vector3.ZERO:
		face_direction(facing)
	if mode == "fly":
		noclip = false
		mode = "walk"
		mode_changed.emit(mode)


func _unhandled_input(event: InputEvent) -> void:
	if not input_enabled:
		return
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		var sens: float = Settings.mouse_sensitivity
		var dy: float = event.relative.y * (-1.0 if Settings.invert_y else 1.0)
		set_view(yaw - event.relative.x * sens, pitch - dy * sens)
	elif event is InputEventMouseButton and event.pressed and mode == "fly":
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			change_fly_speed(1.25)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			change_fly_speed(0.8)


func change_fly_speed(factor: float) -> void:
	fly_speed = clamp(fly_speed * factor, FLY_MIN, FLY_MAX)
	fly_speed_changed.emit(fly_speed)


func toggle_mode() -> void:
	set_mode("walk" if mode == "fly" else "fly")


func set_mode(m: String) -> void:
	if m == mode:
		return
	if m == "fly":
		mode = "fly"
		velocity = Vector3(0, 3.0, 0)
	else:
		noclip = false
		_glide_to_ground()
		mode = "walk"
	mode_changed.emit(mode)


func set_noclip(on: bool) -> void:
	noclip = on and mode == "fly"
	mode_changed.emit(mode)


func _glide_to_ground() -> void:
	var space := get_world_3d().direct_space_state
	var q := PhysicsRayQueryParameters3D.create(global_position, global_position + Vector3(0, -2000, 0), WORLD_MASK)
	q.exclude = [get_rid()]
	var hit := space.intersect_ray(q)
	if hit.is_empty():
		return
	var target: Vector3 = hit.position + Vector3(0, HEIGHT * 0.5 + 0.05, 0)
	var drop := global_position.y - target.y
	if drop < 1.5:
		return
	_gliding = true
	velocity = Vector3.ZERO
	var tw := create_tween()
	_glide_tween = tw
	tw.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_property(self, "global_position", target, clamp(drop / 70.0, 0.35, 1.8))
	tw.finished.connect(func(): _gliding = false)


func _physics_process(delta: float) -> void:
	if _gliding:
		return
	var input_dir := Vector2.ZERO
	if input_enabled:
		input_dir = Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	if mode == "walk":
		_walk(delta, input_dir)
	else:
		_fly(delta, input_dir)
	global_position.x = clamp(global_position.x, -BOUNDS, BOUNDS)
	global_position.z = clamp(global_position.z, -BOUNDS, BOUNDS)


func _walk(delta: float, input_dir: Vector2) -> void:
	var wish := Basis(Vector3.UP, yaw) * Vector3(input_dir.x, 0, input_dir.y)
	wish.y = 0
	if wish.length() > 1.0:
		wish = wish.normalized()
	var sprint := input_enabled and Input.is_action_pressed("sprint")
	var target := wish * (SPRINT_SPEED if sprint else WALK_SPEED) * Settings.move_speed
	var k := 1.0 - exp(-(ACCEL_GROUND if is_on_floor() else ACCEL_AIR) * delta)
	velocity.x = lerp(velocity.x, target.x, k)
	velocity.z = lerp(velocity.z, target.z, k)
	if is_on_floor():
		if input_enabled and Input.is_action_just_pressed("jump"):
			velocity.y = JUMP_VELOCITY
		else:
			velocity.y = 0.0 # Do not retain the upward component of the previous tread/slope.
	else:
		velocity.y -= gravity * delta
	var was_on_floor := is_on_floor()
	var horizontal := Vector3(velocity.x, 0, velocity.z)
	move_and_slide()
	if was_on_floor and wish.length() > 0.1 and _blocked_by_wall():
		_try_step(horizontal.normalized() if horizontal.length() > 0.05 else wish.normalized())
	if velocity.y <= 0.0:
		# A contact can be lost for one frame at a descending nosing. Re-snap only
		# downward, within the existing 0.45 m reach; rising jumps remain untouched.
		apply_floor_snap()
	if global_position.y < -30.0:   # safety net, should never trigger
		push_warning("Player fell below the world; returning to spawn")
		velocity = Vector3.ZERO
		global_position.y = 5.0


## True when a contact is too steep to walk on (walls, and the rounded contact a
## capsule makes with a curb edge, whose normal is ~55-60 deg from vertical).
func _blocked_by_wall() -> bool:
	var floor_y := cos(floor_max_angle)
	for i in get_slide_collision_count():
		var n := get_slide_collision(i).get_normal()
		if n.y < floor_y and n.y > -0.3:
			return true
	return false


## Climb a ledge up to STEP_HEIGHT: move up, forward, then settle down onto it.
func _try_step(dir: Vector3) -> bool:
	if dir.length() < 0.01:
		return false
	var up := Vector3(0, STEP_HEIGHT, 0)
	var xf := global_transform
	if test_move(xf, up):
		return false
	xf.origin += up
	var fwd := dir * 0.32
	if test_move(xf, fwd):
		return false
	xf.origin += fwd
	var col := KinematicCollision3D.new()
	if not test_move(xf, -up - Vector3(0, 0.05, 0), col):
		return false
	xf.origin += col.get_travel()
	if col.get_normal().y < cos(floor_max_angle):
		return false
	global_transform = xf
	apply_floor_snap()
	return true


func _fly(delta: float, input_dir: Vector2) -> void:
	var dir := head.global_transform.basis * Vector3(input_dir.x, 0, input_dir.y)
	if input_enabled:
		var vert := 0.0
		if Input.is_action_pressed("fly_up"):
			vert += 1.0
		if Input.is_action_pressed("fly_down"):
			vert -= 1.0
		dir += Vector3.UP * vert
		if Input.is_action_just_pressed("speed_up"):
			change_fly_speed(1.25)
		if Input.is_action_just_pressed("speed_down"):
			change_fly_speed(0.8)
	var boost := 4.0 if (input_enabled and Input.is_action_pressed("sprint")) else 1.0
	var target := dir.normalized() * fly_speed * boost * Settings.move_speed if dir.length() > 0.01 else Vector3.ZERO
	velocity = velocity.lerp(target, 1.0 - exp(-5.0 * delta))
	if noclip:
		global_position += velocity * delta
	else:
		move_and_slide()
	global_position.y = clamp(global_position.y, -1.0, 1500.0)
