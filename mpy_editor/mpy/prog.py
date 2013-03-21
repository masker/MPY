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


#--------------------------------------------------------
def runcmd( command_line, log=False ):
    args = shlex.split(command_line)
    if log:   print 'command_line=', args
    p = subprocess.Popen( args , stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    output = p.communicate()[0] 
    # remove any double linefeeds
    output = re.sub('\r', '', output)
    if log:   print 'x=', output
    return output

#--------------------------------------------------------
def get_py_file_linenum( line, comment_char ):
    '''Retrieve the file and linenumber placed at the end of the line
    e.g.  "   a = b ; // &C:\MPY\mpy_examples\blinky.mpy&13"  > ('C:\MPY\mpy_examples\blinky.mpy', '13')
    ''' 
    py_file = None
    py_linenum = None
    flds = re.findall('%s &([^&]+)&(\d+)$' % comment_char, line )
    if len(flds) >= 1 and len(flds[0]) >= 2:
        py_file = flds[0][0]
        py_linenum = flds[0][1]   
    return py_file, py_linenum   



#--------------------------------------------------------
def hotspotify_c_log( op_log, file ):
    '''Take the output log from the C compiler, and search for any recognizable errors
    when found reformat the line so that it looks like a Python error line, and print it out.
    Editra will then process the line and turn it into a hotspot so that it can be clicked on 
    and the C file will come into focus at the correct line where the error was detected'''
    
    lines = op_log.split('\n')
    for line in lines:
        flds = re.findall('^(.+):(\d+)(:(\d+):)? error: (.*)', line )
        if len(flds) >= 1 and len(flds[0]) >= 5:
            c_file = flds[0][0]
            c_linenum = flds[0][1]
            c_colnum  = flds[0][3]
            error_str = flds[0][4]
            
            if c_file not in file_contents:
                file_contents[ c_file ] = read_source_file( c_file )

            c_line = get_file_line( c_file, c_linenum )
                
            py_file, py_linenum = get_py_file_linenum( c_line, '//' )    
            if py_file:
                pyer_line = '(File "%s", line %s)\n File "%s", line %s\n    %s\n' % (  c_file, c_linenum, py_file, py_linenum, error_str)
            else:
                pyer_line = '                    (File "%s", line %s)\n    %s\n' % ( c_file, c_linenum, error_str)
            print pyer_line 
        else:
            flds = re.findall("^(.*\.c):.*: undefined reference to `(.*)'", line )
            if len(flds) >= 1 and len(flds[0]) >= 2:
               c_file = flds[0][0] 
               c_ref  = flds[0][1]
               print line, c_file, c_ref
               if c_file not in file_contents:
                   file_contents[ c_file ] = read_source_file( c_file )
                   c_line, c_linenum = search_file_line( c_file, c_ref, '//' )
                   if c_line:
                        py_file, py_linenum = get_py_file_linenum( c_line, '//' ) 
                        pyer_line = ' File "%s", line %s\n (File "%s", line %s)\n    %s\n' % ( py_file, py_linenum, c_file, c_linenum, line)
                        print pyer_line         
                        
              
               
#--------------------------------------------------------------
def read_source_file( file ):
    fip = open( file, 'r' )
    lines = []
    for line in fip:
        lines.append(line)
    fip.close()
    
    return lines
    
#--------------------------------------------------------------
def get_file_line( file, lineno ):
    retstr = ''
    lineno = int(lineno)
    if file in file_contents and lineno <= len(file_contents[file]):
        retstr = file_contents[file][lineno-1]
    
    return retstr

#----------------------------------------------------------          
def search_file_line( file, ref, comment_char ):
    '''Search through the file for the first occurance ref that is not inside a comment
    return the line, and the linenumber'''
    
    for i,ln in enumerate( file_contents[file] ):
        if re.search( r'%s[\W$]' % ref, ln):
            ref_pos     = ln.find(ref)
            comment_pos = ln.find(comment_char)
            if ref_pos > 0 and (comment_pos < 0 or comment_pos > ref_pos):
                return ln, i+1
    return None,None   


#----------------------------------------------------------          
def get_macro_def( chip_id ):
    '''We need to have our own preprocessor macro definition which is dependant on the chip id.
    This is needed as different devices have different peripherals and so some functions in the mpy_function.c
    need to be modified based on the device. This function will provide a macro definition name
    based on the device
    '''
    
    macro_def = ' '
    if chip_id[-1] in ['3'] :
        macro_def +=  '-D MPY_USCI '
        macro_def +=  '-D MPY_TIMER1 '

    if chip_id[-1] in ['2'] :
        macro_def +=  '-D MPY_USI '

    if chip_id[-2] in ['3','5'] :
        macro_def +=  '-D MPY_ADC '

    if chip_id[-2:] in ['53','13', '52', '12', '11'] :
        macro_def +=  '-D MPY_COMPA '
    
    return macro_def


###########################################################
## main prog starts here ##################################
###########################################################


python_exe   = r'%s\python.exe' % ( sys.exec_prefix )
idx = sys.argv[0].index(  r'\mpy_editor\mpy\prog.py' )
mpy_dir = sys.argv[0][:idx]


mspgcc_ver   = r'mspgcc-20120406'
mspdebug_ver = r'mspdebug_v020'

file_contents = {}
debug = False

# Main Program

file = sys.argv[1]
file = os.path.abspath(file)
(fileroot, fileext) = os.path.splitext(file)
#print '[prog] argv = ', sys.argv

chip_id = sys.argv[2]

status = 'good'

if chip_id == 'Unknown':
    chip_id = 'msp430g2553'
    print "\n*** warning *** The microcontroller chip is unknown, will use '%s'" % chip_id


# Find the .h file for the chip_id device
hfile = r'%s\%s\msp430\include\%s.h'  % (mpy_dir, mspgcc_ver, chip_id.lower())



#######################################################################
#  mspdebug rf2500 exit  - run mspdebug initially to see which cpu is connected
#######################################################################
if 0:
        chip_id_dict = { '0xf201': 'msp430g2231', 
                         '0x2553': 'msp430g2553',
                         '0x2452': 'msp430g2452',
                       }
        chip_id = 'Un-recognized'
        print '(mspdebug started)...',
        install_dir = r'%s\%s' % (mpy_dir, mspdebug_ver)
        cmd = r'%s\mspdebug.exe' % install_dir
        cmd_opts = r'rf2500 "exit"' 
        command_line = '"%s" %s' % (cmd,cmd_opts)
        op = runcmd( command_line )
        if re.search('usbutil: unable to find a device matching 0451:f432',op):
            print '*** ERROR *** Launchpad not connected, or driver not installed (click Install or run mpy_driver_install.exe)'
        elif re.search('Device ID: (\S+)',op):
            print '(mspdebug passed)   ' , 
            wds =  re.findall('Device ID: (\S+)', op)
            device_id = wds[-1]
            if device_id in chip_id_dict:  
                chip_id = chip_id_dict[ device_id ]
                print  ' found chip ', chip_id 
            else:
                print  ' Device ID:', device_id, chip_id 
        elif re.search('Could not find device',op):
            print '*** ERROR *** MSP430 chip could not be found, make sure msp430 is plugged into socket and that it is the correct way round\n' 
        else:
            print 'error !!\n'
            print op


        cpu = chip_id
        
#######################################################################
#  mpy2c
#######################################################################
if file != None:
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
#  mspgcc
#######################################################################
    if status == 'good':    
        # Compile the C file using mspgcc
        print '(mspgcc started)  ...', 
        macro_def = get_macro_def( chip_id )
        install_dir = r'%s\%s' % (mpy_dir, mspgcc_ver)
        cmd      = r'%s\bin\msp430-gcc.exe' % install_dir
        cmd_opts = r'%s -L"%s\msp430\lib\ldscripts\%s"   -mmcu=%s -Os -fdata-sections -ffunction-sections -o "%s.elf" "%s.c" -Wl,--gc-sections -Wl,--strip-all' % ( macro_def, install_dir, chip_id, chip_id, fileroot, fileroot )
        command_line = '"%s" %s' % (cmd,cmd_opts)
        op = runcmd( command_line )
        if re.search(': error:',op)              or \
           re.search('undefined reference',op)   or \
           re.search('ld returned 1 exit status',op):
              print '\n\n    *** (mspgcc FAILED) ***\n'
              print op
              status = 'failed mspgcc'
        else:    
           print '(mspgcc passed) wrote: %s.elf' % fileroot
    
        # Make the C error log output look like Python style errors, so that Editra Hotspot Python Handler will highlight it  
        if status == 'failed mspgcc':
            hotspotify_c_log( op, file)
    
#        print op
    
#######################################################################
#  mspdebug
#######################################################################
    if status == 'good':    
        print '(mspdebug started)...',
        install_dir = r'%s\%s' % (mpy_dir, mspdebug_ver)
        # Run mspdebug to program the msp430 microcontroller
        cmd = r'%s\mspdebug.exe' % install_dir
        cmd_opts = r'rf2500 "prog %s.elf"' % fileroot
        command_line = '"%s" %s' % (cmd,cmd_opts)
        op = runcmd( command_line )
#        if not re.search("Done, \d+ bytes written",op):  # v0.19
        if not re.search("Done, \d+ bytes total",op):   # v0.20
            print '\n\n    *** (mspdebug FAILED) ***\n'
            
            status == 'failed mspdebug'
            
            if re.search("unable to find a device matching",op):
                print '*** ERROR *** Launchpad not connected, or driver not installed (click Install Launchpad Driver, or run mpy_driver_install.exe)'
            elif re.search('Could not find device',op):
                print '*** ERROR *** MSP430 chip could not be found, make sure msp430 is plugged into socket and that it is the correct way round\n' 
            else:
                print op
        else:
            print '(mspdebug passed)   ', 
            num_bytes = re.findall('(\d+ bytes total)', op)
            print num_bytes[0], 'to ', chip_id

else:    
    print '*** ERROR *** open and select the .mpy file to be programmed'
    status = 'no file'

