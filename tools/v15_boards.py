"""V14 (before) | V15 (after) matched boards from genuine Godot captures; same stored pose/FOV/preset."""
import json,sys
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];V=R/'output/validation/v15';A=V/(sys.argv[1] if len(sys.argv)>1 else 'final');B=A/'v14'
out=A/'comparisons';out.mkdir(exist_ok=True)
pa=json.loads((A/'v15/game_capture_perf_v15.json').read_text());pb=json.loads((B/'game_capture_perf_v14.json').read_text())
rows=[]
for v in pa['views']:
    s=Image.new('RGB',(1920,580),(20,20,20));d=ImageDraw.Draw(s)
    for i,(p,l) in enumerate([(B/'game_captures'/f'v14_{v}.png','V14 candidate (before)'),(A/'v15/game_captures'/f'v15_{v}.png','V15 candidate (after)')]):
        s.paste(Image.open(p).convert('RGB').resize((960,540)),(i*960,40));d.text((i*960+8,14),f'{l} - {v}',fill='white')
    same=pb['views'][v]['pose']==pa['views'][v]['pose']
    s.save(out/f'{v}.jpg',quality=90);rows.append(dict(view=v,board=str((out/f'{v}.jpg').relative_to(R)),same_pose=same))
(out/'index.json').write_text(json.dumps(dict(fov=pa['fov'],preset=pa['preset'],resolution=pa['actual_render_resolution'],boards=rows),indent=2))
print(len(rows),'boards; all same pose:',all(r['same_pose'] for r in rows))
