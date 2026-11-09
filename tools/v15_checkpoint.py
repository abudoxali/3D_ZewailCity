"""V15 checkpoint: SHA-256 manifest of protected trees (read-only). Usage: v15_checkpoint.py <out.json>"""
import hashlib, json, sys, datetime
from pathlib import Path
R = Path(__file__).resolve().parents[1]
PROTECTED = ['releases/ZewailCityExplorer_Windows', 'output/Zewail_City_3D.blend', 'output/game_ready/campus_full.glb',
             'src', 'game/godot/scripts', 'game/godot/shaders', 'STATUS.md',
             'output/validation/v14/candidate', 'output/validation/v13/candidate/releases',
             'output/validation/v12/recovery/candidate/releases']
SKIP = ('.godot', '__pycache__')
def h(p):
    d = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            d.update(b)
    return d.hexdigest()
files = {}
for rel in PROTECTED:
    p = R / rel
    items = [p] if p.is_file() else sorted(q for q in p.rglob('*') if q.is_file() and not any(s in q.parts for s in SKIP))
    for q in items:
        files[q.relative_to(R).as_posix()] = [q.stat().st_size, h(q)]
out = Path(sys.argv[1])
if out.exists() and len(sys.argv) > 2 and sys.argv[2] == '--verify':
    ref = json.loads(out.read_text())['files']
    bad = [k for k in ref if k != 'STATUS.md' and files.get(k) != ref[k]]
    print(json.dumps({'checked': len(ref), 'mismatch': len(bad), 'examples': bad[:20]}))
    raise SystemExit(1 if bad else 0)
out.write_text(json.dumps({'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'count': len(files),
                           'bytes': sum(v[0] for v in files.values()), 'files': files}, indent=1))
print(len(files), sum(v[0] for v in files.values()))
