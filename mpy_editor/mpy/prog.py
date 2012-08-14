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
               pyer_line = ' File "%s", line %s\n (File "%s", line %s)\n    %s\n' % ( py_file, py_linenum, c_file, c_linenum, error_str)
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
        ref_pos     = ln.find(ref)
        comment_pos = ln.find(comment_char)
        if ref_pos > 0 and (comment_pos < 0 or comment_pos > ref_pos):
            return ln, i+1
    return None,None   


python_exe   = r'%s\python.exe' % ( sys.exec_prefix )
idx = sys.argv[0].index(  r'\mpy_editor\mpy\prog.py' )
mpy_dir = sys.argv[0][:idx]

file_contents = {}

mspgcc_ver   = r'mspgcc-20120406'
mspdebug_ver = r'mspdebug_v019'

debug = False

# Main Program

file = sys.argv[1]
file = os.path.abspath(file)
(fileroot, fileext) = os.path.splitext(file)
#print '[prog] argv = ', sys.argv

chip_id = sys.argv[2]

status = 'good'



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
           
        cmd_opts = '"%s\mpy_editor\mpy\mpy2c.py" "%s" %s %s' % ( mpy_dir, file, chip_id, debug_str )
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
        install_dir = r'%s\%s' % (mpy_dir, mspgcc_ver)
        cmd      = r'%s\bin\msp430-gcc.exe' % install_dir
        cmd_opts = r'-L"%s\msp430\lib\ldscripts\%s"   -mmcu=%s -Os -o "%s.elf" "%s.c"' % ( install_dir, chip_id, chip_id, fileroot, fileroot )
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
            print num_bytes[0], 'to ', chip_id

else:    
    print '*** ERROR *** open and select the .mpy file to be programmed'
    status = 'no file'

