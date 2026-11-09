#!/usr/bin/env bash
# Back-to-back 10-view benchmark: V14 candidate vs V15 candidate (x2, alternating), identical settings.
set -e
cd "$(dirname "$0")/.."
P=tools/.venv/Scripts/python.exe; W="$(pwd -W)"; F=output/validation/v15/bench
BENCH="G1_exterior_eye,O16_dome_axis_terrace,P13_court_photo,academic_central_passage,academic_stair_left,admin_entrance_axis,dorm_garden_paths,drone_overview,main_approach_road,ring_road_eye,V15_median_eye,V13_approach_aerial"
declare -A G=([v14]="$W/output/validation/v15/baseline_v14_godot" [v15]="$W/game/godot")
for v in v14 v15; do mkdir -p $F/$v; cp output/validation/v15/poses_base.json $F/$v/game_view_poses.json; done
for run in a b; do for v in v14 v15; do
$P tools/v15_run.py bench_${v}_$run --timeout 400 -- godot_console --path "${G[$v]}" --resolution 1920x1080 res://tests/V9Capture.tscn -- --tag=${v}_$run "--out=$W/$F/$v" "--only=$BENCH" --preset=high --uncapped --skip-images
done; done
echo BENCH_DONE
