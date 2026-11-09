extends Control
## Original architectural illustration; not a surveyed campus plan.
func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	resized.connect(queue_redraw)

func _draw() -> void:
	draw_set_transform(Vector2.ZERO, 0, size / Vector2(850, 690))
	var ink := Color("6b9aaa")
	var light := Color("cee0e5")
	for y in range(180, 650, 48):
		draw_line(Vector2(25, y), Vector2(825, y), Color("e2ecee"), 1, true)
	for x in range(50, 850, 48):
		draw_line(Vector2(x, 160), Vector2(x, 650), Color("e2ecee"), 1, true)
	draw_colored_polygon(PackedVector2Array([Vector2(50,420),Vector2(340,310),Vector2(780,400),Vector2(480,590)]), Color("e1ecee"))
	for r in [Rect2(110,294,190,122),Rect2(520,302,206,132),Rect2(285,254,249,153)]:
		draw_style_box(_block_style(), r)
		for x in range(int(r.position.x + 16), int(r.end.x - 8), 28):
			draw_line(Vector2(x,r.position.y+32), Vector2(x,r.end.y-16), light, 9, true)
		draw_line(r.position, Vector2(r.end.x,r.position.y), ink, 3, true)
	draw_arc(Vector2(408,254), 68, PI, TAU, 48, ink, 3, true)
	draw_line(Vector2(340,254), Vector2(476,254), ink, 3, true)
	for x in range(340,490,30):
		draw_line(Vector2(x,330), Vector2(x,414), ink, 5, true)
	draw_line(Vector2(324,326), Vector2(498,326), ink, 5, true)
	for i in range(4):
		draw_line(Vector2(316-i*7,420+i*9),Vector2(505+i*7,420+i*9),ink,1.5,true)
	draw_line(Vector2(410,460),Vector2(520,632),Color("a3bdc6"),2,true)
	draw_line(Vector2(455,460),Vector2(645,632),Color("a3bdc6"),2,true)
	for p in [Vector2(180,480),Vector2(250,520),Vector2(675,490),Vector2(730,455)]:
		draw_line(p,p-Vector2(0,62),ink,2,true)
		for d in [Vector2(-28,-12),Vector2(26,-18),Vector2(-25,8),Vector2(22,5)]:
			draw_line(p-Vector2(0,62),p-Vector2(0,62)+d,ink,2,true)
	draw_circle(Vector2(76,126),28,Color("d3e5eb"))
	draw_line(Vector2(20,650),Vector2(820,650),ink,1,true)

func _block_style() -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = Color("f9fbfa")
	s.border_color = Color("8caeba")
	s.set_border_width_all(2)
	return s
