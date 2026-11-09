extends "res://tests/v5_ground.gd"
## Actual exported-campus physics acceptance; run by the integration owner.
## Blender (x, y, z) -> Godot (x, z, -y). Unfinished lobby ends at z=-9.4.

func run_validation() -> void:
	main._start_explore()
	await follow_route("Administration road to steps and supported landing",[Vector2(0,-40),Vector2(0,-33),Vector2(0,-30),Vector2(0,-25)])
	check("Administration landing floor contact at 0.72 m",player.is_on_floor() and absf(player.feet_position().y-.72)<.09,{"feet_y":player.feet_position().y})
	# One continuous traversal from the road, through the axis door, into the lobby,
	# then out via the second door. No teleport between entrance and exit legs.
	await follow_route("Administration axis doorway, lobby, second doorway and return",[Vector2(0,-40),Vector2(0,-33),Vector2(0,-25),Vector2(0,-21),Vector2(0,-17),Vector2(0,-12),Vector2(3,-12),Vector2(3,-17),Vector2(3,-21),Vector2(3,-25)])
	check("Administration returned landing has floor contact at 0.72 m",player.is_on_floor() and absf(player.feet_position().y-.72)<.09,{"feet_y":player.feet_position().y})
	# Every follow_route starts outside the canopy: inherited place() samples
	# ground from above, which could otherwise place the player on a roof.
	await follow_route("Administration second doorway reaches lobby floor",[Vector2(3,-40),Vector2(3,-33),Vector2(3,-25),Vector2(3,-21),Vector2(3,-17),Vector2(3,-12)])
	check("Administration lobby floor contact at 0.72 m",player.is_on_floor() and absf(player.feet_position().y-.72)<.09,{"feet_y":player.feet_position().y})
	for x in [-16.,16.]:
		check("Administration facade retained x="+str(x),not ray(Vector3(x,1.8,-25),Vector3(x,1.8,-15)).is_empty())
	for x in [-10.,0.,10.]:
		check("Administration bounded lobby back wall x="+str(x),not ray(Vector3(x,2.32,-10.4),Vector3(x,2.32,-8.4)).is_empty())
	for x in [0.,3.]:
		check("Administration doorway clear x="+str(x),ray(Vector3(x,1.8,-20),Vector3(x,1.8,-17.8)).is_empty())
	# V10 final review: the fixed lower glazing panels block (Codex High fix), only
	# the two doorways are open.
	for x in [-8.,-5.,7.,9.]:
		check("Administration lobby glazing blocks x="+str(x),not ray(Vector3(x,1.8,-25),Vector3(x,1.8,-15)).is_empty())
	# V10 Academic forecourt arcade (P09): walk its full length on the paved floor
	# under the upper floors, then confirm the 8.2 m soffit above.
	for ax in [22.3,-22.3]:
		await follow_route("Academic arcade walk x="+str(ax),[Vector2(ax,171.),Vector2(ax,190.),Vector2(ax,205.),Vector2(ax,216.)])
		check("Academic arcade floor contact x="+str(ax),player.is_on_floor() and absf(player.feet_position().y-.21)<.08 and player.position.z>213.,{"feet_y":player.feet_position().y,"z":player.position.z})
		check("Academic arcade soffit overhead x="+str(ax),not ray(Vector3(ax,2.,195.),Vector3(ax,9.,195.)).is_empty())
	save_json(OUT_VALID+"v10_admin_entry_runtime.json",{"checks":results,"all_pass":results.all(func(r):return r["pass"])})
