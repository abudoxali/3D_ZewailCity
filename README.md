# Zewail City 3D Campus — reconstruction, explorer and Blender source

An evidence-based 3D reconstruction of the Zewail City of Science, Technology and Innovation campus
(6th of October, Egypt): a procedural Blender source scene, a game-ready export and a Godot 4.6
walk/fly explorer with an Arabic (default) and English interface. It is an **estimated
reconstruction, not a survey**; see [STATUS.md](STATUS.md) for the current verification state and
remaining known differences.

Current version: **15.0.0** — the V15 pilot rebuilt the main entrance corridor
(Gate G1 → main approach → median → walkways → Administration and Cultural Building forecourt):
modular precast kerb units, raised kerbed planting beds with CC0 groundcover, crossover paver bands,
a worn palm-median lawn and softly graded natural ground. Details, measurements and the
before/after evidence are in [STATUS.md](STATUS.md).

## Repository layout

| Path | Contents |
|---|---|
| `src/` | Procedural Blender generators (`build_scene.py`, `build_game_assets.py`, `utilities/`). `utilities/survey.py` holds the OSM/Sentinel-2 survey layout; `utilities/v15_corridor.py` the V15 corridor system. |
| `game/godot/` | Godot 4.6 explorer project (scenes, scripts, shaders, regression tests, CC0 PBR maps, campus GLB via Git LFS). |
| `references/` | Evidence registers, geodata, OSM/NDVI extracts and CC0 asset sources with licence manifests. Reference *photographs* are kept out of this public repository. |
| `tools/` | Pipeline, capture, benchmark, regression and asset tools (`v15_*`), plus vendored Shapely. |
| `output/Zewail_City_3D.blend` | Authoritative editable Blender scene (Git LFS). |
| `output/validation/v15/` | V15 evidence: matched comparisons, benchmark, regression logs, asset manifest. |
| `docs/` | Game asset guide. |

## Run the explorer

**From the Godot project** (Godot 4.6.2):

```bash
godot --path game/godot
```

A packaged Windows build is produced with `godot --headless --path game/godot --export-release "Windows Desktop"`
(output under `releases/`, not committed).

### Controls

| Key | Action |
|---|---|
| W A S D / mouse | Move / look |
| Shift | Sprint (walk), boost ×4 (fly) |
| Space | Jump (walk), ascend (fly) |
| E | Operate a nearby gate (walk); ascend (fly) |
| Ctrl or Q | Descend (fly) |
| F | Switch walk ↔ drone fly |
| C | Fly: toggle collision (no-clip) |
| R | Reset to the last spawn point |
| 1 – 7 | Teleport to a spawn point (7 = outside the main gate) |
| T | Guided tour; P pauses, Esc exits |
| M | Minimap |
| H / F1 | Help |
| F12 | Screenshot to `user://screenshots` |
| Esc | Pause menu |

Command line (after `--`): `--explore`, `--autotour=TOUR_Guided`, `--quit-at-end`, `--preset=low|medium|high`, `--smoketest`.

## Rebuild pipeline

Requires Blender 5.2.3 and Godot 4.6.2 (`godot_console` on PATH) and the project venv in `tools/.venv`
(`tools/requirements-v5.txt`).

```bash
bash tools/v15_rebuild.sh <tag>      # scene -> game assets -> paths -> source GLB -> checks -> Godot import
python tools/v15_regressions.py      # 18 Godot regression suites (incl. V15Corridor)
bash tools/v15_capture.sh <dir> v15  # 1920x1080 High captures at stored poses
bash tools/v15_bench.sh              # 10-view GPU benchmark
```

## Coordinate system

* Metres. Origin = dome centre. +Y = toward the main gate along the campus axis (N 36.5° W). Z up.
* Godot / glTF: (x, y, z)_godot = (x, z, −y)_blender.
* The OSM → Blender transformation is documented in `src/utilities/survey.py`.

## Licences

* Source code: see repository owner.
* Poly Haven assets (asphalt_01, concrete_pavement_03, sand_01, sparse_grass, beige_wall_001, dirt,
  pachira_aquatica_01, crystalline_iceplant, kloofendal sky): CC0 1.0. Innerscene palm models: CC0.
  Per-file sources and SHA-256 are in `game/godot/assets/pbr/manifest.json`,
  `references/assets/*/manifest.json` and `output/validation/v15/external_asset_manifest.json`.
* OpenStreetMap data © OpenStreetMap contributors (ODbL); Copernicus Sentinel-2 data.

## Optional editor integrations (not vendored)

Live Blender/Godot inspection used these MCP servers; clone them into `tools/integrations/` if needed:
[ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) and [slangwald/godot-mcp](https://github.com/slangwald/godot-mcp).

## History and rollback

Earlier versions (V1–V14, the V11 Windows release and all backups) are archived outside this repository by
the owner's decision; see the rollback notes in [STATUS.md](STATUS.md).
