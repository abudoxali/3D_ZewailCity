extends RefCounted
const INK := Color("173b51")
const BLUE := Color("146e8c")
const MUTED := Color("56717d")
const PAPER := Color("f4f7f6")
const FONT := preload("res://ui/fonts/NotoSansArabic.ttf")

static func box(color: Color, radius := 10, border := Color.TRANSPARENT) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = color
	s.set_corner_radius_all(radius)
	s.set_border_width_all(2)
	s.border_color = border
	s.content_margin_left = 24
	s.content_margin_right = 24
	s.content_margin_top = 6
	s.content_margin_bottom = 6
	return s

static func theme() -> Theme:
	var th := Theme.new()
	th.default_font = FONT
	th.default_font_size = 23
	for type in ["Label", "Button", "CheckBox", "OptionButton", "PopupMenu"]:
		th.set_color("font_color", type, INK)
		th.set_color("font_hover_color", type, BLUE)
		th.set_color("font_pressed_color", type, INK)
		th.set_color("font_focus_color", type, INK)
	for type in ["Button", "OptionButton"]:
		th.set_stylebox("normal", type, box(Color.WHITE))
		th.set_stylebox("hover", type, box(Color("e0eef1")))
		th.set_stylebox("pressed", type, box(Color("c8e0e8")))
		th.set_stylebox("focus", type, box(Color.TRANSPARENT, 10, BLUE))
		th.set_stylebox("normal_mirrored", type, box(Color.WHITE))
		th.set_stylebox("hover_mirrored", type, box(Color("e0eef1")))
		th.set_stylebox("pressed_mirrored", type, box(Color("c8e0e8")))
	th.set_stylebox("panel", "PopupMenu", box(PAPER, 10, Color("a5c7d1")))
	th.set_stylebox("hover", "PopupMenu", box(Color("d7e9ee")))
	th.set_stylebox("slider", "HSlider", box(Color("bdcfd5"), 3))
	th.set_stylebox("grabber_area", "HSlider", box(BLUE, 3))
	return th

static func icon(action: String, white := false) -> Texture2D:
	var paths := {
		"StartExploration": '<path d="M9 5l11 9-11 9z"/>',
		"GuidedTour": '<circle cx="14" cy="14" r="11"/><path d="M18 9l-2 7-6 3 2-7z"/>',
		"LocationSelection": '<path d="M14 25s9-10 9-15a9 9 0 0 0-18 0c0 5 9 15 9 15z"/><circle cx="14" cy="10" r="3"/>',
		"GraphicsSettings": '<path d="M3 7h22M3 14h22M3 21h22"/><path d="M9 3v8M19 10v8M11 17v8"/>',
		"Exit": '<path d="M14 2v11M7 6a11 11 0 1 0 14 0"/>',
	}
	var svg := '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28"><g fill="none" stroke="#%s" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">%s</g></svg>' % ["ffffff" if white else "146e8c", paths.get(action, "")]
	var img := Image.new()
	img.load_svg_from_string(svg)
	return ImageTexture.create_from_image(img)
