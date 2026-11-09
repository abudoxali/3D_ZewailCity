extends "res://tests/v5_ground.gd"
## Configuration-space flood fill using the REAL exported physics shapes and player capsule.
## Complements real walking attempts: catches paths turning around wing/perimeter junctions.
const GRID := .4
var floor_excludes: Array[RID] = []

func flood(blocked: PackedByteArray, width: int, height: int, seed: Vector2i, target: Vector2i, locations: Array[Vector3]) -> Array[int]:
	var start := seed.y*width+seed.x
	var goal := target.y*width+target.x
	if blocked[start] or blocked[goal]:
		return []
	var visited := PackedByteArray()
	visited.resize(blocked.size())
	var queue: Array[int] = [start]
	visited[start] = 1
	var head := 0
	var parent := PackedInt32Array()
	parent.resize(blocked.size())
	parent.fill(-1)
	while head < queue.size():
		var cell := queue[head]
		head += 1
		if cell == goal:
			var path: Array[int] = []
			while cell != -1:
				path.push_front(cell)
				cell=parent[cell]
			return path
		var x := cell % width
		var y := int(cell / width)
		for d in [Vector2i(1,0),Vector2i(-1,0),Vector2i(0,1),Vector2i(0,-1)]:
			var xx: int = x+d.x
			var yy: int = y+d.y
			if xx<0 or xx>=width or yy<0 or yy>=height:
				continue
			var index := yy*width+xx
			if not visited[index] and not blocked[index]:
				# Occupancy alone can miss one-sided concave faces when a grid cell
				# lies inside a solid. Require a swept player move along every edge.
				if player.test_move(Transform3D(Basis(),locations[cell]),locations[index]-locations[cell]):
					continue
				visited[index]=1
				parent[index]=cell
				queue.append(index)
	return []

func run_validation() -> void:
	main._start_explore()
	floor_excludes.append(player.get_rid())
	for b in campus.campus_root.find_children("*","PhysicsBody3D",true,false):
		if not String(b.name).contains("COL_Ground"):
			floor_excludes.append(b.get_rid())
	for g in campus.manifest.gates:
		var gid: String = g.id
		var c := Vector2(g.model_position_blender_m[0],-g.model_position_blender_m[1])
		var angle: float = 0.0 if gid=="G1" else g.wall_angle_radians
		var u := Vector2(cos(angle),-sin(angle))
		var v := Vector2(-u.y,u.x)
		if v.dot(Vector2(g.inward[0],-g.inward[1])) < 0:
			v=-v
		var half: float = 68.0 if gid=="G1" else g.parameters_v8.wall_connection_half+4.0
		var tmin := -32.0 if gid=="G1" else -12.0
		var tmax := 20.0 if gid=="G1" else 12.0
		var width := int(2.0*half/GRID)+1
		var height := int((tmax-tmin)/GRID)+1
		var locations: Array[Vector3] = []
		for yy in height:
			for xx in width:
				var p := c+u*(-half+xx*GRID)+v*(tmin+yy*GRID)
				var q := PhysicsRayQueryParameters3D.create(Vector3(p.x,3,p.y),Vector3(p.x,-5,p.y),1)
				q.exclude=floor_excludes
				var hit := space().intersect_ray(q)
				locations.append(Vector3(p.x,(hit.position.y if not hit.is_empty() else -2.0)+player.HEIGHT*.5+.05,p.y))
		var sx := -19.0 if gid=="G1" else 0.0
		var seed := Vector2i(roundi((sx+half)/GRID),roundi(((-29.0 if gid=="G1" else -9.0)-tmin)/GRID))
		var target := Vector2i(seed.x,roundi(((15.0 if gid=="G1" else 9.0)-tmin)/GRID))
		for opened in [false,true]:
			campus.gate_controller.set_gate(gid,opened,true)
			await frames(4)
			var blocked := PackedByteArray()
			blocked.resize(locations.size())
			var query := PhysicsShapeQueryParameters3D.new()
			query.shape=player.shape
			query.collision_mask=1
			query.exclude=[player.get_rid()]
			for i in locations.size():
				query.transform=Transform3D(Basis(),locations[i])
				blocked[i]=0 if space().intersect_shape(query,1).is_empty() else 1
			var path := flood(blocked,width,height,seed,target,locations)
			var reachable := not path.is_empty()
			if reachable and not opened:
				save_json(OUT_VALID+"perimeter_candidate_"+gid+".json",{"path":path.map(func(i):return r3(locations[i]))})
			check(gid + (" open capsule flood finds a route" if opened else " closed capsule flood has NO edge/perimeter bypass"),reachable==opened,
				{"grid_m":GRID,"cells":locations.size(),"half_width_m":half,"normal_bounds":[tmin,tmax],"reachable":reachable})
	save_json(OUT_VALID+"v11_perimeter_seal.json",{"checks":results,"all_pass":results.all(func(r):return r.pass),
		"method":"Real PhysicsDirectSpaceState capsule occupancy on ground collider, 0.4 m grid, 4-neighbor flood with a swept player.test_move on every edge (prevents concave-solid interior false routes). Complements physical player walks; not a substitute for them."})
