

;------------------------------------------------------------------------------
; Mpy Editor Windows Installer Build Script
; Author: Mike Asker
; Language: NSIS
; Licence: GPL
;------------------------------------------------------------------------------


;##############################################################################
;------------------------------ Start MUI Setup -------------------------------

; Global Variables
!define PRODUCT_NAME "MpyEditor"
!define PRODUCT_VERSION "0.1.a11"
!define PRODUCT_PUBLISHER "MpyProjects"
!define PRODUCT_WEB_SITE "http://www.mpyprojects.com"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\${PRODUCT_NAME}.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

SetCompressor lzma

; MUI 2.0 compatible ------
!include "MUI2.nsh"
!include Sections.nsh
!include "Locate.nsh"  
!include StrRep.nsh
!include ReplaceInFile.nsh
!include LogicLib.nsh
!include "x64.nsh"


!macro RepInFile SOURCE_FILE SEARCH_TEXT REPLACEMENT
  ${If} "${SEARCH_TEXT}" != "${REPLACEMENT}"
      !insertmacro _ReplaceInFile  "${SOURCE_FILE}" "${SEARCH_TEXT}\" "${REPLACEMENT}\"
  ${EndIf}
!macroend


; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON     "pixmaps\mpy_logo.ico"
!define MUI_UNICON   "pixmaps\mpy_logo.ico"
!define MUI_FILEICON "pixmaps\mpy_logo.ico"


#-------------------------------------
# Variables

Var PythonDir
Var MpyDir
Var MpyUserSettings







;#######################################################################################
;#####  PAGES       ####################################################################
;#######################################################################################
; Welcome page
!insertmacro MUI_PAGE_WELCOME

; License page (Read the Licence)license
!define MUI_LICENSEPAGE_TEXT_TOP "MpyEditor is Licenced under GPL3 - Click Next to Agree" 
!insertmacro MUI_PAGE_LICENSE "COPYING"

; Directory page (Set Where to Install)

DirText "Setup will now install the MpyEditor into the directory shown below.$\n$\nNote: This directory must not contain spaces$\n$\nClick Next to Continue"
!insertmacro MUI_PAGE_DIRECTORY

; Components Page (Select what parts to install)
!define MUI_PAGE_CUSTOMFUNCTION_PRE detect_components_already_installed
!insertmacro MUI_PAGE_COMPONENTS


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

  StrCpy "$MpyDir" "$INSTDIR"
  StrCpy $PythonDir "C:\Python27"

  ; Remove any vestiges of python27
  RmDir /r "$PythonDir"  
  
  SetOverwrite try
  SetOutPath "$TEMP"
  File "C:\mpy_temp\python-2.7.3.msi"

  ; run the python installation msi
  ExecWait '"msiexec.exe" /package "$TEMP\python-2.7.3.msi" /passive' $0
  DetailPrint "Python installer returned $0"
  ${If} $0 != 0
      MessageBox MB_OK|MB_ICONEXCLAMATION "Error ($0) while installing Python 2.7. Installation Failed"
      Abort
  ${EndIf}

;  Delete "$TEMP\python-2.7.3.msi"

SectionEnd



;------------------------------------------
; Section to install WXPython if necessary
;------------------------------------------
Section /o "WXPython" WXPythonSection


  StrCpy "$MpyDir" "$INSTDIR"


;;;;; install pywin32   postinstall silent method
  SetOverwrite try
  SetOutPath "$PythonDir\Lib\site-packages"
  File /r "C:\mpy_temp\pywin32-217_postinstall\SCRIPTS\*"
  File /r "C:\mpy_temp\pywin32-217_postinstall\PLATLIB\*"
;  MessageBox MB_OK "pywin32 install start"
  ExecWait '"$PythonDir\python.exe" pywin32_postinstall.py -install' $0
  DetailPrint "pywin32 installer returned $0"
  ${If} $0 != 0
      MessageBox MB_OK|MB_ICONEXCLAMATION "Error ($0) while installing pywin32. Installation Failed"
      Abort
  ${EndIf}

;  MessageBox MB_OK "pywin32 install finished"
  Delete "pywin32_postinstall.py"
  

;;;; identify the wxpython installation exe
;  MessageBox MB_OK "WXpython install"
  SetOverwrite try
  SetOutPath "$TEMP"
  File  "C:\mpy_temp\wxPython2.8-win32-unicode-2.8.12.1-py27.exe"

  ; install wxpython
  ExecWait '"$TEMP\wxPython2.8-win32-unicode-2.8.12.1-py27.exe"  /SILENT' $0
  DetailPrint "WXpython installer returned $0"
  ${If} $0 != 0
      MessageBox MB_OK|MB_ICONEXCLAMATION "Error ($0) while installing wxPython. Installation Failed"
      Abort
  ${EndIf}

;  Delete "$TEMP\wxPython2.8-win32-unicode-2.8.12.1-py27.exe"
;  MessageBox MB_OK "WXpython install"

;;;; install pyserial
;  MessageBox MB_OK "Pyserial install"
  SetOverwrite try
  SetOutPath "$TEMP\pyserial-2.5"
  File /r "C:\mpy_temp\pyserial-2.5.tar\pyserial-2.5\pyserial-2.5"
  SetOutPath "$TEMP\pyserial-2.5\pyserial-2.5"
  ExecWait '"$PythonDir\python.exe" setup.py install' $0
  DetailPrint "Pyserial installer returned $0"
  ${If} $0 != 0
      MessageBox MB_OK|MB_ICONEXCLAMATION "Error ($0) while installing pyserial. Installation Failed"
      Abort
  ${EndIf}

;  MessageBox MB_OK "pyserial install"

SectionEnd



;------------------------------------------
; Section to install Editra if necessary
;------------------------------------------
Section /o "Editra" EditraSection

  StrCpy "$MpyDir" "$INSTDIR"
 
  ; identify the Editra instalation script
;  MessageBox MB_OK "Editra install"
  SetOverwrite try
  SetOutPath "$TEMP\Editra"
  File  /r "C:\mpy_temp\Editra-0.7.12.tar\dist\Editra-0.7.12\Editra-0.7.12"


  ; install wxpython
  SetOutPath "$TEMP\Editra\Editra-0.7.12"
  ExecWait '"$PythonDir\python.exe" setup.py install' $0
  DetailPrint "Editra installer returned $0"
  ${If} $0 != 0
      MessageBox MB_OK|MB_ICONEXCLAMATION "Error ($0) while installing Editra. Installation Failed"
      Abort
  ${EndIf}

  !insertmacro RepInFile  "$PythonDir\Lib\site-packages\Editra\src\ed_main.py" \
            "        if _PGET('LAST_SESSION') == mgr.DefaultSession:" \
            "        if 1 or _PGET('LAST_SESSION') == mgr.DefaultSession:"


;  Delete "$TEMP\wxPython2.8-win32-unicode-2.8.12.1-py27.exe"
;  MessageBox MB_OK "editra install"

SectionEnd



;------------------------------------------
; SECTION 
; Install MPY tools
;------------------------------------------
Section /o "MPY Tools" MpyToolsSection
  SectionIn 1 2
  ; Extract the files and make shortcuts

  StrCpy "$MpyDir" "$INSTDIR"

  SetOverwrite try
  SetOutPath "$MpyDir"
  File /r "C:\MPY\mspgcc"
  File /r "C:\MPY\mspdebug"
  File    "C:\MPY\mpy_driver_installer.0.1.exe"

SectionEnd

;------------------------------------------
; SECTION 
; Install Driver
;------------------------------------------
#Section /o "MSP430 CDC Uart Driver" MpyDriverSection
#  SectionIn 1 2

Section "MSP430 CDC Uart Driver" MpyDriverSection


    ###################################
    # Look to see if a previous libusb driver has been installed by looking for it's inf file in the system dirs 
	${locate::Open} "$WINDIR\system32|$WINDIR\system|$WINDIR\sysWOW64" `/F=1 \
					/D=0 \
					/M=usb_human_interface_device_(interface_1).inf \
					/B=1`  $0 					

	StrCmp $0 0  done_libusb	
	${locate::Find} $0 $1 $2 $3 $4 $5 $6
    # If we didn't find traces of a previous libusb then don't try uninstalling it
    StrCmp $1 '' done_libusb

    MessageBox MB_OK|MB_ICONEXCLAMATION 'Found previous libusb driver inf file. It will now be uninstalled$\n\
           [$1]$\n\
           $\n\ 
           Please PLUG IN LAUNCHPAD BOARD so the driver can be recognized and removed.$\n\
           Also please OK any rollback driver messages that may pop up.$\n\
           This can sometimes take a few minutes...'
    #
    ###################################




  #### Remove the last libusb driver, maybe skipped if the inf file was not found

  StrCpy "$MpyDir" "$INSTDIR"

  ; Remove any remnants of the libusb driver, just in case.
  SetOverwrite try
  SetOutPath "$MpyDir\mpy_setup\drivers\libusb-win32-bin-1.2.5.0"

  File /r "C:\MPY\mpy_setup\drivers\libusb-win32-bin-1.2.5.0\"

  # Change directory to the executable which matches the cpu
  ${If} ${RunningX64}
     SetOutPath "$MpyDir\mpy_setup\drivers\libusb-win32-bin-1.2.5.0\bin\amd64"
  ${Else}
     SetOutPath "$MpyDir\mpy_setup\drivers\libusb-win32-bin-1.2.5.0\bin\x86"
  ${EndIf}
  ExecWait 'install-filter.exe uninstall --inf="$MpyDir\mpy_setup\drivers\libusb-win32-bin-1.2.5.0\USB_Human_Interface_Device_(Interface_1).inf"' $0
  DetailPrint "LibUsb install-filter.exe returned $0"
#  MessageBox MB_OK|MB_ICONEXCLAMATION "Error ($0) while installing LibUsb MspDebug Driver. Try re-installing, or use inf-wizard.exe"

  done_libusb:
  ${locate::Close} $0
  ${locate::Unload}



  SetOverwrite try
  SetOutPath "$MpyDir\mpy_setup\drivers\eZ430-UART"
  File /r    "C:\MPY\mpy_setup\drivers\eZ430-UART\"

  ExecWait '"$MpyDir\mpy_setup\drivers\eZ430-UART\preinstalCDC.exe"' $0
  DetailPrint "MSP430 Uart preinstalCDC $0"

  ${If} ${RunningX64}
      ExecWait '"$MpyDir\mpy_setup\drivers\eZ430-UART\dpinst64.exe" /c /q /sa /sw ' $0
  ${Else}
      ExecWait '"$MpyDir\mpy_setup\drivers\eZ430-UART\dpinst.exe" /c /q /sa /sw ' $0
  ${EndIf}
  DetailPrint "MSP430 Uart dpinst.exe returned $0"
#  MessageBox MB_OK|MB_ICONEXCLAMATION "Error ($0) while installing eZ430-UART Driver. Try re-installing, or use Device Manager to install"

 
SectionEnd



;------------------------------------------
; SECTION 4
; Install MPY editor
;------------------------------------------
Section /o "MPY Editor" MpyEditorSection
  SectionIn 1 2
  ; Extract the files and make shortcuts

  SetOverwrite try
  SetOutPath "$MpyDir"
  File /r "C:\MPY\mpy_editor"
  ;File /r "C:\MPY\mpy_uart"
  File /r "C:\MPY\mpy_setup"
  File /r "C:\MPY\mpy_examples"
  File /r "C:\MPY\www.mpyprojects.com"


  SetOverwrite try  
  SetOutPath "$PythonDir\Lib\site-packages\Editra\plugins" 
  File       "C:\Python27\Lib\site-packages\Editra\plugins\*.*"

  # re define the link to point to the actual MPY instalation directory
  !insertmacro RepInFile  "$PythonDir\Lib\site-packages\Editra\plugins\mpy.egg-link"     "C:\MPY" "$INSTDIR"
  !insertmacro RepInFile  "$PythonDir\Lib\site-packages\Editra\plugins\mpyuart.egg-link" "C:\MPY" "$INSTDIR"
  


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



  
SectionEnd


;------------------------------------------
; SECTION 4
; Install MPY Default User Settings
;------------------------------------------
Section /o "MPY User Settings" MpyEditorSettingsSection
  SectionIn 1
  SetOverwrite try
  
  # we have to try all combinations 
  SetShellVarContext current
  SetOutPath "$APPDATA\Editra\"
  File /r "C:\Documents and Settings\mike asker\Application Data\Editra\*.*"
  SetOverwrite try
  SetOutPath "$LOCALAPPDATA\Editra\"
  File /r "C:\Documents and Settings\mike asker\Application Data\Editra\*.*"

#  # re define the link to point to the actual MPY instalation directory
#  !insertmacro RepInFile       "$APPDATA\Editra\sessions\default.session"   "C:\MPY" "$INSTDIR"
#  !insertmacro RepInFile  "$LOCALAPPDATA\Editra\sessions\default.session"   "C:\MPY" "$INSTDIR"
#  !insertmacro RepInFile       "$APPDATA\Editra\sessions\__default.session" "C:\MPY" "$INSTDIR"
#  !insertmacro RepInFile  "$LOCALAPPDATA\Editra\sessions\__default.session" "C:\MPY" "$INSTDIR"


SectionEnd




;------------------------------------------
; Make/Install Shortcut links
;------------------------------------------
Section -AdditionalIcons
  SetOutPath  "$MpyDir"
  WriteIniStr "$MpyDir\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  SetShellVarContext all
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk"    "$PythonDir\Scripts\editra.bat"           "" "$MpyDir\mpy_setup\install\${MUI_ICON}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Website.lnk"            "$MpyDir\${PRODUCT_NAME}.url"             "" "$MpyDir\mpy_setup\install\${MUI_ICON}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\MpyDriverInstaller.lnk" "$MpyDir\mpy_driver_installer.0.1.a1.exe" "" "$MpyDir\mpy_setup\install\${MUI_ICON}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk"          "$MpyDir\uninst.exe"                      "" "$MpyDir\mpy_setup\install\${MUI_ICON}"
SectionEnd



;------------------------------------------
; Post installation setup
;------------------------------------------
Section -Post


  ; run the driver installer
  SetOutPath "$MpyDir"
;  ExecWait "$MpyDir\mpy_driver_installer.0.1.exe" $0
  


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


  # Check to see if user is running with Admin previleges,
  # Admin is required for the install
  # call userInfo plugin to get user info.  The plugin puts the result in the stack
  userInfo::getAccountType
  pop $0
  ${If} $0 != "Admin"
      MessageBox MB_OK|MB_ICONEXCLAMATION "You must 'Run as Administrator' (Account type = $0). Instllation Cancelled"
      Abort
  ${EndIf}
 

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
  Abort

  done:
  
FunctionEnd

; - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
  
Function detect_components_already_installed

  
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
      Goto WXPython29DoesNotExist
  ${EndIf}
  

  ; WXPYTHON
  IfFileExists "$PythonDir\Lib\site-packages\wx-2.8-msw-unicode" DoneWXPythonCheck WXPython28DoesNotExist
  WXPython28DoesNotExist:
  IfFileExists "$PythonDir\Lib\site-packages\wx-2.9-msw-unicode" DoneWXPythonCheck WXPython29DoesNotExist
  WXPython29DoesNotExist:
  !insertmacro SelectSection ${WXPythonSection}
  Goto EditraDoesNotExist
  DoneWXPythonCheck:

  ; EDITRA
  IfFileExists "$PythonDir\Lib\site-packages\Editra" DoneEditraCheck EditraDoesNotExist
  EditraDoesNotExist:
  !insertmacro SelectSection ${EditraSection}
  DoneEditraCheck:
  
  StrCpy "$MpyDir" "$INSTDIR"
  
  ; MPYTOOLS
  IfFileExists "$MpyDir\devcon" DoneMpyToolsCheck MpyToolsDoesNotExist
  MpyToolsDoesNotExist:
  !insertmacro SelectSection ${MpyToolsSection}
  DoneMpyToolsCheck:

  ; MSP430 CDC Driver, always install the driver
  !insertmacro SelectSection ${MpyDriverSection}

  ; MPY_EDITOR
  IfFileExists "$MpyDir\mpy_editor" DoneMpyEditorCheck MpyEditorDoesNotExist
  MpyEditorDoesNotExist:
  !insertmacro SelectSection ${MpyEditorSection}
  DoneMpyEditorCheck:


  ; MPY_USER_SETTINGS
#  StrCpy $MpyUserSettings "not_present"
#  ${If} ${FileExists}     "$APPDATA\Editra"
#      StrCpy $MpyUserSettings "present"
#  ${ElseIf} ${FileExists} "$LOCALAPPDATA\Editra"
#      StrCpy $MpyUserSettings "present"
#  ${EndIf}
#  
#  ${If} $MpyUserSettings == "not_present"
#      !insertmacro SelectSection ${MpyEditorSettingsSection}
#  ${EndIf}

  # always update the user settings so that novice users always get a reset and clean startup directory in editra 
  !insertmacro SelectSection ${MpyEditorSettingsSection}

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
  !insertmacro MUI_DESCRIPTION_TEXT ${MpyDriverSection} "MSP430 Uart 430CDC Driver"
  !insertmacro MUI_DESCRIPTION_TEXT ${MpyEditorSection}         "Mpy Editor"
  !insertmacro MUI_DESCRIPTION_TEXT ${MpyEditorSettingsSection} "Mpy Load Default User Settings"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

ComponentText "Python will be installed in directory $PythonDir$\nMpy components will be installed in directory $INSTDIR" 


;------------------------------- End Installer --------------------------------
;##############################################################################
;##############################################################################








;##############################################################################
;##############################################################################
;----------------------------- Start Uninstaller ------------------------------

Function un.onInit

  # Check to see if user is running with Admin previleges,
  # Admin is required for the install
  # call userInfo plugin to get user info.  The plugin puts the result in the stack
  userInfo::getAccountType
  pop $0
  ${If} $0 != "Admin"
      MessageBox MB_OK|MB_ICONEXCLAMATION "You must 'Run as Administrator' (Account type = $0). Un-installer Cancelled"
      Abort
  ${EndIf}
 
FunctionEnd


# Only remove python27 stuff, this is the only version of python that this instalation installed
Section /o "un.Python Modules" UNPythonModulesSection
  SectionIn 1


  ExecWait '"C:\Python27\Lib\site-packages\wx-2.8-msw-unicode\unins000.exe"  /SILENT' $0 
  RmDir /r "C:\Python27"

  DeleteRegKey HKLM "*\wxPython2.8-unicode-py27_is1"
  DeleteRegKey HKLM "*\pywin32-py2.7"
    
SectionEnd



Section /o "un.MPY Tools" UNMpyToolsSection
  SectionIn  1
  RmDir /r "$INSTDIR\devcon"
  RmDir /r "$INSTDIR\mspdebug_*"
  RmDir /r "$INSTDIR\mspgcc-*"
  RmDir /r "$INSTDIR\mspdebug"
  RmDir /r "$INSTDIR\mspgcc"
SectionEnd



Section "un.MPY Editor" UNMpyEditorSection
  ; Ensure shortcuts are removed from user directory as well
  
  RmDir /r "$INSTDIR\mpy_editor"
  RmDir /r "$INSTDIR\mpy_examples"
  RmDir /r "$INSTDIR\www.mpyprojects.com"
  RmDir /r "$INSTDIR\mpy_setup"
  Delete  "$INSTDIR\mpy_driver_installer.*.exe"  
  Delete  "$INSTDIR\Mpy*.*"  
  
#  RmDir "$INSTDIR"   ## Too dangerous !!  
  

  
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
  DeleteRegKey HKCR ".mpy"

  RmDir /r "$INSTDIR\mpy_uart"

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
  !insertmacro MUI_DESCRIPTION_TEXT ${UNPythonModulesSection} "Python Core Language, PySerial, Pywin32, WxPython, Editra"
!insertmacro MUI_UNFUNCTION_DESCRIPTION_END

;------------------------------ End Uninstaller -------------------------------
