;------------------------------------------------------------------------------
; Mpy Editor Windows Installer Build Script
; Author: Mike Asker
; Language: NSIS
; Licence: GPL
;------------------------------------------------------------------------------


;##############################################################################
;------------------------------ Start MUI Setup -------------------------------

; Global Variables
!define PRODUCT_NAME "MpyDriverInstaller"
!define PRODUCT_VERSION "0.1.a2"
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


!include LogicLib.nsh
!include "x64.nsh"


/*
    ${If} ${RunningX64}
       MessageBox MB_OK "running on x64"
    ${Else}
       MessageBox MB_OK "running on x86"
    ${EndIf}
*/









;#######################################################################################
;#####  PAGES       ####################################################################
;#######################################################################################
; Welcome page

!define MUI_WELCOMEPAGE_TITLE_3LINES "True"
!define MUI_TEXT_WELCOME_INFO_TITLE 'MPY DRIVER INSTALLER$\n\
Plug in your Launchpad board now.$\n\
Then Click the Install Button'


!insertmacro MUI_PAGE_WELCOME


!insertmacro MUI_PAGE_INSTFILES



;#######################################################################################
;#######################################################################################


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
OutFile "C:\MPY\mpy_driver_installer.${PRODUCT_VERSION}.exe"
;InstallDir "$PROGRAMFILES\${PRODUCT_NAME}"
InstallDir "$EXEDIR"
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


Section "Plug-in Launchpad" PlugInSection

#  System::Call "kernel32::GetCurrentDirectory(i ${NSIS_MAX_STRLEN}, t .r0)"
#  StrCpy "$0" $INSTDIR
#  StrCpy $EXEDIR $INSTDIR

#  MessageBox MB_OKCANCEL|MB_ICONINFORMATION  \
#  "Plug in the Launchpad board now. then press OK,$\nor press Cancel to skip the Driver Installation$\n$\n(Note you should Cancel the Windows 'Found New Driver' Wizard if it pops up, the Mpy Driver Installer is going to do the installation instead)" \
#  IDOK done
#  Abort
  
  done:


SectionEnd


;------------------------------------------
; Section to install Libusb driver 
;------------------------------------------
Section "LibUsb MspDebug" LibUsbSection

/*
  ${If} ${RunningX64}
     MessageBox MB_OK "running on x64"
  ${Else}
     MessageBox MB_OK "running on x32" 
  ${EndIf}
*/

  SetOverwrite try
  SetOutPath "$INSTDIR\mpy_setup\drivers\libusb-win32-bin-1.2.5.0"
  File /r "C:\MPY\mpy_setup\drivers\libusb-win32-bin-1.2.5.0"

  # Change directory to the executable which matches the cpu
  ${If} ${RunningX64}
     SetOutPath "$INSTDIR\mpy_setup\drivers\libusb-win32-bin-1.2.5.0\bin\amd64"
  ${Else}
     SetOutPath "$INSTDIR\mpy_setup\drivers\libusb-win32-bin-1.2.5.0\bin\x86"
  ${EndIf}
  ExecWait 'install-filter.exe install --inf="$INSTDIR\mpy_setup\drivers\libusb-win32-bin-1.2.5.0\USB_Human_Interface_Device_(Interface_1).inf"' $0
  DetailPrint "LibUsb install-filter.exe returned $0"

#  ${If} $0 != 0
#      MessageBox MB_OK|MB_ICONEXCLAMATION "Error ($0) while installing LibUsb MspDebug Driver. Try re-installing, or use inf-wizard.exe"
#  ${EndIf}




SectionEnd





;------------------------------------------
; Section to install Uart Driver
;------------------------------------------
Section "MSP430 Uart" CDC430Section

  SetOverwrite try
  SetOutPath "$INSTDIR\mpy_setup\drivers\eZ430-UART"
  File /r "C:\MPY\mpy_setup\drivers\eZ430-UART"

  ExecWait '"$INSTDIR\mpy_setup\drivers\eZ430-UART\preinstalCDC.exe"' $0
  DetailPrint "MSP430 Uart preinstalCDC $0"


  ${If} ${RunningX64}
#      ExecWait '"$INSTDIR\mpy_setup\drivers\eZ430-UART\dpinst64.exe" /c /q /sa /sw /f /PATH "$INSTDIR\mpy_setup\drivers\eZ430-UART"' $0
      ExecWait '"$INSTDIR\mpy_setup\drivers\eZ430-UART\dpinst64.exe" /c /q /sa /sw ' $0
  ${Else}
#      ExecWait '"$INSTDIR\mpy_setup\drivers\eZ430-UART\dpinst.exe" /c /q /sa /sw /f /PATH "$INSTDIR\mpy_setup\drivers\eZ430-UART"' $0
      ExecWait '"$INSTDIR\mpy_setup\drivers\eZ430-UART\dpinst.exe" /c /q /sa /sw ' $0
  ${EndIf}
  DetailPrint "MSP430 Uart dpinst.exe returned $0"
#  ${If} $0 != 0
#      MessageBox MB_OK|MB_ICONEXCLAMATION "Error ($0) while installing eZ430-UART Driver. Try re-installing, or use Device Manager to install"
#  ${EndIf}

 
SectionEnd



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
  System::Call 'kernel32::CreateMutexA(i 0, i 0, t "launchpad_driver_installer") i .r1 ?e'
  Pop $R0
  StrCmp $R0 0 +3
    MessageBox MB_OK|MB_ICONEXCLAMATION "The Launchpad Driver Installer is already running."
    Abort


  
FunctionEnd










;###############################################################################################
;###############################################################################################

/*
; Description Texts for Component page
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${LibUsbSection} "Libusb0 MspDebug Driver"
  !insertmacro MUI_DESCRIPTION_TEXT ${CDC430Section} "MSP430 Application UART COM Driver"
!insertmacro MUI_FUNCTION_DESCRIPTION_END
*/




;------------------------------- End Installer --------------------------------
;##############################################################################
;##############################################################################








