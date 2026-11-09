"""V15: archive old versions outside the project and promote the accepted V15 candidate.

Owner decision (2026-11-09): old versions are MOVED (not deleted) to
  C:/Users/Abud/Desktop/GitHub/zc/_archive_zewail_old/<UTC stamp>/
so rollback stays possible; V15 becomes the main project tree if QA passes.

Dry run by default; pass --apply to move. Every move is recorded in
output/validation/v15/archive_moves.json (source -> archive path, bytes, file count).
"""
import json
import shutil
import sys
import datetime
from pathlib import Path

R = Path(__file__).resolve().parents[1]
C = R / 'output/validation/v15/candidate'
STAMP = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
A = R.parent / '_archive_zewail_old' / STAMP
APPLY = '--apply' in sys.argv

# 1. Old versions and superseded outputs -> archive (relative to project root).
OLD = ['backups', 'v10_pre_v11_20261108T105635Z', 'releases/ZewailCityExplorer_Windows',
       'src', 'game', 'README.md',
       'output/Zewail_City_3D.blend', 'output/Zewail_City_3D.blend1', 'output/comparison', 'output/exports',
       'output/game_ready', 'output/previews', 'output/tours', 'output/verification_report.json',
       'output/validation/v15/baseline_v14_godot']
OLD += [f'output/validation/{p.name}' for p in sorted((R / 'output/validation').iterdir()) if p.name != 'v15']
OLD_TOOL_PREFIX = ('v10_', 'v11_', 'v12_', 'v121_', 'v13_', 'v14_', 'compare_v', 'render_v', 'inspect_', 'rebuild_live_v',
                   'mcp_render_', 'mcp_reopen_', 'reopen_v8', 'probe_v', 'preserve_', 'verify_delivery_v', 'verify_windows_v1',
                   'verify_windows_v5', 'verify_windows_v6', 'verify_windows_v7', 'verify_windows_v8', 'verify_windows_v9',
                   'v15_rebuild_noscene', 'finalize_live_source', 'render_live_ground', 'start_live_bridge')
KEEP_TOOLS = {'verify_windows_v15.ps1'}
OLD += [f'tools/{p.name}' for p in sorted((R / 'tools').iterdir())
        if p.name.startswith(OLD_TOOL_PREFIX) and p.name not in KEEP_TOOLS]
# Leftover debug probe carried since V9 (code review): not part of the delivered test set.
LEFTOVER_IN_CANDIDATE = ['game/godot/tests/V9LeakProbe.tscn', 'game/godot/tests/v9_leak_probe.gd',
                         'game/godot/tests/v9_leak_probe.gd.uid', 'game/godot/v11',
                         'output/v12_integration.json', 'Zewail_V6_Reference_Kit', 'tools']

# 2. Promotion: candidate subtree -> project root.
PROMOTE = [('src', 'src'), ('game', 'game'), ('output/Zewail_City_3D.blend', 'output/Zewail_City_3D.blend'),
           ('output/game_ready', 'output/game_ready'), ('output/exports', 'output/exports'),
           ('output/previews', 'output/previews'), ('output/tours', 'output/tours'),
           ('output/v12_material_diagnostics.json', 'output/v12_material_diagnostics.json'),
           ('output/validation/v11', 'output/validation/generator_logs'),
           ('releases/ZewailCityExplorer_Windows_V15', 'releases/ZewailCityExplorer_Windows_V15')]


def size(p):
    if p.is_file():
        return p.stat().st_size, 1
    fs = [q for q in p.rglob('*') if q.is_file()]
    return sum(q.stat().st_size for q in fs), len(fs)


log = {'apply': APPLY, 'archive_root': str(A), 'moved_to_archive': [], 'promoted': [], 'merged_references': [], 'missing': []}


def move(src, dst, bucket):
    if not src.exists():
        log['missing'].append(str(src.relative_to(R)))
        return
    b, n = size(src)
    log[bucket].append({'from': src.relative_to(R).as_posix(), 'to': str(dst), 'bytes': b, 'files': n})
    if APPLY:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))


for rel in OLD:
    move(R / rel, A / rel, 'moved_to_archive')
for rel in LEFTOVER_IN_CANDIDATE:
    move(C / rel, A / 'v15_candidate_leftovers' / rel, 'moved_to_archive')
for src, dst in PROMOTE:
    move(C / src, R / dst, 'promoted')
# references: merge candidate assets/json into the root register (photos stay local, git-ignored).
for p in sorted((C / 'references').iterdir()) if (C / 'references').exists() else []:
    dst = R / 'references' / p.name
    log['merged_references'].append(p.name)
    if APPLY:
        if dst.exists():
            old = A / 'references_replaced' / p.name
            old.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dst), str(old))
        shutil.move(str(p), str(dst))
tot = sum(x['bytes'] for x in log['moved_to_archive'])
log['archive_bytes'] = tot
out = R / 'output/validation/v15/archive_moves.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(log, indent=1))
print(('APPLIED' if APPLY else 'DRY RUN'), 'archive', round(tot / 1e9, 2), 'GB in', len(log['moved_to_archive']), 'items;',
      len(log['promoted']), 'promoted;', 'missing', log['missing'])
