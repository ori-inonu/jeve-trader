Target amd64-unicode
Unicode true
Name "JevWIN"
OutFile "${OUTPUT}"
RequestExecutionLevel user
SilentInstall silent
AutoCloseWindow true
ShowInstDetails nevershow
SetCompressor lzma
!include "FileFunc.nsh"

Function .onInit
  ${GetParameters} $0
  IfFileExists "$EXEDIR\runtime\python.exe" 0 missing
  IfFileExists "$EXEDIR\runtime\pythonw.exe" 0 missing
  IfFileExists "$EXEDIR\windows_launcher.py" 0 missing
  nsExec::ExecToStack /TIMEOUT=30000 '"$EXEDIR\runtime\python.exe" -I -X faulthandler "$EXEDIR\windows_launcher.py" --preflight'
  Pop $1
  Pop $2
  StrCmp $1 "0" ready failed
ready:
  ClearErrors
  Exec '"$EXEDIR\runtime\pythonw.exe" -I -X faulthandler "$EXEDIR\windows_launcher.py" $0'
  IfErrors failed done
missing:
  MessageBox MB_OK|MB_ICONSTOP "Arquivos do JevWIN ausentes. Extraia a pasta inteira do pacote ou execute novamente o instalador."
  Quit
failed:
  MessageBox MB_OK|MB_ICONSTOP "O JevWIN não conseguiu iniciar.$\r$\n$\r$\nCódigo: $1$\r$\n$2$\r$\n$\r$\nAbra Diagnosticar_JevWIN.cmd nesta pasta.$\r$\nRegistros: %LOCALAPPDATA%\JevWIN\logs"
done:
  Quit
FunctionEnd

Section
SectionEnd
