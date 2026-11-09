"""V15: fetch a small CC0 Poly Haven shortlist with provider MD5 verification and SHA-256 record.
Each asset goes to its own empty directory under output/validation/v15/downloads/<asset>/."""
import hashlib, json, sys, urllib.request, datetime
from pathlib import Path
R = Path(__file__).resolve().parents[1]
D = R / 'output/validation/v15/downloads'
UA = {'User-Agent': 'zc-v15-asset-fetch/1.0'}
TEX = {'asphalt_01': '2k', 'aerial_asphalt_01': '2k', 'concrete_pavement': '2k', 'dirt': '2k', 'dry_ground_01': '2k'}
MAPS = {'Diffuse': 'diff', 'nor_gl': 'nor_gl', 'Rough': 'rough', 'AO': 'ao'}
MODELS = {'crystalline_iceplant': '1k'}
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()
def save(asset, url, md5, name=None):
    data = get(url)
    ok = hashlib.md5(data).hexdigest() == md5 if md5 else None
    p = D / asset / (name or url.rsplit('/', 1)[1]); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
    return dict(path=p.relative_to(R).as_posix(), source_url=url, bytes=len(data), provider_md5_verified=ok,
                sha256=hashlib.sha256(data).hexdigest())
rows = []
for asset, res in TEX.items():
    info = json.loads(get(f'https://api.polyhaven.com/info/{asset}'))
    files = json.loads(get(f'https://api.polyhaven.com/files/{asset}'))
    out = []
    for key, short in MAPS.items():
        if key not in files: continue
        f = files[key][res]['jpg']
        out.append(dict(map=short, **save(asset, f['url'], f.get('md5'))))
    rows.append(dict(asset=asset, kind='texture', page=f'https://polyhaven.com/a/{asset}', license='CC0 1.0',
                     license_url='https://polyhaven.com/license', authors=list(info.get('authors', {})),
                     physical_size_mm=info.get('dimensions'), resolution=res, files=out))
    print(asset, [(o['map'], o['provider_md5_verified']) for o in out], flush=True)
for asset, res in MODELS.items():
    info = json.loads(get(f'https://api.polyhaven.com/info/{asset}'))
    files = json.loads(get(f'https://api.polyhaven.com/files/{asset}'))
    g = files['gltf'][res]['gltf']
    out = [dict(map='gltf', **save(asset, g['url'], g.get('md5')))]
    for rel, inc in g.get('include', {}).items():
        out.append(dict(map=rel, **save(asset, inc['url'], inc.get('md5'), name=rel)))
    rows.append(dict(asset=asset, kind='model', page=f'https://polyhaven.com/a/{asset}', license='CC0 1.0',
                     license_url='https://polyhaven.com/license', authors=list(info.get('authors', {})),
                     polycount=info.get('polycount'), resolution=res, files=out))
    print(asset, len(out), all(o['provider_md5_verified'] for o in out), flush=True)
(D / 'fetch_manifest.json').write_text(json.dumps({'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'assets': rows}, indent=1))
