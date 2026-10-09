param([string]$Installer = '.artifacts\desktop-windows\JevWIN_0.4.0_setup-isolated-test.exe')
$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$installDir = [IO.Path]::GetFullPath((Join-Path $workspace '.artifacts\install-test'))
$dataDir = [IO.Path]::GetFullPath((Join-Path $workspace '.artifacts\installed-test-data'))
if (-not $installDir.StartsWith($workspace + '\') -or -not $dataDir.StartsWith($workspace + '\')) { throw 'Test paths escaped workspace' }
$registry = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\JevWIN-Isolated-Test'
if (Test-Path -LiteralPath $registry) { throw 'An isolated installation already exists; preserve it and inspect before testing' }
$installerPath = (Resolve-Path (Join-Path $workspace $Installer)).Path
if ((Split-Path $installerPath -Leaf) -notlike '*-isolated-test.exe') { throw 'Only the isolated installer may run in this test' }
function LegacyFingerprint {
    $legacy = Join-Path $env:LOCALAPPDATA 'JevWIN'
    if (-not (Test-Path -LiteralPath $legacy)) { return '' }
    return ((Get-ChildItem -LiteralPath $legacy -File | Sort-Object Name | ForEach-Object { $_.Name + ':' + (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }) -join '|')
}
$beforeLegacy = LegacyFingerprint
$primaryRegistry = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\JevWIN'
$beforePrimary = if (Test-Path $primaryRegistry) { (Get-ItemProperty $primaryRegistry | Select-Object DisplayVersion,InstallLocation | ConvertTo-Json -Compress) } else { '' }
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
$marker = Join-Path $dataDir 'preservation-fixture.txt'
'Synthetic preservation fixture' | Set-Content -LiteralPath $marker -Encoding utf8
$markerHash = (Get-FileHash -LiteralPath $marker).Hash
$previousData = $env:JEV_TRADER_DATA_DIR
$app = $null
try {
    $install = Start-Process -FilePath $installerPath -ArgumentList ('/S /D=' + $installDir) -WindowStyle Hidden -Wait -PassThru
    if ($install.ExitCode -ne 0 -or -not (Test-Path (Join-Path $installDir 'JevWIN.exe'))) { throw 'Silent installation failed' }
    $env:JEV_TRADER_DATA_DIR = $dataDir
    $diagnosticText = & (Join-Path $installDir 'jeve-engine.exe') --diagnose
    if ($LASTEXITCODE) { throw 'Installed engine diagnostic failed' }
    $diagnostic = $diagnosticText | ConvertFrom-Json
    $app = Start-Process -FilePath (Join-Path $installDir 'JevWIN.exe') -WindowStyle Hidden -PassThru
    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    do {
        Start-Sleep -Milliseconds 250
        $app.Refresh()
        if ($app.HasExited) { throw 'Native application exited during startup' }
        $children = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$($app.Id)" | Where-Object { $_.ExecutablePath -eq (Join-Path $installDir 'jeve-engine.exe') })
    } while (($app.MainWindowHandle -eq 0 -or $children.Count -eq 0 -or -not (Test-Path (Join-Path $dataDir 'decision-lab.sqlite3'))) -and [DateTime]::UtcNow -lt $deadline)
    if ($app.MainWindowHandle -eq 0 -or $children.Count -eq 0) { throw 'Native window/owned engine was not observed' }
    $engineIds = @($children.ProcessId)
    # Process lifecycle test, not UI automation. Only terminate this owned root.
    Stop-Process -Id $app.Id -ErrorAction Stop
    $app.WaitForExit()
    Start-Sleep -Milliseconds 500
    if (@(Get-Process -Id $engineIds -ErrorAction SilentlyContinue).Count) { throw 'Owned engine survived the root process termination' }
    $app = $null
    $databaseHash = (Get-FileHash -LiteralPath (Join-Path $dataDir 'decision-lab.sqlite3')).Hash
    $update = Start-Process -FilePath $installerPath -ArgumentList ('/S /D=' + $installDir) -WindowStyle Hidden -Wait -PassThru
    if ($update.ExitCode -ne 0) { throw 'Reinstallation failed' }
    if ($databaseHash -ne (Get-FileHash -LiteralPath (Join-Path $dataDir 'decision-lab.sqlite3')).Hash) { throw 'Reinstallation changed stored account data' }
    $uninstall = Start-Process -FilePath (Join-Path $installDir 'Desinstalar_JevWIN.exe') -ArgumentList '/S' -WindowStyle Hidden -Wait -PassThru
    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    while (((Test-Path (Join-Path $installDir 'JevWIN.exe')) -or (Test-Path $registry)) -and [DateTime]::UtcNow -lt $deadline) { Start-Sleep -Milliseconds 250 }
    if ((Test-Path (Join-Path $installDir 'JevWIN.exe')) -or (Test-Path $registry)) { throw 'Uninstallation did not remove program/isolated registration' }
    if ($markerHash -ne (Get-FileHash -LiteralPath $marker).Hash -or $databaseHash -ne (Get-FileHash -LiteralPath (Join-Path $dataDir 'decision-lab.sqlite3')).Hash) { throw 'Uninstallation changed data' }
    $afterPrimary = if (Test-Path $primaryRegistry) { (Get-ItemProperty $primaryRegistry | Select-Object DisplayVersion,InstallLocation | ConvertTo-Json -Compress) } else { '' }
    if ($beforeLegacy -ne (LegacyFingerprint) -or $beforePrimary -ne $afterPrimary) { throw 'Primary JevWIN installation/data changed' }
    [ordered]@{ status='PASS'; platform='Windows 11 x64'; diagnostic=$diagnostic; silent_install=$true; native_window_observed=$true; owned_sidecar_observed=$true; forced_root_exit_cleans_sidecar=$true; reinstall_preserves_data=$true; uninstall_preserves_data=$true; primary_installation_unchanged=$true; native_ui_interactions_verified=$false; excel_rtd_verified=$false } |
        ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $workspace '.artifacts\desktop-windows\installation-verification.json') -Encoding utf8
    Write-Output 'PASS: isolated installation, native startup, process cleanup, reinstall, uninstall, data preservation'
} finally {
    if ($app -and -not $app.HasExited) { Stop-Process -Id $app.Id }
    $env:JEV_TRADER_DATA_DIR = $previousData
}
