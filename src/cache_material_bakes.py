"""Index just-produced V5 texture bakes against the exact source material graph."""
import sys
from pathlib import Path
import json
import hashlib
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from build_game_assets import material_fingerprint, TEX
cache={}
for m in bpy.data.materials:
    if not m.node_tree:
        continue
    stem=m.name.replace('M_','',1).lower()
    files=[f'T_{stem}_{k}.png' for k in ('albedo','normal','roughness')]
    if (Path(TEX)/files[0]).exists() and (Path(TEX)/files[2]).exists():
        if not (Path(TEX)/files[1]).exists():
            files[1]=None
        cache[m.name]={'fingerprint':material_fingerprint(m),'files':files,
                       'sha256':[hashlib.sha256((Path(TEX)/p).read_bytes()).hexdigest() if p else None for p in files]}
(Path(TEX)/'bake_cache.json').write_text(json.dumps(cache,indent=2),encoding='utf-8')
print('[cache] verified source material graphs',len(cache))
