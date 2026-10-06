@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0runtime\python.exe" goto missing
if not exist "%~dp0windows_launcher.py" goto missing
"%~dp0runtime\python.exe" -I -X faulthandler "%~dp0windows_launcher.py" %*
set "JEV_RESULT=%errorlevel%"
if not "%JEV_RESULT%"=="0" goto failed
exit /b 0
:missing
echo Arquivos do pacote JevWIN ausentes. Extraia a pasta inteira do ZIP.
echo O interpretador deve estar em runtime\python.exe.
pause
exit /b 1
:failed
echo.
echo JevWIN nao conseguiu abrir. Codigo: %JEV_RESULT%
echo Abra Diagnosticar_JevWIN.cmd. Os registros ficam em %%LOCALAPPDATA%%\JevWIN\logs.
pause
exit /b %JEV_RESULT%
