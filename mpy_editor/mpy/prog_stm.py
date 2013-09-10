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
#   prog.py  
#   
#   This python script is used to run the mpy toolchain. 
#   It is intended to be launched within the Editra tool using plugin file 'mpy.py'
#   in a similar way to the Editra 'Launch' plugin.
#   This file is run when the user presses the 'Prog' button on the Editra MPY shelf window.
#   The Editra filename tab which has focus is passed into this file with sys.arg, 
#   as is the chip id (which is auto identified)
#   It preforms the following operations:
#       1) Runs the mpy2c.py preprocessor program that translates the mpy format file into C.
#       2) Runs mspgcc compiler
#       3) Runs mspdebug and flashes the Launchpad MSP430 microcontroller
#
#    If the Editra file is a C file then step 1) is ommitted and the C file is compiled directly.
#    Errors in the users mpy file and errors found with mspgcc are detected and hotspt (red links) in the
#    Mpy window allow the user to click on the link and the corresponding line is highlighted in the source file
#    tab, for both the mpy and C files.
# 
#    If the mspdebug flashing fails it will write a warning to connect a Launchpad board
#    or to install the Launchpad driver
#
############################################################################
  

import subprocess
import sys
import os
import shlex
import time
import re
import find_stlink
from prog_util import *




###########################################################
## main prog starts here ##################################
###########################################################


python_exe   = r'%s\python.exe' % ( sys.exec_prefix )
idx = sys.argv[0].find(  r'\mpy_editor\mpy\prog_stm.py' )
mpy_dir = sys.argv[0][:idx]


armgcc    = r'arm-none-eabi-gcc'
armsize   = r'arm-none-eabi-size'

file_contents = {}
debug = False

# Main Program
if len(sys.argv) > 1:
    file = sys.argv[1]
    file = os.path.abspath(file)
else:
    print 'error: no file specified'

file = r'C:\Development\Workspace\iotogglem0\src\main.c'

fileroot, fileext = os.path.splitext(file)
filedir, filename = os.path.split(fileroot)


if len(sys.argv) > 2:
    chip_id = sys.argv[2]
else:
    chip_id = 'Unknown'


status = 'good'

if chip_id == 'Unknown':
    chip_id = 'msp430g2553'
    print "\n*** warning *** The microcontroller chip is unknown, will use '%s'" % chip_id


# Find the .h file for the chip_id device
hfile = r'%s\%s\msp430\include\%s.h'  % (mpy_dir, armgcc, chip_id.lower())



#######################################################################
#  mpy2c
#######################################################################
if 0 and file != None:
    # If we are compiling from a .mpy file then run the upy2c program
    if fileext == '.mpy':
        print '(mpy2c started)   ...', 
        cmd      = python_exe
        if debug : 
           debug_str = 'Debug'
        else:
           debug_str = ''
           
            
        cmd_opts = '"%s\mpy_editor\mpy\mpy2c.py" "%s" %s "%s" %s' % ( mpy_dir, file, chip_id, hfile, debug_str )
        command_line = '"%s" %s' % (cmd,cmd_opts)
        op = runcmd( command_line )    
        if re.search('Traceback \(most recent call last\):',op):
            print '\n\n  *** (mpy2c FAILED) ***\n'
            print op
            status = 'failed mpy2c'
        elif re.search('mpy2c failed|SyntaxError:',op):
            print '\n\n    *** (mpy2c FAILED) ***\n'
            print op
            status = 'failed mpy2c'
        elif re.search( 'mpy2c completed debug', op):     
            print '\n\n ############################ (mpy2c COMPLETED DEBUG BEGIN) ######################\n'
            print op
            print '\n\n ############################ (mpy2c COMPLETED DEBUG END) ########################\n'

        # if it didn't get to the end print out any output that might be of use
        elif not re.search( 'mpy2c completed', op):
            print '\n\n    *** (mpy2c FAILED) ***\n'
            print op
            status = 'failed mpy2c'

        if status == 'good':
            # get the cpu name    
            oplines = op.split('\n')
            for line in oplines:
                wds = line.split()
                if len(wds) == 2 and wds[0].strip() == '@@MMCU@@:':
                    chip_id = wds[1].strip()      
            print '(mpy2c passed)  wrote: %s.c   using CPU: %s' % (fileroot, chip_id)

            if debug:
                print op


#######################################################################
#  armgcc
#######################################################################
if 1:
    if status == 'good':    
        # Compile the C file using arm-none-eabi-gcc
        print '(ARM compiler started)'
#        macro_def = get_macro_def( chip_id )
        #print macro_def

        src_files = [  filename + '.c',
                       'startup_stm32l1xx_md.s',
                       'stm32l1xx_it.c',
                       'system_stm32l1xx.c',
                       'stm32l1xx_gpio.c',
                       'stm32l1xx_rcc.c',
                     ]
        stmroot = r'C:\Development\STM32L1_Discovery_Firmware_Pack_V1.0.3'
        search_dirs = [ filedir,
                        filedir + r'\..\startup',
                        filedir + r'\..\inc',
                        stmroot + r'\Libraries\STM32L1xx_StdPeriph_Driver',
                        stmroot + r'\Libraries\CMSIS\Device\ST\STM32L1xx',
                        stmroot + r'\Libraries\CMSIS',
                        stmroot + r'\Utilities\STM32L-DISCOVERY',
                      ]
        # The full directory names for the source and include files is
        # constructed using the simroot search_dirs and stmroot
        src_dirs = [ '.', 'src', 'Source', ]
        inc_dirs = [ '.', 'inc', 'Include', ]

        include_str = make_include_str( search_dirs, inc_dirs, ['.h','.hpp'] )

        arm_dir  =  r'C:\Program Files (x86)\GNU Tools ARM Embedded\4.6 2012q4\bin'
        armgcc   = r'arm-none-eabi-gcc.exe'
        cmd_exe  = r'%s\%s' % (arm_dir, armgcc)
        gcc_cmd_options = '''\
 -c -mcpu=cortex-m3 -Os -gdwarf-2 -mthumb -fomit-frame-pointer \
 -Wall -Wstrict-prototypes -fverbose-asm -DSTM32L1XX -DUSE_STDPERIPH_DRIVER \
 -DRUN_FROM_FLASH=1 %s'''     % (include_str)

        asm_cmd_options = '''\
 -x assembler-with-cpp -c -mcpu=cortex-m3 -g -gdwarf-2 -mthumb '''



        clean = 1
        # Clean out all the .o files
        if clean:
            for src in src_files:
                sfile = find_file(src, search_dirs, src_dirs )
                froot, ext = os.path.splitext(sfile)
                o_file = froot + '.o'
                if os.access(o_file, os.W_OK):
                    os.remove(o_file)

        # Compile each of source files, if needed
        optot = ''
        for src in src_files:
            # Locate the src file in the search directories
            # and see if is updated (ie it is more recent than the .o file)
            src_file = get_src_if_more_recent( src, search_dirs, src_dirs )

            if src_file:
                froot, ext = os.path.splitext(src_file)
                o_file = froot + '.o'

                if ext == '.c':
                    command_full = r'"%s" %s "%s" -o "%s"' \
                        % (cmd_exe, gcc_cmd_options, src_file, o_file)
                elif  ext == '.s':
                    command_full = r'"%s" %s "%s" -o "%s"' \
                        % (cmd_exe, asm_cmd_options, src_file, o_file)
                print 'compiling - ',  src_file
                print command_full
                op = runcmd( command_full )
                if re.search(' error:',op)              or \
                   re.search('undefined reference',op)   or \
                   re.search('ld returned 1 exit status',op):
                      print '\n\n    *** (armgcc FAILED) ***\n'
                      print op
                      optot += op
                      status = 'failed armgcc'


        # Link and produce the output elf file
        link_files = ''
        for src in src_files:
            sfile = find_file(src, search_dirs, src_dirs )
            froot, ext = os.path.splitext(sfile)
            o_file = froot + '.o'
            link_files += r' "%s"' % o_file

        link_cmd_options = ''' -mcpu=cortex-m3 -mthumb -nostartfiles \
-Wl,-Map=iotogglem0_rom.map,--cref,--no-warn-mismatch '''

        link_script = r'C:\Development\Workspace\iotogglem0\linker\stm32f0_linker.ld'

        command_full = r'"%s" %s -T"%s" %s-o "%s.elf"' \
                % (cmd_exe, link_files, link_script, link_cmd_options, fileroot)
        print command_full
        op = runcmd( command_full )
        if op != '':
           print 'LINK error'
           print op
           optot += 'Link error: ', op
           status = 'failed armgcc'

        # Make the C error log output look like Python style errors, so that Editra Hotspot Python Handler will highlight it  
        if status == 'failed armgcc':
            hotspotify_c_log( optot, file)

        armsize   = r'arm-none-eabi-size.exe'
        cmd_exe   = r'%s\%s' % (arm_dir, armsize)
        command_full = r'"%s" "%s.elf"' \
                % (cmd_exe, fileroot)
        print command_full
        op = runcmd( command_full )

        print op
    
#######################################################################
#  Flash the part using openocd telnet connection
#######################################################################
    if status == 'good':    
        print '(openocd flash started)...',


        micro = find_stlink.find_stlink()
        micro.telnet_session = micro.start_telnet_session()
        op = micro.flash_program( "%s.elf" % fileroot )
        print op
        micro.close_telnet_session()


#         if not re.search("Done, \d+ bytes total",op):   # v0.20
#             print '\n\n    *** (mspdebug FAILED) ***\n'
#
#             status == 'failed mspdebug'
#
#             if re.search("unable to find a device matching",op):
#                 print '*** ERROR *** Launchpad not connected, or driver not installed (click Install Launchpad Driver, or run mpy_driver_install.exe)'
#             elif re.search('Could not find device',op):
#                 print '*** ERROR *** MSP430 chip could not be found, make sure msp430 is plugged into socket and that it is the correct way round\n'
#             else:
#                 print op
#         else:
#             print '(mspdebug passed)   ',
#             num_bytes = re.findall('(\d+ bytes total)', op)
#             print num_bytes[0], 'to ', chip_id

else:    
    print '*** ERROR *** open and select the .mpy file to be programmed'
    status = 'no file'

