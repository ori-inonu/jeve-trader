; NSIS 3.13 ships x86 Unicode stubs; the installed application remains x64.
Target x86-unicode
Unicode true
Name "JevWIN ${VERSION}"
OutFile "${OUTPUT}"
!ifdef ISOLATED_TEST
InstallDir "$LOCALAPPDATA\Programs\JevWIN-Isolated-Test"
!else
InstallDir "$LOCALAPPDATA\Programs\JevWIN"
!endif
RequestExecutionLevel user
SetCompressor /SOLID lzma
SetCompressorDictSize 32
SetOverwrite on
ShowInstDetails show
ShowUninstDetails show
BrandingText "JevWIN - fluxo, hipóteses e capital"
VIProductVersion "${VERSION}.0"
VIAddVersionKey /LANG=1046 "ProductName" "JevWIN"
VIAddVersionKey /LANG=1046 "FileDescription" "Instalador JevWIN para Windows x64"
VIAddVersionKey /LANG=1046 "FileVersion" "${VERSION}"
VIAddVersionKey /LANG=1046 "ProductVersion" "${VERSION}"
VIAddVersionKey /LANG=1046 "LegalCopyright" "Licenças dos componentes incluídas no pacote"
!ifdef ISOLATED_TEST
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\JevWIN-Isolated-Test"
!else
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\JevWIN"
!endif
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "WinVer.nsh"
!include "x64.nsh"
!define MUI_WELCOMEPAGE_TITLE "Instalar JevWIN ${VERSION}"
!define MUI_WELCOMEPAGE_TEXT "Este assistente instala o JevWIN para o usuário atual.$\r$\n$\r$\nO Python e as bibliotecas necessárias estão incluídos. Não é necessário instalar Python nem usar uma conta de administrador.$\r$\n$\r$\nA pasta do programa será: $LOCALAPPDATA\Programs\JevWIN"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\JevWIN.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Abrir JevWIN"
!define MUI_FINISHPAGE_TEXT "Instalação concluída.$\r$\n$\r$\nUse o atalho JevWIN na área de trabalho ou no menu Iniciar.$\r$\n$\r$\nSe a interface não abrir, use o atalho Diagnosticar JevWIN. A janela de diagnóstico permanece aberta e registra o erro."
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "PortugueseBR"

Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_OK|MB_ICONSTOP "O JevWIN exige Windows de 64 bits."
    Quit
  ${EndIf}
  ${IfNot} ${AtLeastWin10}
    MessageBox MB_OK|MB_ICONSTOP "O JevWIN exige Windows 10 ou 11 de 64 bits."
    Quit
  ${EndIf}
  SetShellVarContext current
  SetRegView 64
FunctionEnd

Section "Programa" SEC_MAIN
  SetShellVarContext current
  SetOutPath "$INSTDIR"
  File /r "${PAYLOAD}\*"
  WriteUninstaller "$INSTDIR\Desinstalar_JevWIN.exe"
!ifndef ISOLATED_TEST
  CreateDirectory "$SMPROGRAMS\JevWIN"
  CreateShortCut "$SMPROGRAMS\JevWIN\JevWIN.lnk" "$INSTDIR\JevWIN.exe"
  CreateShortCut "$SMPROGRAMS\JevWIN\Diagnosticar JevWIN.lnk" "$INSTDIR\Diagnosticar_JevWIN.cmd"
  CreateShortCut "$SMPROGRAMS\JevWIN\Desinstalar JevWIN.lnk" "$INSTDIR\Desinstalar_JevWIN.exe"
  CreateShortCut "$DESKTOP\JevWIN.lnk" "$INSTDIR\JevWIN.exe"
!endif
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayName" "JevWIN ${VERSION}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "Publisher" "JevWIN"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\JevWIN.exe"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "UninstallString" '$\"$INSTDIR\Desinstalar_JevWIN.exe$\"'
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoRepair" 1
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "EstimatedSize" ${SIZE_KB}
SectionEnd

Section "Uninstall"
  SetShellVarContext current
  SetRegView 64
!ifndef ISOLATED_TEST
  Delete "$DESKTOP\JevWIN.lnk"
  Delete "$SMPROGRAMS\JevWIN\JevWIN.lnk"
  Delete "$SMPROGRAMS\JevWIN\Diagnosticar JevWIN.lnk"
  Delete "$SMPROGRAMS\JevWIN\Desinstalar JevWIN.lnk"
  RMDir "$SMPROGRAMS\JevWIN"
!endif
  DeleteRegKey HKCU "${UNINSTALL_KEY}"
  RMDir /r "$INSTDIR\runtime"
  RMDir /r "$INSTDIR\app"
  RMDir /r "$INSTDIR\licenses"
  Delete "$INSTDIR\JevWIN.exe"
  Delete "$INSTDIR\jeve-engine.exe"
  Delete "$INSTDIR\LICENSES.txt"
  Delete "$INSTDIR\JevWIN.cmd"
  Delete "$INSTDIR\Diagnosticar_JevWIN.cmd"
  Delete "$INSTDIR\windows_launcher.py"
  Delete "$INSTDIR\LEIA-ME.txt"
  Delete "$INSTDIR\package-manifest.json"
  Delete "$INSTDIR\Desinstalar_JevWIN.exe"
  RMDir "$INSTDIR"
  ; User settings, journal, and diagnostic logs in LOCALAPPDATA\JevWIN remain.
SectionEnd
