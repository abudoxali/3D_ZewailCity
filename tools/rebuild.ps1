param([switch]$FromScratch,[string]$Blender=$env:BLENDER_EXE,[string]$Godot=$env:GODOT_EXE)
$ErrorActionPreference='Stop'
$r=Split-Path -Parent $PSScriptRoot
if(-not $Blender){$Blender=(Get-Command blender -ErrorAction SilentlyContinue).Source}
if(-not $Blender){$Blender='C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'}
if(-not $Godot){$Godot=(Get-Command godot_console -ErrorAction SilentlyContinue).Source}
if(-not $Godot){$Godot=(Get-Command godot).Source}
function B([string[]]$Arguments){ & $Blender @Arguments; if($LASTEXITCODE){throw 'Blender stage failed'} }
if($FromScratch){B -Arguments @('--factory-startup','-b','--python-exit-code','1','--python',"$r/src/build_scene.py")}
B -Arguments @('--factory-startup','-b',"$r/output/Zewail_City_3D.blend",'--python-exit-code','1','--python',"$r/tools/finalize_native.py")
B -Arguments @('--factory-startup','-b',"$r/output/Zewail_City_3D.blend",'--python-exit-code','1','--python',"$r/tools/prepare_portable.py")
B -Arguments @('--factory-startup','-b',"$r/output/Zewail_City_3D.blend",'--python-exit-code','1','--python',"$r/src/build_game_assets.py")
B -Arguments @('--factory-startup','-b',"$r/output/Zewail_City_3D.blend",'--python-exit-code','1','--python',"$r/src/export_camera_paths.py")
& $Godot --headless --path "$r/game/godot" --import
if($LASTEXITCODE){throw 'Godot import failed'}
Write-Output 'Rebuild complete. Run tools/verify_project.py and re-export Windows before refreezing.'
