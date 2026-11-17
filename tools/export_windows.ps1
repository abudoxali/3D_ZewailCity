param([string]$Godot=$env:GODOT_EXE)
$ErrorActionPreference='Stop'
$r=Split-Path -Parent $PSScriptRoot
if(-not $Godot){$Godot=(Get-Command godot_console).Source}
New-Item -ItemType Directory -Force "$r/releases/Windows" | Out-Null
& $Godot --headless --path "$r/game/godot" --export-release 'Windows Desktop'
if($LASTEXITCODE){throw 'Windows export failed'}
