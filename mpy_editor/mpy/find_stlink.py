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
import telnetlib

try:
   import util
except ImportError:
   pass
   
#import scan_ports


MPY_STATUS_FLAG_ADDR  = 0x2000000


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

        if read_output==True:
            op    = subprocess.PIPE
            operr = subprocess.STDOUT
        else:
            fh = open("NUL","w")
            op = fh
            operr = fh

        proc = subprocess.Popen( args , stdout=op,stderr=operr, startupinfo=startupinfo)
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
        if log:   print '<runcmd op>=', output
        return output, proc 

#------------------------------------------------------------------------



################################################################################
class find_stlink( object ):


    def __init__( self, 
                  config_pattern=None,
                  config_file_guess=None,
                  openocd_exe=None, ):
        '''Finds a connected STM STLINK/V2 board, and starts an openocd session. 
        @param  parent_window   window object to send output 
        @param  config_pattern  Glob pattern to match config files (if it 
                                contains '\' dir charaters then prefix the 
                               pattern with the openocd board/scripts directory)
        @param  config_file_guess   Name of config file to try first, which is
                                probably the name of the previously found board
        @param  openocd_exe     Full pathname for the openocd exe
        '''

        self.stlink_device  = None
        self.config_file    = None
        self.openocd_exe    = openocd_exe
        self.openocd_popen  = None
        self.telnet_session = None
        self.comport_name   = None


        # If this is called without the openocd_exe value then we cannot start
        # start the openocd session, assume that it is already running
        # (this is the case when we flash the part from the prog_stm script)
        if openocd_exe != None:
            self.openocd_dir    = r'C:\openocd-0.7.0\openocd-0.7.0'
            scripts_dir         = os.path.join( self.openocd_dir, 'scripts' )
            config_dir          = os.path.join( scripts_dir, 'board' )


            # if the config_file_guess is not a fullpath then prepend with the config_dir
            if not (re.search(r'\\.', config_file_guess) or
                    re.search(r'\/.', config_file_guess)):
                  config_file_guess = os.path.join(config_dir, config_file_guess)


            # Forcefully kill any previously running openocd process (windows only)
            runcmd( 'taskkill /f /im "openocd*"' )

            self.find_config_top( config_dir, config_pattern, config_file_guess)

            if self.config_file:
                pr("found stlink config %s" % self.config_file)
                self.openocd_popen  = self.start_openocd_session(self.config_file)
#                self.telnet_session = self.start_telnet_session()


        
    #---------------------------------------------------------------------------
    def find_config_top(self, config_dir, config_pattern, config_file_guess):


        # If we are given a config file as a guess try it first. It is likely
        # that the guess is the result of the previous successful connection
        if config_file_guess != None:
            self.config_file, self.stlink_device = self.find_openocd_config(config_file_guess)

        # if the guess doesn't work look through all the config files that match

        if not self.config_file:
            # Find all the stm config files in the
            config_fullpath_pattern = os.path.join(config_dir, config_pattern)

            for cfg in glob.glob(config_fullpath_pattern ):
                self.config_file, self.stlink_device = self.find_openocd_config(cfg)
                if self.config_file:
                    break

    #---------------------------------------------------------------------------
    def get_mpy_data(self, input=None):
        '''Return data from the STLINK connection using the mpy_data_buffer and
        mpy_data_flag.
        This is a higher level function. If the stlink terminal connection is
        not running then start it up now. If the terminal connection is not
        responding then the board is likely not connected anymore so kill the
        openocd_popen process.
        '''

        opstr = ''
        # The openocd session must be running first to do anything
        if self.openocd_popen:

            if self.telnet_session:
                 # Send command to probe whether it is still alive
                 mpy_flag = self.get_mpy_flag_status()
                 if mpy_flag > 0:
                     opstr = self.read_mpy_buffer(mpy_flag)
                 if mpy_flag == 0:
                     opstr = ' get_mpy_data=0\n'
                 if mpy_flag == None:
                     self.close_telnet_session()
                     self.kill_openocd_session()
            else:
                 pr('(get_mpy_data) openocd running but telnet is not running')
                 self.kill_openocd_session()

        return opstr

    #-----------------------------------------------------------------------------------------
    def get_mpy_flag_status(self):
        '''Reads the mpy status flag on the microcontroller, and returns status
        @return status: 1 = data available in the mpy_data_buffer
                        0 = no new data avaliable
                        None = Connection lost
        '''


        # Read the flag up to 10 times to ensure that we get a good
        # read (in case of bad communication)
        byte = self.read_mem(MPY_STATUS_FLAG_ADDR, 1)


        if byte != None:
            byte = byte[0]

        return byte

    #---------------------------------------------------------------------------
    def read_mem(self, address, count):
        '''Reads count memory bytes (8bit) locations starting at address
        Returns None if the read was not able to be done (closed session)
        '''

        cmd =   'mdb 0x%0x %s' % (MPY_STATUS_FLAG_ADDR, count)
        optxt = self.send_telnet_command( cmd )

        mem_list = None
        if optxt != None:

            flds = optxt.split()
            for wd in flds:
                wd = wd.strip()
                if len(wd) == 2:
                    try:
                        num = int(wd,16)
                    except ValueError:
                        mem_list = None
                        break
                    if mem_list == None:
                        mem_list = [num]
                    else:
                        mem_list.append(num)

        if mem_list == None:
            pr('(read_mem) *Error* no data read for command "%s"' % cmd)
            pr('(read_mem) optxt= "%s"' % optxt)

        if mem_list and len(mem_list) != count:
            pr('(read_mem) *Error* read different read %d bytes expected %d' \
                % ( len(flds), count ) )
            mem_list = None


        return mem_list

    #---------------------------------------------------------------------------
    def flash_program(self, flash_prog):
        '''Function that flashes a program onto the microcontroller'''

        op = '(flash_program) not run'

        # Don't try to program the part if we can't find the flash file
        if not os.access( flash_prog, os.R_OK):
             pr( "(flash_prog) Cannot flash program, file not found '%s'" \
                 % flash_prog )

        else: # We have found the flash_file

            op = ''

            # Change the directory seperators char from \ to / to be
            # compatible with openocd
            flash_prog = re.sub(r'\\', '/', flash_prog)
            sector = 0   # only program the first sector (May need to update <<)

            # Create a list of commands to perform the flash
            commands_str = r'''
            reset halt
            poll
            flash probe 0
            flash protect 0 0 %s off
            flash erase_sector 0 0 %s
            flash write_image "%s"
            flash protect 0 0 %s on
            soft_reset_halt
            ''' % (sector, sector, flash_prog, sector)

            # Break the commands_str into a list of separate commands and
            # and feed them one by one into the openocd telnet connection
            commands = commands_str.split('\n')
            op = ''
            for cmd in commands:
                cmd = cmd.strip()
                if len(cmd) > 0:
                    pr( cmd )
                    op += self.send_telnet_command(cmd)

        return op

    #---------------------------------------------------------------------------
    def send_telnet_command(self, cmd):
        '''Sends a command to the telnet session and waits for a response
        @param cmd: command line to be sent, (no \n need, added in this func)
        @return resp: String containing the response
        '''

        if cmd[-1] != '\n':
            cmd += '\n'

        try:
            self.telnet_session.write(cmd)
            op = self.telnet_session.read_until( '>', 1 )
        except EOFError:
            op = None
        except AttributeError:
            op = None

        # Remove the trailing space characters and the '>'
        op = re.sub(r'\S*>\S*$', '', op)
        return op

    #-----------------------------------------------------------------------------------------
    def read_mpy_buffer(self, input=None, string=True):
        '''Reads the mpy data in the mpy_data_buffer
        @param string:  True returns data as a null terminated ascii string
                        False returns the data as a list of numbers
        @return data:   returns string or data depending on the string param
        '''




#         if input not in [None,'']:
#             input +=  '\n'
#             pr('writing %s' % input )
#             self.telnet_session.write(input)
#             pr('wrote %s' % input )

        op = 'reading mpy buffer  <%s>\n' % input

        return op


    #-----------------------------------------------------------------------------------------
    def kill_openocd_session(self):
        '''Tries to kill an openocd process'''

        pr( '(kill_openocd_session) trying to kill openocd' )
        if self.openocd_popen and not self.openocd_popen.poll():
            self.openocd_popen.kill()
            self.openocd_popen = None
            pr( '(kill_openocd_session) killed openocd' )

    #-----------------------------------------------------------------------------------------
    def close_telnet_session(self):
        '''Tries to kill the running telnet session'''

        if self.telnet_session:
            self.send_telnet_command('exit')
            pr('closing telnet session: %s' % self.telnet_session)
            self.telnet_session.close()
            self.telnet_session = None



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


   #-----------------------------------------------------------------------------------------
    def start_telnet_session(self):
        '''Starts a telnet session communicating with the openocd process
        The port is localhost port 4444
        '''

        HOST = 'localhost'
        PORT = 4444
        telnet = telnetlib.Telnet(HOST,PORT)

        pr('started telnet session: %s' % telnet)
        op = telnet.read_until( '>' )

#         telnet.write('mdb 0x20000000 256\n')
#
#         op = telnet.read_until( '>' )
#        pr( op )

        return telnet

        
#--------------------------------------------------------------------------------    
def pr( txt ):  

    opstr =  '[mpy find_stlink] %s' %  txt
    try:
        util.Log(opstr)
    except:
        print opstr
      
      
        
    
########################################################################
########################################################################

if __name__ == '__main__':
    

       if 1:
           stlink = find_stlink(None,
                      config_pattern=r'stm*discovery.cfg',
                      config_file_guess='stm32ldiscovery.cfg',
                      openocd_exe=r'C:\openocd-0.7.0\openocd-0.7.0\bin-x64\openocd-x64-0.7.0.exe',
                      )

           print 'done', stlink.config_file, stlink.stlink_device, stlink.openocd_popen

#            stlink.telnet_session.set_debuglevel(7)
#            stlink.telnet_session.write( "debug_level 3\r\n")
#            time.sleep(0.01)
#            op = stlink.telnet_session.read_until( '>', 1 )
#            print 'c=%d{%s}' % (-1,op)
           count = 0
           for i in range(40):
               for j in range(40):
#                   stlink.telnet_session.write( "debug_level 0\r\n")
#                   stlink.telnet_session.write( "mdb 0x2000000 1\r\n")
#                   time.sleep(0.01)
#                   op = stlink.telnet_session.read_until( '>', 1 )
#                   print 'c=%d{%s}' % (count,op)
                   print stlink.get_mpy_data() ,
#                    print stlink.read_mem(MPY_STATUS_FLAG_ADDR, 1) ,
                   count += 1
               print ''
           print stlink.send_telnet_command('flash probe 0')
#           stlink.telnet_session.close()
#           time.sleep(30)
#           stlink.kill_openocd_session()