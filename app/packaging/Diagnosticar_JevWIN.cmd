@echo off
setlocal
cd /d "%~dp0"
echo DIAGNOSTICO DO JEVWIN - esta janela permanecera aberta.
echo.
set "JEV_LOG_DIR=%LOCALAPPDATA%\JevWIN\logs"
if not exist "%JEV_LOG_DIR%" mkdir "%JEV_LOG_DIR%" 2>nul
if not exist "%JEV_LOG_DIR%" set "JEV_LOG_DIR=%TEMP%\JevWIN-logs"
if not exist "%JEV_LOG_DIR%" mkdir "%JEV_LOG_DIR%" 2>nul
set "JEV_CONSOLE_LOG=%JEV_LOG_DIR%\diagnostic-console.log"
echo DIAGNOSTICO JEVWIN %DATE% %TIME% > "%JEV_CONSOLE_LOG%"
if not exist "%~dp0runtime\python.exe" goto missing
if not exist "%~dp0windows_launcher.py" goto missing
"%~dp0runtime\python.exe" -I -X faulthandler "%~dp0windows_launcher.py" --diagnose >> "%JEV_CONSOLE_LOG%" 2>&1
set "JEV_RESULT=%errorlevel%"
echo Codigo de saida: %JEV_RESULT% >> "%JEV_CONSOLE_LOG%"
type "%JEV_CONSOLE_LOG%"
echo.
echo Registros: %JEV_LOG_DIR%
echo Copie a mensagem acima e diagnostic-console.log ao relatar o problema.
echo Se nao houver mensagem do Python, copie tambem o aviso exibido pelo Windows.
pause
exit /b %JEV_RESULT%
:missing
echo Arquivos do pacote ausentes. Extraia a pasta inteira do ZIP.
echo Arquivos do pacote ausentes. >> "%JEV_CONSOLE_LOG%"
pause
exit /b 1
