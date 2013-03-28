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
#     along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#
#     (C) Copyright 2013 Mike Asker    mike.asker@gmail.com
#
###########################################################################
#
#   run_uart_comport.py  
#   
#   This python script is used to make a windows COM port connection to the a Launchpad board.
#   It runs the python scan_ports module to determine what Launchpad device (if any)
#   is attached and which COM port number is is assigned.
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

import scan_ports

##################################################################################
class FindComport( object ):


    def __init__( self, parent_window, device_id=None, run_in_separate_thread=False ):
        '''opens a comport which is connected to device_id and echoes 
        the recieved characters to the parent window''' 
        
        
        self.parent_window = parent_window
        self.device_id     = device_id
        self.lp_nc_message_done = False


        if self.parent_window != None:        
            self.parent_window._buffer.AppendUpdate('[FindComport] started\n')
        
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
        for p in all_ports:
            if 'name'             in p and   \
               'hardwareinstance' in p and   \
               'active'           in p and   \
               'available'        in p and   \
               'class'            in p :
              if device_id in p['hardwareinstance']:
#                    print '%8s active=%s avail=%s class=%s HWID=%30s' % (p['name'], p['active'], p['available'], p['class'], p['hardwareinstance'])
                    if p['active'] == True:
                        self.lp_nc_message_done = False
                        return p['name']
    
#         if self.lp_nc_message_done == False:
#              print '* No active Launchpad found, either it is not connected, or the comport driver is not installed *'
#              self.lp_nc_message_done = True
        return None
        
    #--------------------------------------------------------------------------------    
    def pr( self, txt ):  

        if self.parent_window != None:
            self.parent_window._buffer.AppendUpdate('%s' % txt)
        else:
            print txt,

        

          
          
        
    
########################################################################
########################################################################

if __name__ == '__main__':
    
    
    while 1:
    
       ruc = FindComport(None, 
          device_id=r'USB\VID_0451&PID_F432&MI_00', 
          run_in_separate_thread=False )

       print ruc.comport_name
       time.sleep(1)
    
