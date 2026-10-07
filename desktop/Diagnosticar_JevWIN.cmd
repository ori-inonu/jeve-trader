@echo off
cd /d "%~dp0"
"%~dp0jeve-engine.exe" --diagnose
echo.
echo Diagnostico offline. API JEV e ordens nao sao utilizadas.
pause
