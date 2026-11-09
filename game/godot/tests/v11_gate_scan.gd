extends "res://tests/v5_ground.gd"
## V11 diagnostic: lateral ray scan across a closed secondary gate.
func run_validation() -> void:
	main._start_explore()
	var gc = campus.gate_controller
	var out := {}
	for g in campus.manifest.get("gates", []).slice(1):
		gc.set_gate(g.id, false, true)
	for i in 3:
		await get_tree().physics_frame
	for g in campus.manifest.get("gates", []).slice(1):
		var x: float = g.model_position_blender_m[0]
		var z: float = -g.model_position_blender_m[1]
		var inw := Vector2(g.inward[0], -g.inward[1]).normalized()
		var lat := Vector2(-inw.y, inw.x)
		var fl = campus.ground_at(x, z)
		var h: float = (fl.y if fl != null else 0.0) + 1.0
		var clear := []
		for k in range(-12, 13):
			var c := Vector2(x, z) + lat * float(k) * 0.5
			var r := ray(Vector3(c.x - inw.x * 4, h, c.y - inw.y * 4), Vector3(c.x + inw.x * 4, h, c.y + inw.y * 4))
			if r.is_empty():
				clear.append(float(k) * 0.5)
		out[g.id] = {"clear_lateral_m": clear, "leaves": str(gc.gates[g.id].map(func(d): return [d.leaf, d.open, (d.body as Node3D).global_position, (d.body as Node3D).global_rotation_degrees]))}
		if g.id == "G3":
			for d in gc.gates[g.id]:
				var body = d.body
				for ch in body.get_children():
					print("[leaf-detail] ", d.leaf, " ", ch.name, " xf=", ch.global_transform, " bounds=", ch.get_aabb() if ch is MeshInstance3D else ch.shape.size)
			print("[gate-detail] ", g)
	print("[gate-scan] ", JSON.stringify(out))
	get_tree().quit(0)
