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



        
        
python_exe   = r'C:\Python27\python.exe'
mpy_dir      = r'C:\MPY'
mspgcc_ver   = r'mspgcc-20120406'
mspdebug_ver = r'mspdebug_v019'

debug = False

# Main Program

file = sys.argv[1]
file = os.path.abspath(file)
(fileroot, fileext) = os.path.splitext(file)
# print '[prog] argv = ', sys.argv

cpu = 'msp430g2553'

status = 'good'


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
           
        cmd_opts = '"%s\mpy_editor\mpy\mpy2c.py" "%s" %s' % ( mpy_dir, file, debug_str )
        command_line = '"%s" %s' % (cmd,cmd_opts)
        op = runcmd( command_line )    
        if re.search('Traceback \(most recent call last\):',op):
            print '\n\n  *** (mpy2c FAILED) ***\n'
            print op
            status = 'failed mpy2c'
        elif re.search('mpy2c failed',op):
            print '\n\n    *** (mpy2c FAILED) ***\n'
            print op
            status = 'failed mpy2c'
        elif status == 'good':
            # get the cpu name    
            oplines = op.split('\n')
            for line in oplines:
                wds = line.split()
                if len(wds) == 2 and wds[0].strip() == '@@MMCU@@:':
                    cpu = wds[1].strip()      
            print '(mpy2c passed)  wrote: %s.c   using CPU: %s' % (fileroot, cpu)

            if debug:
                print op

    
#######################################################################
#  mspgcc
#######################################################################
    if status == 'good':    
        # Compile the C file using mspgcc
        print '(mspgcc started)  ...', 
        install_dir = r'%s\%s' % (mpy_dir, mspgcc_ver)
        cmd      = r'%s\bin\msp430-gcc.exe' % install_dir
        cmd_opts = r'-L"%s\msp430\lib\ldscripts\%s"   -mmcu=%s -Os -o "%s.elf" "%s.c"' % ( install_dir, cpu, cpu, fileroot, fileroot )
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
        if not re.search("Done, \d+ bytes written",op):
            print '\n\n    *** (mspdebug FAILED) ***\n'
            print op
            status == 'failed mspdebug'
        else:
            print '(mspdebug passed)   ', 
            num_bytes = re.findall('(\d+ bytes written)', op)
            print num_bytes[0], 'to ', cpu

else:    
    print '*** ERROR *** open and select the .mpy file to be programmed'
    status = 'no file'

