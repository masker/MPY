# -*- coding: utf-8 -*-
###############################################################################
# Name: launch.py                                                             #
# Purpose: Launch Ui                                                          #
# Author: Cody Precord <cprecord@editra.org>                                  #
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
        self._worker = None
        self._busy = False
        self._isready = False
        self._state = dict(file='', lang=0, cfile='', clang=0, last='', 
                           lastlang=0, prelang=0, largs='', lcmd='')

#         self.python_exe  = r'C:\Python27\python.exe'
#         self.mpy_dir     = r'C:\MPY'

        self.python_exe   = r'C:\Python%s%s\python.exe' % ( sys.version_info.major, sys.version_info.minor )
        tstr = sys.modules[__name__].__file__
        idx = tstr.index(  r'\mpy_editor\mpy' )
        self.mpy_dir = tstr[:idx]


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
        # but only start it if it is not already running 
        
#         self.run_uart_comport = run_uart_comport.run_uart_comport(self, \
#             device_id=r'USB\VID_0451&PID_F432&MI_00',  
#             run_in_separate_thread=True)

#        self.StartStopProg(run_during_startup=True)




    #---- Properties ----#
    Locked = property(lambda self: self._lockFile.IsChecked())
    MainWindow = property(lambda self: self._mw)
    Preferences = property(lambda self: Profile_Get(handlers.CONFIG_KEY, default=None),
                           lambda self, prefs: Profile_Set(handlers.CONFIG_KEY, prefs))
    State = property(lambda self: self._state)





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
#        ctrlbar.SetBackgroundColour(wx.Colour(204, 50, 50))
#        ctrlbar.SetForegroundColour(wx.Colour(204, 50, 50))
        
        # Preferences
        self._pbtn = self.AddPlateButton(u"", ed_glob.ID_PREF)
        self._pbtn.SetToolTipString(_("Settings"))


        # Script Label
        ctrlbar.AddControl((5, 5), wx.ALIGN_LEFT)
        self._lockFile = wx.CheckBox(ctrlbar, wx.ID_ANY)
        self._lockFile.SetToolTipString(_("Lock File"))
        ctrlbar.AddControl(self._lockFile, wx.ALIGN_LEFT)
        self._chFiles = wx.Choice(ctrlbar, wx.ID_ANY)#, choices=[''])
        ctrlbar.AddControl(self._chFiles, wx.ALIGN_LEFT)


        # Button
        self._prog = self.AddPlateButton(_("   Prog    "), ID_PROG,   wx.ALIGN_LEFT)
        self._prog.SetToolTipString(_("Compiles the file (mpy2c, mspgcc)\nDownloads the program to the Launchpad\nPrograms the Microcontroller\nthen it will Run (mspdebug)"))
        # Button
        self._run   = self.AddPlateButton(_("  Run/Stop  "),   ed_glob.ID_BIN_FILE, wx.ALIGN_LEFT)
        self._run.SetToolTipString(_("Run or Stop the Microcontroller"))
        # Button
        self._drvinst = self.AddPlateButton(_("  Install  "), ID_DRVINST,   wx.ALIGN_LEFT)
        self._drvinst.SetToolTipString(_("Install Launchpad Drivers"))
        
        # Spacer
        ctrlbar.AddStretchSpacer()
        
        # Button
        self._clear = self.AddPlateButton(_("Clear"), ed_glob.ID_DELETE,   wx.ALIGN_RIGHT)
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
        if e_obj == self._pbtn:
            app = wx.GetApp()
            win = app.GetWindowInstance(cfgdlg.ConfigDialog)
            if win is None:
                config = cfgdlg.ConfigDialog(self.MainWindow)
                config.CentreOnParent()
                config.Show()
            else:
                win.Raise()
        elif e_obj is self._run:
            # May be run or abort depending on current state
            self.StartStopProcess()
        elif e_obj is self._prog:
            # May be run or abort depending on current state
            self.StartStopProg()
        elif e_obj is self._drvinst:
            # May be run or abort depending on current state
            self.RunDrvInstScript()
        elif e_obj == self._clear:
            self._buffer.Clear()
        else:
            evt.Skip()

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
        if e_obj is self._lockFile:
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
                         self._chFiles, self._lockFile):
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
                         self._chFiles, self._lockFile):
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
        util.Log("[mpy][RunDrvInstScript] Starting Script %s" % cmd)
        self.State['lcmd'] = cmd
        args = ''
        self.State['largs'] = args
        self._buffer.AppendUpdate( '[mpy] dir=%s cmd=%s\n' % (os.getcwd(), cmd) )
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
            
            mpy_dir = r'C:\MPY'
            cmd = r'%s -u "%s\mpy_editor\mpy\prog.py"' % ( self.python_exe, self.mpy_dir)


 
            
            self.State['lcmd'] = cmd
#            cmd = handler.GetCommand(cmd)

#            args = self.FindWindowById(ID_ARGS).GetValue().split()
            args = ''
            self.State['largs'] = args
#            self.Run(self.State['file'], cmd, args, self.State['lang'])

            
#            self.Run(self.State['file'], cmd, args, self.State['lang'])
            
           
            self._buffer.AppendUpdate( '[mpy] dir=%s cmd=%s\n' % (os.getcwd(), cmd) )
            # Must give it a python type file for some reason!
            self.Run(self.State['file'], cmd, args, 32161)   


        elif self._worker:
            util.Log("[mpy][info] Aborting process")
            self._worker.Abort()
            self._worker = None

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
            self._run.SetBitmap(abort)
            self._run.SetLabel(_("  Run/Stop  "))
        else:
            rbmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_BIN_FILE), wx.ART_MENU)
            if rbmp.IsNull() or not rbmp.IsOk():
                rbmp = None
            self._run.SetBitmap(rbmp)
            self._run.SetLabel(_("  Run/Stop  "))
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
