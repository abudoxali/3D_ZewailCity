#!/usr/bin/env bash
# V15 post-rebuild verification: regressions (18 suites), material diagnostics, geometry
# fingerprints vs V14, alternating GPU benchmark, Windows export and walkthrough recording.
cd "$(dirname "$0")/.."
P=tools/.venv/Scripts/python.exe; B="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"; C=.; L=output/validation/v15/logs
$P tools/v15_regressions.py > $L/v15_final_regressions.log 2>&1 || echo REGRESSION_FAILURE
$P tools/v15_run.py v15_final_material_diag --timeout 300 -- godot_console --headless --path $C/game/godot res://tests/V12Materials.tscn || echo MATDIAG_FAILURE
$P tools/v15_run.py v15_final_geometry --timeout 900 -- "$B" -b --python-exit-code 1 --python tools/v15_geometry_fingerprints.py -- v15_final || echo GEOMETRY_FAILURE
bash tools/v15_bench.sh
$P tools/v15_bench_report.py > $L/v15_final_bench_report.txt 2>&1
$P tools/v15_run.py v15_final_export --timeout 1200 -- godot_console --headless --path $C/game/godot --export-release "Windows Desktop" || echo EXPORT_FAILURE
echo FINAL_CHECKS_DONE
