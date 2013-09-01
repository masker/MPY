###########################################################################
#  
#     This file is part of mpyEditor.
# 
#     mpyEditor is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     mpyEditor is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with mpyEditor.  If not, see <http://www.gnu.org/licenses/>.
#
#     (C) Copyright 2013 Mike Asker    mike.asker@gmail.com
#
###########################################################################
#
#   find_launchpad.py
#   
#   This python script is used to make detect whether a Launchpad board is connected or not.
#   It runs the python scan_ports module to list all the COM port devices available on the PC
#   It returns the object with attribute   <obj>.comport_name for the first launchpad device found
#   If no active launchpad device is found comport_name is None
# 
############################################################################

import subprocess
import sys
import os
import shlex
import time
import shutil
import serial
import re
import threading
import traceback
import wx

import scan_ports

##################################################################################
class find_launchpad( object ):


    def __init__( self, parent_window, device_id=r'USB\VID_0451&PID_F432&MI_00'):
        '''finds a comport which is connected to device_id and echoes 
        the recieved characters to the parent window''' 
        
        
        self.parent_window = parent_window
        self.device_id     = device_id
        self.lp_nc_message_done = False


#         if self.parent_window != None:        
#             self.parent_window._buffer.AppendUpdate('[find_launchpad] started\n')
        
        # Before we try to open up the port make sure it is not
        # already running. If it is the go ahead and close it
        # and we will reopen it.
                

        comport_name = self.find_comport(device_id)
        
        self.comport_name = comport_name
        


    #-----------------------------------------------------------------------------------------
    def find_comport(self, device_id):

        # scan for active ports in the registry
        all_ports=scan_ports.comscan()
        
        
        # Report the ports that have a hardwareinstance (HWID) that matches the device_id
        wx.CallAfter( self.pr, ('\n') )
        for p in all_ports:
            if 'name'             in p and   \
               'hardwareinstance' in p and   \
               'active'           in p and   \
               'available'        in p and   \
               'class'            in p :
              if device_id in p['hardwareinstance']:
                    txt = '%8s active=%s avail=%s class=%s HWID=%30s\n' % (p['name'], p['active'], p['available'], p['class'], p['hardwareinstance'])
                    wx.CallAfter( self.pr, (txt) )     
                    if p['active'] == True:
                        self.lp_nc_message_done = False
                        self.pr(p)
                        return p['name']
#         if self.lp_nc_message_done == False:
#              print '* No active Launchpad found, either it is not connected, or the comport driver is not installed *'
#              self.lp_nc_message_done = True
        return None
        
    #--------------------------------------------------------------------------------    
    def pr( self, txt ):  

        if 0 and not self.parent_window.uartStopped:
            if self.parent_window != None:
                self.parent_window._buffer.AppendUpdate('%s' % txt)
                self.parent_window._buffer.FlushBuffer()
            else:
                print txt,

        

          
          
        
    
########################################################################
########################################################################

if __name__ == '__main__':
    
    
    while 1:
    
       ruc = find_launchpad(None)

       print ruc.comport_name
       time.sleep(1)
    
