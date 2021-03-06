# -*- coding: utf-8 -*-
###############################################################################
# Name: __init__.py                                                           #
# Purpose: Mpy Plugin                                                      #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################
# Plugin Metadat
"""Run the script in the current buffer"""

__author__ = "Cody Precord"
__svnid__ = "$Id: __init__.py 67746 2011-05-14 16:52:56Z CJP $"
__revision__ = "$Revision: 67746 $"

#-----------------------------------------------------------------------------#
# Imports
import wx

# Local modules
import mpy
import cfgdlg

# Editra imports
import ed_glob
import iface
import plugin
import ed_msg
import profiler
import util
import syntax.synglob as synglob
from ed_menu import EdMenuBar

#-----------------------------------------------------------------------------#
# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#
# Interface Implementation
class Mpy(plugin.Plugin):
    """Script Launcher and output viewer"""
    plugin.Implements(iface.ShelfI)
    ID_MPY = wx.NewId()
    INSTALLED = False
    SHELF = None

    __name__ = u'Mpy'

    def AllowMultiple(self):
        """Mpy allows one instance only"""
        return False

    def CreateItem(self, parent):
        """Create a Mpy panel"""
        util.Log("[Mpy][info] Creating Mpy instance for Shelf")
#        win = mpy.LaunchWindow(parent)
        win = mpy.MpyWindow(parent)
        return win

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_BIN_FILE), wx.ART_MENU)
        return bmp

    def GetId(self):
        """The unique identifier of this plugin"""
        return Mpy.ID_MPY

    def GetMenuEntry(self, menu):
        """This plugins menu entry"""
        item = wx.MenuItem(menu, Mpy.ID_MPY, Mpy.__name__, 
                           _("Run script from current buffer"))
        item.SetBitmap(self.GetBitmap())
        return item

    def GetMinVersion(self):
        return "0.6.27"

    def GetName(self):
        """The name of this plugin"""
        return Mpy.__name__

    def InstallComponents(self, mainw):
        """Install extra menu components
        param mainw: MainWindow Instance

        """
        # Delete obsolete configuration from older versions
        profiler.Profile_Del('Mpy.Prefs') # New config is Mpy.Config2
#        tmenu = mainw.GetMenuBar().GetMenuByName("tools")
#         tmenu.Insert(0, ed_glob.ID_RUN_LAUNCH, _("Run") + \
#                      EdMenuBar.keybinder.GetBinding(ed_glob.ID_RUN_LAUNCH),
#                      _("Run the file associated with the current buffer in Mpy"))
#         mainw.AddMenuHandler(ed_glob.ID_RUN_LAUNCH, OnRequestHandler)
#         mainw.AddUIHandler(ed_glob.ID_RUN_LAUNCH, OnUpdateMenu)
#         tmenu.Insert(1, ed_glob.ID_LAUNCH_LAST, _("Run last executed") + \
#                      EdMenuBar.keybinder.GetBinding(ed_glob.ID_LAUNCH_LAST),
#                      _("Re-run the last run program"))
#         mainw.AddMenuHandler(ed_glob.ID_LAUNCH_LAST, OnLaunchLast)
#         mainw.AddUIHandler(ed_glob.ID_LAUNCH_LAST, OnUpdateMenu)
#         tmenu.Insert(2, wx.ID_SEPARATOR)

    def IsInstalled(self):
        """Check whether Mpy has been installed yet or not
        @note: overridden from Plugin
        @return bool

        """
        return Mpy.INSTALLED

    def IsStockable(self):
        return True

#-----------------------------------------------------------------------------#

def GetConfigObject():
    return LaunchConfigObject()

class LaunchConfigObject(plugin.PluginConfigObject):
    """Plugin configuration object. Plugins that wish to provide a
    configuration panel should implement a subclass of this object
    in their __init__ module.

    """
    def GetConfigPanel(self, parent):
        """Get the configuration panel for this plugin
        @param parent: parent window for the panel
        @return: wxPanel

        """
        return cfgdlg.ConfigNotebook(parent)

    def GetLabel(self):
        """Get the label for this config panel
        @return string

        """
        return _("Mpy")

#-----------------------------------------------------------------------------#

def OnRequestHandler(evt):
    """Handle the Run Script menu event and dispatch it to the currently
    active Launch panel

    """
    ed_msg.PostMessage(mpy.MSG_RUN_LAUNCH)

def OnLaunchLast(evt):
    """Handle the Run Last Script menu event and dispatch it to the currently
    active Launch panel

    """
    ed_msg.PostMessage(mpy.MSG_RUN_LAST)

def OnUpdateMenu(evt):
    """Update the Run Mpy menu item
    @param evt: UpdateUI

    """
    e_id = evt.GetId()
    if e_id == ed_glob.ID_RUN_LAUNCH:
        evt.Enable(ed_msg.RequestResult(mpy.REQUEST_ACTIVE))
    elif e_id == ed_glob.ID_LAUNCH_LAST:
        evt.Enable(ed_msg.RequestResult(mpy.REQUEST_RELAUNCH))
    else:
        evt.Skip()
