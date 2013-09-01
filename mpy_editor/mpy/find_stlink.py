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
#   find_stlink.py
#   
#   This python script is used to detect whether a ST board is connected using 
#   the STLINK/V2 usb interface and which micro chip.
#   It repeatedly runs 'openocd' command for every STM32 device for which there
#   is a config file that matches STM32*.cfg. Once found it returns config file
#   and the cpu name found. If the optional config_guess parameter is given it
#   will try this file first, to save time. If nothing is found then it returns
#   None.
#   This module requires that openocd is installed (version 0.7.0 and above)
#   and the STLINK/V2 driver.  
#   The STM onboard STLINK firmware should be upgraded. 
# 
############################################################################

import subprocess
import sys
import os
import shlex
import time
import shutil
#import serial
import re
#import threading
#import traceback
#import wx
import glob
import util

#import scan_ports


#--------------------------------------------------------
def runcmd( command_line, read_output=True, log=False ):
        '''Runs the command_line as a subprocess.
        @param  command_line    Command line as a string
        @param  read_output     If True will read the cmd output *Blocks* if 
                                False will return straight away without output
        @param  log             If True will print out the cmd and the output
        @return op              If readoutput==True returns Output of the cmd
                                else returns None
        @return proc            If read_output=False returns the process so that
                                it can be accessed later. (proc may be None
                                if the process has already completed.
        '''


        args = shlex.split(command_line)
        if log:   print 'command_line=', args
        
        # options to prevent console window from openning
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        proc = subprocess.Popen( args , stdout=subprocess.PIPE,stderr=subprocess.STDOUT, startupinfo=startupinfo)
#         while True:
#             data = proc.stdout.read(1)
#             if len(data) == 0:
#                 break
#             output += data
#        
        output = ''
        if read_output == True:
            output = proc.communicate()[0] 
        # remove any double linefeeds
        output = re.sub('\r', '', output)
        if log:   print 'x=', output
        return output, proc 

#------------------------------------------------------------------------



################################################################################
class find_stlink( object ):


    def __init__( self, 
                  parent_window, 
                  config_pattern=None,
                  config_file_guess=None,
                  openocd_exe=None,
                  previous_micro=None,
                 ):
        '''Finds a connected STM STLINK/V2 board, and starts an openocd session. 
        @param  parent_window   window object to send output 
        @param  config_pattern  Glob pattern to match config files (if it 
                                contains '\' dir charaters then prefix the 
                               pattern with the openocd board/scripts directory)
        @param  config_file_guess   Name of config file to try first, which is
                                probably the name of the previously found board
        @param  openocd_exe     Full pathname for the openocd exe
        @param  previous_micro id of a previous object, this is required for 
                                the openocd session which is already running
        ''' 

        if previous_micro == None:
            proc = None
        else:
            proc = previous_micro.openocd_popen
        util.Log("[mpy][info](find_stlink)  %s  %s" % (previous_micro,proc ) )
        
        
        
        # If the previous session is still running don't do anything, but
        # return with all the previous data
        if previous_micro and previous_micro.openocd_popen:
            util.Log("[mpy][info](find_stlink) using previous process 1 %s" % (previous_micro.openocd_popen) )
            if not previous_micro.openocd_popen.poll():
                self.parent_window = previous_micro.parent_window
                self.stlink_device = previous_micro.stlink_device
                self.config_file = previous_micro.config_file
                self.openocd_exe = previous_micro.openocd_exe
                self.openocd_popen = previous_micro.openocd_popen
                util.Log("[mpy][info](find_stlink) using previous process 2 %s" % (previous_micro.openocd_popen) )
                return
             
        
        self.parent_window = parent_window
        self.stlink_device     = None
        self.config_file = None
        self.openocd_exe = openocd_exe
        self.openocd_popen = None
        
        self.openocd_dir  = r'C:\openocd-0.7.0\openocd-0.7.0'
        scripts_dir        = os.path.join( self.openocd_dir, 'scripts' )
        config_dir        = os.path.join( scripts_dir, 'board' )
        config_fullpath_pattern = os.path.join(config_dir, config_pattern)

        # if the config_file_guess is not a fullpath then prepend with the config_dir
        if not (re.search(r'\\.', config_file_guess) or 
                re.search(r'\/.', config_file_guess)):
              config_file_guess = os.path.join(config_dir, config_file_guess)
        
        # If we are given a config file as a guess try it first. It is likely 
        # that the guess is the result of the previous successful connection
        if config_file_guess != None:
            self.config_file, self.stlink_device = self.find_openocd_config(config_file_guess)    
        
        # if the guess doesn't work look through all the config files that match
        
        config_dir = os.path.join( self.openocd_dir, config_pattern )
        if not self.config_file:
            # Find all the stm config files in the 
            
            for cfg in glob.glob(config_fullpath_pattern ):
                self.config_file, self.stlink_device = self.find_openocd_config(cfg)    
                if self.config_file:
                    break
                    
        if self.config_file:           
            util.Log("[mpy][info](find_stlink)    config found")
            time.sleep(0.5)
            self.openocd_popen = self.start_openocd_session(self.config_file)
            util.Log("[mpy][info](find_stlink)            self.openocd_popen= %s" % (self.openocd_popen) )

        
        


    #-----------------------------------------------------------------------------------------
    def find_openocd_config(self, config):
    
    
        cmd = self.openocd_exe
        cmd_opts = r'-f "%s" -c "shutdown"' % config 
#        cmd_opts = r'-f "%s"' % config 
        command_line = '"%s" %s' % (cmd,cmd_opts)
        (op,p) = runcmd( command_line )
        
        
        
        # return None if any error, this can't be the correct config for the connected board
        if re.search('error', op, re.I):
            return None, None
        else:
            # check for 'info' and 'breakpoint'
            flds = re.findall( 'Info : (\S+): hardware has \d+ breakpoint', op)
            if len(flds) == 1:
                return config, flds[0]
          
                
      
        return None, None


    #-----------------------------------------------------------------------------------------
    def start_openocd_session(self, config):
        '''Starts an openocd session.
        @param  config           openocd configuration full filename path
        @return proc             process id for the session
        This function will try to start an openocd session using the config
        file provided. No output from openocd is returned from this command,
        this is because the command has to be non-blocking
        '''
        
        cmd = self.openocd_exe
        cmd_opts = r'-f "%s"' % config 
        command_line = '"%s" %s' % (cmd,cmd_opts)
        (op,proc) = runcmd( command_line, read_output=False )
        
        
        return proc
        
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
    
    
    
       stlink = find_stlink(None,
                  config_pattern=r'stm*discovery.cfg',
                  config_file_guess='stm32ldiscovery.cfg',
                  openocd_exe=r'C:\openocd-0.7.0\openocd-0.7.0\bin-x64\openocd-x64-0.7.0.exe',
                  openocd_popen=None)

       print 'done', stlink.config_file, stlink.stlink_device, stlink.openocd_popen
    
