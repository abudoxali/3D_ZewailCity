extends "res://tests/v5_ground.gd"
## V15 pilot (G1 -> approach -> Administration): real walking across the rebuilt kerbs, beds and
## median, collision continuity over the corridor, and visual-only precast kerb units.
## Godot (x, z) = Blender (x, -y).
func run_validation() -> void:
	main._start_explore()
	# 1. Continuous walk: outside G1 -> inbound walkway -> ring junction -> Administration forecourt.
	await follow_route("V15 walk G1 exterior > inbound walkway > Administration forecourt", [
		Vector2(-19,-337),Vector2(-19,-310),Vector2(-16.3,-290),Vector2(-16.3,-200),Vector2(-16.3,-110),
		Vector2(-25,-55),Vector2(0,-42),Vector2(0,-25)])
	# 2. Perpendicular crossings of the new kerbed verge bed (road kerb, raised bed, bed/walkway kerb).
	await follow_route("V15 cross inbound verge: carriageway > road kerb > bed > walkway kerb > walkway",
		[Vector2(-6,-200),Vector2(-17,-200)])
	await follow_route("V15 cross outbound verge back to carriageway",
		[Vector2(17,-180),Vector2(6,-180)])
	# 3. Across the palm median (two kerbs and the raised worn lawn).
	await follow_route("V15 cross median between carriageways", [Vector2(-6,-170),Vector2(6,-170)])
	# 4. Along both carriageways through the crossover bands, inside G1 to the ring junction.
	await follow_route("V15 inbound carriageway through crossover bands", [Vector2(-6,-300),Vector2(-6,-250),Vector2(-6,-120)])
	await follow_route("V15 outbound carriageway through crossover bands", [Vector2(6,-120),Vector2(6,-250),Vector2(6,-300)])
	# 5. Collision continuity: 0.5 m grid over the corridor surface (no holes, no invisible barriers).
	var holes := []
	var high := []
	var edge_misses := 0
	var n := 0
	for xi in range(-44, 45):
		for zi in range(-600, -199):
			var x := xi * 0.5
			var z := zi * 0.5
			n += 1
			var q := PhysicsRayQueryParameters3D.create(Vector3(x, 3.0, z), Vector3(x, -1.0, z), 1)
			q.exclude = [player.get_rid()]
			var hit := space().intersect_ray(q)
			if hit.is_empty():
				# A ray exactly on a shared trimesh edge can miss (Godot precision); classify a hole
				# only when four 2 cm offset rays also miss (same method as V5Ground).
				edge_misses += 1
				for o in [Vector3(.02,0,0),Vector3(-.02,0,0),Vector3(0,0,.02),Vector3(0,0,-.02)]:
					q.from = Vector3(x, 3.0, z) + o
					q.to = Vector3(x, -1.0, z) + o
					hit = space().intersect_ray(q)
					if not hit.is_empty():
						break
			if hit.is_empty():
				holes.append([x, z])
			elif hit.position.y > 0.62 and String(hit.collider.name).contains("COL_Ground"):
				high.append([x, z, snappedf(hit.position.y, 0.001), str(hit.collider.name)])
	check("V15 corridor collision has no holes (0.5 m grid, x -22..22, Blender y 100..300)", holes.is_empty(), {"samples": n, "single_ray_edge_misses": edge_misses, "holes": holes.slice(0, 20), "hole_count": holes.size()})
	check("V15 corridor has no raised invisible collision over the walkable surface", high.is_empty(), {"count": high.size(), "examples": high.slice(0, 20)})
	# 6. Precast kerb units exist as render geometry and add no collider of their own.
	var units: Node = campus.campus_root.find_child("SW_Curb_Precast_Units", true, false)
	var tris := 0.0
	if units is MeshInstance3D and (units as MeshInstance3D).mesh:
		for i in (units as MeshInstance3D).mesh.get_surface_count():
			tris += (units as MeshInstance3D).mesh.surface_get_array_index_len(i) / 3.0
	var unit_body := false
	for b in campus.campus_root.find_children("*", "StaticBody3D", true, false):
		if String(b.name).contains("Precast"):
			unit_body = true
	check("V15 precast kerb units rendered (visual only, no own collider)", tris > 50000 and not unit_body, {"triangles": tris, "own_collider": unit_body})
	save_json(OUT_VALID + "v15_corridor_test.json", {"checks": results, "all_pass": results.all(func(r): return r.pass),
		"method": "Real walking input with existing collision; physics ray grid over the pilot corridor"})
