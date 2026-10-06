param([string]$Python = 'py', [string]$MakeNSIS = '')
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if ($Python -eq 'py') { & py -3.12 -m venv .build-venv }
else { & $Python -m venv .build-venv }
if ($LASTEXITCODE -ne 0) { throw 'Use Windows Python 3.12 x64 with Tcl/Tk.' }
$BuildPython = Join-Path $PSScriptRoot '.build-venv\Scripts\python.exe'
& $BuildPython -c "import struct,sys; assert sys.platform == 'win32' and sys.version_info[:2] == (3,12) and struct.calcsize('P') == 8, 'Windows Python 3.12 x64 required'"
if ($LASTEXITCODE -ne 0) { throw 'Windows Python 3.12 x64 required.' }
if ($MakeNSIS -eq '') {
    $FoundNSIS = Get-Command makensis.exe -ErrorAction SilentlyContinue
    if ($FoundNSIS) { $MakeNSIS = $FoundNSIS.Source }
    else { $MakeNSIS = Join-Path ${env:ProgramFiles(x86)} 'NSIS\makensis.exe' }
}
if (-not (Test-Path $MakeNSIS)) { throw 'Install NSIS 3.09 or newer, or pass -MakeNSIS with its executable path.' }
New-Item -ItemType Directory -Force '.build-wheels' | Out-Null
& $BuildPython -m pip download --disable-pip-version-check --only-binary=:all: --no-deps --dest .build-wheels -r requirements-runtime.txt
if ($LASTEXITCODE -ne 0) { throw 'Runtime wheel download failed.' }
$Runtime = (& $BuildPython -c 'import sys; print(sys.base_prefix)').Trim()
& $BuildPython packaging\build_installer.py --runtime $Runtime --comtypes-wheel .build-wheels\comtypes-1.4.17-py3-none-any.whl --tzdata-wheel .build-wheels\tzdata-2025.2-py2.py3-none-any.whl --makensis $MakeNSIS --output-dir dist
if ($LASTEXITCODE -ne 0) { throw 'Installer build failed.' }
$Report = Join-Path $PSScriptRoot 'dist\source-self-test.json'
& (Join-Path $PSScriptRoot 'dist\JevWIN-portable\runtime\python.exe') -E -s (Join-Path $PSScriptRoot 'dist\JevWIN-portable\app\desktop_app.py') --self-test --report $Report
if ($LASTEXITCODE -ne 0) { throw 'Packaged application source self-test failed.' }
Write-Host 'Built dist\JevWIN_Instalador.exe and dist\JevWIN_Portatil.zip.'
Write-Host 'Validate installation, desktop launch and diagnosis on a separate Windows test user before publishing.'
Get-FileHash dist\JevWIN_Instalador.exe -Algorithm SHA256
