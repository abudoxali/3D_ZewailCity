"""V15 external asset licence/usage manifest (from the verified fetch manifest)."""
import json, hashlib
from pathlib import Path
R = Path(__file__).resolve().parents[1]
V = R / 'output/validation/v15'
fetch = json.loads((V / 'downloads/fetch_manifest.json').read_text())
USAGE = {
 'dirt': ('INSTALLED', 'Raised kerbed verge beds and outer approach beds (M_V15_Planted_Bed_Soil): Blender source albedo at the 2.0 m physical tile and Godot detail maps (pbr_mode 2, anti-tiling). Files: game/godot/assets/pbr/dirt/*_2k.jpg'),
 'crystalline_iceplant': ('INSTALLED', 'Groundcover rows in the verge beds: 4 clumps of 9 rosettes, decimated to ~6.5 % (~1.6k tris), greener derived albedo crystalline_iceplant_diff_1k_v15green.jpg (x(0.80,1.0,0.74), +15 % saturation). Files: references/assets/crystalline_iceplant/'),
 'asphalt_01': ('EVALUATED, NOT UPGRADED', 'The 2K set adds no visible detail over the installed V12 1K set at the 2.1 m tile; the albedo is inherently brown-grey and stays calibrated by the V12 tint (tone_targets.json, saturation 0.2). The dusty V12 trial is not reintroduced.'),
 'aerial_asphalt_01': ('REJECTED', '30 m physical tile = 68 px/m at 2K: too coarse at eye level; distinctive tyre marks/cracks would repeat visibly.'),
 'concrete_pavement': ('REJECTED (pilot)', 'Running-bond slab texture duplicates the V11 jointed slab sidewalks already matched to C02; no measured gain.'),
 'dry_ground_01': ('REJECTED', 'Cracked clay crust; the site is sandy loam (C02, P07), cracked mud is not evidenced.'),
}
NOT_DOWNLOADED = {
 'concrete_pavers': 'Rejected in V12 (zig-zag unit shape; campus pavers are rectangular running bond, photo D02).',
 'patterned_concrete_pavers': 'Not evidenced on the approach (C02/D02 show rectangular grey running bond).',
 'sand_01': 'Already installed since V12 as detail on sand/soil; as a whole surface it read as grey cracked crust (V12 QA).',
 'ambientcg.com': 'PavingStones125A was rejected in V13 (grain smearing); no further ambientCG set needed for this pilot.',
}
rows = []
for a in fetch['assets']:
    st, use = USAGE.get(a['asset'], ('DOWNLOADED', ''))
    rows.append(dict(a, status=st, usage=use))
extra = R / 'references/assets/crystalline_iceplant/textures/crystalline_iceplant_diff_1k_v15green.jpg'
out = {'schema': 'zewail-v15-assets/1', 'utc': fetch['utc'], 'licence_check': 'Poly Haven asset pages and https://polyhaven.com/license: CC0 1.0; provider MD5 verified for every file',
       'assets': rows, 'derived_files': [{'path': extra.relative_to(R).as_posix(), 'sha256': hashlib.sha256(extra.read_bytes()).hexdigest(), 'from': 'crystalline_iceplant_diff_1k.jpg (CC0)'}],
       'not_downloaded': NOT_DOWNLOADED, 'excluded_styles': 'No PSX, stylized, Ghibli or low-poly packs were used.'}
(V / 'external_asset_manifest.json').write_text(json.dumps(out, indent=1))
print(len(rows), 'assets')
