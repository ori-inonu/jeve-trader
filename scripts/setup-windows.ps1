param([string]$Python = 'py')
$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $RepoRoot '.venv\Scripts\python.exe'
$Check = 'import sys, tkinter; assert sys.platform == "win32" and sys.version_info >= (3, 10), "Use Windows Python >=3.10 with Tcl/Tk (3.12 recommended)"'
if ($Python -eq 'py') { & py -3.12 -c $Check }
else { & $Python -c $Check }
if ($LASTEXITCODE -ne 0) { throw 'Python/Tcl/Tk check failed. Install official Windows Python 3.12 with Tcl/Tk, or pass -Python with an installed interpreter path.' }
if (-not (Test-Path $VenvPython)) {
    if ($Python -eq 'py') { & py -3.12 -m venv (Join-Path $RepoRoot '.venv') }
    else { & $Python -m venv (Join-Path $RepoRoot '.venv') }
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
}
& $VenvPython -c $Check
if ($LASTEXITCODE -ne 0) { throw 'Existing .venv does not meet the Python/Tcl/Tk requirement; recreate it with the intended interpreter.' }
& $VenvPython -m pip install --disable-pip-version-check -r (Join-Path $RepoRoot 'app\requirements-runtime.txt')
if ($LASTEXITCODE -ne 0) { throw 'Runtime dependency installation failed.' }
& $VenvPython -c 'from zoneinfo import ZoneInfo; print("Ready:", ZoneInfo("America/Sao_Paulo"))'
if ($LASTEXITCODE -ne 0) { throw 'Timezone check failed.' }
Write-Host "Verify: & '$VenvPython' '$(Join-Path $RepoRoot 'scripts\verify.py')'"
Write-Host 'This script does not change execution policies, Defender settings or permissions.'
