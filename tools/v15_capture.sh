#!/usr/bin/env bash
# V15 matched captures. Tag v14: the V14 candidate project (read-only use, its own harness; V15-only
# poses are skipped there). Tag v15: the V15 candidate. Same stored poses, FOV, preset, resolution.
set -e
cd "$(dirname "$0")/.."
P=tools/.venv/Scripts/python.exe; W="$(pwd -W)"; DIR=${1:-final}; WHICH=${2:-v15}
O=output/validation/v15/$DIR; mkdir -p $O/v14 $O/v15
for d in v14 v15; do cp output/validation/v15/poses_base.json $O/$d/game_view_poses.json; done
VIEWS=${VIEWS:-"G1_exterior_eye,O02_G1_inside,V12_G1_close,O03_G1_paving_curb,V14_g1_median_nose,V14_g1_gate_sand,V14_g1_forecourt_beds,V15_g1_inside_kerbs,V13_approach_aerial,main_approach_road,V12_approach_close,V15_median_eye,V15_crossover_bands_eye,V15_verge_bed_close,V15_kerb_close,V15_ring_junction_kerbs,V12_junction_dropoff_eye,junction_dropoff_ring,V12_junction_ring_east_eye,V14_junction_admin_close,V14_ring_sidewalk_step,ring_road_eye,admin_entrance_axis,admin_lobby_threshold,O07_academic_front,P13_court_photo,dorm_garden_paths,drone_overview,academic_court_aerial"}
G13="$W/output/validation/v15/baseline_v14_godot"; G14="$W/game/godot"
if [ "$WHICH" != "v15" ]; then $P tools/v15_run.py ${DIR}_cap_v14 --timeout 900 -- godot_console --path "$G13" --resolution 1920x1080 res://tests/V9Capture.tscn -- --tag=v14 "--out=$W/$O/v14" "--only=$VIEWS" --preset=high --uncapped; fi
if [ "$WHICH" != "v14" ]; then $P tools/v15_run.py ${DIR}_cap_v15 --timeout 900 -- godot_console --path "$G14" --resolution 1920x1080 res://tests/V9Capture.tscn -- --tag=v15 "--out=$W/$O/v15" "--only=$VIEWS" --preset=high --uncapped; fi
echo CAPTURE_DONE
