#!/usr/bin/env bash
# V15 iteration: full rebuild, scene verify, matched captures (V14 baseline copy + V15), boards.
set -e
cd "$(dirname "$0")/.."
T=$1; WHICH=${2:-v15}
bash tools/v15_rebuild.sh v15_$T
tools/.venv/Scripts/python.exe tools/v15_run.py v15_${T}_verify_scene --timeout 300 -- "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b output/Zewail_City_3D.blend --python-exit-code 1 --python src/verify_scene.py
bash tools/v15_capture.sh $T $WHICH
tools/.venv/Scripts/python.exe tools/v15_boards.py $T
echo ITER_DONE
