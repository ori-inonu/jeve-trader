#requires -Version 7.0
param([switch]$SkipInstallDependencies, [switch]$IsolatedInstaller)
$ErrorActionPreference = 'Stop'
$workspace = Split-Path $PSScriptRoot -Parent
$version = (Get-Content -LiteralPath (Join-Path $workspace 'app\version.json') -Raw | ConvertFrom-Json).version
if ($version -notmatch '^\d+\.\d+\.\d+$') { throw 'Invalid canonical application version' }
$packageVersion = (Get-Content -LiteralPath (Join-Path $PSScriptRoot 'package.json') -Raw | ConvertFrom-Json).version
$tauriVersion = (Get-Content -LiteralPath (Join-Path $PSScriptRoot 'src-tauri\tauri.conf.json') -Raw | ConvertFrom-Json).version
$cargoConfig = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'src-tauri\Cargo.toml') -Raw
if ($version -ne $packageVersion -or $version -ne $tauriVersion -or $cargoConfig -notmatch ('(?m)^version = "'+[regex]::Escape($version)+'"\r?$')) { throw 'Application version metadata differs' }
$python = Join-Path $workspace '.venv\Scripts\python.exe'
$cargo = Join-Path $env:USERPROFILE '.cargo\bin\cargo.exe'
$nsis = Join-Path ${env:ProgramFiles(x86)} 'NSIS\makensis.exe'
foreach ($path in @($python, $cargo, $nsis)) { if (-not (Test-Path -LiteralPath $path)) { throw "Build dependency missing: $path" } }
$env:PATH = "$(Split-Path $cargo);$env:PATH"
$artifacts = Join-Path $workspace '.artifacts\desktop-windows'
$payload = Join-Path $artifacts 'portable'
New-Item -ItemType Directory -Force -Path $payload | Out-Null
Push-Location $workspace
try {
    if (-not $SkipInstallDependencies) {
        & $python -m pip install -r app\requirements-desktop-build.txt
        if ($LASTEXITCODE) { throw 'Python build dependencies failed' }
        Push-Location $PSScriptRoot
        try { & npm.cmd ci; if ($LASTEXITCODE) { throw 'npm ci failed' } } finally { Pop-Location }
    }
    Push-Location $PSScriptRoot
    try { & npm.cmd run build; if ($LASTEXITCODE) { throw 'Frontend build failed' } } finally { Pop-Location }
    $pyinstallerArgs = @('-m', 'PyInstaller', '--noconfirm', '--clean', '--onefile', '--console', '--name', 'jeve-engine',
        '--distpath', $payload, '--workpath', (Join-Path $artifacts 'pyinstaller'), '--specpath', $artifacts,
        '--paths', (Join-Path $workspace 'app'), '--hidden-import', 'comtypes.client', '--collect-data', 'tzdata',
        '--exclude-module', 'tkinter', '--exclude-module', 'numpy', '--exclude-module', 'scipy', '--exclude-module', 'sklearn')
    foreach ($resource in @('desktop_service.py', 'app_core.py', 'app_store.py', 'capital_example.py', 'decision_engine.py',
        'decision_store.py', 'context_requests.py', 'candidate_engine.py', 'candidate_research.py', 'flow_engine.py',
        'profit_bridge.py', 'recommendation_engine.py', 'jev_client.py', 'copilot.py', 'capital_planner.py', 'risk.py',
        'risk_research.py', 'release_updates.py', 'version.json', 'config.json', 'flow_rules.json', 'observer_questions.json')) {
        $pyinstallerArgs += @('--add-data', "$(Join-Path $workspace "app\$resource");.")
    }
    $pyinstallerArgs += (Join-Path $workspace 'app\desktop_service.py')
    & $python @pyinstallerArgs
    if ($LASTEXITCODE) { throw 'Python sidecar build failed' }
    Push-Location (Join-Path $PSScriptRoot 'src-tauri')
    try { & $cargo build --release --locked --features custom-protocol; if ($LASTEXITCODE) { throw 'Tauri build failed' } } finally { Pop-Location }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'src-tauri\target\release\JevWIN.exe') -Destination $payload -Force
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'LICENSES.txt') -Destination $payload -Force
    & $python scripts\collect_desktop_licenses.py --output (Join-Path $payload 'licenses')
    if ($LASTEXITCODE) { throw 'License notice collection failed' }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Diagnosticar_JevWIN.cmd') -Destination $payload -Force
    @'
Jeve Trader 0.4 — painel experimental Windows x64
Extraia a pasta inteira e abra JevWIN.exe. Ordens permanecem manuais no Profit Pro.
Requer WebView2 Evergreen. O instalador 0.4 preserva LOCALAPPDATA\JevWIN.
Os dados locais incluem journal.sqlite3 e decision-lab.sqlite3; faça backup antes de migrar de máquina.
Custos e margem iniciais são parâmetros manuais de demonstração, sem tarifa verificada.
Probabilidade financeira permanece não estimada até validação empírica e integração de um modelo aprovado.
Diagnosticar_JevWIN.cmd testa o motor em pasta temporária, sem chamar a API.
'@ | Set-Content -LiteralPath (Join-Path $payload 'LEIA-ME.txt') -Encoding utf8
    $diagnostic = & (Join-Path $payload 'jeve-engine.exe') --diagnose
    if ($LASTEXITCODE) { throw 'Packaged Python diagnostic failed' }
    $diagnostic | Set-Content -LiteralPath (Join-Path $artifacts 'sidecar-diagnostic.json') -Encoding utf8
    $files = Get-ChildItem -LiteralPath $payload -File -Recurse | Where-Object { $_.Name -ne 'package-manifest.json' } | ForEach-Object {
        [ordered]@{ name=[IO.Path]::GetRelativePath($payload, $_.FullName); bytes=$_.Length; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }
    }
    [ordered]@{ version=$version; platform='Windows x64'; created_utc=[DateTime]::UtcNow.ToString('o');
        orders_enabled=$false; model_deployment_approved=$false; files=@($files) } |
        ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $payload 'package-manifest.json') -Encoding utf8
    $sizeKb = [int][Math]::Ceiling(((Get-ChildItem -LiteralPath $payload -File -Recurse | Measure-Object Length -Sum).Sum)/1024)
    $suffix = if ($IsolatedInstaller) { '-isolated-test' } else { '' }
    $installer = Join-Path $artifacts "JevWIN_${version}_setup$suffix.exe"
    $nsisArgs = @('/INPUTCHARSET', 'UTF8', "/DVERSION=$version", "/DOUTPUT=$installer", "/DPAYLOAD=$payload", "/DSIZE_KB=$sizeKb")
    if ($IsolatedInstaller) { $nsisArgs += '/DISOLATED_TEST' }
    $nsisArgs += (Join-Path $workspace 'app\packaging\installer.nsi')
    & $nsis @nsisArgs
    if ($LASTEXITCODE) { throw 'Installer build failed' }
    $portableZip = Join-Path $artifacts "JevWIN_${version}_portable.zip"
    Compress-Archive -LiteralPath (Get-ChildItem -LiteralPath $payload).FullName -DestinationPath $portableZip -Force
    Get-FileHash -LiteralPath $installer, $portableZip -Algorithm SHA256 | ForEach-Object { "$($_.Hash.ToLowerInvariant())  $(Split-Path $_.Path -Leaf)" } | Set-Content -LiteralPath (Join-Path $artifacts "SHA256SUMS-$version.txt") -Encoding utf8
    Write-Output "Portable: $payload"
    Write-Output "Installer: $installer"
} finally { Pop-Location }
