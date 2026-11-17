param([string]$Godot=$env:GODOT_EXE)
$ErrorActionPreference='Stop'
if(-not $Godot){$Godot=(Get-Command godot_console -ErrorAction SilentlyContinue).Source}
if(-not $Godot){$Godot=(Get-Command godot).Source}
if(-not (Test-Path "$PSScriptRoot/game/godot/.godot/imported")){
 & $Godot --headless --path "$PSScriptRoot/game/godot" --import
 if($LASTEXITCODE){throw 'First import failed'}
}
& $Godot --path "$PSScriptRoot/game/godot" -- --preset=high
