#!/usr/bin/env bash
# Full source rebuild of the main project tree: scene -> game assets -> paths -> GLB -> checks -> import.
set -e
cd "$(dirname "$0")/.."
B="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"
C=.
P=tools/.venv/Scripts/python.exe
T=${1:-v13}
$P tools/v15_run.py ${T}_scene --timeout 1500 -- "$B" -b --python-exit-code 1 --python $C/src/build_scene.py
$P tools/v15_run.py ${T}_game --timeout 1500 -- "$B" -b $C/output/Zewail_City_3D.blend --python-exit-code 1 --python $C/src/build_game_assets.py
$P tools/v15_run.py ${T}_paths --timeout 300 -- "$B" -b $C/output/Zewail_City_3D.blend --python-exit-code 1 --python $C/src/export_camera_paths.py
$P tools/v15_run.py ${T}_source_glb --timeout 1500 -- "$B" -b $C/output/Zewail_City_3D.blend --python-exit-code 1 --python $C/src/export_glb.py
$P tools/v15_run.py ${T}_game_check --timeout 300 -- "$B" -b $C/output/game_ready/Zewail_City_Game.blend --python-exit-code 1 --python $C/src/validate_v5_assets.py
$P tools/v15_run.py ${T}_verify_scene --timeout 300 -- "$B" -b $C/output/Zewail_City_3D.blend --python-exit-code 1 --python $C/src/verify_scene.py
$P tools/v15_run.py ${T}_v8_source --timeout 300 -- "$B" -b $C/output/Zewail_City_3D.blend --python-exit-code 1 --python $C/src/validate_v8_source.py
$P tools/v15_run.py ${T}_import --timeout 1200 -- godot_console --headless --path $C/game/godot --import
$P tools/v15_optimize_imports.py
$P tools/v15_run.py ${T}_reimport --timeout 1200 -- godot_console --headless --path $C/game/godot --import
echo REBUILD_DONE
