;------------------------------------------------------------------------------
; Mpy Editor Windows Installer Build Script
; Author: Mike Asker
; Language: NSIS
; Licence: wxWindows License
;------------------------------------------------------------------------------


;##############################################################################
;------------------------------ Start MUI Setup -------------------------------

; Global Variables
!define PRODUCT_NAME "MpyEditor"
!define PRODUCT_VERSION "0.1.a3"
!define PRODUCT_PUBLISHER "MpyProjects"
!define PRODUCT_WEB_SITE "http://www.mpyprojects.com"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\${PRODUCT_NAME}.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

SetCompressor lzma

; MUI 2.0 compatible ------
!include "MUI2.nsh"
!include Sections.nsh

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "pixmaps\mpy_logo.ico"
!define MUI_UNICON "pixmaps\mpy_logo.ico"














;#######################################################################################
;#####  PAGES       ####################################################################
;#######################################################################################
; Welcome page
!insertmacro MUI_PAGE_WELCOME

; License page (Read the Licence)
!insertmacro MUI_PAGE_LICENSE "COPYING"

; Components Page (Select what parts to install)
!insertmacro MUI_PAGE_COMPONENTS

; Directory page (Set Where to Install)
!insertmacro MUI_PAGE_DIRECTORY

; Instfiles page (Do the installation)
!insertmacro MUI_PAGE_INSTFILES

; Finish page (Post installation tasks)
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_TEXT "Run Mpy Editor"
!define MUI_FINISHPAGE_RUN_FUNCTION "LaunchMpyEditor"
!insertmacro MUI_PAGE_FINISH

;#######################################################################################
;#######################################################################################

; Un-Installer pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_COMPONENTS
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

;#######################################################################################
;#######################################################################################













;#######################################################################################
;#######################################################################################

; Language files
!insertmacro MUI_LANGUAGE "English"

; Reserve files
;;; !insertmacro MUI_RESERVEFILE_INSTALLOPTIONS

ReserveFile '${NSISDIR}\Plugins\InstallOptions.dll'

;------------------------------- End MUI Setup --------------------------------
;##############################################################################
 
 
 
 
 
;##############################################################################
;##############################################################################
;------------------------------ Start Installer -------------------------------

;---- Constants
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "C:\mpy_full_setup.${PRODUCT_VERSION}.exe"
;InstallDir "$PROGRAMFILES\${PRODUCT_NAME}"
InstallDir "C:\MPY"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

RequestExecutionLevel admin 

;---- !defines for use with SHChangeNotify
!ifdef SHCNE_ASSOCCHANGED
!undef SHCNE_ASSOCCHANGED
!endif
!define SHCNE_ASSOCCHANGED 0x08000000

!ifdef SHCNF_FLUSH
!undef SHCNF_FLUSH
!endif
!define SHCNF_FLUSH        0x1000




;#########################################################################
;####     SECTIONS       #################################################
;#########################################################################
;  The following sections are the commands that will be run with the 
;  components and the install page

;------------------------------------------
; Section to install python if necessary
;------------------------------------------
Section /o "Python 2.7" PythonSection

  ; identify the python instalation file
;  MessageBox MB_OK "pyhon27 install"  
  SetOverwrite try
  SetOutPath "$TEMP"
  File "C:\mpy_temp\python-2.7.3.msi"

  ; run the python installation msi
  ExecWait '"msiexec.exe" /package "$TEMP\python-2.7.3.msi" /passive' $0
  DetailPrint "Python installer returned $0"
;  Delete "$TEMP\python-2.7.3.msi"

SectionEnd



;------------------------------------------
; Section to install WXPython if necessary
;------------------------------------------
Section /o "WXPython+PySerial" WXPythonSection

  ; identify the wxpython installation exe
;  MessageBox MB_OK "WXpython install"
  SetOverwrite try
  SetOutPath "$TEMP"
  File  "C:\mpy_temp\wxPython2.8-win32-unicode-2.8.12.1-py27.exe"

  ; install wxpython
  ExecWait '"$TEMP\wxPython2.8-win32-unicode-2.8.12.1-py27.exe"  /SILENT' $0
  DetailPrint "WXpython installer returned $0"
;  Delete "$TEMP\wxPython2.8-win32-unicode-2.8.12.1-py27.exe"

  ; install pyserial
;  MessageBox MB_OK "Pyserial install"
  SetOverwrite try
  SetOutPath "$TEMP\pyserial-2.5"
  File /r "C:\mpy_temp\pyserial-2.5.tar\pyserial-2.5\pyserial-2.5"
  SetOutPath "$TEMP\pyserial-2.5\pyserial-2.5"
  ExecWait '"C:\python27\python.exe" setup.py install' $0
  DetailPrint "Pyserial installer returned $0"

SectionEnd



;------------------------------------------
; Section to install Editra if necessary
;------------------------------------------
Section /o "Editra" EditraSection
  
  ; identify the Editra instalation script
;  MessageBox MB_OK "Editra install"
  SetOverwrite try
  SetOutPath "$TEMP\Editra"
  File  /r "C:\mpy_temp\Editra-0.7.01.tar\dist\Editra-0.7.01\Editra-0.7.01"


  ; install wxpython
  SetOutPath "$TEMP\Editra\Editra-0.7.01"
  ExecWait '"C:\python27\python.exe" setup.py install' $0
  DetailPrint "Editra installer returned $0"
;  Delete "$TEMP\wxPython2.8-win32-unicode-2.8.12.1-py27.exe"
;  MessageBox MB_OK "Editra install done"

SectionEnd



;------------------------------------------
; SECTION 4
; Install MPY tools
;------------------------------------------
Section "MPY Tools" MpyToolsSection
  SectionIn 1 2
  ; Extract the files and make shortcuts

  SetOverwrite try
  SetOutPath "$INSTDIR"
  File /r "C:\MPY\devcon"
  File /r "C:\MPY\mspgcc-20120406"
  File /r "C:\MPY\mspdebug_v019"

SectionEnd


;------------------------------------------
; SECTION 4
; Install MPY editor
;------------------------------------------
Section "MPY Editor" MpyEditorSection
  SectionIn 1 2
  ; Extract the files and make shortcuts

  SetOverwrite try
  SetOutPath "$INSTDIR"
  File /r "C:\MPY\mpy_editor"
  File /r "C:\MPY\mpy_uart"
  File /r "C:\MPY\mpy_setup"
  File /r "C:\MPY\mpy_examples"

  SetOverwrite try
  SetOutPath "$APPDATA"
  File /r "C:\Documents and Settings\mike asker\Application Data\Editra"

  SetOverwrite try  
  SetOutPath "C:\Python27\Lib\site-packages\Editra\plugins" 
  File       "C:\Python27\Lib\site-packages\Editra\plugins\*.*"
  
  
SectionEnd







;------------------------------------------
; EDITRA     Extract the files from the installer to the install location
;------------------------------------------
Section "Editra Core" SEC01
;  SectionIn RO 1 2
  SectionIn 1 2

  ; Check that Editra is not running before starting to copy the files
  FindProcDLL::FindProc "${PRODUCT_NAME}.exe"
  StrCmp $R0 0 continueInstall
    MessageBox MB_ICONSTOP|MB_OK "${PRODUCT_NAME} is still running please close all running instances and try to install again"
    Abort
  continueInstall:

;  ; Extract the files and make shortcuts
;  SetOverwrite try
;  SetOutPath "$INSTDIR\"
;  File /r "C:\MPY\*.*"

  ; Add the shortcuts to the start menu and desktop
  SetShellVarContext all
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  SetOutPath  "C:\Python27\Scripts"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "C:\Python27\Scripts\editra.bat" "" "$INSTDIR\mpy_setup\install\${MUI_ICON}"
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "C:\Python27\Scripts\editra.bat" "" "$INSTDIR\mpy_setup\install\${MUI_ICON}"
SectionEnd



;------------------------------------------
; SECTION 2
; Enabled if Add openwith entry is checked
;------------------------------------------
Section "Context Menus" SEC02
  SectionIn 1
  WriteRegStr HKCR "*\shell\OpenWithEditra" "" "Edit with ${PRODUCT_NAME}"
  WriteRegStr HKCR "*\shell\OpenWithEditra\command" "" '"C:\Python27\Scripts\editra.bat"  "%1"'
;  WriteRegStr HKCR "*\shell\OpenWithEditra\DefaultIcon" "" "${MUI_FILEICON}"

  ; Notify of the shell extension changes
  System::Call 'Shell32::SHChangeNotify(i ${SHCNE_ASSOCCHANGED}, i ${SHCNF_FLUSH}, i 0, i 0)'
SectionEnd



;------------------------------------------
; SECTION 3
; Add QuickLaunch Icon (That small icon bar next to the start button)
;------------------------------------------
Section "Add Quick Launch Icon" SEC03
  SectionIn 1
  SetOutPath  "C:\Python27\Scripts"
  CreateShortCut "$QUICKLAUNCH\${PRODUCT_NAME}.lnk" "C:\Python27\Scripts\editra.bat" "" "$INSTDIR\mpy_setup\install\${MUI_ICON}"
SectionEnd






;------------------------------------------
; Make/Install Shortcut links
;------------------------------------------
Section -AdditionalIcons
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  SetShellVarContext all
  SetOutPath  "C:\Python27\Scripts"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Website.lnk" "$INSTDIR\${PRODUCT_NAME}.url" "" "$INSTDIR\mpy_setup\install\${MUI_UNICON}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "$INSTDIR\uninst.exe" "" "$INSTDIR\mpy_setup\install\${MUI_UNICON}}"
SectionEnd



;------------------------------------------
; Post installation setup
;------------------------------------------
Section -Post
  ;---- Write registry keys for uninstaller
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\${PRODUCT_NAME}.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\mpy_setup\install\${MUI_UNICON}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd
;###############################################################################################
;###############################################################################################











; - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
; - FUNCTIONS - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
; - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
; Prepare for installation

Function .onInit

  ; Prevent running multiple instances of the installer
  System::Call 'kernel32::CreateMutexA(i 0, i 0, t "editra_installer") i .r1 ?e'
  Pop $R0
  StrCmp $R0 0 +3
    MessageBox MB_OK|MB_ICONEXCLAMATION "The installer is already running."
    Abort

  ; Check for existing installation warn before installing new one
  ReadRegStr $R0 ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString"
  StrCmp $R0 "" done

  MessageBox MB_YESNO|MB_ICONEXCLAMATION \
  "An existing installation of Editra has been found. $\nDo you want to remove the previous version before installing $(^Name) ?" \
  IDNO done

  ; Run the uninstaller
  ClearErrors
  ExecWait '$R0 _?=$INSTDIR' ; Do not copy the uninstaller to a temp file

  done:
  


  
  ; Check which components are already present
  ; and enable or disable the checkboxes on the components page 
  ; according to whether they have already been installed
  

  ; PYTHON
  ; Look for the existance of the C:\Python27 exe file, this is sufficient
  IfFileExists "C:\Python27\python.exe" DonePython27Check Python27DoesNotExist
  Python27DoesNotExist:
  !insertmacro SelectSection ${PythonSection}
  DonePython27Check:

  ; WXPYTHON
  IfFileExists "C:\Python27\Lib\site-packages\wx-2.8-msw-unicode" DoneWXPythonCheck WXPython28DoesNotExist
  WXPython28DoesNotExist:
  IfFileExists "C:\Python27\Lib\site-packages\wx-2.9-msw-unicode" DoneWXPythonCheck WXPython29DoesNotExist
  WXPython29DoesNotExist:
  !insertmacro SelectSection ${WXPythonSection}
  DoneWXPythonCheck:

  ; EDITRA
  IfFileExists "C:\Python27\Lib\site-packages\Editra" DoneEditraCheck EditraDoesNotExist
  EditraDoesNotExist:
  !insertmacro SelectSection ${EditraSection}
  DoneEditraCheck:
  
  ; MPYTOOLS
  IfFileExists "C:\MPY\devcon" DoneMpyToolsCheck MpyToolsDoesNotExist
  MpyToolsDoesNotExist:
  !insertmacro SelectSection ${MpyToolsSection}
  DoneMpyToolsCheck:


  ; MPY_EDITOR
  IfFileExists "C:\MPY\mpy_editor" DoneMpyEditorCheck MpyEditorDoesNotExist
  MpyEditorDoesNotExist:
  !insertmacro SelectSection ${MpyEditorSection}
  DoneMpyEditorCheck:
  
FunctionEnd








; - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
; - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
; Called if Run Editra is checked on the last page of installer
Function LaunchMpyEditor
  Exec "C:\Python27\Scripts\editra.bat"
FunctionEnd





;###############################################################################################
;###############################################################################################

; Description Texts for Component page
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN

;  !insertmacro MUI_DESCRIPTION_TEXT ${SEC04} "MPY Editor core files"
;  !insertmacro MUI_DESCRIPTION_TEXT ${SEC05} "MSPGCC C compiler"
;  !insertmacro MUI_DESCRIPTION_TEXT ${SEC06} "Programs the Launchpad MSP430"


  !insertmacro MUI_DESCRIPTION_TEXT ${SEC01} "Required core program files"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC02} "Add context menu item 'Edit with ${PRODUCT_NAME}'"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC03} "Add shortcut to Quick Launch Bar"
!insertmacro MUI_FUNCTION_DESCRIPTION_END





;------------------------------- End Installer --------------------------------
;##############################################################################
;##############################################################################








;##############################################################################
;##############################################################################
;----------------------------- Start Uninstaller ------------------------------

;Function un.onInit
;FunctionEnd

; Cleans up registry, links, and main program files
Section "un.Program Data" UNSEC01
  SectionIn RO 1

  ; Ensure shortcuts are removed from user directory as well
  RmDir /r "$SMPROGRAMS\${PRODUCT_NAME}"
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
  Delete "$QUICKLAUNCH\${PRODUCT_NAME}.lnk"
  
  ; Remove all shortcuts from All Users directory
  SetShellVarContext all
  RmDir /r "$SMPROGRAMS\${PRODUCT_NAME}"
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
  Delete "$QUICKLAUNCH\${PRODUCT_NAME}.lnk"

  ; Cleanup Registry
  DeleteRegKey HKCR "*\shell\OpenWithEditra"
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"

  ; Remove all Files
  RmDir /r "$INSTDIR\"
  RmDir /r "C:\Python27\Lib\site-packages\serial"
  RmDir /r "C:\Python27\Lib\site-packages\pyserial"
  RmDir /r "C:\Python27\Lib\site-packages\Editra"
  RmDir /r "C:\Python27\Lib\site-packages\wx*"

  SetAutoClose false
SectionEnd

; Optionally cleans up user data/plugins
Section /o "un.User settings and plugins" UNSEC02
    SectionIn 1
    SetShellVarContext current ; Current user only
    RmDir /r "$APPDATA\${PRODUCT_NAME}" ; Remove app generated config data/plugins
    RmDir /r "$LOCALAPPDATA\${PRODUCT_NAME}" ; Remove app generated config data/plugins
SectionEnd

;Function un.onUninstSuccess
;FunctionEnd

; Description Texts for Component page
!insertmacro MUI_UNFUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${UNSEC01} "Core program files"
  !insertmacro MUI_DESCRIPTION_TEXT ${UNSEC02} "User settings and plugins"
!insertmacro MUI_UNFUNCTION_DESCRIPTION_END

;------------------------------ End Uninstaller -------------------------------
