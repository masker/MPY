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
!define PRODUCT_VERSION "0.1.a7"
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
!define MUI_ICON     "pixmaps\mpy_logo.ico"
!define MUI_UNICON   "pixmaps\mpy_logo.ico"
!define MUI_FILEICON "pixmaps\mpy_logo.ico"


#-------------------------------------
# Variables

Var PythonDir
Var MpyDir



#!macro ConfigureMpyDirPage type var
#!define MUI_DIRECTORYPAGE_VARIABLE ${var}
#!define MUI_PAGE_HEADER_SUBTEXT "Choose the folder in which to install $(^NameDA) ${type}"
#!define MUI_DIRECTORYPAGE_TEXT_TOP "Setup will install $(^NameDA) ${type} in the following folder. To install in a different folder, click Browse and select another folder. $_CLICK"
#!define MUI_DIRECTORYPAGE_TEXT_DESTINATION "${type} $(^DirSubText)"
#!macroend




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
!define PYTHON  "C:\Python27"

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

    StrCpy $MpyDir $INSTDIR

    DetailPrint "Instdir is : $INSTDIR ,    and MpyDir is :  $MpyDir , and PythonDir is : $PythonDir"
    MessageBox MB_OK "PYTHONSECTION  START"  


  ; identify the python instalation file
;  MessageBox MB_OK "pyhon27 install"  

  ; Remove any vestiges of python27
  RmDir /r "$PythonDir"
  
  
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
Section /o "WXPython" WXPythonSection

  StrCpy $MpyDir $INSTDIR

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
  ExecWait '"$PythonDir\python.exe" setup.py install' $0
  DetailPrint "Pyserial installer returned $0"



SectionEnd



;------------------------------------------
; Section to install Editra if necessary
;------------------------------------------
Section /o "Editra" EditraSection

  StrCpy $MpyDir $INSTDIR
 
  ; identify the Editra instalation script
;  MessageBox MB_OK "Editra install"
  SetOverwrite try
  SetOutPath "$TEMP\Editra"
  File  /r "C:\mpy_temp\Editra-0.7.01.tar\dist\Editra-0.7.01\Editra-0.7.01"


  ; install wxpython
  SetOutPath "$TEMP\Editra\Editra-0.7.01"
  ExecWait '"$PythonDir\python.exe" setup.py install' $0
  DetailPrint "Editra installer returned $0"
;  Delete "$TEMP\wxPython2.8-win32-unicode-2.8.12.1-py27.exe"

SectionEnd



;------------------------------------------
; SECTION 4
; Install MPY tools
;------------------------------------------
Section "MPY Tools" MpyToolsSection
  SectionIn 1 2
  ; Extract the files and make shortcuts

  StrCpy $MpyDir $INSTDIR

  SetOverwrite try
  SetOutPath "$MpyDir"
  File /r "C:\MPY\devcon"
  File /r "C:\MPY\mspgcc-20120406"
  File /r "C:\MPY\mspdebug_v019"
  File    "C:\MPY\mpy_driver_installer.0.1.a2.exe"
SectionEnd


;------------------------------------------
; SECTION 4
; Install MPY editor
;------------------------------------------
Section "MPY Editor" MpyEditorSection
  SectionIn 1 2
  ; Extract the files and make shortcuts

  SetOverwrite try
  SetOutPath "$MpyDir"
  File /r "C:\MPY\mpy_editor"
  File /r "C:\MPY\mpy_uart"
  File /r "C:\MPY\mpy_setup"
  File /r "C:\MPY\mpy_examples"


  SetOverwrite try  
  SetOutPath "$PythonDir\Lib\site-packages\Editra\plugins" 
  File       "C:\Python27\Lib\site-packages\Editra\plugins\*.*"


  ; Copy the spash screen image from the mpy install directory into Editra's src dir. 
  ; the splash screen image is generated from the image .png into a python file using png2py wx utility
  SetOverwrite try  
  SetOutPath "$PythonDir\Lib\site-packages\Editra\src" 
  File       "C:\MPY\mpy_setup\install\edimage.py"



  ; Add the shortcuts to the start menu and desktop
  SetShellVarContext all
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  SetOutPath  "$PythonDir\Scripts"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$PythonDir\Scripts\editra.bat" "" "$PythonDir\mpy_setup\install\${MUI_ICON}"
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$PythonDir\Scripts\editra.bat" "" "$MpyDir\mpy_setup\install\${MUI_ICON}"

  ; setup the icon for .mpy files in explorer
  WriteRegStr HKCR ".mpy" "" "MpyEditor.Document"
  WriteRegStr HKCR "MpyEditor.Document\DefaultIcon" ""  "$MpyDir\mpy_setup\install\${MUI_FILEICON}"
  WriteRegStr HKCR "MpyEditor.Document\shell\open\command" "" '"$PythonDir\Scripts\editra.bat"  "%1"'
  
  WriteRegStr HKCR "*\shell\OpenWithEditra" "" "Edit with Editra MpyEditor"
  WriteRegStr HKCR "*\shell\OpenWithEditra\command" "" '"$PythonDir\Scripts\editra.bat"  "%1"'
;  WriteRegStr HKCR "*\shell\OpenWithEditra\DefaultIcon" "" "${MUI_FILEICON}"


  SetOutPath  "$MpyDir"
  CreateShortCut "$QUICKLAUNCH\${PRODUCT_NAME}.lnk" "$PythonDir\Scripts\editra.bat" "" "$MpyDir\mpy_setup\install\${MUI_ICON}"



  ; Notify of the shell extension changes
  System::Call 'Shell32::SHChangeNotify(i ${SHCNE_ASSOCCHANGED}, i ${SHCNF_FLUSH}, i 0, i 0)'


  ; install pywin32
  SetOverwrite try
  SetOutPath "$TEMP"
  File  "C:\mpy_temp\pywin32-217.win32-py2.7.exe"
  ExecWait '"$TEMP\pywin32-217.win32-py2.7.exe"  /SILENT' $0
  DetailPrint "pywin32 installer returned $0"
;  Delete "$TEMP\pywin32-217.win32-py2.7.exe"
;  MessageBox MB_OK "pywin32 install done"


  
SectionEnd


;------------------------------------------
; SECTION 4
; Install MPY Default User Settings
;------------------------------------------
Section "MPY User Settings" MpyEditorSettingsSection
  SectionIn 1
  SetOverwrite try
  
  # we have to try all combinations 
  SetShellVarContext current
  SetOutPath "$APPDATA\Editra\"
  File /r "C:\Documents and Settings\mike asker\Application Data\Editra\*.*"
  SetOverwrite try
  SetOutPath "$LOCALAPPDATA\Editra\"
  File /r "C:\Documents and Settings\mike asker\Application Data\Editra\*.*"

SectionEnd




;------------------------------------------
; Make/Install Shortcut links
;------------------------------------------
Section -AdditionalIcons
  WriteIniStr "$MpyDir\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  SetShellVarContext all
  SetOutPath  "$MpyDir\Scripts"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Website.lnk"            "$MpyDir\${PRODUCT_NAME}.url"             "" "$MpyDir\mpy_setup\install\${MUI_UNICON}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\MpyDriverInstaller.lnk" "$MpyDir\mpy_driver_installer.0.1.a1.exe" "" "$MpyDir\mpy_setup\install\${MUI_UNICON}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk"          "$MpyDir\uninst.exe"                      "" "$MpyDir\mpy_setup\install\${MUI_UNICON}"
SectionEnd



;------------------------------------------
; Post installation setup
;------------------------------------------
Section -Post


  ; run the driver installer
  SetOutPath "$MpyDir"
  ExecWait "$MpyDir\mpy_driver_installer.0.1.a2.exe" $0
  


  ;---- Write registry keys for uninstaller
  WriteUninstaller "$MpyDir\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$MpyDir\${PRODUCT_NAME}.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName"      "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString"  "$MpyDir\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon"      "$MpyDir\mpy_setup\install\${MUI_UNICON}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion"   "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout"     "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher"        "${PRODUCT_PUBLISHER}"
SectionEnd
;###############################################################################################
;###############################################################################################











; - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
; - FUNCTIONS - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
; - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
; Prepare for installation

Function .onInit

  ; Prevent running multiple instances of the installer
  System::Call 'kernel32::CreateMutexA(i 0, i 0, t "mpy_installer") i .r1 ?e'
  Pop $R0
  StrCmp $R0 0 +3
    MessageBox MB_OK|MB_ICONEXCLAMATION "The MPY installer is already running."
    Abort

  ; Check for existing installation warn before installing new one
  ReadRegStr $R0 ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString"
  StrCmp $R0 "" done

  MessageBox MB_YESNO|MB_ICONEXCLAMATION \
  "An existing installation of Mpy has been found. $\nDo you want to remove any components of $(^Name) ?" \
  IDNO done

  ; Run the uninstaller
  ClearErrors
  ExecWait '$R0 _?=$INSTDIR' ; Do not copy the uninstaller to a temp file
#  Abort

  done:
  


  
  ; Check which components are already present
  ; and enable or disable the checkboxes on the components page 
  ; according to whether they have already been installed
  

  ; PYTHON
  ; Look for the existance of the C:\Python26 exe file, this is sufficient to determine that the python26 is installed
  
  StrCpy $PythonDir "?"
  ${If} ${FileExists} "C:\Python27\python.exe" 
      StrCpy $PythonDir "C:\Python27"
  ${ElseIf} ${FileExists} "C:\Python26\python.exe"
      StrCpy $PythonDir "C:\Python26"
  ${EndIf}
  
  ${If} $PythonDir == "?"
      StrCpy $PythonDir "C:\Python27"
      !insertmacro SelectSection ${PythonSection}
  ${EndIf}
  

  ; WXPYTHON
  IfFileExists "$PythonDir\Lib\site-packages\wx-2.8-msw-unicode" DoneWXPythonCheck WXPython28DoesNotExist
  WXPython28DoesNotExist:
  IfFileExists "$PythonDir\Lib\site-packages\wx-2.9-msw-unicode" DoneWXPythonCheck WXPython29DoesNotExist
  WXPython29DoesNotExist:
  !insertmacro SelectSection ${WXPythonSection}
  DoneWXPythonCheck:

  ; EDITRA
  IfFileExists "$PythonDir\Lib\site-packages\Editra" DoneEditraCheck EditraDoesNotExist
  EditraDoesNotExist:
  !insertmacro SelectSection ${EditraSection}
  DoneEditraCheck:
  
  ; MPYTOOLS
  IfFileExists "$MpyDir\devcon" DoneMpyToolsCheck MpyToolsDoesNotExist
  MpyToolsDoesNotExist:
  !insertmacro SelectSection ${MpyToolsSection}
  DoneMpyToolsCheck:


  ; MPY_EDITOR
  IfFileExists "$MpyDir\mpy_editor" DoneMpyEditorCheck MpyEditorDoesNotExist
  MpyEditorDoesNotExist:
  !insertmacro SelectSection ${MpyEditorSection}
  DoneMpyEditorCheck:
  
FunctionEnd








; - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
; - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
; Called if Run Editra is checked on the last page of installer
Function LaunchMpyEditor
  Exec "$PythonDir\Scripts\editra.bat"
FunctionEnd





;###############################################################################################
;###############################################################################################

; Description Texts for Component page
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${PythonSection}   "Core Python Language"
  !insertmacro MUI_DESCRIPTION_TEXT ${WXPythonSection} "WxPython Graphics Module, PySerial and PyWin32"
  !insertmacro MUI_DESCRIPTION_TEXT ${EditraSection}   "Editra Editor"
  !insertmacro MUI_DESCRIPTION_TEXT ${MpyToolsSection} "Tools to program the Launchpad MSP430 (MSPGCC and MSPDEBUG)"
  !insertmacro MUI_DESCRIPTION_TEXT ${MpyEditorSection}         "Mpy Editor"
  !insertmacro MUI_DESCRIPTION_TEXT ${MpyEditorSettingsSection} "Mpy Load Default User Settings"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

ComponentText "Python will be installed in directory $PythonDir$\nMpy components will be installed in directory C:\MPY" 


;------------------------------- End Installer --------------------------------
;##############################################################################
;##############################################################################








;##############################################################################
;##############################################################################
;----------------------------- Start Uninstaller ------------------------------

;Function un.onInit
;FunctionEnd



Section /o "un.Python Modules" UNPythonModulesSection
  SectionIn 1
  RmDir /r "C:\Python27"
SectionEnd



Section /o "un.MPY Tools" UNMpyToolsSection
  SectionIn  1
  RmDir /r "$MpyDir\devcon"
  RmDir /r "$MpyDir\mspdebug_v019"
  RmDir /r "$MpyDir\mspgcc-20120406"
SectionEnd



Section "un.MPY Editor" UNMpyEditorSection
  ; Ensure shortcuts are removed from user directory as well
  
  RmDir /r "$MpyDir\mpy_editor"
  RmDir /r "$MpyDir\mpy_uart"
  RmDir /r "$MpyDir\mpy_examples"
  RmDir /r "$MpyDir\mpy_setup"

  
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
  DeleteRegKey HKCR "MpyEditor.Document"

  SetAutoClose false
SectionEnd



; Optionally cleans up user data/plugins
Section /o "un.User settings and plugins" UNUserSection
    SectionIn 1
    SetShellVarContext current ; Current user only
    RmDir /r "$APPDATA\Editra" ; Remove app generated config data/plugins
    RmDir /r "$LOCALAPPDATA\Editra" ; Remove app generated config data/plugins
SectionEnd

;Function un.onUninstSuccess
;FunctionEnd

; Description Texts for Component page
!insertmacro MUI_UNFUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${UNUserSection}          "Delete User settings"
  !insertmacro MUI_DESCRIPTION_TEXT ${UNMpyEditorSection}     "Mpy Editor"
  !insertmacro MUI_DESCRIPTION_TEXT ${UNMpyToolsSection}      "Tools to program the Launchpad MSP430 (MSPGCC and MSPDEBUG)"
  !insertmacro MUI_DESCRIPTION_TEXT ${UNPythonModulesSection} "Python Core Language"
!insertmacro MUI_UNFUNCTION_DESCRIPTION_END

;------------------------------ End Uninstaller -------------------------------
