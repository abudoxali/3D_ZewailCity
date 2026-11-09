extends Node
func _ready():
    var report={"textures":[],"materials":[],"failures":[]}
    var assets=["asphalt_01","concrete_pavement_03","sand_01","sparse_grass","beige_wall_001"]
    for asset in assets:
        for kind in ["diff","nor_gl","rough"]:
            var path="res://assets/pbr/%s/%s_%s_%s" % [asset,asset,kind,"2k.jpg" if asset=="paving_stones_125a" else "1k.jpg"]
            var tex=load(path) as Texture2D
            if tex==null:
                report.failures.append("Missing "+path)
                continue
            var img=tex.get_image()
            var row={"path":path,"size":[tex.get_width(),tex.get_height()],"format":img.get_format(),"mipmaps":img.has_mipmaps()}
            if not img.has_mipmaps(): report.failures.append("No mipmaps: "+path)
            if img.is_compressed(): img.decompress()
            var sample=img.get_pixel(img.get_width()/2,img.get_height()/2)
            row["sample_linear_data"]=[sample.r,sample.g,sample.b]
            if kind=="nor_gl":
                var xy=Vector2(sample.r*2-1,sample.g*2-1)
                row["reconstructed_gl_z"]=sqrt(maxf(0.001,1.0-xy.length_squared()))
            report.textures.append(row)
    var main=load("res://scenes/Main.tscn").instantiate()
    add_child(main)
    while not main.ready_done: await get_tree().process_frame
    for key in main.campus._ground_cache:
        var mat=main.campus._ground_cache[key]
        report.materials.append({"name":mat.resource_name,"shader":mat.shader.resource_path,"pbr_mode":mat.get_shader_parameter("pbr_mode"),"tile_m":mat.get_shader_parameter("pbr_tile_m"),"tint":mat.get_shader_parameter("pbr_tint")})
    report["renderer"]=RenderingServer.get_video_adapter_name()
    report["anisotropy_enum"]=ProjectSettings.get_setting("rendering/textures/default_filters/anisotropic_filtering_level")
    report["source_of_normals"]="Provider OpenGL +Y maps; source_color on diffuse only; world projection derivative frame; +Z reconstructed for BC5"
    var f=FileAccess.open("res://../../output/v12_material_diagnostics.json",FileAccess.WRITE)
    f.store_string(JSON.stringify(report,"  "));f.close()
    print("[V12 materials] ",report.textures.size()," maps; ",report.materials.size()," material mappings; ",report.failures.size()," failures")
    get_tree().quit(0 if report.failures.is_empty() else 1)
