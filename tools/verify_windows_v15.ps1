$ErrorActionPreference='Stop'
$workspace=Split-Path -Parent $PSScriptRoot
$out=Join-Path $workspace 'output/validation/v15/windows_build'
$root=$workspace
$exe=Join-Path $root 'releases/ZewailCityExplorer_Windows_V15/ZewailCityExplorer.exe'
$userData=Join-Path $env:APPDATA 'Godot/app_userdata/Zewail City Campus Explorer'
New-Item -ItemType Directory -Force $out | Out-Null
$started=Get-Date
$p=Start-Process $exe -ArgumentList @('--audio-driver','Dummy','--resolution','1920x1080','--log-file',"`"$out/exe.log`"",'--','--smoketest','--capture','--mcp-bridge','--preset=high') -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 8
$ports=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object {$_.OwningProcess -eq $p.Id} | Select-Object LocalAddress,LocalPort)
if(-not $p.WaitForExit(150000)){throw "V15 smoke still running, PID $($p.Id)"}
foreach($name in @('smoketest.json','smoketest_arabic_menu.png','smoketest_gate.png','smoketest_v6_courtyard.png','smoketest_v6_dormitory.png')){
    $item=Get-Item -LiteralPath (Join-Path $userData $name)
    if($item.LastWriteTime -lt $started){throw "Stale smoke result: $name"}
    Copy-Item -LiteralPath $item.FullName -Destination (Join-Path $out $name)
}
$rep=Get-Content "$out/smoketest.json" | ConvertFrom-Json
$manifest=Get-Content "$root/output/game_ready/campus_manifest.json" | ConvertFrom-Json
$peVersion=(Get-Item -LiteralPath $exe).VersionInfo
$result=@{exe=$exe;exe_sha256=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLower();exit_code=$p.ExitCode;passed=$rep.passed;failed=$rep.failed;version=$rep.version;pe_file_version=$peVersion.FileVersion;source_blend_sha256=$rep.source_blend_sha256;source_hash_match=($rep.source_blend_sha256 -eq $manifest.source_blend_sha256);glb_hash_match=($rep.packaged_manifest_glb_sha256 -eq $manifest.game_glb_sha256);release_control_ports=$ports.Count;input_control=$rep.input_control;finished=(Get-Date).ToString('o')}
$result | ConvertTo-Json | Set-Content "$out/build_verification.json"
if($p.ExitCode -ne 0 -or $rep.failed -ne 0 -or $rep.passed -lt 38 -or $rep.version -ne '15.0.0' -or -not $result.source_hash_match -or -not $result.glb_hash_match -or $ports.Count -ne 0 -or $peVersion.FileVersion -notlike '15.0.0*'){throw 'V15 Windows smoke failed; inspect evidence'}
Write-Output "V15 Windows: $($rep.passed)/$($rep.passed+$rep.failed); exit 0; PBR textures packaged; no control ports."
