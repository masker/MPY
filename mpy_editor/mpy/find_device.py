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



python_exe   = r'%s\python.exe' % ( sys.exec_prefix )        
idx = sys.argv[0].index(  r'\mpy_editor\mpy\find_device.py' )
mpy_dir = sys.argv[0][:idx]

mspdebug_ver = r'mspdebug_v020'

debug = False

# Main Program

file = sys.argv[1]
file = os.path.abspath(file)
(fileroot, fileext) = os.path.splitext(file)


#######################################################################
#  mspdebug rf2500 exit  - run mspdebug initially to see which cpu is connected
#######################################################################
if 1:
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
        
