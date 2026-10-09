param([switch]$BrowserPreview, [string]$DataDirectory)
$ErrorActionPreference = 'Stop'
$workspace = Split-Path $PSScriptRoot -Parent
$cargoDirectory = Join-Path $env:USERPROFILE '.cargo\bin'
$env:PATH = "$cargoDirectory;$env:PATH"
if ($DataDirectory) { $env:JEV_TRADER_DATA_DIR = [IO.Path]::GetFullPath($DataDirectory) }
Push-Location (Join-Path $workspace 'desktop')
try {
    if (-not (Test-Path -LiteralPath 'node_modules')) { & npm.cmd ci; if ($LASTEXITCODE) { throw 'npm ci failed' } }
    if ($BrowserPreview) { & npm.cmd run dev } else { & npm.cmd run tauri -- dev }
    if ($LASTEXITCODE) { throw 'Desktop startup failed' }
} finally { Pop-Location }
