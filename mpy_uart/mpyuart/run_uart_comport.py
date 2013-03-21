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
class run_uart_comport( object ):


    def __init__( self, parent_window, device_id=None, run_in_separate_thread=False ):
        '''opens a comport which is connected to device_id and echoes 
        the recieved characters to the parent window''' 
        
        
        self.parent_window = parent_window
        self.device_id     = device_id

        if self.parent_window != None:        
            self.parent_window._buffer.AppendUpdate('[run_uart_comport] started\n')
        
        # Before we try to open up the port make sure it is not
        # already running. If it is the go ahead and close it
        # and we will reopen it.
                
             
        self.close_comport()
            
        if self.comport_state == 'closed':            
            if run_in_separate_thread == True:
                # Open the port in a separate thread so as not to hog the current process
                self.comport_thread = threading.Thread(target=self.start_comport, args=())
                self.comport_thread.start()
            else:
                self.start_comport()
    


    #-------------------------------------------------------------------------------------    
    def close_comport(self):
        try:
            try:
                if self.comport != None:
                    self.comport.close()
                    self.comport_state = 'closed'
            except AttributeError:   # when the port has not been openned yet
                pass
            except:  # every other error print out the traceback      
                traceback.print_exc(file=sys.stdout)
        finally:
            self.comport_state = 'closed'
        
        
        
    #-------------------------------------------------------------------------------------    
    def start_comport(self):
        ''' Open a com port using the pySerial. And enter an infinite loop of listening
        to the comport and echoing the received characters out to the parent_window buffer'''

        if self.parent_window != None:        
            self.parent_window._buffer.AppendUpdate('[run_uart_comport] START_COMPORT\n')

#        print '(run_uart_comport) start_comport()'
        
        while 1:
            (self.comport, self.comport_name) = self.open_comport(self.device_id)
        
            if self.comport != None:
                self.run_comport_loop(self.comport, self.device_id, self.comport_name )
        
            time.sleep(3)
        
        
    #---------------------------------------------------------------------------------    
    def open_comport(self, device_id, log=False):
        '''Tries to open the comport on the device_id
        It uses the scan_ports module (called within find_ports) to determine the COM port number assigned.
        If the device is not found attached then it will exit.
        returns
            comport handle - if it succeeded in openning the port
            None - If it could not open it for any reason (eg not plugged in)
        '''



        if log: print '\n&&& [run_uart_comport.open_comport]  Looking for comport to OPEN'
        comport_name = self.find_comport(device_id)
        serial_port = None
        if comport_name != None:        
            done = False
            open_attempts_count = 0
            if log: print '&&&  (run_uart_comport.open_comport)           attempting to open port ', comport_name
            try:
                serial_port = serial.Serial( comport_name, 9600, timeout=1 )   
                done = True
                if log: print '&&&  (run_uart_comport.open_comport)               succeeded in openning port ', comport_name

            except:
                print '*** ERROR *** could not open port %s, may be another MPY Editor is using it' % comport_name
                    
        if log: print '&&&  (run_uart_comport.open_comport) finished', comport_name
        
        if serial_port == None:
            comport_name = 'Not_Available'
            
        return serial_port, comport_name


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
                        return p['name']
        else:
            print '* No active Launchpad found, either it is not connected, or the comport driver is not installed *'
            return None
        
    #--------------------------------------------------------------------------------    
    def pr( self, txt ):  

        if self.parent_window != None:
            self.parent_window._buffer.AppendUpdate('%s' % txt)
        else:
            print txt,

        
    #--------------------------------------------------------------------------------    
    def run_comport_loop(self, serial_port, device_id, comport_name):
        '''An infinite loop where the data that is received on the serial_port
        is read a line at a time and the output to the parent_window 
         
        This loop will run so long as the com port is running,
        if it finds that com port driver is not running then the 
        loop will stop and it will return'''

        self.pr( '''
####################################################
###   UART OUTPUT  STARTED ON PORT %s          ### 
####################################################\n''' % comport_name )
           
            
        i = 0
        try:    # Any errors reading the comport will cause the comport to close and return to have another go at opening it
            while(1):
            
                # Read a line of data from the comport (a line which ends with a cariage return \n)
                line = serial_port.readline()
                if line != '': 
                   self.pr( line )
                   i = 1
                else:
                   i = (i + 1) % 3
                time.sleep(0.05)  # wait 1/20 sec before looking again (frees up the cpu)
                
                # After the comport is quite for three seconds check if the comport is still active 

                if i==0 and  self.find_comport(device_id) != comport_name:
                     print '(run_comport_loop) comport %s NOT FOUND  closing the port' % comport_name
                     break
                
        except:
            pass

        self.close_comport()
#        serial_port.close()

        self.pr( '''
####################################################
###   UART OUTPUT  STOPPED  ON COM PORT %s    ### 
####################################################\n''' % comport_name )

          
          
        
    
########################################################################
########################################################################

if __name__ == '__main__':
    
    run_uart_comport = run_uart_comport(None, 
       device_id=r'USB\VID_0451&PID_F432&MI_00', 
       run_in_separate_thread=False )


