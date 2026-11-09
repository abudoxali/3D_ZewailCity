"""Apply the reproducible foundation pass to the already rebuilt Phase A candidate."""
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from utilities.ground_system import foundations, repair_foundation_winding
foundations()
repair_foundation_winding()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
