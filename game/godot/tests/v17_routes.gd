extends RefCounted
## V18 estimated rear public gallery, reached through actual rear return doors.
static func rear_gallery(side: float = -1.) -> Array:
	# V19 uses the physical gallery centre (75.05..78.6m annulus),
	# avoiding the jamb corner cut reproduced in uncapped MCP gameplay.
	var points:Array=[Vector2(0,330),Vector2(0,326.),Vector2(side*4.,325.5)]
	for deg in range(266,239,-2):
		var a=deg_to_rad(float(deg))
		points.append(Vector2(-side*76.8*cos(a),249.-76.8*sin(a)))
	return points
## Follow emitted public-path centerlines; never cut across photographed hedges.
static func garden() -> Array:
	var plan=JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/dorm_garden_plan.json"))
	var points:Array=[]
	var first:Array=plan.walk_paths_godot[0]
	var branch:Array=plan.walk_paths_godot[2]
	var junction:int=0;var distance:float=INF
	for i in first.size():
		var p:Vector2=Vector2(first[i][0],first[i][1])
		var d:float=p.distance_to(Vector2(410,584))
		if d<distance:distance=d;junction=i
	for p in first.slice(0,junction+1):points.append(Vector2(p[0],p[1]))
	var end:int=0;distance=INF
	for i in branch.size():
		var p:Vector2=Vector2(branch[i][0],branch[i][1])
		var d:float=p.distance_to(Vector2(424,608))
		if d<distance:distance=d;end=i
	for p in branch.slice(0,end+1):points.append(Vector2(p[0],p[1]))
	points.append(Vector2(424,608));points.append(Vector2(409,608));points.append(Vector2(404,608))
	return points
