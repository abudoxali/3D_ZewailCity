"""After promotion: point the V15 tools at the main project tree instead of the isolated candidate.
The V14 baseline project is archived, so captures/bench default to the main tree only."""
from pathlib import Path
T = Path(__file__).resolve().parent
EDITS = {
    'v15_rebuild.sh': [('# V13 candidate full source rebuild (isolated tree output/validation/v15/candidate).',
                        '# Full source rebuild of the main project tree: scene -> game assets -> paths -> GLB -> checks -> import.'),
                       ('C=output/validation/v15/candidate', 'C=.')],
    'v15_final_checks.sh': [('C=output/validation/v15/candidate', 'C=.')],
    'v15_iter.sh': [('output/validation/v15/candidate/output/Zewail_City_3D.blend', 'output/Zewail_City_3D.blend'),
                    ('output/validation/v15/candidate/src/verify_scene.py', 'src/verify_scene.py'),
                    ('T=$1; WHICH=${2:-both}', 'T=$1; WHICH=${2:-v15}')],
    'v15_capture.sh': [('G14="$W/output/validation/v15/candidate/game/godot"', 'G14="$W/game/godot"'),
                       ('WHICH=${2:-both}', 'WHICH=${2:-v15}')],
    'v15_bench.sh': [('[v15]="$W/output/validation/v15/candidate/game/godot"', '[v15]="$W/game/godot"')],
    'v15_regressions.py': [("G=O/'candidate/game/godot'", "G=R/'game/godot'")],
    'v15_optimize_imports.py': [("G=R/'output/validation/v15/candidate/game/godot'", "G=R/'game/godot'")],
    'v15_geometry_fingerprints.py': [("C=O/'candidate'", "C=R")],
    'v15_manifest.py': [("R / 'output/validation/v15/candidate/references/", "R / 'references/")],
    'verify_windows_v15.ps1': [("$root=Join-Path $workspace 'output/validation/v15/candidate'", "$root=$workspace")],
    'pipeline.ps1': [('tools/v11_run.py', 'tools/v15_run.py'),
                     ('releases/ZewailCityExplorer_Windows/', 'releases/ZewailCityExplorer_Windows_V15/'),
                     ('releases\\ZewailCityExplorer_Windows"', 'releases\\ZewailCityExplorer_Windows_V15"')],
}
for name, pairs in EDITS.items():
    p = T / name
    raw = p.read_bytes().decode('utf-8')
    for a, b in pairs:
        if a not in raw:
            print('WARN not found', name, a[:60])
        raw = raw.replace(a, b)
    p.write_bytes(raw.encode('utf-8'))
print('retargeted', len(EDITS))
