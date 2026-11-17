extends "res://tests/v5_ground.gd"
## V18 photo correction: local upper landing 4.41 m, Academic pad -1.2 m.
## Independent absolute contact target; original 15 cm tolerance retained.
const UPPER_WORLD := 3.21

## V11: the Academic core is a two-level system. Two great stairs (Blender y -208.9 ->
## -219, |x| 7..19.5) reach a 4.41 m terrace, covered hall and court bridge with two railed
## voids over the open lower passage (|x| < 7). Godot z = -Blender y.

## Balustrade rails are open bars: probe at the actual rail heights above the 4.41 m deck.
func _rail_hit(a: Vector3, b: Vector3) -> bool:
	for offset in [.135,.435,.735,1.09]:
		var h:float=UPPER_WORLD+offset
		if not ray(Vector3(a.x,h,a.z),Vector3(b.x,h,b.z)).is_empty():
			return true
	return false

func run_validation() -> void:
	main._start_explore()
	await follow_route("academic approach > lower passage > courtyard > rear ground",[
		Vector2(-2.3,200),Vector2(-2.3,215),Vector2(-2.3,235),Vector2(-2.3,253),Vector2(0,280),Vector2(0,310),Vector2(0,335),Vector2(0,352),Vector2(0,368)])
	for x in [-13.,13.]:
		await follow_route("great stair ascend "+str(x),[Vector2(x,200),Vector2(x,212),Vector2(x,221.5)])
		var height: float=player.feet_position().y
		check("great stair reaches the photo-corrected terrace "+str(x),absf(height-UPPER_WORLD)<.15,{"feet_y":height,"expected_world_m":UPPER_WORLD})
		await follow_route("terrace > covered hall "+str(x),[Vector2(x,221.5),Vector2(signf(x)*11.,233.),Vector2(signf(x)*11.,245.)],false)
		check("covered hall at corrected terrace datum "+str(x),player.is_on_floor() and absf(player.feet_position().y-UPPER_WORLD)<.15,{"feet_y":player.feet_position().y})
		await follow_route("hall > court bridge "+str(x),[Vector2(signf(x)*11.,245.),Vector2(signf(x)*11.,262.)],false)
		check("court bridge walkable "+str(x),player.is_on_floor() and absf(player.feet_position().y-UPPER_WORLD)<.15,{"feet_y":player.feet_position().y})
		# Real movement toward the covered void: the balustrade must hold the player on the deck.
		player.face_direction(Vector3(-signf(x),0,0))
		await hold("move_forward",2.5)
		check("void balustrade stops a walking player "+str(x),player.is_on_floor() and player.feet_position().y>UPPER_WORLD-.21 and absf(player.position.x)>5.8,{"position":r3(player.position)})
		# The guard test deliberately leaves the capsule at x=6.2 beside the
		# void. Centre it behind the actual recessed doorway before crossing it.
		await follow_route("back to the stair head "+str(x),[Vector2(signf(x)*6.2,262.),Vector2(signf(x)*11.,250.),Vector2(signf(x)*11.,233.),Vector2(x,221.5)],false)
		# Keep the same real player position at the landing when testing descent.
		player.face_direction(Vector3(0,0,-1))
		await hold("move_forward",4.)
		check("great stair descent grounded "+str(x),player.is_on_floor() and player.position.z<208 and player.feet_position().y<.5,{"position":r3(player.position)})
	# V7: tiers are concentric with the inner glazing (r 62/51/40 m). Follow the public
	# walkway between platform edge and glass (r ~69.5 m) round to the central route.
	await follow_route("courtyard seating circulation",[Vector2(0,258),Vector2(30,258),Vector2(55,256),Vector2(68.4,261.1),
		Vector2(63,278.4),Vector2(53.2,293.7),Vector2(39.9,305.9),Vector2(23.8,314.3),Vector2(6.1,318.2),Vector2(0,318.5)])
	# Off-path checks: lobby walls stay solid beside the passage; the passage clears a capsule.
	var wall:=ray(Vector3(3,1.7,232),Vector3(11,1.7,232))
	check("academic lobby wall beside passage remains solid",not wall.is_empty())
	var clear:=ray(Vector3(-2.3,.8,215),Vector3(-2.3,.8,262))
	check("lower passage eye-height clearance",clear.is_empty())
	# V11 owner 14/08: real railed openings, no roof slab over the voids.
	for zz in [225.5, 250.]:
		check("void guarded by a collidable railing z="+str(zz),_rail_hit(Vector3(9,0,zz),Vector3(-9,0,zz)))
		var down:=ray(Vector3(0,6.5,zz),Vector3(0,-1.0,zz))
		check("void opens onto the lower passage z="+str(zz),not down.is_empty() and down.position.y<.6,{"hit_y":down.position.y if not down.is_empty() else null})
	check("terrace front between the stairs is guarded",_rail_hit(Vector3(-3,0,221.),Vector3(-3,0,217.)))
	save_json("res://../../output/checks/academic_runtime.json",{"checks":results,"all_pass":results.all(func(r):return r["pass"])})
