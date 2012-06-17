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

        print '(run_uart_comport) start_comport()'
        
        while 1:
            (self.comport, self.comport_name) = self.open_comport(self.device_id)
        
            if self.comport != None:
                self.run_comport_loop(self.comport, self.device_id, self.comport_name )
        
        
        
    #---------------------------------------------------------------------------------    
    def open_comport(self, device_id, log=False):
        '''Tries to open the comport on the device_id
        It uses devcon.exe to determine the COM port number assigned.
        If the device is not attached then it will exit.
        returns
            comport handle - if it succeeded in openning the port
            None - If it could not open it for any reason (eg not plugged in)
        '''

        if log: print '\n&&& [run_uart_comport.open_comport]  Looking for comport to OPEN'

#        self.pr(',')
        if log: print '&&&  (run_uart_comport.open_comport) started', device_id
        devcon_opstr = devcon( 'status'   , '', device_id, 20  )    
        fnd = re.findall('Name:.*\(COM(\d+)\)',devcon_opstr)
        serial_port = None
        if len(fnd) == 1:        
            comport_num = int( fnd[0] ) -1 
            comport_name = 'COM%s' % fnd[0]
            done = False
            open_attempts_count = 0
            while not done:
                self.pr('o\n')
                open_attempts_count += 1
                if log: print '&&&  (run_uart_comport.open_comport)           attempting to open port ', comport_name
                try:
                    serial_port = serial.Serial( comport_num, 9600, timeout=1 )   
                    done = True
                    if log: print '&&&  (run_uart_comport.open_comport)               succeeded in openning port ', comport_name
    
                except:
#                     self.pr('d\n')
#                     devcon_opstr = devcon( 'disable'  , 'Device is disabled|Device is currently stopped',        r'USB\VID_0451&PID_F432&MI_00', 20, log=log )    
#                     time.sleep(5)
#                     self.pr('e\n')
#                     devcon_opstr = devcon( 'enable'   , 'Driver is running',         r'USB\VID_0451&PID_F432&MI_00', 20, log=log )    
#                     time.sleep(10)
                    pass
                if open_attempts_count > 5:
                    self.pr('X\n')
                    break
                    
        if log: print '&&&  (run_uart_comport.open_comport) finished', serial_port
        
        if serial_port == None:
            comport_name = 'Not_Available'
            
        return serial_port, comport_name
        
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
        while(1):
            if i == 0:
#                self.pr('?\n')
                dstr = devcon( 'status'  , '',  device_id, 0, log=False)
                if not re.search('Driver is running', dstr):
                    break
            line = serial_port.readline()
            if line != '': 
               self.pr( line )
            time.sleep(0.05)  # wait 1/20 sec before looking again (frees up the cpu)
            i += 1
            i  = i % 10


        self.close_comport()
#        serial_port.close()

        self.pr( '''
####################################################
###   UART OUTPUT  STOPPED  ON COM PORT %s    ### 
###   IT IS NOW SAFE TO RECONNECT DEVICE         ### 
####################################################\n''' % comport_name )

          
          
########################################################################
#--------------------------------------------------------
def runcmd( command_line, log=True ):
    args = shlex.split(command_line)
    if log:   print 'command_line=', args
    p = subprocess.Popen( args , stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    output = p.communicate()[0] 
    if log:   print '      [command output]:', output,
    return output



#--------------------------------------------------------
def devcon( devcmd, confirm_str, interface,  max_loops=0, log=False ):

    if log : print '\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'
    if log : print '@@(devcon %s command for %s)' % (devcmd, interface)

    python_exe  = r'C:\Python27\python.exe'
    mpy_dir     = r'C:\MPY'


    # run the devcon command
    cmd      = r'%s\devcon\i386\devcon.exe' % mpy_dir
    cmd_opts = r'%s  "%s"' % (devcmd, interface)
    command_line = '"%s" %s' % (cmd,cmd_opts)
    op = runcmd( command_line , log=log )
    

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
           op = runcmd( command_line , log=log )
           if re.search(confirm_str, op):
                done = True
           i += 1
    
    if log: print '@@(devcon %s finished %s  on interface %s)' % (devcmd, done, interface)
    
    return op
        
        
    
########################################################################
########################################################################

if __name__ == '__main__':
    
    run_uart_comport = run_uart_comport(None, 
       device_id=r'USB\VID_0451&PID_F432&MI_00', 
       run_in_separate_thread=False )


