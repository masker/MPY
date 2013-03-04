# -*- coding: utf-8 -*-
###############################################################################
# Name: mpy.py                                                                #
# Purpose:                                                                    #
# Authors: 
#         Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""Launch User Interface"""
__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id: launch.py 67746 2011-05-14 16:52:56Z CJP $"
__revision__ = "$Revision: 67746 $"

#-----------------------------------------------------------------------------#
# Imports
import os
import wx
import wx.stc
import sys

# Local Imports
import handlers
import cfgdlg

# Editra Libraries
import ed_glob
import ed_basestc
import util
from profiler import Profile_Get, Profile_Set
import ed_txt
import ed_msg
import ebmlib
import eclib
import ed_basewin

import subprocess
import shlex
import time
import re
import threading


#import run_uart_comport

#-----------------------------------------------------------------------------#
# Globals
ID_EXECUTABLE = wx.NewId()
ID_ARGS    = wx.NewId()
ID_PROG    = wx.NewId()
ID_DRVINST = wx.NewId()

# Profile Settings Key
#LAUNCH_PREFS = 'Launch.Prefs' # defined in cfgdlg

# Custom Messages
MSG_RUN_LAUNCH = ('launch', 'run')
MSG_RUN_LAST = ('launch', 'runlast')
MSG_LAUNCH_REGISTER = ('launch', 'registerhandler') # msgdata == xml string

# Value request messages
REQUEST_ACTIVE = 'Launch.IsActive'
REQUEST_RELAUNCH = 'Launch.CanRelaunch'

_ = wx.GetTranslation
#-----------------------------------------------------------------------------#

def OnRegisterHandler(msg):
    """Register a custom handler
    @param msg: dict(xml=xml_str, loaded=bool)

    """
    data = msg.GetData()
    loaded = False
    if isinstance(data, dict) and 'xml' in data:
        loaded = handlers.LoadCustomHandler(data['xml'])
    data['loaded'] = loaded
ed_msg.Subscribe(OnRegisterHandler, MSG_LAUNCH_REGISTER)

#-----------------------------------------------------------------------------#

class MpyWindow(ed_basewin.EdBaseCtrlBox):
    """Control window for showing and running scripts"""
    def __init__(self, parent):
        super(MpyWindow, self).__init__(parent)


        

        # Attributes
        self._log = wx.GetApp().GetLog()
        self._mw = ed_basewin.FindMainWindow(self)
        self._buffer = OutputDisplay(self)
        self._fnames = list()
        self._run = None        # Created in __DoLayout
        self._pbtn = None       # Created in __DoLayout
        self._clear = None      # Created in __DoLayout
        self._lockFile = None   # Created in __DoLayout
        self._chFiles = None    # Created in __DoLayout
        self._chDevices = None
        self._worker = None
        self._busy = False
        self._isready = False
        self._state = dict(file='', lang=0, cfile='', clang=0, last='', 
                           lastlang=0, prelang=0, largs='', lcmd='')


        # MPY setup
        self.python_exe   = r'%s\python.exe' % ( sys.exec_prefix )
        tstr = sys.modules[__name__].__file__
        idx = tstr.index(  r'\mpy_editor\mpy' )
        self.mpy_dir = tstr[:idx]

        self.mspDebugLock = threading.Lock()
        self.mspDeviceSelected = 'Auto'
        self.mspDeviceDetected = 'Unknown'
        self.mspDevices = ['Auto', 'msp430g2211','msp430g2231','msp430g2452','msp430g2553' ]
        self.mspDevice = 'Unknown'
        self.mspLaunchpadStatus_previous = 'Not_Connected'
        
        self.colors = { 'yellow'      : wx.Colour(255, 210,  95), 
                        'green'       : wx.Colour(174, 255, 111), 
                        'light_green' : wx.Colour(76,  239,  92),
                        'red'         : wx.Colour(255, 133, 106), 
                        'grey'        : wx.Colour(128, 128, 128),  }
                        
        self.Locked = False
        self.mspStatusStr  =  '.             unknown               .'
        self.mspStatusColor   = wx.Colour(255, 210, 95)


        # Setup
        self.__DoLayout()
        if not handlers.InitCustomHandlers(ed_glob.CONFIG['CACHE_DIR']):
            util.Log(u"[mpy][warn] failed to load launch extensions")

        # Ensure preferences have been initialized
        if self.Preferences is None:
            self.Preferences = dict(autoclear=False,
                                    errorbeep=False,
                                    wrapoutput=False,
                                    defaultf=self._buffer.GetDefaultForeground().Get(),
                                    defaultb=self._buffer.GetDefaultBackground().Get(),
                                    errorf=self._buffer.GetErrorForeground().Get(),
                                    errorb=self._buffer.GetErrorBackground().Get(),
                                    infof=self._buffer.GetInfoForeground().Get(),
                                    infob=self._buffer.GetInfoBackground().Get(),
                                    warnf=self._buffer.GetWarningForeground().Get(),
                                    warnb=self._buffer.GetWarningBackground().Get())

        self.UpdateBufferColors()
        cbuffer = GetTextBuffer(self.MainWindow)
        self.SetupControlBar(cbuffer)
        self.State['lang'] = GetLangIdFromMW(self.MainWindow)
        self.UpdateCurrentFiles(self.State['lang'])
        self.SetFile(cbuffer.GetFileName())

        # Setup filetype settings
        self.RefreshControlBar()

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnButton)
        self.Bind(wx.EVT_CHOICE, self.OnChoice)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheck)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy, self)
        ed_msg.Subscribe(self.OnPageChanged, ed_msg.EDMSG_UI_NB_CHANGED)
        ed_msg.Subscribe(self.OnFileOpened, ed_msg.EDMSG_FILE_OPENED)
        ed_msg.Subscribe(self.OnThemeChanged, ed_msg.EDMSG_THEME_CHANGED)
        ed_msg.Subscribe(self.OnLexerChange, ed_msg.EDMSG_UI_STC_LEXER)
        ed_msg.Subscribe(self.OnConfigChange,
                         ed_msg.EDMSG_PROFILE_CHANGE + (handlers.CONFIG_KEY,))
        ed_msg.Subscribe(self.OnRunMsg, MSG_RUN_LAUNCH)
        ed_msg.Subscribe(self.OnRunLastMsg, MSG_RUN_LAST)
        ed_msg.RegisterCallback(self._CanLaunch, REQUEST_ACTIVE)
        ed_msg.RegisterCallback(self._CanReLaunch, REQUEST_RELAUNCH)

        # Start the MPY uart serial COM-PORT interface        
        self.con_check_thread = threading.Thread(target=self.CheckConnectionLoop, args=())
        self.con_check_thread.start()


    #---- Properties ----#
#    Locked = property(lambda self: self._lockFile.IsChecked())
    MainWindow = property(lambda self: self._mw)
    Preferences = property(lambda self: Profile_Get(handlers.CONFIG_KEY, default=None),
                           lambda self, prefs: Profile_Set(handlers.CONFIG_KEY, prefs))
    State = property(lambda self: self._state)


    

    #-------------------------------------------------------------------------------
    def OnDestroy(self, evt):
        if self:
            ed_msg.Unsubscribe(self.OnPageChanged)
            ed_msg.Unsubscribe(self.OnFileOpened)
            ed_msg.Unsubscribe(self.OnThemeChanged)
            ed_msg.Unsubscribe(self.OnLexerChange)
            ed_msg.Unsubscribe(self.OnConfigChange)
            ed_msg.Unsubscribe(self.OnRunMsg)
            ed_msg.Unsubscribe(self.OnRunLastMsg)
            ed_msg.UnRegisterCallback(self._CanLaunch)
            ed_msg.UnRegisterCallback(self._CanReLaunch)

    def __DoLayout(self):
        """Layout the window"""
        ctrlbar = self.CreateControlBar(wx.TOP)
        ctrlbar.SetBackgroundColour(wx.Colour(112,157,186))
        
        ctrlbar._color  = wx.Colour(33,  128, 188)
        ctrlbar._color2 = wx.Colour(162, 177, 186)
        ctrlbar.SetMargins( 3, 3 )
        
        
        
        # Preferences
#        self._pbtn = self.AddPlateButton(u"", ed_glob.ID_PREF)
#        self._pbtn.SetToolTipString(_("Settings"))


        # Script Label
#        self._lockFile = wx.CheckBox(ctrlbar, wx.ID_ANY)
#        self._lockFile.SetToolTipString(_("Lock File"))       
#        ctrlbar.AddControl(self._lockFile, wx.ALIGN_LEFT)




#         # Button
#         self._prog = self.AddPlateButton(_("   Prog    "), ID_PROG,   wx.ALIGN_LEFT)
#         self._prog.SetToolTipString(_("Compiles the file (mpy2c, mspgcc)\nDownloads the program to the Launchpad\nPrograms the Microcontroller\nthen it will Run (mspdebug)"))

        # add the mpy image
        ctrlbar.AddControl((5, 5), wx.ALIGN_LEFT)
#        bitmap = wx.Bitmap(r"C:\projects\msp_editra\images\mpy_logo_46x50.bmp", wx.BITMAP_TYPE_ANY)
        bitmap = wx.Bitmap(r"%s\mpy_setup\install\pixmaps\mpy_logo_controlbar.png" % self.mpy_dir, wx.BITMAP_TYPE_ANY)
        image = wx.ImageFromBitmap(bitmap)
        image = image.Scale(30, 30, wx.IMAGE_QUALITY_HIGH)
        bitmap = wx.BitmapFromImage(image)
        self.mpy_bitmap = wx.StaticBitmap(self, -1, bitmap )
        ctrlbar.AddControl( self.mpy_bitmap, wx.ALIGN_LEFT)

        ctrlbar.AddControl((5, 5), wx.ALIGN_LEFT)

        self._conStatusTxt = wx.StaticText(ctrlbar, wx.ID_ANY, 'Launchpad: ')
        self._conStatusTxt.SetForegroundColour(wx.Colour(0, 0, 0))
        ctrlbar.AddControl(self._conStatusTxt, wx.ALIGN_LEFT)

        # Connection Status of Launchpad  
        self._conStatus = wx.StaticText(ctrlbar, wx.ID_ANY, self.mspStatusStr)
        self._conStatus.SetForegroundColour(wx.Colour(0, 0, 0))
        self._conStatus.SetBackgroundColour(self.mspStatusColor)
#        self._conStatus.SetLabel(_(".             unknown               ."))
        ctrlbar.AddControl(self._conStatus, wx.ALIGN_LEFT)
        self._conStatus.SetToolTipString(_("The Launchpad Chip Connection Status"))


        # List of Devices to choose from  
#         self._chDevices = wx.Choice(ctrlbar, wx.ID_ANY, choices=self.mspDevices)
#         self._chDevices.SetSelection( 0 )
#         ctrlbar.AddControl(self._chDevices, wx.ALIGN_LEFT)
#         self._chDevices.SetToolTipString(_("Select the Microcontroller chip used in the Launchpad,\nor select 'Auto' to automatically detect the chip (recommended)"))
 

        self._chFiles = wx.Choice(ctrlbar, wx.ID_ANY)#, choices=[''])
        ctrlbar.AddControl(self._chFiles, wx.ALIGN_LEFT)

        ctrlbar.AddControl((5, 5), wx.ALIGN_LEFT)
        
        # Button
        self._run = wx.Button(ctrlbar, ID_PROG, "Program")
        self._run.SetBackgroundColour(self.colors['green'])
        self._run.SetToolTipString(_("PROGRAM the Launchpad\n - Compiles the file (mpy2c, mspgcc)\n - Downloads the program to the Launchpad\n - Programs the Microcontroller\n - Then it will run (mspdebug)"))
        ctrlbar.AddControl(self._run, wx.ALIGN_LEFT)
#        self._run   = self.AddPlateButton(_("  PROG  "),   ed_glob.ID_BIN_FILE, wx.ALIGN_LEFT)
#        self._run   = self.AddPlateButton(_("  PROG  "),   ID_PROG, wx.ALIGN_LEFT)
#        self._run.SetPressColor( self.colors['green'] )        

        # Spacer
        ctrlbar.AddStretchSpacer()

 
        # Button
        self._drvinst = wx.Button(ctrlbar, ID_DRVINST,_("  Install Launchpad Driver  "))
        self._drvinst.SetToolTipString(_("Runs the Launchpad Driver Software Installation Program"))
        self._drvinst.SetBackgroundColour(self.colors['green'])
        ctrlbar.AddControl(self._drvinst, wx.ALIGN_LEFT)
#        self._drvinst = self.AddPlateButton(_("  Install Launchpad Driver  "), ID_DRVINST,   wx.ALIGN_RIGHT)
#        self._drvinst.SetPressColor( self.colors['green'] )
        ctrlbar.AddControl((5, 5), wx.ALIGN_LEFT)
        
        # Button
        self._clear = self.AddPlateButton(_("Clear"), ed_glob.ID_DELETE,   wx.ALIGN_RIGHT)
        self._clear.SetPressColor( self.colors['green'] )
        self.SetWindow(self._buffer)
        



    def _CanLaunch(self):
        """Method to use with RegisterCallback for getting status"""
        val = self.CanLaunch()
        if not val:
            val = ed_msg.NullValue()
        return val

    def _CanReLaunch(self):
        """Method to use with RegisterCallback for getting status"""
        val = self.CanLaunch()
        if not val or not len(self.State['last']):
            val = ed_msg.NullValue()
        return val

    def CanLaunch(self):
        """Can the launch window run or not
        @return: bool

        """
        return self.TopLevelParent.IsActive() and self._isready

    def GetFile(self):
        """Get the file that is currently set to be run
        @return: file path

        """
        return self.State['file']

    def GetLastRun(self):
        """Get the last file that was run
        @return: (fname, lang_id)

        """
        return (self.State['last'], self.State['lastlang'])

    def OnButton(self, evt):
        """Handle events from the buttons on the control bar"""
        e_obj = evt.GetEventObject()
#         if e_obj == self._pbtn:
#             app = wx.GetApp()
#             win = app.GetWindowInstance(cfgdlg.ConfigDialog)
#             if win is None:
#                 config = cfgdlg.ConfigDialog(self.MainWindow)
#                 config.CentreOnParent()
#                 config.Show()
#             else:
#                 win.Raise()
        if e_obj is self._run:
            # May be run or abort depending on current state
            self.StartStopProg()
#            self.StartStopProcess()
#         elif e_obj is self._prog:
#             # May be run or abort depending on current state
#             self.StartStopProg()
        elif e_obj is self._drvinst:
            # May be run or abort depending on current state
            self.RunDrvInstScript()
        elif e_obj == self._clear:
            self._buffer.Clear()
        else:
            evt.Skip()


    #-------------------------------------------------------------------------------------
    def OnTimerCheckConnection(self, evt=None):
        """Handle the Timer event for checking the connection status
        @param evt: wx.CommandEvent
        
        """
 
        # Check to see if the launchpad board is connected or not
        self.mspLaunchpadDetected, self.mspLaunchpadStatus, self.mspLaunchpadStatusColor = run_mspdebug(self)

        # If the connection status changed from not connected to connected,
        # then do a full check to find out which microcontroller is on the board.
        # Be aware that this will reset the microcontroller, so we only do a 
        # full check when the launchpad connection status changes

        if self.mspLaunchpadStatus == 'Connected' and self.mspLaunchpadStatus_previous != 'Connected':
            self.mspDeviceDetected, self.mspDeviceStatus, self.mspDeviceStatusColor = run_mspdebug_full(self)
            tstr = re.sub( '_', ' ', self.mspDeviceDetected.upper() )
            tstr = 'Connected: %s' % tstr
            self.mspLaunchpadStatusStr = tstr
            self.mspStatusColor = self.colors[self.mspDeviceStatusColor]
        elif self.mspLaunchpadStatus == 'Not_Connected':   # not connected
            tstr = re.sub( '_', ' ', self.mspLaunchpadStatus )
            self.mspLaunchpadStatusStr = tstr
            self.mspStatusColor = self.colors[self.mspLaunchpadStatusColor]
#             self._conStatus.SetLabel( tstr )
#             self._conStatus.SetBackgroundColour(color)        
        
        else:  # still connected, don't update the connection status
            pass
            

        self.mspLaunchpadStatus_previous = self.mspLaunchpadStatus
        
#        self.timer_con_status.Start(2000, oneShot=True)
        return  (self.mspLaunchpadStatusStr, self.mspStatusColor )

    #--------------------------------------------------------------------------------
    def CheckConnectionLoop( self ):
        '''Continuously running loop is run in a separate thread and is responsible for
        checcking the connection status to the Launchpad'''
        
        while 1:    
            time.sleep(2)
            (tstr, color) = self.OnTimerCheckConnection()
            wx.CallAfter( self.UpdateConnectionStatus, (tstr,color) )

    #--------------------------------------------------------------------------------
    def UpdateConnectionStatus( self, status):
        '''Updates the GUI connection status, from the wx.CallAfter call from the  
        CheckConnectionLoop funcion which is running in a separate thread
        '''
        
        (tstr, color) = status    
        self._conStatus.SetLabel( tstr )
        self._conStatus.SetBackgroundColour(color)        

    
    #--------------------------------------------------------------------------------
    def OnChoice(self, evt):
        """Handle events from the Choice controls
        @param evt: wx.CommandEvent

        """
        e_id = evt.GetId()
        e_sel = evt.GetSelection()
        if e_id == self._chFiles.GetId():
            fname = self._fnames[e_sel]
            self.SetFile(fname)
            self._chFiles.SetToolTipString(fname)
        elif e_id == self._chDevices.GetId():
            self.mspDeviceSelected = self._chDevices.GetStringSelection()

            
        elif e_id == ID_EXECUTABLE:
            e_obj = evt.GetEventObject()
            handler = handlers.GetHandlerById(self.State['lang'])
            cmd = e_obj.GetStringSelection()
            e_obj.SetToolTipString(handler.GetCommand(cmd))
        else:
            evt.Skip()

    def OnCheck(self, evt):
        """CheckBox for Lock File was clicked"""
        e_obj = evt.GetEventObject()
        if 0 and e_obj is self._lockFile:
            if self.Locked:
                self._chFiles.Disable()
            else:
                self._chFiles.Enable()
                cbuff = GetTextBuffer(self.MainWindow)
                if isinstance(cbuff, ed_basestc.EditraBaseStc):
                    self.UpdateCurrentFiles(cbuff.GetLangId())
                    self.SetupControlBar(cbuff)
        else:
            evt.Skip()

    def OnConfigChange(self, msg):
        """Update current state when the configuration has been changed
        @param msg: Message Object

        """
        util.Log("[MspPy][info] Saving config to profile")
        self.RefreshControlBar()
        self._buffer.UpdateWrapMode()
        self.UpdateBufferColors()

    @ed_msg.mwcontext
    def OnFileOpened(self, msg):
        """Reset state when a file open message is received
        @param msg: Message Object

        """
        if self.Locked:
            return # Mode is locked ignore update

        # Update the file choice control
        self.State['lang'] = GetLangIdFromMW(self.MainWindow)
        self.UpdateCurrentFiles(self.State['lang'])

        fname = msg.GetData()
        self.SetFile(fname)

        # Setup filetype settings
        self.RefreshControlBar()

    @ed_msg.mwcontext
    def OnLexerChange(self, msg):
        """Update the status of the currently associated file
        when a file is saved. Used for updating after a file type has
        changed due to a save action.
        @param msg: Message object

        """
        self._log("[mpy][info] Lexer changed handler - context %d" %
                  self.MainWindow.GetId())

        if self.Locked:
            return # Mode is locked ignore update

        mdata = msg.GetData()
        # For backwards compatibility with older message format
        if mdata is None:
            return

        fname, ftype = msg.GetData()
        # Update regardless of whether lexer has changed or not as the buffer
        # may have the lexer set before the file was saved to disk.
        if fname:
            self.UpdateCurrentFiles(ftype)
            self.SetControlBarState(fname, ftype)

    @ed_msg.mwcontext
    def OnPageChanged(self, msg):
        """Update the status of the currently associated file
        when the page changes in the main notebook.
        @param msg: Message object

        """
        # The current mode is locked
        if self.Locked:
            return

        mval = msg.GetData()
        ctrl = mval[0].GetCurrentCtrl()
        if isinstance(ctrl, ed_basestc.EditraBaseStc):
            self.UpdateCurrentFiles(ctrl.GetLangId())
            self.SetupControlBar(ctrl)
        else:
            self._log("[mpy][info] Non STC object in notebook")
            return # Doesn't implement EdStc interface

    def OnRunMsg(self, msg):
        """Run or abort a launch process if this is the current 
        launch window.
        @param msg: MSG_RUN_LAUNCH

        """
        if self.CanLaunch():
            shelf = self.MainWindow.GetShelf()
            shelf.RaiseWindow(self)
            self.StartStopProcess()

    def OnRunLastMsg(self, msg):
        """Re-run the last run program.
        @param msg: MSG_RUN_LAST

        """
        if self.CanLaunch():
            fname, ftype = self.GetLastRun()
            # If there is no last run file return
            if not len(fname):
                return

            shelf = self.MainWindow.GetShelf()
            self.UpdateCurrentFiles(ftype)
            self.SetFile(fname)
            self.RefreshControlBar()
            shelf.RaiseWindow(self)

            if self.Preferences.get('autoclear'):
                self._buffer.Clear()

            self.SetProcessRunning(True)

            self.Run(fname, self.State['lcmd'], self.State['largs'], ftype)

    def OnThemeChanged(self, msg):
        """Update icons when the theme has been changed
        @param msg: Message Object

        """
        ctrls = ((self._pbtn, ed_glob.ID_PREF),
                 (self._clear, ed_glob.ID_DELETE))
        if self._busy:
            ctrls += ((self._run, ed_glob.ID_STOP),)
        else:
            ctrls += ((self._run, ed_glob.ID_BIN_FILE),)

        for btn, art in ctrls:
            bmp = wx.ArtProvider.GetBitmap(str(art), wx.ART_MENU)
            btn.SetBitmap(bmp)
            btn.Refresh()
        self.GetControlBar().Refresh()

    def RefreshControlBar(self):
        """Refresh the state of the control bar based on the current config"""
        handler = handlers.GetHandlerById(self.State['lang'])
        cmds = handler.GetAliases()

        # Get the controls
#         exe_ch = self.FindWindowById(ID_EXECUTABLE)
#         args_txt = self.FindWindowById(ID_ARGS)
        exe_ch = 'dummy_exe'
        args_txt = 'dummy_args'

#         csel = exe_ch.GetStringSelection()
#         exe_ch.SetItems(cmds)
#         ncmds = len(cmds)
#         if ncmds > 0:
#             exe_ch.SetToolTipString(handler.GetCommand(cmds[0]))

        util.Log("[mpy][info] Found commands %s" % repr(cmds))
        if handler.GetName() != handlers.DEFAULT_HANDLER and \
            len(self.GetFile()):
#           ncmds > 0 and len(self.GetFile()):
#            for ctrl in (exe_ch, args_txt, self._run,
            for ctrl in (self._run,
                         self._chFiles):
#                         self._chFiles, self._lockFile):
                ctrl.Enable()

            self._isready = True
            if self.Locked:
                self._chFiles.Enable(False)

#             if self.State['lang'] == self.State['prelang'] and len(csel):
#                 exe_ch.SetStringSelection(csel)
#             else:
#                 csel = handler.GetDefault()
#                 exe_ch.SetStringSelection(csel)
# 
#             exe_ch.SetToolTipString(handler.GetCommand(csel))
            self.GetControlBar().Layout()
        else:
            self._isready = False
#            for ctrl in (exe_ch, args_txt, self._run,
            for ctrl in (self._run,
                         self._chFiles):
#                         self._chFiles, self._lockFile):
                ctrl.Disable()

    def Run(self, fname, cmd, args, ftype):
        """Run the given file
        @param fname: File path
        @param cmd: Command to run on file
        @param args: Executable arguments
        @param ftype: File type id

        """
        
        util.Log( '@@@@@@@@@@ MA(Run) <%s> <%s> <%s> <%s>' % (fname, cmd, args, ftype) )
        # Find and save the file if it is modified
        nb = self.MainWindow.GetNotebook()
        for ctrl in nb.GetTextControls():
            tname = ctrl.GetFileName()
            if fname == tname:
                if ctrl.GetModify():
                    ctrl.SaveFile(tname)
                    break

        handler = handlers.GetHandlerById(ftype)
        path, fname = os.path.split(fname)
        if wx.Platform == '__WXMSW__':
            fname = u"\"" + fname + u"\""
#            cmd   = u"\"" + cmd   + u"\""
        else:
            fname = fname.replace(u' ', u'\\ ')

        self._worker = eclib.ProcessThread(self._buffer,
                                           cmd, fname,
                                           args, path,
                                           handler.GetEnvironment(),
                                           use_shell=True,)
        self._worker.start()

    #----------------------------------------------------------------------------
    def RunDrvInstScript(self):
        """Starts a process to run the Launchpad Driver Install Script"""

        if self.Preferences.get('autoclear', False):
            self._buffer.Clear()

        
        cmd = r'%s -u %s\mpy_editor\mpy\driver_install.py'  % (self.python_exe, self.mpy_dir)       
        cmd = r'%s\mpy_driver_installer.0.1.a2.exe'  % (self.mpy_dir)       
            
        util.Log("[mpy][RunDrvInstScript] Starting Script %s" % cmd)
        self.State['lcmd'] = cmd
        args = ''
        self.State['largs'] = args
#        self._buffer.AppendUpdate( '[mpy] dir=%s cmd=%s\n' % (os.getcwd(), cmd) )
        self._buffer.AppendUpdate( "[mpy] Check for 'User Account Control' in background window\n[mpy] Click Yes to allow mpy_driver_installer.exe to make changes to this computer\n" )
        self._drvinst.SetBackgroundColour(self.colors['grey'])

        # Must give it a python type file for some reason!
        self.Run(self.State['file'], cmd, args, 32161)   


    #----------------------------------------------------------------------------
    def StartStopProcess(self):
        """Run or abort the context of the current process if possible"""
        if self.Preferences.get('autoclear', False):
            self._buffer.Clear()

        # Check Auto-save preferences
        if not self._busy:
            if self.Preferences.get('autosaveall', False):
                self.MainWindow.SaveAllBuffers()
            elif self.Preferences.get('autosave', False):
                self.MainWindow.SaveCurrentBuffer()

        # Start or stop the process
        self.SetProcessRunning(not self._busy)
        if self._busy:
            util.Log("[mpy][info] Starting process")
            handler = handlers.GetHandlerById(self.State['lang'])
            cmd = self.FindWindowById(ID_EXECUTABLE).GetStringSelection()
            self.State['lcmd'] = cmd
            cmd = handler.GetCommand(cmd)
            args = self.FindWindowById(ID_ARGS).GetValue().split()
            self.State['largs'] = args
            self.Run(self.State['file'], cmd, args, self.State['lang'])
        elif self._worker:
            util.Log("[mpy][info] Aborting process")
            self._worker.Abort()
            self._worker = None


    def StartStopProg(self, run_during_startup=False):
        """Run the Prog function
        Run or abort the context of the current process if possible"""
        
        if self.Preferences.get('autoclear', False):
            self._buffer.Clear()

        # Check Auto-save preferences
        if not self._busy:
            if self.Preferences.get('autosaveall', False):
                self.MainWindow.SaveAllBuffers()
            elif self.Preferences.get('autosave', False):
                self.MainWindow.SaveCurrentBuffer()

        # Start or stop the process
        self.SetProcessRunning(not self._busy)
        if self._busy:
            util.Log("[mpy][info] Starting process")
            handler = handlers.GetHandlerById(self.State['lang'])


            if  self.mspDeviceSelected == 'Auto':
                 self.mspDevice = self.mspDeviceDetected
            else:
                 self.mspDevice = self.mspDeviceSelected

            
            mpy_dir = r'C:\MPY'
            cmd = r'%s -u "%s\mpy_editor\mpy\prog.py "' % ( self.python_exe, self.mpy_dir,)


 
            
            self.State['lcmd'] = cmd
#            cmd = handler.GetCommand(cmd)

#            args = self.FindWindowById(ID_ARGS).GetValue().split()
            args = self.mspDevice
            self.State['largs'] = args
#            self.Run(self.State['file'], cmd, args, self.State['lang'])

            
#            self.Run(self.State['file'], cmd, args, self.State['lang'])
            
           
#            self._buffer.AppendUpdate( '[mpy] dir=%s cmd=%s\n' % (os.getcwd(), cmd) )
            # Must give it a python type file for some reason!
            
#            self._buffer.AppendUpdate( 'prog started' )
#            self._buffer.FlushBuffer()

#            self.mspDebugLock.acquire()
            self._run.SetBackgroundColour(self.colors['grey'])

            self.Run(self.State['file'], cmd, args, 32161)   


#            self._buffer.AppendUpdate( 'prog finished' )
#            self._buffer.FlushBuffer()


        elif self._worker:
            util.Log("[mpy][info] Aborting process")
            self._worker.Abort()
            self._worker = None
#            self.mspDebugLock.release()

    def SetFile(self, fname):
        """Set the script file that will be run
        @param fname: file path

        """
        # Set currently selected file
        self.State['file'] = fname
        self._chFiles.SetStringSelection(os.path.split(fname)[1])
        self.GetControlBar().Layout()

    def SetLangId(self, langid):
        """Set the language id value(s)
        @param langid: syntax.synglob lang id

        """
        self.State['prelang'] = self.State['lang']
        self.State['lang'] = langid

    def SetProcessRunning(self, running=True):
        """Set the state of the window into either process running mode
        or process not running mode.
        @keyword running: Is a process running or not

        """
        self._busy = running
        if running:
            self.State['last'] = self.State['file']
            self.State['lastlang'] = self.State['lang']
            self.State['cfile'] = self.State['file']
            self.State['clang'] = self.State['lang']
            abort = wx.ArtProvider.GetBitmap(str(ed_glob.ID_STOP), wx.ART_MENU)
            if abort.IsNull() or not abort.IsOk():
                abort = wx.ArtProvider.GetBitmap(wx.ART_ERROR,
                                                 wx.ART_MENU, (16, 16))
#            self._run.SetBitmap(abort)
            self._run.SetLabel(_("  PROG  "))
        else:
            rbmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_BIN_FILE), wx.ART_MENU)
            if rbmp.IsNull() or not rbmp.IsOk():
                rbmp = None
#            self._run.SetBitmap(rbmp)
            self._run.SetLabel(_("  PROG  "))
            # If the buffer was changed while this was running we should
            # update to the new buffer now that it has stopped.
            self.SetFile(self.State['cfile'])
            self.SetLangId(self.State['clang'])
            self.RefreshControlBar()

        self.GetControlBar().Layout()
        self._run.Refresh()

    def SetupControlBar(self, ctrl):
        """Set the state of the controlbar based data found in the buffer
        passed in.
        @param ctrl: EdStc

        """
        fname = ctrl.GetFileName()
        lang_id = ctrl.GetLangId()
        self.SetControlBarState(fname, lang_id)

    def SetControlBarState(self, fname, lang_id):
        # Don't update the bars status if the buffer is busy
        if self._buffer.IsRunning():
            self.State['cfile'] = fname
            self.State['clang'] = lang_id
        else:
            if not self.Locked:
                self.SetFile(fname)
                self.SetLangId(lang_id)

                # Refresh the control bars view
                self.RefreshControlBar()

    def UpdateBufferColors(self):
        """Update the buffers colors"""
        colors = dict()
        for color in ('defaultf', 'defaultb', 'errorf', 'errorb',
                      'infof', 'infob', 'warnf', 'warnb'):
            val = self.Preferences.get(color, None)
            if val is not None:
                colors[color] = wx.Colour(*val)
            else:
                colors[color] = val

        self._buffer.SetDefaultColor(colors['defaultf'], colors['defaultb'])
        self._buffer.SetErrorColor(colors['errorf'], colors['errorb'])
        self._buffer.SetInfoColor(colors['infof'], colors['infob'])
        self._buffer.SetWarningColor(colors['warnf'], colors['warnb'])

    def UpdateCurrentFiles(self, lang_id):
        """Update the current set of open files that are of the same
        type.
        @param lang_id: Editra filetype id
        @postcondition: all open files that are of the same type are set
                        and stored in the file choice control.

        """
        self._fnames = list()
        for txt_ctrl in self.MainWindow.GetNotebook().GetTextControls():
            if lang_id == txt_ctrl.GetLangId():
                self._fnames.append(txt_ctrl.GetFileName())

        items = [ os.path.basename(fname) for fname in self._fnames ]
        try:
            if len(u''.join(items)):
                self._chFiles.SetItems(items)
                if len(self._fnames):
                    self._chFiles.SetToolTipString(self._fnames[0])
        except TypeError:
            util.Log("[mpy][err] UpdateCurrent Files: " + str(items))
            self._chFiles.SetItems([''])

#-----------------------------------------------------------------------------#

class OutputDisplay(eclib.OutputBuffer, eclib.ProcessBufferMixin):
    """Main output buffer display"""
    def __init__(self, parent):
        eclib.OutputBuffer.__init__(self, parent)
        eclib.ProcessBufferMixin.__init__(self)

        # Attributes
        self._mw = parent.MainWindow
        self._cfile = ''
        
        self.parent_obj = parent

        # Setup
        font = Profile_Get('FONT1', 'font', wx.Font(11, wx.FONTFAMILY_MODERN,
                                                    wx.FONTSTYLE_NORMAL,
                                                    wx.FONTWEIGHT_NORMAL))
        self.SetFont(font)
        self.UpdateWrapMode()

    Preferences = property(lambda self: Profile_Get(handlers.CONFIG_KEY, default=dict()),
                           lambda self, prefs: Profile_Set(handlers.CONFIG_KEY, prefs))

    def ApplyStyles(self, start, txt):
        """Apply any desired output formatting to the text in
        the buffer.
        @param start: Start position of new text
        @param txt: the new text that was added to the buffer

        """
        handler = self.GetCurrentHandler()
        style = handler.StyleText(self, start, txt)

        # Ring the bell if there was an error and option is enabled
        if style == handlers.STYLE_ERROR and \
           self.Preferences.get('errorbeep', False):
            wx.Bell()

    def DoFilterInput(self, txt):
        """Filter the incoming input
        @param txt: incoming text to filter

        """
        handler = self.GetCurrentHandler()
        return handler.FilterInput(txt)

    def DoHotSpotClicked(self, pos, line):
        """Pass hotspot click to the filetype handler for processing
        @param pos: click position
        @param line: line the click happened on
        @note: overridden from L{eclib.OutputBuffer}

        """
        fname, lang_id = self.GetParent().GetLastRun()
        handler = handlers.GetHandlerById(lang_id)
        handler.HandleHotSpot(self._mw, self, line, fname)
        self.GetParent().SetupControlBar(GetTextBuffer(self._mw))

    def DoProcessError(self, code, excdata=None):
        """Handle notifications of when an error occurs in the process
        @param code: an OBP error code
        @keyword excdata: Exception string
        @return: None

        """
        if code == eclib.OPB_ERROR_INVALID_COMMAND:
            self.AppendUpdate(_("The requested command could not be executed.") + u"\n")

        # Log the raw exception data to the log as well
        if excdata is not None:
            try:
                excstr = str(excdata)
                if not ebmlib.IsUnicode(excstr):
                    excstr = ed_txt.DecodeString(excstr)
                util.Log(u"[mpy][err] %s" % excdata)
            except UnicodeDecodeError:
                util.Log(u"[mpy][err] error decoding log message string")

    def DoProcessExit(self, code=0):
        """Do all that is needed to be done after a process has exited"""
        
#        self.parent_obj.mspDebugLock.release()
        self.parent_obj._run.SetBackgroundColour(self.parent_obj.colors['green'])
        self.parent_obj._drvinst.SetBackgroundColour(self.parent_obj.colors['green'])
        
#        self.AppendUpdate("DoProcessExit\n")
#        self.FlushBuffer()


        
        # Peek in the queue to see the last line before the exit line
        queue = self.GetUpdateQueue()
        prepend_nl = True
        if len(queue):
            line = queue[-1]
        else:
            line = self.GetLine(self.GetLineCount() - 1)
        if line.endswith('\n') or line.endswith('\r'):
            prepend_nl = False
        final_line = u">>> %s: %d%s" % (_("Exit Code"), code, os.linesep)
        # Add an extra line feed if necessary to make sure the final line
        # is output on a new line.
        if prepend_nl:
            final_line = os.linesep + final_line
        self.AppendUpdate(final_line)
        self.Stop()
        self.GetParent().SetProcessRunning(False)

    def DoProcessStart(self, cmd=''):
        """Do any necessary preprocessing before a process is started"""
        self.GetParent().SetProcessRunning(True)
        self.AppendUpdate(">>> %s%s" % (cmd, os.linesep))

    def GetCurrentHandler(self):
        """Get the current filetype handler
        @return: L{handlers.FileTypeHandler} instance

        """
        lang_id = self.GetParent().GetLastRun()[1]
        handler = handlers.GetHandlerById(lang_id)
        return handler

    def UpdateWrapMode(self):
        """Update the word wrapping mode"""
        mode = wx.stc.STC_WRAP_NONE
        if self.Preferences.get('wrapoutput', False):
            mode = wx.stc.STC_WRAP_WORD
        self.SetWrapMode(mode)


#--------------------------------------------------------
def runcmd( command_line, log=False ):
        args = shlex.split(command_line)
        if log:   print 'command_line=', args
        
        # options to prevent console window from openning
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        p = subprocess.Popen( args , stdout=subprocess.PIPE,stderr=subprocess.STDOUT, startupinfo=startupinfo)
        output = p.communicate()[0] 
        # remove any double linefeeds
        output = re.sub('\r', '', output)
        if log:   print 'x=', output
        return output

#------------------------------------------------------------------------
def run_mspdebug(parent):
        '''This function runs mspdebug to determine whether the Launchpad is connected
        It does not cause the launchpad microcontroller chip to reset'''

#        parent.mspDebugLock.acquire()

        chip_id_dict = { '0xf201': 'msp430g2231', 
                         '0x2553': 'msp430g2553',
                         '0x2452': 'msp430g2452',
                       }
        chip_id = 'Unknown'
        mspdebug_ver = r'mspdebug_v020'
#        print '(mspdebug started)...',
        install_dir = r'%s\%s' % (parent.mpy_dir, mspdebug_ver)
        cmd = r'%s\mspdebug.exe' % install_dir
        cmd_opts = r'rf2500 "--usb-list"' 
        command_line = '"%s" %s' % (cmd,cmd_opts)
        op = runcmd( command_line )
        
        if re.search('0451:f432 eZ430-RF2500',op):
            connection_status = 'Connected'  # green
            color = 'yellow'
        else: 
            connection_status = 'Not_Connected'  # red
            color = 'red'
        
        
        if connection_status[0] == '_':
            chip_id = connection_status 


#        parent.mspDebugLock.release()
        
        return 'unknown', connection_status, color
        
        
#------------------------------------------------------------------------
def run_mspdebug_full(parent):
        '''This function will run mspdebug and find the chip number of the launchpad.
        Running this function will cause the microcontroller to reset.'''

#        parent.mspDebugLock.acquire()

        chip_id_dict = { '0xf201': 'msp430g2231', 
                         '0x2553': 'msp430g2553',
                         '0x2452': 'msp430g2452',
                       }
        chip_id = 'Un-recognized'
        mspdebug_ver = r'mspdebug_v020'
        print '(mspdebug started)...',
        install_dir = r'%s\%s' % (parent.mpy_dir, mspdebug_ver)
        cmd = r'%s\mspdebug.exe' % install_dir
        cmd_opts = r'rf2500 "exit"' 
        command_line = '"%s" %s' % (cmd,cmd_opts)
        op = runcmd( command_line )
        if re.search('usbutil: unable to find a device matching 0451:f432',op):
            print '*** ERROR *** Launchpad not connected, or driver not installed (click Install or run mpy_driver_install.exe)'
            connection_status = '_Launchpad_Not_Found'  # red
            color = 'red'
        elif re.search('Device ID: (\S+)',op):
            print '(mspdebug passed)   ' , 
            wds =  re.findall('Device ID: (\S+)', op)
            device_id = wds[-1]
            if device_id in chip_id_dict:  
                chip_id = chip_id_dict[ device_id ]
                print  ' found chip ', chip_id 
                connection_status = 'Chip_Recognized'  # green
                color = 'green'
            else:
                print  ' Device ID:', device_id, chip_id 
                connection_status = '_Chip_Not_Recognized'  # yellow
                color = 'yellow'
        elif re.search('Could not find device',op):
            print '*** ERROR *** MSP430 chip could not be found, make sure msp430 is plugged into socket and that it is the correct way round\n' 
            connection_status = '_Launchpad_Chip_Not_Found'   # yellow
            color = 'yellow'
        elif re.search("can't claim interface: The requested resource is in use", op):
            print '*** ERROR *** mspdebug is already running, close the other program\n' 
            connection_status = '_mspdebug_in_use'   # yellow
            color = 'red'
        else:
            print 'error !!\n'
            print op
            connection_status = '_Unknown_Error'  # red
            color = 'red'
        
        
        if connection_status[0] == '_':
            chip_id = connection_status 


#        parent.mspDebugLock.release()
        
        return chip_id, connection_status, color
    

#-----------------------------------------------------------------------------#
def GetLangIdFromMW(mainw):
    """Get the language id of the file in the current buffer
    in Editra's MainWindow.
    @param mainw: mainwindow instance

    """
    ctrl = GetTextBuffer(mainw)
    if hasattr(ctrl, 'GetLangId'):
        return ctrl.GetLangId()

def GetTextBuffer(mainw):
    """Get the current text buffer of the current window"""
    nb = mainw.GetNotebook()
    return nb.GetCurrentCtrl()
