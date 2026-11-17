# Zewail City 3D — Frozen V19

Final reusable campus baseline. Technical closure is verified; photographic/architectural fidelity remains **PARTIAL**. The single `STATUS.md` records closure, evidence and known limitations. No new visual development was performed during closure.

## Open and play

- Editable master: `output/Zewail_City_3D.blend` (Blender 5.2.3 LTS). Textures are packed and also resolve to project-relative files. All scene coordinates, object identities and material assignments are preserved.
- Godot source: open `game/godot/project.godot` in Godot 4.6.2 Standard, Forward+. Allow the first import to finish. No Python environment or MCP service is needed to play. The optional editor MCP plugin is retained but disabled by default; enable it manually only for future MCP-assisted editing.
- Windows build: run `releases/Windows/ZewailCityExplorer.exe`.
- Source launcher: PowerShell `./Launch.ps1`. It imports once if `.godot` is absent, then runs High quality. Graphics are configurable in-game. Controls and Arabic UI are unchanged; see in-game help.

## Modify and rebuild

Work on a **copy or new branch** of this frozen baseline. `FROZEN_BASELINE.json` identifies the delivered files; later modifications require new verification and hashes.

1. Edit the Blender master for manual art/cinematic work. Save into your working copy. Rendering cameras and editable source curves remain available.
2. For changes that must survive procedural regeneration, edit `src/utilities/` as well. These layered version-named modules are active dependencies, not obsolete milestones. `tools/export_alignments.py` exports editable transport curves for the existing source override round trip.
3. Run `./tools/rebuild.ps1` to regenerate the affected architecture/finalization and export game assets/camera paths from the master. Optional `-FromScratch` regenerates the full source campus and can overwrite manual edits; it was **not** invoked during maintenance. Choose the normal incremental build for the frozen master.
4. The build accepts `-Blender <executable>` and `-Godot <executable>` or `BLENDER_EXE` / `GODOT_EXE`. Blender is required for `.py` modelling/export scripts; standard Python runs the verification driver. Shapely is vendored for Windows Python 3.13; see `licenses/` for other platforms.
5. Run `py tools/verify_project.py` on Windows, or `python tools/verify_project.py` with an installed Python 3.11+ interpreter (or set `GODOT_EXE` for a different Godot binary). Frozen test inputs live in `game/godot/tests/fixtures/`; generated check results go to `output/checks/`. Do not weaken fixture contracts to hide geometry regressions.
6. Run `./tools/export_windows.ps1`, then `./tools/verify_windows.ps1`. Windows export templates for Godot 4.6.2 must already be installed.

`output/build_metadata/` holds generator inputs/reports needed by the retained build stack. `output/game_ready/` contains reusable per-building/per-asset GLBs, collision-ready whole-campus export, baked textures and a game-authoring Blender scene. The Godot runtime keeps its own complete importable campus GLB and textures. Those source/derived representations are intentional, not disposable cache duplicates. The closure did not rebuild terrain or alter architecture.

## Reuse in games or cinematics

- Blender: duplicate the master, retain metric units (1 unit = 1 metre), select required building/vegetation collections, and light/render with the existing cameras or your own. GLB export tools are under `src/`.
- Godot: copy the complete project, or import the campus/per-building GLBs into a new project. Retain scripts/shaders/material resources if you want the current PBR response, gate controls, collisions, player and tours. Avoid importing only mesh files while omitting their shader/texture dependencies.
- Coordinates: Blender origin is the dome centre, Z up, +Y toward G1. Godot conversion is `(x, y, z) = (Blender X, Blender Z, -Blender Y)`. Do not recenter building exports without accounting for their stored origins.
- Keep `LICENSES.md`, relevant manifests and notices with derived distributions. Original reference photos are private evidence, not public-release assets.

## Preserved history and limitations

A verified V15 rollback, the original unmodified V19 snapshot and earlier experiments/evidence are archived outside the active project. Their exact paths are in `STATUS.md` and `ARCHIVE_INDEX.json`. The root `.git` history is retained; no push was performed.

Known limits include estimated dome/facade/arcade proportions, sparse/approximate galleries and garden planting, unverified G2 external road connection, historical GIS alignment rather than surveyed geometry, and seven inherited Texture RID shutdown warnings. The maintenance freeze certifies portability/functionality, not a new visual accuracy acceptance.

Generated `.godot`, `__pycache__`, raw capture movies, old comparison iterations and development environments are excluded from the portable package. They can be recreated or found in the external archive.
