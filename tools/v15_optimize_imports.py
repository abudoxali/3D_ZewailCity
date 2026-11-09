from pathlib import Path
R=Path(__file__).resolve().parents[1];G=R/'game/godot'
for p in (G/'assets/pbr').rglob('*.import'):
    if not p.name.endswith(('.jpg.import','.png.import')):continue
    s=p.read_text().replace('compress/mode=0','compress/mode=2').replace('compress/high_quality=false','compress/high_quality=true').replace('mipmaps/generate=false','mipmaps/generate=true')
    s=s.replace('compress/normal_map=0','compress/normal_map=1' if 'nor_gl' in p.name else 'compress/normal_map=2')
    p.write_text(s)
p=G/'project.godot';s=p.read_text()
if 'textures/default_filters/anisotropic_filtering_level' not in s:s+='\ntextures/default_filters/anisotropic_filtering_level=4\n'
p.write_text(s)
print('PBR originals use durable VRAM compression, mipmaps, GL normal import, 16x anisotropy')
