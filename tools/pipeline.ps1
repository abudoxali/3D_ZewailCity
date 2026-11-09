<#
Zewail City V11 pipeline (Windows PowerShell). Run from anywhere:

    powershell -ExecutionPolicy Bypass -File tools\pipeline.ps1                  # everything
    powershell -ExecutionPolicy Bypass -Command "& 'tools/pipeline.ps1' -Steps paths,godot"   # some steps (-File passes a comma list as one string)

Steps (in order):
  scene     rebuild output/Zewail_City_3D.blend from permanent src/
  game      build output/game_ready/* and copy into game/godot
  paths     export the Blender camera / tour paths to JSON (~5 s)
  godot     re-import the Godot project (headless)
  validate  run the automated Godot checks (headless, ~1.5 min)
  export    build the Windows release into releases/ZewailCityExplorer_Windows_V15/
  visuals   V9 matched reference renders (src/render_v9.py after; poses stored in output/validation/v9)
  performance  1080p High captures + GPU benchmark into output/validation/v7/
  movie     record the V7 architectural showcase (CIN_V7_Architectural_Showcase) with Godot
            Movie Maker and encode MP4 (needs ffmpeg). Allow several minutes.
  movie-v6  re-record the historical V6 continuous walk.

Override tool paths with -Blender / -Godot if they are not the defaults below.
#>
param(
    [string[]]$Steps = @("scene", "game", "paths", "geometry", "game-check", "source-check", "godot", "validate", "export"),
    [string]$Blender = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
    [string]$Godot = "godot_console"
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Gd = Join-Path $Root "game\godot"
$Blend = Join-Path $Root "output\Zewail_City_3D.blend"

function Run($exe, [string[]]$a) {
    Write-Host ">> $exe $($a -join ' ')" -ForegroundColor Cyan
    & $exe @a
    if ($LASTEXITCODE -ne 0) { throw "$exe failed with exit code $LASTEXITCODE" }
}

foreach ($s in $Steps) {
    switch ($s) {
        "scene"    { Run $Blender @("-b", "--python-exit-code", "1", "--python", "$Root\src\build_scene.py") }
        "game"     { Run $Blender @("-b", $Blend, "--python-exit-code", "1", "--python", "$Root\src\build_game_assets.py") }
        "paths"    { Run $Blender @("-b", $Blend, "--python-exit-code", "1", "--python", "$Root\src\export_camera_paths.py") }
        "geometry" { Run $Blender @("-b", $Blend, "--python-exit-code", "1", "--python", "$Root\src\export_glb.py") }
        "game-check" { Run $Blender @("-b", "$Root\output\game_ready\Zewail_City_Game.blend", "--python-exit-code", "1", "--python", "$Root\src\validate_v5_assets.py") }
        "source-check" {
            Run $Blender @("-b", $Blend, "--python-exit-code", "1", "--python", "$Root\src\verify_scene.py")
            Run $Blender @("-b", $Blend, "--python-exit-code", "1", "--python", "$Root\src\validate_v8_source.py")
        }
        "godot"    { Run $Godot @("--headless", "--path", $Gd, "--import") }
        "validate" {
            $failedTests = @()
            foreach($testScene in @('Validate','V5Ground','V5Gates','V5Academic','V5Dormitory','V6Academic','V6Dormitory','V5Journey','V6Journey','V8Gates','V8Entries','V10AdminEntry','V11Gates','V11GateCoverage','V11PerimeterSeal','V11FullJourney','V11Ui')){
                # Deterministic 60 Hz simulation; no real-time synchronization.
                # Rendered performance and Windows smoke tests use real time.
                & "$Root/tools/.venv/Scripts/python.exe" "$Root/tools/v15_run.py" --timeout 240 "test_$testScene" -- $Godot --headless --fixed-fps 60 --path $Gd "res://tests/$testScene.tscn"
                if ($LASTEXITCODE -ne 0) { $failedTests += $testScene }
            }
            if ($failedTests.Count) { throw "Failed or timed out suites: $($failedTests -join ', ')" }
        }
        "visuals" { Run $Blender @('-b',$Blend,'--python-exit-code','1','--python',"$Root\src\render_v9.py",'--','after') }
        "performance" { Run $Godot @('--path',$Gd,'--resolution','1920x1080','res://tests/Validate.tscn','--','--capture','--preset=high') }
        "export"   {
            New-Item -ItemType Directory -Force "$Root\releases\ZewailCityExplorer_Windows_V15" | Out-Null
            Run $Godot @("--headless", "--path", $Gd, "--export-release", "Windows Desktop")
        }
        "movie"    {
            $avi = "$Root\output\tours\v7_architectural_showcase.avi"
            Run $Godot @("--path", $Gd, "--resolution", "1920x1080", "--write-movie", $avi, "--fixed-fps", "30",
                         "--", "--autotour=CIN_V7_Architectural_Showcase", "--quit-at-end", "--capture", "--preset=high")
            # Drop boot/spawn frames before the tour starts and the camera-reset frame at exit.
            $rawProbe = (& ffprobe -v error -show_streams -of json $avi | ConvertFrom-Json)
            if($LASTEXITCODE -ne 0){throw 'Raw video probe failed'}
            $rawFrames = [int](($rawProbe.streams | Where-Object codec_type -eq 'video' | Select-Object -First 1).nb_frames)
            $movieTrim = "trim=start_frame=3:end_frame=$($rawFrames-1),setpts=PTS-STARTPTS"
            Run "ffmpeg" @("-y", "-i", $avi, "-vf", $movieTrim, "-an", "-c:v", "libx264", "-preset", "slow", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart",
                           "$Root\output\tours\v7_architectural_showcase.mp4")
            & ffprobe -v error -show_streams -show_format -of json "$Root\output\tours\v7_architectural_showcase.mp4" | Set-Content "$Root\output\validation\v7\movie_probe.json"
            @{raw_frames=$rawFrames;trimmed_startup_frames=3;trimmed_exit_frames=1;final_frames=$rawFrames-4;source='CIN_V7_Architectural_Showcase'} | ConvertTo-Json | Set-Content "$Root\output\validation\v7\movie_recording.json"
        }
        default    { throw "unknown step '$s'" }
    }
}
Write-Host "Done: $($Steps -join ', ')" -ForegroundColor Green
