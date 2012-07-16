###############################################################################
# Name: driver_install.py                                                     #
# Purpose: Installs the Launchpad drivers                                     #
# Author:  Mike Asker <mike.asker@mpyprojects.com>                            #
# Copyright: (c) 2012 Mike Asker <www.mpyprojects.com>                        #
# License: wxWindows License                                                  #
###############################################################################



import subprocess
import sys
import os
import shlex
import time
import shutil
import serial
import re

# print '[prog] argv = ', sys.argv

# python_exe   = r'C:\Python27\python.exe'
# mpy_dir      = r'C:\MPY'

python_exe   = r'C:\Python%s%s\python.exe' % ( sys.version_info.major, sys.version_info.minor )
idx = sys.argv[0].index(  r'\mpy_editor\mpy' )
mpy_dir = sys.argv[0][:idx]


#--------------------------------------------------------
def runcmd( command_line, log=True ):
    args = shlex.split(command_line)
    if log:   print 'command_line=', args
    p = subprocess.Popen( args , stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    output = p.communicate()[0] 
    # remove any double linefeeds
    output = re.sub('\r', '', output)
    if log:   print 'x=', output
    return output



#--------------------------------------------------------
def devcon( devcmd, confirm_str, interface,  max_loops=0, log=True ):
    if log : print '@@(devcon %s command for %s)' % (devcmd, interface)

    # run the devcon command
    cmd      = r'%s\devcon\i386\devcon.exe' % mpy_dir
    cmd_opts = r'%s  "%s"' % (devcmd, interface)
    command_line = '"%s" %s' % (cmd,cmd_opts)
    op = runcmd( command_line , log=False )
    

    # now run the devcon status command to check that the
    # first command has been completed
    done = None
    if max_loops>0:
        cmd_opts = r'status  "%s"' % interface
        command_line = '"%s" %s' % (cmd,cmd_opts)
        done = False
        
        i = 0
        while not done and i<max_loops:
           time.sleep(0.5)
           op = runcmd( command_line , log=False )
           if re.search(confirm_str, op):
                done = True
           i += 1
    
    if log: print '@@(devcon %s finished %s  on interface %s)' % (devcmd, done, interface)
    
    return op

#------------------------------------------------------------------------
def run_mpy_driver_installer():
    '''runs the NSIS driver installer script'''
    
    # run the devcon command
    cmd      = r'%s\mpy_driver_installer.0.1.a1.exe' % mpy_dir
    cmd_opts = r''
    command_line = '"%s" %s' % (cmd,cmd_opts)
    op = runcmd( command_line , log=False )

    return op
        
#------------------------------------------------------------------------
def get_driver_service( devcon_opstr, interface_str ):
    '''Determine which driver service is being used used for the given interface'''
    
    lines = devcon_opstr.split('\n')
    found = None

    for line in lines:
    
        if found == 'Controlling service':
            return line.strip()
    
        if line.find(interface_str) >=0:
            found = 'interface'
            
        if  found == 'interface' and line.find('Controlling service') >= 0:
            found = 'Controlling service'
        
    
    return None
    
#------------------------------------------------------------------------


# Check to see if a Launchpad device is plugged in.

# Check to see which drivers need installing - use the devcon stack command
# to see which driver is currently being used






log = True

run_mpy_driver_installer()

sys.exit()


                  #   devcon cmd  confirm_str    device_id                  log_output
devcon_opstr = devcon( 'stack'   , '',         r'USB\VID_0451&PID_F432&MI*', log=log )

print devcon_opstr

hid_driver  = get_driver_service(devcon_opstr, r'USB\VID_0451&PID_F432&MI_01')
uart_driver = get_driver_service(devcon_opstr, r'USB\VID_0451&PID_F432&MI_00')

if not hid_driver and not uart_driver:
    print '********************************************************'
    print '*** Launchpad Board (VID_0451&PID_F432) Not Found    ***'
    print '*** Please plug in your Launchpad Board              ***'
    print '*** into the PC USB socket and try again             ***'
    print "*** *BUT* Cancel the 'Found New Hardware' Wizzard    ***"
    print '********************************************************'
    sys.exit()


# install the libusb0 driver for MSPDEBUG

driver = uart_driver
if driver != 'usbser':
    cmd = r'update "%s\mpy_setup\drivers\eZ430-UART\430cdc.inf" ' % mpy_dir
    devcon_opstr = devcon( cmd   , '',         r'USB\Vid_0451&Pid_f432&MI_00', log=log )
    print devcon_opstr
uart_driver = get_driver_service(devcon_opstr, r'USB\VID_0451&PID_F432&MI_00')
 
    
driver = hid_driver
if driver != 'libusb0':
    cmd = r'update "%s\mpy_setup\drivers\libusb-win32-bin-1.2.5.0\USB_Human_Interface_Device_(Interface_1).inf" '  % mpy_dir       
    devcon_opstr = devcon( cmd   , '',         r'USB\Vid_0451&Pid_f432&MI_01', log=log )
    print devcon_opstr
hid_driver  = get_driver_service(devcon_opstr, r'USB\VID_0451&PID_F432&MI_01')

if hid_driver == 'libusb0' and uart_driver == 'usbser':
    print '************************************************'
    print '*** Launchpad Board Drivers are Installed    ***'
    print '*** uart=%-10s, and hid=%-10s      ***' % (uart_driver, hid_driver)
    print "*** You are now ready to 'Prog' your msp430  ***"      
    print '************************************************'
else:
    print '******************************************************'
    print '***                ERROR                           ***'
    print '*** Launchpad Board Drivers could not be Installed ***'
    print '*** uart=%-10s, and hid=%-10s      ***' % (uart_driver, hid_driver)
    print '*** Please ask for help !!!                        ***'
    print '******************************************************'

sys.exit()



