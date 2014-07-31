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
#   mpy2c.py  
#   
#   This python program is used to preprocess a 'mpy' format file into C.
#   It uses the python 'ast' python code parser to read a file, which is 
#   then traversed and an output token list is built with a C syntax.
#   More operations are performed to complete the translation, these include
#       Multiple macro substitutions
#       Loading in of included files
#       Print statement processing
#       Interrupt function insertion
#       Adding variable declarations, including globals
#       Converition of 'for' and 'range' loops
#       Reordering of functions at top of file, and adding of main function
#       Reading in of device macro mpy files for definition of portpin names and other inline type functions
#       Source filename and line numbers are added to the output that allow errors to be highlighted in the source
#
############################################################################
  


import ast
import types
import sys
import os
import re


###########################################################################
class mpy2c( object ):
    '''Class mpy2c will convert the .mpy file (microcontroller python subset)
    into a .c file suitable for compiling onto a microcontroller''' 
 
    #######################################################################
    def __init__(self, code, full_conversion=True, filename='<unknown>', chip_id=None, hfile=None, vlist=None ):
        '''Creates the mpy2c object. It does the following:
            1) Reads the code and parses it using the 'ast' library module
            2) Then walks the ast tree for the code and translates each element into an equivelant c syntax (nearly)
            3) Then adds the C variable declarations
            4) Converts the python FOR loops which use the range() statement into C format FOR statements 
            5) Revoves the last redundant ',' from parameter lists to make it legal C syntax
        
        code :  string containing all the input .mpy text
        
        self.op  :  C code'''
        
        self.op_names = ['UAdd','USub','Add','Sub','Mult','Div','Mod','Pow','LShift','RShift','BitOr','BitXor','BitAnd','FloorDiv', \
                               'Eq', 'NotEq', 'Lt', 'LtE', 'Gt', 'GtE', 'Is', 'IsNot', 'In', 'NotIn', 'And', 'Or', 'Invert']
        self.op_chars = ['+',   '-',   '+',  '-',  '*',   '/',  '%',  '**', '<<',    '>>',    '|',    '^',     '&',     '//',       \
                               '==', '!=',    '<',  '<=',  '>',  '>=',  'Is', 'IsNot', 'In', 'NotIn', '&&',  '||', '~']  

        # look for the presence  of __mpy_debug_on__
        self.switch_debug_on(code)


        # Change the print statements to a print_mpy function call
        # this is most easily done before we pass the code to the ast parser
        code = self.replace_print( code ) 


        if full_conversion:
            self.micro_name = chip_id   
            
            self.function_children   = {}
            self.function_parents    = {}
            self.function_parameters = {}
            self.function_variables  = {}
            self.function_current    = None
        

        # if the code is surrounded by quotes then remove them if there is a '=' char
        # (when running get_macros() we need to process the macros without quotes,
        #  but if there is no '=' character then this code string is likely to be a bare string
        # which we don't want to remove)
        code = code.strip()
        
        if (1 or code.find('=') >= 0)   and \
          code[0]  in ['"',"'"] and \
          code[-1] in ['"',"'"] :
              code = code[1:-1]
        
        # if we have a multi line script add a final newline to keep the parser happy
        if code.find('\n') >= 0:
           code += '\n'
 
        self.code_ast = ast.parse(code,filename=filename)
        self.code_lines = code.split('\n')


        self.filename = filename
        self.tok_num = 0
        self.level  = 0
        self.indent = 0
        self.op     = []
        self.current_lineno = -1
        self.scope = '__top_level__'
        self.define_micro_flag = None
        self.include_flag = None
        self.include_name = None
        self.last_body_end_idx = None
        self.global_vars = {}           # lists of global variables, a list for each scope        
                
        if full_conversion:
#            self.setup_standard_variables_list()        
            self.setup_hfile_variables_list(hfile)
        else:
            self.standard_var_list = vlist    
 
        self.walk_node( None, self.code_ast, None, None, None, None, 'TOP', filename=filename)  
                

        if full_conversion:
            self.reorder_functions()

        self.convert_for_statements()
        # Look for the print statements and convert them into the variable argument format that is
        # compatible with C
        if full_conversion:
            self.convert_print_statements()

        self.remove_last_commas()


        # now process the macros (only do this once on the main code)
        if full_conversion:
            self.replace_define_micro()

            self.add_main_definition()
            
            self.remove_includes()

            # Do an in-line replacement for the 'macro' statements (the mpy #define function)
            self.get_macros()
            self.add_mpy_macros()  # add macros for OUT IN etc

            # go through the code replacing each macro in the code
            # but do it multiple times as some macros may map to other macros
            # To start just replace the paramterless macros when they are done
            # do the ones with parameters
            num = 0
            paramless_only = True
            for i in range(20):
                self.tok_num = 0

                num, last_replace = self.replace_macros(paramless_only)
                if num == 0 and paramless_only == False:
                    break
                if num == 0 and paramless_only == True:
                    paramless_only = False
                
            if num > 0:
                print '*** ERROR *** macro recursion limit exceeded, possible'
                print "  endless macro loop detected, last macro = '%s'" % (last_replace)
            

            self.add_variable_definitions()

            self.process_interrupt_functions()
            
        if debug:
             self.output_toks()
 
 
    #########################################################################
    def process_interrupt_functions(self):
        '''Functions for interrupts need to be modified so that the interrupt keyword and interrupt
        vector added as a prefix to the function 
        
        eg     interrupt(PORT1_VECTOR) flash_led ( ) 
        '''
 
        # find all the interrupt_setup commands
        # and get their portpin_intr and interrupt function names       
        self.interrupt_info = {}
        state = None
        marker = None
        arg_count = 0
        portpin = None
        param = None
        intr_function = None
        
        for t in self.op:
            # look for calls for the interrupt_setup functions
            if t[5] not in [None, '', '.']:
                 marker = t[5]
            
            txt = t[0]

            
            if state == 'in_args' and marker == 'Call_end' :
                state = None
                arg_count = 0
                self.interrupt_info[intr_function]  = { 'portpin': portpin }
               
            # we have a tok with a real value
            
            if marker == 'Call' and txt == 'interrupt_setup':
                 state = 'intr_call_found'   
                 
            if txt in [None,'.','','(',')','{','}',',',';','[',']']:
                continue

            if state in ['intr_call_found', 'in_args'] and marker == 'arg_start' :
                state = 'in_args'
                arg_count += 1

            if arg_count == 1:
                portpin = txt
            if arg_count == 2:
                param = txt
            if arg_count == 3:
                intr_function = txt
                

#            print  txt , arg_count, portpin, param, intr_function

        # Go round again looking for all the function definitions
        # when a function matches one of the interrupt function names
        # add the interrupt(VECTOR) prefix                
        op_new = []
        state = None
        marker = None
        for t in self.op:
            # look for calls for the interrupt_setup functions
            if t[5] not in [None, '', '.']:
                 marker = t[5]
            
            txt = t[0]
            if marker == 'FunctionDef' and txt not in [None,'.','','(',')','{','}',',',';','[',']']:
                if txt in self.interrupt_info:
                    portpin = self.interrupt_info[txt]['portpin']
                    intr_vector_str = self.get_interrupt_vector_str( portpin )
                    tt = t[:]
                    tt[0] = ' interrupt( %s ) ' % intr_vector_str
                    op_new.append(tt)
            
            op_new.append( t )
 
        self.op = op_new
 
    #########################################################################
    def get_interrupt_vector_str( self, portpin_str ):
        '''Given an extended portpin name this function returns the name of the
        corresponding interrupt vector as defined in the msp430xxxx.h files
        An extended portpin defines regular IO pins plus other peripherals
        such as the the Watchdog timer, and USCI Uart devices.'''
        
        try:
            portpin = int(portpin_str)
        except:
            portpin = 0
        
        if ( 0x10 <= portpin < 0x20 ):  # P1.x  interrupts
            return 'PORT1_VECTOR' 
        if ( 0x20 <= portpin < 0x30 ):  # P2.x  interrupts
            return 'PORT2_VECTOR' 
        if (    portpin == 1 ):         #  INTERVAL_TIMER interrupt using the watchdog timer
            return 'WDT_VECTOR' 
        if (    portpin == 2 ):         #  UART_RX 
            return 'USCIAB0RX_VECTOR' 
        
        print "*** error *** the portpin defined in interrupt_setup( %s ... ) command is not recognized" % portpin_str

        
        return 'ILLEGAL_VECTOR'
    
    #########################################################################
    def blank_strings_and_comments(self, line):
        '''This function goes through a line and replaces any quoted string with the string @@@\d@@@
        which effectively blanks out the contents of any quoted string from being mistaken as code tokens.
        Comments are stripped off completely (and not replaced). The original line is returned with the 
        quoted strings replaced with the @@@\d@@@. The list of the orginal quoted strings 
        is also returned in quote_strings.
        ''' 
        opline = ''
        str_count = 0
        in_str = False
        in_comment = False
        quoted_strings = []
        ch_end = None
        i = 0

        print '(blank_strings_and_comments)' , line
        for ch in line:
        
            # Start here! Look for an openning quote
            if not in_comment and not in_str and ch in ["'", '"']:
               ch_end = ch
               in_str = True
               current_quoted_string = ''
               opline += '@@@%d@@@' % str_count   
               str_count += 1
#               print '(blank_strings_and_comments) start', i, ch, str_count, in_comment, in_str
            else:
                # End of string here! Look for a matching closing quote
                if not in_comment and in_str and ch == ch_end:
                   ch_end = ch
                   in_str = False
                   current_quoted_string += ch
                   ch = ''   # Clear the ch (ch_end), we do not want it being added to the opline.
                   quoted_strings.append(current_quoted_string)
#                   print '(blank_strings_and_comments) end  ', i, ch, str_count, in_comment, in_str
                   continue_quote = None

            # Look for trailing comment
            if not in_comment and not in_str and ch == '#':
               in_comment = True
               current_quoted_string = ''
#               opline += '@@@#@@@' 
            
            
            # if the ch is a \ control character we need to double it up
            if ch == '\\' :
               ch = '\\\\'
               
            # We are in a quoted string therefore add the character to the current quoted string
            # else add the character to output line

            if in_str or in_comment:
               current_quoted_string += ch
            else:
               opline += ch                 

            i += 1

#         if in_comment:
#             quoted_strings.append(current_quoted_string)
            
        return (opline, quoted_strings, continue_quote)

    #########################################################################
    def reinsert_strings_and_comments(self, line, quoted_strings):
        '''Replace all blanked out strings and comments back into the line.
        This function is used on a line that has been previously processed
        with blank_strings_and_comments() function. It replaces all blanked 
        out strings and comments back into the original values.
        All blanked out strings will match pattern @@@\d@@@ where the \d digit
        is the match count. The parameter quoted_strings contains a list of all
        the original strings
        '''
        i = 0
        new_line = line
        for repstr in quoted_strings:
            new_line = re.sub(r'@@@%d@@@' % i, quoted_strings[i], new_line)
            i += 1
            
        return new_line
    
    #########################################################################
    def switch_debug_on(self, code):
        '''If the code contains the debug on switch then switch debug on'''
        
        global debug, debug_reduced
        
        lines = code.split('\n')
        for line in lines:
 
            if re.findall('__mpy_verbose_debug_on__',line):
                debug = True
            if re.findall('__mpy_debug_on__',line):
                debug_reduced = True
                
                
                
               

    #########################################################################
    def replace_print(self, code):
        '''Go through the input source file and replace the print function 
        with a print__mpy__() function call. We do this to support variable
        length argument list, and arguments with a trailing ',' to indicate
        no newline.
        
        Assumptions:
                1) The print command is on a single line
                2) The print command is either a statement or a function
                3) The print command may occur in a multi-command line separated with ; characters
        '''
        
        
        lines = code.split('\n')
        new_lines = []
        for line in lines:
            new_line = line
            
            # Look for a possible print line
            # this search may not definitively find a print command, as it is possible for 'print' to be contained
            # inside a quoted string, in which case we should ignore it. 
            
            if re.findall(r'^\s*(\S*print)[\s|\(]',line):
                (blanked_line, quoted_strings) = self.blank_strings_and_comments(line)
                cmds = blanked_line.split(';')
                new_cmds = []
                for cmd in cmds:
                    new_cmd = cmd
                    # Looking for " print(..." or " print X..."
                    flds = re.findall(r'^\s*(\S*print)[\s|\(]',cmd)
                    if len(flds) == 1:
                        
                        # Find out which  print function is used and associated lowlevel character print function
                        if flds[0] == 'print':
                            tx_func = '__mpy_write_uart_TxByte'
                        elif flds[0] == 'lcd_print':
                            tx_func = '__mpy_write_lcd_TxByte'
                        else:
                            tx_func = '***ERROR PRINT NOT RECOGNIZED***'
                         
                                               
                        # Check to see if it is  function or a statement by looking for an openning bracket
                        if re.match(r'^\s*\S*print\s*\(', cmd):
                            fnd_function = True
                        else:
                            fnd_function = False
                            
                        pars = cmd.split(',')

                        # Change the command from 'print' to 'print___mpy__'
                        if fnd_function:
                            pars[0] = re.sub('\S*print', 'print__mpy__', pars[0])
                        else:
                            pars[0] = re.sub('\S*print', 'print__mpy__(', pars[0])
                            
                        # For consistency remove any spaces before the '('
                        pars[0] = re.sub(r'print__mpy__\s+\(', 'print__mpy__(', pars[0])
                            
                        
                        # Add the lowlevel character print function
                        pars[0] = re.sub(r'print__mpy__\(',  'print__mpy__( %s, ' % tx_func, pars[0])
                        
                            
                        #Insert a function pointer to the print function to be used. This is the function that will be used
                        # to send out a character byte to the output device.
 
                        #Look at the last pars value and determine if a newline is required or not
                        #For a print function, if the last pars is a ')' then there is a trailing ',', therefore do not add newline
                        if fnd_function:
                            if  pars[-1].strip() == ')':
                                do_nl = False
                            else:
                                do_nl = True
                        #For a print statement, if the last pars is a ')' then there is a trailing ',', therefore do not add newline
                        else:
                            if pars[-1].strip() == '':
                                do_nl = False
                            else:
                                do_nl = True

                        # Add newline if needed to last pars
                        # but be careful if it is a function to add it before the last ')'
                        if do_nl:
                            if not fnd_function:
                                pars[-1] += ' ,r"\\n"'
                            else:
                                pars[-1] = re.sub( r'\)\s*$', ' ,"\\\\n" )', pars[-1])
                            
                        # Add a trailing bracket if not a function
                        if not fnd_function:
                            pars[-1] += ' )'

                        new_cmd = ','.join(pars)
                        
                    new_cmds.append(new_cmd)
                
                blanked_line = ';'.join(new_cmds)
                new_line = self.reinsert_strings_and_comments(blanked_line, quoted_strings)
            new_lines.append(new_line)
            

        
        return '\n'.join(new_lines)

    #########################################################################
    def escape_embedded_quote_characters( self, line, quote_char=None ):
        '''Looks for any embedded quote characters in strings and escapes them.
        It returns the escaped line and the quote_char

        If the line is a continuation of the previous line then the quote_char
        indicates the quote character that terminates the string.
        If the line contains an unterminated string then the quote_char needed
        to terminate is return and is used again in this function
        on subsequent lines
        '''

        opline = ''
        for ch in line:

            if  ch in [ '"', "'" ]:
                if ch == quote_char:
                    quote_char = None
                elif quote_char == None:
                    quote_char = ch
                else:
                    ch = '\\\\\\\\' + ch

            opline += ch
        print '(escape_embedded_quote_characters opline):', opline

        return  (opline, quote_char)

    #########################################################################
    def setup_hfile_variables_list(self, hfile):
        '''Reads the hfile (the device specific .h file from the mspgcc installation)
        and finds all the defines in the file, and creates a standard list of variables. 
        This list will be used to prevent these variables from being redeclared in the 
        mpy2c generated file
        '''

        self.standard_var_list = []
        
        fip = open( hfile, 'r')

        if fip:
            for line in fip:
                line = line.strip()
                # re to find r'#define CALBC1_1MHZ_          0x10FF    /* BCSCTL1 Calibration Data for 1MHz */'
                #                      ^^^^^^^^^^^^
                fnd = re.findall(r'\s*#define\s+(\S+)\s+', line )
                if len(fnd) == 1 and len(fnd[0]) > 0:
                    self.standard_var_list.append( fnd[0] )
                   
                # re to find = r'const_sfrb(CALBC1_1MHZ, CALBC1_1MHZ_);'
                #                           ^^^^^^^^^^^    
                fnd = re.findall(r'\s*\w*sfr[bw]\s*\(\s*(\w+)\s*,', line )
                if len(fnd) == 1 and len(fnd[0]) > 0:
                    self.standard_var_list.append( fnd[0] )

            fip.close()
        
        else:
        
            print "*** error *** the .h file '%s' cannot be read, check that the mspgcc installation is correct" % (hfile)

        # Add all the mpy functions that are defined as C functions
        mpy_c_functions = ['wait', 'print', 'print_num', 'print_hex', 'print_value', 'adc', 'random' ] 
        self.standard_var_list.extend( mpy_c_functions )

    

    #########################################################################
    def setup_standard_variables_list(self):

        self.standard_var_list = [ 'WDTCTL', 'WDTPW', 'WDTHOLD', 
        'CCTL1', 'CCR0', 'CCR1', 'CCR1', 'TACTL', 'TAR', 
        'TA0CCTL0', 'TA0CCTL1', 'TA0CCTL2', 'TA0CCR0', 'TA0CCR1', 'TA0CCR2', 'TA0CTL', 'TA0R', 
        'TA1CCTL0', 'TA1CCTL1', 'TA1CCTL2', 'TA1CCR0', 'TA1CCR1', 'TA1CCR2', 'TA1CTL', 'TA1R',
        'CACTL1', 'CACTL2', 'MC_1',
        'ADC10SHT_0', 'ADC10SHT_1', 'ADC10SHT_2', 'ENC', 'ADC10ON',
        'ADC10CTL0', 'ADC10CTL1', 'ADC10AE0', 'ADC10MEM', 
        'REFON', 'REFON', 'REF1_5V', 'REF2_5V', 'SREF_0', 'SREF_1', 'SREF_2', 'SREF_3',
        'CALDCO_1MHZ',  'CALBC1_1MHZ',
        'CALDCO_8MHZ',  'CALBC1_8MHZ',
        'CALDCO_12MHZ', 'CALBC1_12MHZ',
        'CALDCO_8MHZ',  'CALBC1_8MHZ',
        'CALDCO_16MHZ', 'CALBC1_16MHZ',
        'BCSCTL1', 'BCSCTL2', 'DCOCTL',
        'wait', 'print', 'print_num', 'print_hex', 'print_value', 'adc', 
        ]
        for i in range(8):
            self.standard_var_list.append( 'P%sDIR' % i )
            self.standard_var_list.append( 'P%sSEL' % i )
            self.standard_var_list.append( 'P%sSEL2' % i )
            self.standard_var_list.append( 'P%sREN' % i )
            self.standard_var_list.append( 'P%sOUT' % i )
            self.standard_var_list.append( 'P%sIN'  % i )
            self.standard_var_list.append( 'TASSEL_%s'  % i )
            self.standard_var_list.append( 'BIT%s'  % i )
            self.standard_var_list.append( 'INCH_%s'  % i )
            self.standard_var_list.append( 'OUTMOD_%s'  % i )
            self.standard_var_list.append( 'OUTMOD%s'  % i )

    ########################################################################
    def add_element(self, optxt, vartf=None):
    
        #                 text   variable  scope  level, linenum

        self.op.append( [ optxt , vartf,   self.scope, self.level, self.current_lineno, None, self.indent, self.current_node_name, self.filename ])
     
    ########################################################################
    def add_marker(self, marker):
        ''' adds a marker in the op buffer to mark the position of some specific point in the code.
        The marker can be used to mark the insertion of varaible definitions or other types of code
        ''' 
    
        #                 text   variable  scope      level,       linenum
        self.op.append( [ '' ,    None,   self.scope, self.level, self.current_lineno, marker, self.indent, self.current_node_name, self.filename  ])

    ########################################################################
    def insert_tok(self, idx, tok):


        self.op.insert( idx, tok )

        print '*** insert_tok', idx , tok
        

    ########################################################################
    def insert_tok_list(self, idx, tok_list):

        self.op_tmp = self.op[:idx]
        self.op_tmp.extend( tok_list )
        self.op_tmp.extend( self.op[idx:] )        
        self.op = self.op_tmp
        

    
    ########################################################################    
    def write_op(self, file=None):
        
        opstr = ''
        lineno = -1
        lastfile = None
        for t in self.op:
        
            # if the filename changes then reset the line counter to 0
            # so that it forces the increment to start again
            if t[8] != None and lastfile != None and t[8] != lastfile:
                lineno = -1
            lastfile = t[8]
        
            if t[4] > lineno:
                opstr += '// &%s&%s\n' % (lastfile, lineno)
                opstr += '  ' * t[6]
                
            lineno = t[4]
            
            
            # Put a space after the element, but not if the element ends with a \n 
            if len(t[0]) > 0 and t[0][-1] != '\n':
                suffix = ' '
            else:
                suffix = ''
                
            opstr += '%s%s' % (t[0], suffix)

        opstr += '// &%s&%s\n' % (lastfile, lineno)
        
        if file == 'screen':
            print opstr
            print '=============================================================='
        elif file != None:    
            fop = open(file, 'w')
            print >> fop, opstr
            fop.close() 

        return opstr
        
#     ########################################################################    
#     def write_toks(self):
#         
#         for t in self.op:
#             print t

    ########################################################################    
    def output_toks(self):
        
        try:
            x = self.tok_num
        except:
            self.tok_num = 0
            
        print '   ---------------------------------------------------------------------------------------------------------------------------'                
        print '   %-15s %10s %10s %10s %10s %15s %10s %10s %10s'% ( 'Txt', 'VarDef', 'Scope', 'Level', 'Linenum', 'Marker', 'Indent', 'node_name', 'file')
        print '   %-15s %10s %10s %10s %10s %15s %10s %10s %10s'% (     0,        1,       2,      3,          4,        5,        6,           7,      8 )
        print '   ---------------------------------------------------------------------------------------------------------------------------'    
        for t in self.op[self.tok_num:]:
            if t[5] == None:
                t5 = '.'
            else:
                t5 = t[5]
            print '   %-15s %10s %10s %10s %10s %15s %10s %10s %10s'% ( "'%s'" % t[0], t[1], t[2], t[3], t[4], t5, t[6], t[7], t[8]) 
            



        print ' op_line = <',
        opstr = ''
        for t in self.op[self.tok_num:]:
            opstr += '%s ' % t[0]
        opstr += '>'
        print opstr
            

        self.tok_num = len(self.op)


    ########################################################################    
    def add_variable_definitions(self):
        '''This function is responsible for determining the type of all the
        variables in the code and adding the type declaration into the self.op
        '''

        # Find all the assigned-to variables, and add them into dict self.var_d
        self.add_var_info()

        # Find all function calls and add them into dict self.call_d
        self.add_call_info()


        if debug:
            print 'VAR_D START'
            for dbgscope in self.var_d:
                print '   scope ', dbgscope
                for dbgvar in self.var_d[ dbgscope ]:
                          print   '             ',  self.var_d[ dbgscope ][dbgvar]
            print 'global_vars=', self.global_vars
        
        # Go through the assigned variables and find all the dependencies
        # and add them to self.var_d as a list.
        # Also get the types (int, str, float, list etc) of those dependencies
        self.find_variable_dependencies()

        # Update the var_d type info for assigned variables and dependencies
        # run this itteratively to propagate the definitions when there are multiple
        # chained assignments
        undefined_count = 1
        i = 0
        while undefined_count > 0 and i < 30:
            undefined_count, update_count = self.update_variable_types_from_dependencies()
            self.update_dependency_types_from_variables()
            self.update_param_types_from_call_info()
            if debug:
                print 'UPDATING VARIABLE TYPES undefined_count, update_count', i, undefined_count, update_count
            i += 1

        # Find any remaining undefined variable types and print out error message
        if  undefined_count > 0:
            self.update_variable_types_from_dependencies( write_undefined_errors=True)


        self.add_const_info()

        # Add the type decalarations into the output buffer self.op
        self.add_typ_decalarions()


        if debug:
            print 'VAR_D END'
            for dbgscope in self.var_d:
                print '   scope ', dbgscope
                for dbgvar in self.var_d[ dbgscope ]:
                          dv =  self.var_d[ dbgscope ][dbgvar]
                          print   '             ',  dbgvar, dv[:4] , dv[5:]
                          for dbgdep in dv[4]:
                              print   '                  ',  dbgdep

    ############################################################################
    def add_const_info(self):
        '''Add const flag in the self.var_d for all variables that
            are only assigned once and are assigned an absolute value
        '''

        for scope in self.var_d:
            for var in self.var_d[scope]:
                info =  self.var_d[scope][var]
                const = None

                # If it is only assigned to once and not a globally declared variable
                if info[2] == 1 and \
                   not self.is_global_var(var)   and \
                   not self.is_augmented_assign(scope,var):
                    # look at all the dependencies
                    deps = info[4]

                    const = 'const'
                    for dep in deps:
                        if dep[1] != 'abs':
                            const = None
                    if len(deps) == 0:
                        const = None
                info[3] = const


    ############################################################################
    def is_augmented_assign(self, scope, var):
        '''Determine if the assignment of variable var is an augmented assinment
        '''

        if scope in self.var_assigns and var in self.var_assigns[scope]:
            i = 0
            for tok in self.var_assigns[scope][var][0]:
                if tok[0] == '':
                    continue
                if i == 1:
                    if tok[0] == '=':
                        return False
                    elif len(tok[0])==2 and tok[0][1]== '=':
                        return True
                    else:
                        return None
                i += 1



    ############################################################################
    def add_typ_decalarions(self):
        '''Using the self.var_d info add the typ decalration into the self.op
        '''

        # Add the variable declaration to the body_start or to the function definition arguments
        opn = []
        in_funct_def = False
        typ = None
        do_op = True
        for t in self.op:
            if t[5] == 'func_args_start':
                in_funct_def = True
            if t[5] == 'func_args_end':
                in_funct_def = False

            if in_funct_def and t[1]:
                scope = t[2]
                v = t[0]
                # check the token v is not a function definition name and check that it has not been done already
                if v not in self.var_d and self.var_d[scope][v][1] == None:
                    typ = self.var_d[scope][v][0]
                    if typ in [None, 'None']:
                        typ = 'int'
                    tv = t[:]
                    tv[0] = '%s ' % typ
                    tv[1] = None
                    opn.append(tv)
                    self.var_d[scope][v][1] = 'done'

            # Add the variable type declaration
            if not in_funct_def and t[1]:

                v = t[0]

                # update the scope imediately when the scope and the variable are
                # the same name, (this happens when we are doing the function name definition)
                if v == t[2]:
                   scope = t[2]

                #
                # Check the token v
                #    it exists in self.var_d
                #    is not declared as a global by some function
                #    check that it has not been done already
                #    check the variable is not the keyword 'return'
#                if not self.is_global_var(v) and v not in self.var_d and self.var_d[scope][v][1] == None and v != 'return':
                if   scope in self.var_d             and \
                     v in self.var_d[scope]          and \
                     not self.is_global_var(v)       and \
                     self.var_d[scope][v][1] == None and \
                     v != 'return':

                    # All consts are declared and intitialized at the start of the
                    # block. Therefore we need to remove the const assignment from
                    # the body of the block
                    if self.var_d[scope][v][3] == 'const':
                       if 1 or scope in ['__top_level__', 'main']:
                            do_op = False
                       else:
                          tv = t[:]
                          tv[0] = 'const'
                          tv[5] = 'var_const'
                          if do_op:
                              opn.append(tv)


                    # If we are doing the function name definition then
                    # substitute the type of its return statment
                    if v == scope:
                        scope = t[2]
                        if 'return' in  self.var_d[scope]:
                            v = 'return'

                    typ = self.var_d[scope][v][0]
                    if typ == 'str':
                        typ = 'char'
                    if typ in [None, 'None']:
                        typ = 'int'
                    tv = t[:]
                    tv[0] = '%s ' % typ
                    tv[1] = None
                    if do_op:
                        opn.append(tv)
                    self.var_d[scope][v][1] = 'done'


            if do_op:
                opn.append(t)

                # place an [] after the declaring a char string
                if typ == 'char':
                    tv = tv[:]
                    tv[0] = '[]'
                    opn.append(tv)
                    typ = None

            # re-enable the output when we get to the end of an assignment line
            if not do_op and t[0] in [';','{']:
                do_op = True

            scope = t[2]
#            if t[5] == 'body_start':
            # Add the variable declarations at the start of each function definition
            # but if we are in the the top_level do the  main then add the main variables as globals
            # in the __top_level__ at the define_micro_end position
            if (t[5] == 'body_start'       and scope != '__top_level__' and scope != 'main') or \
               (t[5] == 'define_micro_end' and scope == '__top_level__' ):
                scope = t[2]

                # pretend we are in the main scope when we are actually in the top_level
                if t[5] == 'define_micro_end' and scope == '__top_level__' :
                    scope = 'main'
                    t_newline  = t[:]
                    t_newline[6] = 0
                    t_newline[0] = '\n'
                    t_newline[5] = ''
                    opn.append(t_newline)

                if debug:
                    print 'found body_start for ', scope, ' on line ', t[4]
                if scope in self.var_d:
                    for v in self.var_d[scope]:

                        # Skip this variable definition if a global ('main') variable of
                        # the same name has been defined in this function scope
                        if scope != 'main'           and \
                           'main' in self.var_d      and \
                           v in  self.var_d['main']  and \
                          (scope in self.global_vars and v in self.global_vars[scope]):
                            continue


                        typ = self.var_d[scope][v][0]
                        if  self.var_d[scope][v][5] and len(self.var_d[scope][v][5]) >= 8:
                            tlnum = self.var_d[scope][v][5][4]
                            tfilename = self.var_d[scope][v][5][8]
                        else:
                            tlnum = ''
                            tfilename = 0

                        if typ in [None, 'None']:
                            typ = 'int'
                        # Check the token v is not a function definition name and check that it has not been done already
                        if v not in self.var_d and self.var_d[scope][v][1] == None:
                            if debug:
                                  print '  adding var definition for ', scope, v, self.var_d[scope][v]

                            # If this variable is identified as a const (one assignment from an abs value)
                            # may declare it as a 'const' to save memory

                            # However we have to assign the value when we declare it
                            # therfore we need to use the assignment from self.var_assign
                            # And when we find the assignment in the main block we
                            # need to remove it.
                            if self.var_d[scope][v][3] == 'const':

                                if v in self.var_assigns[scope] and len(self.var_assigns[scope][v])>=1:
                                   tv = t[:]
                                   tv[0] = 'const'
                                   tv[1] = None
                                   tv[5] = 'var_const'
                                   opn.append(tv)
                                   tv = t[:]
                                   tv[0] = '%s' % ( typ)
                                   tv[1] = None
                                   tv[5] = 'var_type'
                                   opn.append(tv)
                                   # write out the constant definition from var_assign
                                   for tok in self.var_assigns[scope][v][0]:
                                       opn.append(tok)
                                   tv = tok[:]
                                   tv[0] = ';'
                                   tv[1] = None
                                   tv[5] = None
                                   opn.append(tv)
#                                   self.var_d[scope][v][1] = 'done'
                            else:
                                tv = t[:]
                                tv[0] = '%s' % ( typ)
                                tv[1] = None
                                tv[5] = 'var_type'
                                opn.append(tv)
                                tv = t[:]
                                tv[0] = '%s' % (v)
                                tv[1] = None
                                tv[5] = 'var_def'
                                tv[4] = tlnum
                                tv[8] = tfilename
                                opn.append(tv)
                                tv = t[:]
                                tv[0] = ';\n'
                                tv[1] = None
                                tv[5] = None
                                opn.append(tv)
                                self.var_d[scope][v][1] = 'done'

                # pretend we are in the main scope when we are actually in the top_level
                if t[5] == 'define_micro_end' and scope == 'main' :
                    opn.append(t_newline)

        self.op = opn


    ############################################################################
    def add_var_info(self):
        '''Go through all the self.op buffer looking for any
        assigned variables, and add them into self.var_d

        Also find any variables that are defined as a 'global' and add those
        into self.var_d also
        '''

        # Look for all elements where the vardef is True
        # and add the element text to the var_d dict
        self.var_d = {}
        in_args = False
        in_fundef = False
        for t in self.op:

            scope = t[2]
            if t[5] == 'FunctionDef':
                in_fundef = True
            if t[5] == 'func_args_start':
                in_args = True
                in_fundef = False
                arg_position = 1
            if t[5] == 'func_args_end':
                in_args = False

            if t[1] == True:
                if scope not in self.var_d:
                    self.var_d[scope] = {}


                # Add the variable to the var_d dict, but not if
                #   the variable is in the standard variable list, or
                #   the vartable is an argument of a function
                if t[0] not in self.standard_var_list:
                    # Also test whether this vairiable is in the global_var list for this scop. If it is do not add it.
                    if scope not in self.global_vars or t[0] not in self.global_vars[scope]:
                        # to start lets assume that 'all' variables are int's
                        # this will be upgraded later to add strings and lists (hopefully)
                        #                             typename  done_flag
                        if self.is_var_num_str( t[0] ) == 'variable':
                            self.add_var_d( scope, t[0], t, 0 )

            # Add the function arguments as variables to be declared
            if in_args == True:
                if scope not in self.var_d:
                    self.var_d[scope] = {}
                if t[0] not in self.standard_var_list:
                    if self.is_var_num_str( t[0] ) == 'variable':
                        self.add_var_d( scope, t[0], t, arg_position )
                        arg_position += 1
                        t[1] = True

            # Add the function name itself as a variable
            if in_fundef == True and t[1] == False:
                if t[0] == scope:
                   self.add_var_d( 'main', t[0],  t, 0 )




        # Add any global variable definition to the __top_level__ (if they are not already present)
#        print '(add_variable_definitions) global_vars=', self.global_vars
        for k in self.global_vars:
            gvl = self.global_vars[k]
            if len(gvl) > 0:
                for gv in gvl:
                     scope = 'main'
                     if scope not in self.var_d:
                         self.var_d[scope] = {}
                     if gv not in self.var_d[scope]:
                        self.add_var_d( scope, gv,  None, 0 )


    ############################################################################
    def add_var_d( self, scope, varname, tok, arg_position, const_type=None ):
        '''Add a varaible to the var_d dict
        and increment the use count by one
        '''

        vartype = '--?--'

        if scope not in  self.var_d:
            self.var_d[scope] = {}

        if  varname not in  self.var_d[scope]:
            #                                 type        Done  Count, Const, Dependency list
            self.var_d[scope][ varname ]  = [ vartype,    None, 1, const_type, [], tok, arg_position ]
        else:
            vari = self.var_d[scope][ varname ]
            vari[2] += 1
            if const_type != None:
                vari[3] = const_type
            self.var_d[scope][ varname ] = vari

    ########################################################################
    def add_call_info(self):
        '''creates dict of calls - self.call_d
        For every call found in the source create an entry containing the

           scope
           line_number
           paramter_list

        paramter_list is an
        an ordered list of the parameters, each parameter in turn is a list of
        elements that make up the paramter
        '''

        self.call_d = {}




        # Look for all Calls and build a call dict
        self.call_d = {}
        in_args = False
        for t in self.op:

            scope = t[2]
            if t[5] == 'Call':
                in_args = True
                arg_position = 0
            if t[5] == 'Call_end':
                in_args = False

                clist[2] = elist
                self.call_d[callname].append(clist)

            if t[5] == 'arg_start':
                arg_position += 1


            if in_args and t[1] == False:

                if arg_position == 0:
                   callname = t[0]
                   scope    = t[2]
                   if callname not in self.call_d:
                        self.call_d[callname] = []

                   clist = [ scope, t, [] ]
                   elist = []
                else:   # for the next arguments
                   element = t[0]
                   tok     = t
                   typ = None
                   var_func_absvalue, typ, local_global  =  self.get_typ_info( element, scope, t[7] )
                   elist.append( [ element, arg_position, typ, var_func_absvalue, local_global, tok ] )

        if debug:
            print 'CALL_D='
            for callname in self.call_d:
                 print '  ',  callname,  self.call_d[callname]
                 for  clist in self.call_d[callname]:

                      print '      ', len(clist), clist[:2]
                      elist = clist[2]
                      for ele in elist:
                          print '               ', ele

    ########################################################################
    def is_global_var(self, var):
        '''Check to see if this var is a global var,
        returns
           scopes: list containing all scopes where this var is defined as a global
        '''

        scope_list = []
        for scope in self.global_vars:
            if var in self.global_vars[scope]:
                scope_list.append(var)

        return scope_list


    ########################################################################
    def find_variable_dependencies(self):
        '''Go thru all the self.op buffer looking at each variable assignment
        and add a list of dependencies for each varaible found in
        self.var_d[scoep[varname]
        Also create a separate var_assign[scope][varname] list of the assignment commands.
        This is done so that we can relocate the const decalarations assignments
        at the beginning of the __top_level__
        '''

        self.var_assigns = {}
        # Look for all elements where the vardef is True
        # and add the element text to the var_d dict
        in_assign = False
        assign_start = False
        for t in self.op:

             if t[1] == True:
                varname = t[0]
                scope   = t[2]
                # Get the variable definition in the local scope
                # if not found use the global definition
                if varname in  self.var_d[scope]:
                    vardef  =  self.var_d[scope][varname]
                else:
                    vardef  =  self.var_d['main'][varname]
                in_assign = True
                assign_start = True     # used to increment an assingment counter within the add_dependency_info()
                assign_toks = []
             if in_assign and t[0] in [';','{']:
                 if scope not in self.var_assigns:
                      self.var_assigns[scope] = {}
                 if varname not in self.var_assigns[scope]:
                      self.var_assigns[scope][varname] = []
                 self.var_assigns[scope][varname].append(assign_toks)
                 in_assign = False
                 varname = None
                 scope   = None

             # If we are in an assignment
             # build a list of dependency elements for this assignment
             # save the
             #    element name,
             #    whether it is a variable, funct, or absolute value,
             #    type of the element (variable, number, float, string, list)
             #    scope ( this function, or global)
             if in_assign:
                if t[1] == False  and t[0] != '':
                    #                                 type        Done  Count, Const, Dependency list
                    #self.var_d[scope][ varname ]  = [ vartype,    None, 1, const_type, [] ]
                    self.add_dependency_info( scope, varname, t[0], t[7], assign_start )
                    assign_start = False
                assign_toks.append(t)

    ########################################################################
    def add_dependency_info(self, scope, varname, dependency, node_name, assign_start):
        '''Add info for a dependency to the assigned variable in the
        #                                 type        Done  Count, Const, Dependency list
        #self.var_d[scope][ varname ]  = [ vartype,    None, 1, const_type, [] ]

        Dependency_list = [ dependency,  var_funct_absvalue, type, local_global ]
        '''

        # Get the variable definition in the local scope
        # if not found use the global definition
        if varname in  self.var_d[scope]:
            vardef  =  self.var_d[scope][varname]
        else:
            vardef  =  self.var_d['main'][varname]

        deps   = vardef[4]
        if len(deps) == 0:
            assign_count = 0
        else:
            # use the same count as the last assignment element, unless its the start of a new assignment
            assign_count = deps[-1][4]
            if assign_start:
                assign_count += 1

        var_func_absvalue, typ, local_global  =  self.get_typ_info( dependency, scope, node_name )


        deps.append( [dependency,  var_func_absvalue, typ, local_global, assign_count] )



    ########################################################################
    def get_typ_info( self, element, scope, node_name ):
        '''Determine the type of an element, based on the node_name data'''

        local_global = None
        typ = node_name
        var_func_absvalue  = 'abs'

        # If we have a node_name of str this could be an actual string value
        # or it could be then name of a variable or function call.
        # a string would be enclosed with ", if it isn't then we have
        # a varaible or a function

        if scope in self.var_d and node_name == 'str' and element[0] != '"':
            if element in self.var_d[scope]:
                var_func_absvalue = 'var'
                local_global = scope
                typ = None
            elif element in self.var_d['main']:
                var_func_absvalue = 'var'
                local_global = 'main'
                typ = None

            # If it didn't match any variables
            # look for a function (func_local or func_extern)
            # Function names are defined as variables in the
            # scope of the function
            if local_global == None :
                if element in self.var_d:
                    var_func_absvalue = 'func'
                    local_global = element
                    typ = None
                else:
                    # external functions default to ints! NEEDS TO BE UPDATED!!! TBD
                    var_func_absvalue = 'func_extern'
                    typ = 'int'



        return var_func_absvalue, typ, local_global

    ########################################################################
    def update_variable_types_from_dependencies(self, write_undefined_errors=False):
        '''Go thru all the var_d lists and redefine the type depending on the
        tokens that follow.
        '''

        
        # Look for all elements where the vardef is True
        # and add the element text to the var_d dict

        # go through all the var_d variables and determine the type of the
        # variable based on the dependency types
        # if they are all defined and all the same then the variable is the
        # same as its dependency types

        #                                   type        Done  Count, Const,     Dependency list
        # self.var_d[scope][ varname ]  = [ vartype,    None,     1, const_type, [deps] ]
        # dep = [dependency,  var_func_absvalue, typ, local_global ]

        undefined_count = 0
        updated_count = 0
        for scope in self.var_d:
            for var in self.var_d[scope]:
                deps =  self.var_d[scope][var][4]
                typ = self.var_d[scope][var][0]

                # The starting off type name is '--?--' (this is for debug
                # purposes so that it is easily recognized if we miss any
                # Make it a None to start with
                if typ == '--?--':
                    typ = None

                # If the variable name is the same as the scope name then
                # we are trying to determine the return type for the function
                # in this case use the type for the 'return' variable
                if var == scope:
                    if 'return' in self.var_d[scope]:
                        typ =  self.var_d[scope]['return'][0]
                        if typ in [None, 'None']:
                            typ = 'void'
                    else:
                        # clear the typ for functions which don't have a return
                        # this is so that an interrupt function definition
                        # does not get an illegal void definition
                        typ = ''




                # Work out what it is by looking at all the assignments and what the
                # types are for each of the elements in the RHS assignment values
                if var != scope:
                    undefined_count += 1
                    defd = True

                    # At the end we must print out any undefined variables as
                    # errors (there should not be any undefined vars)
                    if write_undefined_errors and typ == None:
                        # If this scope has not been called (redundant code)
                        # then dont bother writing out an error (but not if its 'main' though)
                        if scope == 'main' or scope in self.call_d:
                            print '*** error *** Undefined variable %s in %s' % (var, scope)
                            print '*** error *** ', self.var_d[scope][var]
                            py_file = self.var_d[scope][var][5][8]
                            py_linenum = self.var_d[scope][var][5][4]
                            print '*** error *** File "%s", line %s ' % (py_file, py_linenum)

                    # Find the number of assigns we have for this variable
                    if len(deps) > 0:
                       nassigns = deps[-1][4] +1
                    else:
                       nassigns = 0
                    for asn in range(nassigns):
                        for dep in deps:
                            if dep[4] == asn:
                                # If the dep var name is the same as the assign var name
                                # skip the test and continue onto the next dep
                                if dep[0] == var:
                                    continue
                                # If any dep type is not defined then the result is not
                                # defined also and exit the loop
                                if dep[2] == None:
                                    defd = False
                                    typ = None
                                    break
                                # If the current type for the var is none and the dep
                                # var is set then, set the var to the dep type
                                if typ == None:
                                    typ = dep[2]
                                # If any dep type is different to the previous dep type
                                # promote to float if we have an int and a float or else
                                # then exit the loop with None type
                                if dep[2] != typ:
                                    if dep[2] == 'float' and typ == 'int'   or \
                                       dep[2] == 'int'   and typ == 'float' :
                                        defd = True
                                        typ = 'float'
                                    else:
                                        defd = False
                                        typ = None
                                        break
#                            print 'doing dep', scope, var, asn, dep, typ
                        if typ != None:
                            break


                if typ != None:
                    updated_count +=1
                self.var_d[scope][var][0] = typ
        return  undefined_count, updated_count

    ########################################################################
    def update_dependency_types_from_variables(self):
        '''Go through all the var dependencies and if they have types defined in
        the var_d then update the dependency type info
        '''

        #                                   type        Done  Count, Const,     Dependency list
        # self.var_d[scope][ varname ]  = [ vartype,    None,     1, const_type, [deps] ]
        # dep = [dependency,  var_func_absvalue, typ, local_global ]

        for scope in self.var_d:
            for var in self.var_d[scope]:
                deps =  self.var_d[scope][var][4]
                typ = None
                defd = True
                for dep in deps:
                    if 1 or dep[2] == None:  # ignore the original type, override it with the latest

                       dscope = dep[3]
                       depvar = dep[0]
                       depabs = dep[1]
                       # if the dependent variable is in the var_d dict then use the typ
                       # for this and put it into the dependent variable typ
                       if dscope in self.var_d and depvar in self.var_d[dscope]:
                            typ = self.var_d[dscope][depvar][0]
                            dep[2] = typ
                    # WARNING THIS IS HARD CODED - TBD
                    # ALL EXTERNAL FUNCTIONS RETURN AN INT!
                    elif  dep[1] == 'func_extern':
                      dep[2] = 'int'


    ########################################################################
    def update_param_types_from_call_info(self):
        '''Go through all the var dependencies and if they have types defined in
        the var_d then update the dependency type info
        '''

        #                                   type        Done  Count, Const,     Dependency list
        # self.var_d[scope][ varname ]  = [ vartype,    None,     1, const_type, [deps] ]
        # dep = [dependency,  var_func_absvalue, typ, local_global ]

        for scope in self.var_d:
            for var in self.var_d[scope]:
                if self.var_d[scope][var][6] > 0:   # parameter position number
                    typ2 = self.find_call_param_type( scope,  self.var_d[scope][var][6] )
                    typ1 =  self.var_d[scope][var][0]
                    if typ2 != None and typ1 == None:
                        self.var_d[scope][var][0] = typ2

    ########################################################################
    def find_call_param_type(self, callname, param_position):
        '''Look through the self.call_d  for the the function call, and the
        and the parameter_postition. Find the parameter arguments for each
        call.

        If there is only one definition and its type is not-None then return the
        type, If there are multiple calls, and multiple elements in the parameter
        make sure they are all the same.
        '''

        if debug:
           print 'Searching for the arg type in function %s position %d' % \
                               (callname, param_position)

        # loop round the self.call_d
        typ = None
        ctyp = []
        vtyp = []
        if callname in self.call_d:
            calls = self.call_d[callname]
            for call in calls:
                param_list = call[2]
                for param in param_list:
                   if param[1] == param_position:
                       # add the type for this parameter, if it is known
                       if param[2] != None and param[2] not in ctyp:
                            ctyp.append(param[2])
                       depvar = param[0]
                       scope = param[4]
                       if      scope != None and \
                               scope in self.var_d and \
                               depvar in self.var_d[scope] and \
                               self.var_d[scope][depvar]:
                           vt = self.var_d[scope][depvar][0]  # get the type for this depvar
                           if vt != None and vt not in vtyp:
                               vtyp.append(vt)

            if debug:
                print 'ctyp = ', ctyp
                print 'vtyp = ', vtyp


        else:
            print "(find_call_param_type) callname '%s' not found in self.call_d" % callname

        if len(ctyp) == 1:
            return ctyp[0]
        if len(vtyp) == 1:
            return vtyp[0]

        return None
        
    ########################################################################    
    def convert_for_statements(self):
        '''Convert all Python format for statements into C format for statements.
        
        Go through all the elements looking for for_name, for_call, and for_list markers
        and identify the: for loop variable; the range function; and the range function args  

        Replaces the elements with C format elements. 

        Only 'for' statements which use the range() function are currently supported. 
        '''
        
        opn = []
        for_state = None
        for t in self.op:
        
            if t[5] == 'for_start':
                for_state = 'start'
            if t[5] == 'for_name':
                for_state = 'name'
            if for_state == 'name' and t[7] == 'str':
                finfo = [ t[0] ]

            if t[5] == 'for_call':
                for_state = 'call'
            if for_state == 'call' and t[7] in ['str', 'int' ]:
                finfo.append( t[0] )

            if for_state == None:
                opn.append ( t )

            if t[5] == 'for_end' and for_state == 'call':
                for_state = None
                tn = t[:]
                
                # finfo == [ i, range, min, max, inc ]
                #  for ( i=min;  i<max; i=i+inc )
                #        lv=min;  lv<max; lv=lv+inc ) {
                
                
                
                if len(finfo) == 3:
                    lv  = finfo[0]
                    min = 0
                    max = finfo[2]
                    inc = 1
                elif len(finfo) == 4:
                    lv  = finfo[0]
                    min = finfo[2]
                    max = finfo[3]
                    inc = 1
                elif len(finfo) == 5:
                    lv  = finfo[0]
                    min = finfo[2]
                    max = finfo[3]
                    inc = finfo[4]
                else:
                    print '*** ERROR ***  FOR LOOP '

                # determine which compare is required, if the value of inc is specified as a number then
                # it is easy to get the compare equality 
                # if its not known then we must test the value 
#                 x = int(inc)
#                         
#                 if int(inc) > 0:
#                     comp = '<'
#                 else:
#                     comp = '>'
#                     
#                 txt = '  %s=%s; %s%s%s;  %s=%s+%s ) {' % (
#                         lv, min,
#                         lv, comp, max, 
#                         lv, lv, inc    )


# make the for loop conditon dependant on the polarity of the inc variable                
#                  ((inc > 0 and lv < max) or (inc < 0 and lv > max))
                
                for_txt = ' %s = %s ; for ( ; ( ( %s > 0 && %s < %s ) || ( %s < 0 && %s > %s ) ) ;  %s = %s + %s ) {' % (
                            lv, min,
                            inc, lv, max,  inc, lv, max,  
                            lv, lv, inc    )
                
                for_txt_wds = for_txt.split()
     
     
                
                i = 0
#                for txt in [ lv, '=', min, ';',    lv, comp, max, ';',   lv, '=', lv, '+', inc, ')', '{' ]:
                for txt in for_txt_wds:
                    tn = t[:]
                    tn[0] = str(txt) 
                    if i in [0,29]:
                        tn[1] = True # set the vardef flag for the loop variable
                    if i in [2]:
                        tn[1] = False # set the vardef rhs value
                        tn[7] = 'int' # force it to be an int
                    opn.append( tn )
                    i += 1
        
        self.op = opn    


    ########################################################################    
    def remove_includes(self):

        opn = []
        state = None
        for t in self.op:
            if t[5] == 'include_start':
                state = 'in_include'
                
            if state == None:
                opn.append(t)
                
            if t[5] == 'include_end':
                state = None
              
        self.op = opn
    ########################################################################    
    def convert_print_statements(self):
        '''The print_mpy statement has a variable argument list. We will replace 
        modify the arguments so that the variable argument list can be compiled in C
           print( 'X=', x, 'Y=', y )  -> print__mpy__( print_func, "sdsd", "X=", x, "Y=", y )
        This function inserts an extra format aguement after the print_func argument in the list.
        The format arguement describes the type for each argument in the list.
        (Note the print_mpy() function is actually the print() funtion in the user's
        original input)
        '''  
        
#         self.tok_num = 0
#         self.output_toks()   
                
        opn = []
        opn_pr = []
        first_tok = None
        state = None
        tn = 0
        print_level = 0
        last_tok = ''
        for t in self.op:
        
            # Look for a function call, go to Call state
            if not state and t[5] == 'Call' :
                state = 'Call'
                print_level = t[3]
                
            # Look for the end of a function call, and go back to none state    
            if state == 'Call' and t[5] == 'Call_end' :    
                state = None
                
            # Look for the end of an arg and an end to the function call, at the same level as the starting Call,
            # go to None state, but add the fmt and opn_pr tokens to the opn buffer   
            if state == 'arg_end' and t[5] == 'Call_end' and t[3] == print_level:
            
            
                state = None
                first_tok[0] = '"%s"' % fmt
                first_tok[1] = None
                first_tok[5] = None
                first_tok[7] = 'Str'
                opn.append( first_tok )
                second_tok = first_tok[:]
                second_tok[0] = ','
                opn.append( second_tok )
                opn.extend( opn_pr )
                
                    
            # Look for a call and a print___mpy__ function, go to 'pr' state
            if state == 'Call' and t[0] == 'print__mpy__':
                state = 'pr'
                             
            
                
            # Look for arg_start or arg_done states and an arg_end marker, go to arg_end state    
            if state in ['arg_start', 'arg_done'] and t[5] == 'arg_end':
                state = 'arg_end'
                
            # Look for arg_end state and arg_start marker, go to arg_start state
            if state in ['arg_end', 'arg_start1']   and t[5] == 'arg_start':
                state = 'arg_start'

            # Look for 'pr' state and arg_start, go to arg_start state
            if state == 'pr' and t[5] == 'arg_start':
                # start a new list for the print parameters   
                first_tok = t[:]
                opn_pr = []
                state = 'arg_start1'
                fmt = ''

            
            # Look for arg_start state and non null token, and print_level +2 of the start print level
            # this is an arg
            # when we have a tok arg at the correct level we need to determine it's type
            # and add it to the fmt format string
            if state == 'arg_start' and t[0] != '' and t[3] == print_level+2:
                state = 'arg_done'
                if re.search(r'"', t[0]):
                    fmt += 's'
                elif  re.search(r'_hex$', t[0]):  # if the name ends in '_hex' then mark it to be printed as a hex number
                    fmt += 'h' 
                elif  re.search(r'_bin$', t[0]):
                    fmt +='b' 
                elif  re.search(r'_1000$', t[0]):
                    fmt += 'm' 
                elif  re.search(r'_100$', t[0]):
                    fmt += 'c' 
                elif  re.search(r'_10$', t[0]):
                    fmt += 'x' 
                else:
                    fmt += 'd'                    # else print it as a decimal number.
                
            
            if t[0] != '':
                last_tok = t[:]    
                
            # If the state is in an arg add it to the opn_pr list, else add it to the opn list
            if state not in ['arg_start', 'arg_end', 'arg_done']:
                opn.append(t)
            else:
                opn_pr.append(t)
                
                
            tn += 1  
            

        self.op = opn
        
     

#         self.tok_num = 0
#         self.output_toks()       

    ########################################################################    
    def replace_define_micro(self):
        '''Look for the define_micro_() If found then replace the call with 
            #include <io.h>
            #include "msp430g2231.h"
        '''

        if self.micro_name != None:
            self.micro_name = re.sub( 'm430', 'msp430', self.micro_name.lower() )

        opn = []
        replace_state = None
        for t in self.op:
        
            if replace_state == None and t[0] == 'define_micro' and t[2] == '__top_level__':
                replace_state = 'define_found'

            if replace_state in [None, 'done']:
                opn.append( t )
                
            if replace_state == 'define_found' and t[7] == 'str' and re.search(r'"', t[0]):
                micro_name = re.sub(r'"', '', t[0])
                replace_state = 'name_found'
                
            if replace_state == 'name_found' and t[0] == ';':
                replace_state = 'done'


                self.add_element_opn( opn, t,  '\n#include <msp430.h>\n' ) 
                self.add_element_opn( opn, t,  '#include <signal.h>\n' ) 
                self.add_element_opn( opn, t,  '#include "%s.h"\n' % self.micro_name )
                
                file = os.path.join( script_dir, 'mpy_functions.c' ) 
                self.add_element_opn( opn, t,  '#include "%s"\n' % file ) 

                print '%s  %s' % ( '@@MMCU@@:', self.micro_name )


        if replace_state == 'done':
           self.op = opn    

        # if no define_micro was found, insert the micro includes at the very beginning of the output
        elif self.micro_name != None:

            opt = self.op[:]            
            self.op = []
            
            self.add_element(  '\n#include <msp430.h>\n' ) 
            self.add_element(  '#include <signal.h>\n' ) 
            self.add_element(  '#include "%s.h"\n' % self.micro_name )
            file = os.path.join( script_dir, 'mpy_functions.c' ) 
            self.add_element('#include "%s"\n' % file ) 
            self.add_marker('define_micro_end')
            
            if debug_reduced:
                # Load a debug specific macro file which can include only the macros needed for the debug session
                # this cuts down the volume of log output, making it easier to see what's going on
                self.add_mpy_include( '%s\mpy_macros_common_debug.mpy' % script_dir )
            else:
                self.add_mpy_include( '%s\mpy_macros_common.mpy' % script_dir )
                self.add_mpy_include( '%s\mpy_macros_%s.mpy' % (script_dir, self.micro_name) )


            for t in opt:
               self.op.append( t )
            replace_state = 'done'
        
        

        if replace_state != 'done':
            print '*** ERROR *** (mpy2c failed) Cannot identify microcontroller chip'

        print '%s  %s' % ( '@@MMCU@@:', self.micro_name )


    ########################################################################    
    def add_main_definition( self ):

        # Add the main function definition 
        # find the location of the last body_end marker (which is the last function definition block)
        # or if the source does not contain any function definitions find the location of the
        # define_micro_end marker.


        main_insert_idx = None
        idx = 0
        found = None
        for t in self.op:
            # look for the last body_end marker, this is where we want to insert the
            # main function definition. (but make sure it is not at the end of the
            # file)
            

            if t[5] in ['body_end', 'define_micro_end'] and idx < len(self.op) - 5:
                main_insert_idx = idx
                main_insert_tok = t[:]
                found = idx
        
            idx += 1
            

        # now write self.op into opn
        # and insert the main definition tok and a new body_start marker tok
        # once found change all '__top_level__' scopes to 'main'
        opn = []
        idx = 0
        found_main = False
        for t in self.op:
        
            if found_main and t[2] == '__top_level__':
                t[2] = 'main'
                
            opn.append(t)
        
            if idx == main_insert_idx:
                found_main = True
                
                t = main_insert_tok[:]
                indent = t[6]
                t[2] = 'main'
                t[4] = main_insert_tok[4] + 1
                t[5] = ''
                t[6] = indent
                t[0] = '''
                        
void main (void) { 

    WDTCTL = WDTPW + WDTHOLD; // Stop WDT
    BCSCTL1 = CALBC1_1MHZ;    // Set range
    DCOCTL  = CALDCO_1MHZ;    // SMCLK = DCO = 1MHz

    // set all pins to pulldown inputs
    P1DIR = 0;
    P1REN = 0xFF;
    P1OUT = 0;
    P2DIR = 0;
    P2REN = 0xFF;
    P2OUT = 0;
    P1SEL = 0;
    P2SEL = 0;

'''    
                opn.append(t)
                
                t = main_insert_tok[:]
                t[2] = 'main'
                t[4] = main_insert_tok[4] + 1
                t[6] = 0
                t[0] = ''
                t[5] = 'body_start'
                opn.append(t)
                t = main_insert_tok[:]
                t[2] = 'main'
                t[4] = main_insert_tok[4] + 1
                t[6] = indent                
                t[0] = '\n'
                t[5] = ''
                opn.append(t)
                t[2] = 'main'
                t[4] = main_insert_tok[4] + 1
                t[6] = indent             
                t[0] = '\n'
                t[5] = ''
                opn.append(t)

            idx += 1
            
            
            
        self.op = opn
        
        # Then finish the module with a closing bracket
        # close the 'main()' function we added
        self.add_element( 'while(1);}' )     # Add the while statement so that we never run off the end of main
        self.add_marker(  'body_end' )       # which I think causes interrupts not to work.
            
                
    ########################################################################    
    def add_element_opn(self,  opn, t, txt ):
                tt = t[:]
                tt[0] = txt
                tt[6] = 0
                opn.append(tt) 



#     ########################################################################    
#     def add_print_newline(self):
#         '''Go through the self.op looking for the print__mpy__ commands if there 
#         is a trailing ',' then this indicates that no newline character is needed
#         if the is no trailing ',' then a newline character is needed
#         '''
# 
#         opn = []
# 
#         for i in range(len(self.op)):
#                 t = self.op[i]
#                 elem = t[0]
#                 # look for a ','
#                 if elem == ',':
#                     fnd = False
#                     # then look ahead at the next tokens
#                     # when we find an empty
#                     j = i
#                     while not fnd:
#                         j += 1
#                         tn = self.op[j]
#                         if tn[0] != '' or j >= len(self.op):
#                             if tn[0] == ')':
#                                t[0] = '' 
#                             fnd = True
#                          
#                            
#                 opn.append( t )
#                 
#         
#         self.op = opn


        
    ########################################################################    
    def remove_last_commas(self):
        '''Go through the self.op looking for any ',' elements and remove them
        if the next element is a ')'
        '''

        opn = []

        for i in range(len(self.op)):
                t = self.op[i]
                elem = t[0]
                # look for a ','
                if elem == ',':
                    fnd = False
                    # then look ahead at the next tokens
                    # when we find an empty
                    j = i
                    while not fnd:
                        j += 1
                        tn = self.op[j]
                        if tn[0] != '' or j >= len(self.op):
                            if tn[0] == ')':
                               t[0] = '' 
                            fnd = True
                         
                           
                opn.append( t )
                
        
        self.op = opn

    ########################################################################    
    def get_macros(self):
        '''Go through the self.op looking for any 'macro' elements and build the
        macro replacement list
        '''



        opn = []

        self.macros = []
        self.macros_dict = {}
        self.macros_dict_full = {}
        macro_state = 'not_in_macro'
        macro_name  = 'none'
        macro_value = 'none'
        level = 0
        for i in range(len(self.op)-1):
            t = self.op[i]
            elem = t[0]
            mkr  = t[5]
            t_n = self.op[i+1]
            elem_n = t_n[0]
            mkr_n  = t_n[5]
            
            # get rid of the double quotes added as part of the earlier c conversion
#            elem_n = re.sub( '^"|"$', '', elem_n)

            if macro_state == 'last_in_macro':
                macro_state = 'not_in_macro'
            if macro_state == 'value'   and  elem == ';':
                macro_state = 'last_in_macro'

            if mkr == 'arg_start':  
                level += 1

            if mkr == 'arg_end':  
                level -= 1
 
            if macro_state == 'value' and mkr == 'arg_end' and level == 0:
                macro_state = 'value'
#                mpy_value = elem_n                
                mpy_value_sub = re.sub( 'else:', '\nelse:', mpy_value )
                mpy_value_sub = re.sub( 'elif',  '\nelif', mpy_value_sub )
                
                duc = mpy2c( mpy_value_sub, full_conversion=False, filename=self.filename, vlist=self.standard_var_list)
                duc.remove_trailing_semicolon()
                c_value = duc.write_op(file=None).strip()
                (name_parameters, parameter_list) = self.get_name_params_from_macro(name)
                self.macros.append( [name, mpy_value, c_value, duc, name_parameters, parameter_list] ) 
                self.macros_dict[ name_parameters ] = len(self.macros)-1
                name_parameters_str = name_parameters
                if parameter_list != None:
                    for param in parameter_list:
                      name_parameters_str += ' %s' % param
                self.macros_dict_full[ name_parameters_str ] = len(self.macros)-1
                
            if macro_state == 'name' and mkr == 'arg_end' and level == 0:
                macro_state = 'value'
                mpy_value = ''

            if macro_state == 'value':
                mpy_value += elem_n
                

            if macro_state == 'name':
                name  += re.sub('\s','',elem_n) 


            if macro_state == 'call' and mkr == 'arg_start':
                macro_state = 'name'

                # remove all embeded spaces in the name (we want to strip all spaces from the macro name)
                name  = re.sub('\s','',elem_n) 

            
            if macro_state == 'not_in_macro' and mkr == 'Call' and elem_n == 'macro':
                macro_state = 'call'
           
            if macro_state == 'not_in_macro':
                opn.append(t)

        self.op = opn
        
        if debug:
          for a in self.macros:
            print '%%% macroS %%%', a
          for a in self.macros_dict:
            print '%%% macroS_DICT %%%', '{%s}' % a , self.macros_dict[a]
          for a in self.macros_dict_full:
            print '%%% macroS_DICT_FULL %%%', '{%s}' % a, self.macros_dict_full[a]
     
    ########################################################################    
    def get_name_params_from_op(self, idx):
        '''Get a list of parameters from the op token list and return a string with the name and params seperated using ':' character
            name             returns
            'OUT(a,b,c)' ->  OUT:a:b:c
            'OUT()'      ->  OUT:
            'OUT'        ->  OUT
        '''
        
        
        state = 'not_in_call'
        i = idx
        end_of_call_idx = idx
        done = False
        name_param = ''
        param_names = []
        while not done and i < len(self.op):

            t = self.op[i]
            elem = t[0]
            mkr  = t[5]

#            print '???          fnd elem <%s>' % t

            
            # get rid of the double quotes added as part of the earlier c conversion
            elem = re.sub( '^"|"$', '', elem)
 
            if state == 'args' and elem == ')':
                state = 'not_in_call'
                end_of_call_idx = i+1
                done = True

            if state == 'in_arg':
                if elem != ',':
                    arg += elem
                if mkr == 'arg_end':
                    state = 'args'
                    param_names.append( arg )
#                    print '???          added param_names <%s>' % arg

            if state == 'args' and mkr == 'arg_start':
                state = 'in_arg'
                arg = ''

            if state == 'call':
                state = 'args'
                # remove all embeded spaces in the name (we want to strip all spaces from the macro name)
                name  = elem

            
            if state == 'not_in_call' and mkr == 'Call':
                state = 'call'
            
            i += 1
            

        name_param = '%s:%d' % ( name, len(param_names) )
       
       
        return name_param, param_names, end_of_call_idx

    ########################################################################    
    def get_name_params_from_macro(self, macro_name):
        '''Get a list of parameters from the name string and append it to the main name using ':' character
            name             returns  name param_list
            'OUT(a,b,c)' ->           OUT:3   ['a','b','c']
            'OUT()'      ->           OUT:0   []
            'OUT'        ->           OUT     None
        '''


        # clean up the input
        macro_name = macro_name.strip()
        if macro_name[-1] == ',':
            macro_name = macro_name[:-1]
            
        name = macro_name
        param_list = None
        
        
        
        if re.search( '\(.*\)', macro_name ):
        
            params = re.sub( '.*\(', '', macro_name )
            params = re.sub( '\).*', '', params)
            
            # split the parameters_text into a list and create a string with 
            # the name followed by each paramerter using a ':' seperator 
            params = params.split(',')
            
            param_list = []
            for p in params:
                p = p.strip()
                if p != '':
                   param_list.append(p)
                   
            # add a suffix to the name with the number of pararmeters present
            # this will be used as the dictionary key to store the macro definition            
            name = re.sub( '\(.*', '', macro_name )
            name += ':%d' % len(param_list) 
    
        return name, param_list
            
 
           
    ########################################################################    
    def add_mpy_macros(self):
        '''Go through the self.op looking for any 'macro' elements and build the
        macro replacement list
        '''

        opn = []

        for i in range(len(self.op)):
            pass
            
    ########################################################################    
    def replace_macros(self, parameterless_replacements_only):
        '''Go through the self.op looking for any 'macro' elements and build the
        macro replacement list
        '''


        opn = []
        
        num_of_replacements = 0
        most_recent_replacement = ''
        end_i = 0
        end_of_call_idx = 0
        params_in_code = None
        i = 0
        while i <  len(self.op):

            # Disables the output of the source op until we get to the 
            # end_i, used to prevent writing out of the original un-repleaced Call statement
#            if i >= end_i:  
#                continue
        
#            elem = self.get_name_params_from_op(i)
            t = self.op[i]
            elem = t[0]
            mkr  = t[5]
            scope = t[2]
            
            
            
            # if we have a Call get all the parameters and see if they are present
            params_in_code = None
            if mkr == 'Call':
                elem, params_in_code, end_of_call_idx = self.get_name_params_from_op(i)
                
#                print '??????', i, elem, params_in_code, end_of_call_idx
            
            idx = None
            # If the element (elem) is present in the self.macros_dict then we will replace it with the definition
            # stored in the self.macros list
            if elem in self.macros_dict:
                idx = self.macros_dict[ elem ]
            
            # If we have parameters then look again in the macro_dict_full to see if the function and the
            # parameters match in name, if so then we will use this macro instead of the generic
            # one we found above
            if params_in_code != None and len(params_in_code) > 0:
                elem_params_full = elem
                for param in params_in_code:
                    elem_params_full += ' %s' % param
                
                if elem_params_full in self.macros_dict_full:
                    idx = self.macros_dict_full[ elem_params_full ]
            
            # We need to be able to force it to do parameterless_replacements
            if parameterless_replacements_only == True and params_in_code != None and len(params_in_code) > 0:
                idx = None
                pass
                            
            if idx != None:  
                
                # Get the list of tokens for the replacement, and insert
                # into the output tokens instead of the macro name
                duc = self.macros[idx][3]
                params_in_prototype = self.macros[idx][5]


                num_of_replacements += 1     
                most_recent_replacement = elem           

                 
                linenum_start = t[4]
                indent        = t[6]
                line_offset = None
                vardef        = t[1]

                
                if params_in_prototype and len(params_in_prototype) > 0 and 'portpin' in params_in_prototype:
                    port, bit = self.get_port_bit( params_in_code )
 
                for tro in duc.op:
                    tr = tro[:]
                    tr[0] = tro[0][:]
                    
                    
                    # Check to see if each element is one of the parameters if it is then replace it with the
                    # parameter name used in the  
                    if params_in_prototype != None and len(params_in_prototype) > 0:
                        if tr[0] in params_in_prototype :
                            pipx = params_in_prototype.index( tr[0] )
                            tr[0] = params_in_code[pipx][:]
                        if 'portpin' in params_in_prototype:
                            if tr[0].find('xxx') >= 0:
                                tr[0] = re.sub('xxx', port, tr[0])
                            if tr[0].find('yyy') >= 0:
                                tr[0] = re.sub('yyy', bit, tr[0])
                        # if parameters are used in the macro and the 
                    else:
                      tr[1] = vardef  

                    if not line_offset: 
                        line_offset = linenum_start
                    tr[4] =  linenum_start
                    tr[6] =  indent
                    tr[2] =  scope
                    
                    if tr[0] in self.standard_var_list:
                        tr[1] = False
                        
                    if tr[0] == '':
                        tr[1] = None

#                     vns =  self.is_var_num_str(tr[0], tr[7])
#                     if vns == 'variable':
#                         tr[1] = True
 
 
                    
 
                    opn.append(tr)
                      
                params_in_code = None
                
                 
                if params_in_prototype != None:
                    end_i = end_of_call_idx 
                    i = end_of_call_idx-1
            else:
              if i >= end_i:  
                opn.append(t)
                
            i += 1
                
        self.op = opn
        
        return num_of_replacements, most_recent_replacement


    #######################################################################
    def get_port_bit(self, params_in_code):
        '''Extract the Port and Bit from a port name eg.  'P2_3' -> ('2','3')
        '''

        for param in params_in_code:
            ppl =  re.findall('^P(\d+)_(\d+)$',param)
            if len(ppl) == 1 and len(ppl[0]) == 2:
                return ( ppl[0][0], ppl[0][1] )

        return ('', '')

    #######################################################################
    def is_var_num_str(self, elem, type='str'):
        '''Determine if the element is a string, a variable name or a number'''
        
        if re.search('"',elem):
            return 'string'
        elif re.search('^[0-9\.]+$',elem):
            return 'number'
        elif re.search('^[_a-zA-Z]\S*$', elem) and type == 'str':
            return 'variable'
        else:
            return 'unknown'
    
    ########################################################################    
    def remove_trailing_semicolon(self):
    
        #find the index of the last non blank token 
        # if its a ';' character then null out the token
        i = len(self.op)
        while i >=0:
            i -= 1
            t = self.op[i]
            if t[0] != '':
                if t[0] == ';':
                    t[0] = ''
                break
                
                
    ########################################################################                    
    def add_mpy_include( self, file  ):
 

        self.add_marker( 'INCLUDE_%s  start' % file )

        dirname = os.path.dirname(file)
        if dirname == '':
            dirname = os.path.dirname(self.filename)
            fullfile = os.path.join( dirname, file)
        else:
            fullfile = file
    
    
        if not os.access(fullfile, os.R_OK):
                print "*** error *** the include file '%s' cannot be read, check you have the correct file, mpy2c failed" % (fullfile)
                print ' File "%s", line %s' % (self.filename, self.current_lineno)
        else:
            fip = open( fullfile, 'rb')
            lines = fip.readlines()
            fip.close()
            jlines = ''.join(lines)
            jlines = re.sub(r'\r','',jlines)
            
            uc_inc = mpy2c( jlines, filename=fullfile , full_conversion=False, vlist=self.standard_var_list)
            
            self.op.extend( uc_inc.op )
        
            self.add_marker( 'INCLUDE_%s  end' % file )

        
    ########################################################################            
    def reorder_functions( self ):
        '''Go through all the code finding all function definitions.
        Make sure everything that is not a function definition is placed
        at the end. This will ensure that any 'bare' code will be included
        main section'''    
        
        # all 
        op_functs = []
        
        # toks that are at the __top_level__ will go into the op_main list
        op_main   = []
        # everything else is going into the op_functs list
        op_functs = []
        
        i = 0
        while i <  len(self.op):
        
           t = self.op[i]
           
           i += 1

           if t[2] in ['__top_level__', 'main'] and t[5] != 'FunctionDef':
              op_main.append(t)
           else:
              op_functs.append(t)
              
        # Replace the original self.op list with the op_functs list followed by the op_main list
        self.op = op_functs
        self.op.extend(op_main)

        
    ########################################################################    
    def walk_node( self, parent_node_name, node,  parent_arg_name, arg_name, first_node_name, parent_first_node_name, node_or_field, filename=None):
        '''Traverses the node and adds the node details to self.op to form
        a C format string in self.op.  This is a recursive function.
        
        node:   current node, it points to a node in an ast tree
        parent_stmtop : the stmop of the parent node
        
        In walking the block the 
        nodetype :  type of the current node    'Assign', 'AugAssign', 'Expr', 'Call'
        fldtype  :  type of field,  'body', 'op', 'value', 'left', 'right' , 'target', 'operand'
        stmtop   :  statement or operator name, 'Assign', 'For', 'BinOp' 'Add', 'Name', 'Num', 'UnaryOp' 'UAdd', 'USub', etc
        '''   


        self.level += 1
        level  = self.level
        indent = self.indent
        scope  = self.scope
        
        self.filename = filename
        
        # adjust the length of the indent prefix string
        pfx = '.   ' * self.level  
        pfx_indent = '    ' * self.level 
       

        
   
        node_name  = node.__class__.__name__
        self.current_node_name = node_name

        node0 = None
        node0_name = None
        if isinstance( node, types.ListType ) and len(node) > 0:
                  node0 = node[0]
                  node0_name = node0.__class__.__name__
        typ = '?'
        if isinstance( node, types.ListType ):
            typ = 'L'
        if hasattr( node, '_fields'):
            if typ == 'L':
                typ += 'F'
            else:
                typ = 'F'
        



        # Write out a newline if the current input node is on a new line        
        if 'lineno' in dir(node):
            lineno =  node.lineno
            if lineno > self.current_lineno:
                if debug:
                    self.output_toks()
                    print '============================================================================================'
                    print '============================================================================================'
                    print '(mpy) line = ', self.code_lines[lineno-1]
                    print '..............................................................'
                self.current_lineno = lineno
                self.indent = self.level
                indent = self.indent
#                self.add_element( '\n%s' % pfx_indent )
        else:
            lineno  = '?'  

        #                                 0        1                2              3             4            5          6             7                    8               9    10
        if debug : print '(walk_node) ', pfx, node_or_field, parent_node_name, node_name, parent_arg_name, arg_name, node0_name,       first_node_name, parent_first_node_name, node, typ
#    def walk_node( self,                                    parent_node_name, node,      parent_arg_name, arg_name,                   first_node_name, parent_first_node_name, node_or_field, filename=None):




        # Update the scope
        if parent_node_name == 'FunctionDef' and node_name == 'str' and arg_name == 'name':
            scope      = node
            self.scope = node

        if node_name == 'FunctionDef':
            self.add_marker('FunctionDef')


        ##### mark the element as a variable  ######
        # and use vardef to indicate whether the varaible is the LHS of an assignment
#        if node_name == 'str' and parent_arg_name in [None, 'target', 'value'] and arg_name == 'id':
        if node_name == 'str' and parent_arg_name in [None, 'target'] and arg_name == 'id' and parent_first_node_name == 'Assign' and str(node) not in self.standard_var_list:
            vardef = True
        else:
            vardef = False

        # Look for the augmented assigned varaibles
        if node_name == 'str' and parent_arg_name in ['target'] and arg_name == 'id' and parent_first_node_name == 'Name' and str(node) not in self.standard_var_list:
            vardef = True



        # Look for the function name definitions
        #                   n/f  parentnodename  node_name parentargname arg_name  Node0name  firstnodename  parentfirstname    node
        #                   Fld FunctionDef      str        None          name      None        str          Module             ghost_dance
        if node_name == 'str' and parent_node_name == 'FunctionDef' and arg_name == 'name' and parent_first_node_name == 'Module' and str(node) not in self.standard_var_list:
            vardef = True

        if node == '':
            vardef = None

        
        # when we encounter the macro_micro command then we will be adding the main() function
        if parent_arg_name in ['func'] and node == 'include' and self.scope == '__top_level__':
            self.add_marker('include_start')


        #####   VALUE    ########
        if arg_name in ['n', 'id', 'name', 's']:
            if arg_name == 's':
                # this is a string, if it contain a backslash then escape it to preserve the
                # \n so a new line does not get inserted before mspgcc gets to work on it.
                node_str = str(node)
                node_str = re.sub('\n', '\\\\n' ,  node_str )
                node_str = re.sub('\r', '\\\\r' ,  node_str )
                node_str = re.sub('\t', '\\\\t' ,  node_str )
                node_str = re.sub('\a', '\\\\a' ,  node_str )
                node_str = re.sub('"', '\\\\"' ,  node_str )
                self.add_element( r'"%s"' % node_str, vartf=vardef)
            elif arg_name == 'n':
                self.add_element( '%s'   % str(node), vartf=vardef)
            else:
                self.add_element( '%s'   % str(node), vartf=vardef )
                
                

        ######   OPERATOR  #######
        if arg_name in [None, 'op', 'ops'] :
            try:
                if parent_node_name in ['AugAssign']:
                    suffix = '='
                else:
                    suffix = ''
                if node_name not in ['And', 'Or' ]:
                    idx = self.op_names.index( node_name )                   
                    self.add_element( '%s%s' % (self.op_chars[idx],suffix) )
            except:
                pass


        # add the 'for' statement start marker
        # NOD list For body None None FunctionDef str <_ast.For object at 0x0253AAD0> F
#        if  parent_node_name=='list' and node_name=='For' and first_node_name in ['FunctionDef', 'Module', 'If'] :
        if  parent_node_name=='list' and node_name=='For':
            self.add_marker('for_start')


        ######   FUNCTION    ########
#        if node_name in ['While', 'For', 'FunctionDef', 'Return', 'Print' ]:
        if node_name in ['While', 'For', 'Return', 'Print', 'Break', 'Continue' ]:
            if node_name == 'Return':
                vardef = True
            else:
                vardef = None
            self.add_element( '%s' % node_name.lower(), vartf=vardef )
            
        #####  IF ELSEIF  ELSE  #######
#        if parent_node_name in ['list'] and node_name     in ['If', ] and arg_name == 'body':
        if parent_node_name in ['If'] and node_name  in ['Compare', 'BinOp', 'BoolOp', 'Name', 'Num' ] and arg_name == 'test':
            self.add_element( '%s' % 'if' )
#         if parent_node_name in ['If'] and node_name     in ['list', ] and arg_name == 'orelse' and node0_name == 'If':
#             self.add_element( '%s' % 'ELSIF' )
#         if parent_node_name in ['If'] and node_name     in ['list', ] and arg_name == 'orelse' and node0_name != 'If':
#             self.add_element( '%s' % 'ELSE' )
        if parent_node_name in ['If'] and node_name     in ['list', ] and arg_name == 'orelse' and node0_name != None:
            self.add_element( '%s' % 'else' )


        #####    {{{{{{{    ########        
        if arg_name in ['body']:
            if isinstance( node, types.ListType ) and len(node) > 0 and self.level > 2: 
                self.add_element( '{' )
        if parent_node_name in ['If'] and node_name     in ['list', ] and arg_name == 'orelse' and node0_name not in [ None, 'If']:
                self.add_element( '{' )

        if parent_node_name in ['FunctionDef'] and arg_name == 'body':
#        if parent_node_name in ['Module', 'FunctionDef'] and arg_name == 'body':
            self.add_marker('body_start')
            


        #####    (((((((    ######## 
        if arg_name in ['test']:
            self.add_element( '(' )
#        if arg_name in ['body', 'orelse']:


        if parent_node_name in ['list'] and parent_arg_name in [ 'args'] and first_node_name in ['Call']:
            self.add_marker('arg_start')


        #####    (((((((    ######## 
        if arg_name == 'target' and parent_node_name == 'For' :
            self.add_element( '(' )
        if arg_name == 'args'   and parent_node_name in ['Call']:
            self.add_element( '(' )
        if arg_name == 'values'   and parent_node_name in ['Print']:
            self.add_element( '(' )

        if node_name in ['BinOp', 'arguments', 'BoolOp']:
            self.add_element( '(' )

        if parent_node_name in ['Call',] and node_name == 'Name':
            self.add_marker('Call')

 
        if parent_node_name in ['FunctionDef'] and node_name in [ 'arguments']:
            self.add_marker('func_args_start')


        if parent_node_name in ['For']:
            if node_name == 'Name':
                self.add_marker('for_name')
            if node_name == 'Call':
                self.add_marker('for_call')
            if node_name == 'list':
                self.add_marker('for_end')
            
            
        ###### Look for 'global' keyword definitions
        
        if first_node_name == 'Global' and node_name == 'str' and parent_arg_name == 'names':
            global_var = node
            if scope not in self.global_vars:
                self.global_vars[scope] = []
            self.global_vars[ scope ].append( global_var )

        
        ######  RECURSION  LOOPS  ##############################
        
#        pfx = '.   ' * self.level  
        
        if isinstance( node, types.ListType ):
            done = False
            node_len = len(node)
            node_count = 1
            for nd in node:
 #                           parent_node_name, node,  parent_arg_name, arg_name, first_node_name, node_or_field):
                self.walk_node(  node_name,     nd,      arg_name,       None,   parent_node_name, first_node_name, 'NOD', filename=filename )

                # After processing each line frm the Modlule list of lines, we need it check to see
                # if we need to do an inline include of a mpy file
                if parent_node_name == 'Module' and first_node_name == 'list' and self.include_flag != None:
                    self.include_flag = None
                    self.add_marker('include_end')
                    self.add_mpy_include( self.include_name )
                    self.include_name = None
                if parent_node_name == 'Module' and first_node_name == 'list' and self.define_micro_flag != None:
                    self.define_micro_flag = None
                    self.add_marker('define_micro_end')
                    if debug:
                        # Load a debug specific macro file which can include only the macros needed for the debug session
                        # this cuts down the volume of log output, making it easier to see what's going on
                        self.add_mpy_include( '%s\mpy_macros_common_debug.mpy' % script_dir )
                    else:
                        self.add_mpy_include( '%s\mpy_macros_common.mpy' % script_dir )
                        self.add_mpy_include( '%s\mpy_macros_%s.mpy' % (script_dir, self.micro_name) )

                
                if node_count < node_len and parent_node_name == 'BoolOp' and node_name in ['list'] and parent_arg_name in ['test', None] and node0_name in ['Compare', 'Num', 'Name', 'BoolOp']:
                    idx = self.op_names.index( first_node_name )
                    self.add_element( '%s' % (self.op_chars[idx]) )
                    done = True
                 
                node_count += 1
                 
        if hasattr( node, '_fields'):
                 done = False
                 for field in ast.iter_fields(node):
#                    print '                                                 entering _FIELDS walk_node with', field
                    if not done:
                        first_node_nm = field[1].__class__.__name__
                        done = True
   #                           parent_node_name,  node,  parent_arg_name, arg_name, first_node_name, node_or_field):
                    self.walk_node(  node_name , field[1],  arg_name,     field[0], first_node_nm, first_node_name, 'FLD', filename=filename)
                     
        self.scope  = scope
        self.level  = level
        self.indent = indent
        self.current_node_name = node_name
        #########################################################            


        # Post node stuff
        
        
        ######   ========   ########
        if parent_node_name in ['Assign'] and arg_name in ['target', 'targets']:
            self.add_element( '=' )
#         if parent_node_name in ['AugAssign'] and arg_name in ['op']:
#             self.add_element( '=' )
            
            
        ###    }}}}}}    ########
#        if arg_name in ['body', 'orelse']:
        if arg_name in ['body']:
            if isinstance( node, types.ListType ) and len(node) > 0 and self.level > 2:
                self.add_element( '}' )
        if parent_node_name in ['If'] and node_name     in ['list', ] and arg_name == 'orelse' and node0_name not in [None, 'If']:
                self.add_element( '}' )

        ####    ;;;;;  #########
        if parent_node_name == 'list' and \
           node_name in ['AugAssign', 'Assign', 'Print', 'Return', 'Call', 'Expr', 'Break', 'Continue'] :
                if node_name != 'Call' or self.level == 1:
                   self.add_element( ';' )


        if arg_name == 'args' and parent_node_name in ['Call']:
            self.add_marker( 'Call_end' )

        #####  )))))))   ###########
        if arg_name in ['test']:
            self.add_element( ')' )
        if node_name in ['BinOp', 'arguments', 'BoolOp']:
            self.add_element( ')' )
        if arg_name == 'iter' and parent_node_name == 'For' :
            self.add_element( ')' )
        if arg_name == 'args' and parent_node_name in ['Call', 'Print']:
            self.add_element( ')' )
        if arg_name == 'values' and parent_node_name in ['Print']:
            self.add_element( ')' )
            
        ######    ,,,,,,    ###########
        if parent_node_name == 'list'                and \
           node_name not in ['Compare', 'BoolOp',  ] and \
           parent_arg_name in ['args', 'values']     and \
           first_node_name not in ['BoolOp']:
              self.add_element( ',' )


 

        if parent_node_name in ['FunctionDef'] and node_name in [ 'arguments']:
            self.add_marker('func_args_end')

#        if parent_node_name in ['Module', 'FunctionDef'] and arg_name == 'body':
        if parent_node_name in ['FunctionDef'] and arg_name == 'body':
            self.add_marker('body_end')

        if parent_node_name in ['list'] and parent_arg_name in [ 'args'] and first_node_name in ['Call']:
            self.add_marker('arg_end')

 
        # when we encounter the define_micro command then we will be adding the main() function
        if parent_arg_name in ['func'] and node == 'include' and self.scope == '__top_level__':
            self.include_flag = True
            self.include_name = None
            
        # when we encounter the define_micro command then we will be adding the main() function
        if parent_node_name == 'Str' and self.include_flag == True:
            self.include_name = node

        # when we encounter the define_micro command then we will define the micro name if it not already done
#        if self.define_micro_flag == True and node_name == 'str' and self.scope == '__top_level__' and self.micro_name == None:
        if self.define_micro_flag == True and node_name == 'str' and self.scope == '__top_level__':
            self.micro_name = node.lower()


        # when we encounter the define_micro command then we will be adding the main() function
        if parent_arg_name in ['func'] and node == 'define_micro' and self.scope == '__top_level__':
            self.define_micro_flag = True
            
        
        self.level -= 1

#########################################################################

     

chip_id = None
if len(sys.argv) > 2:
    chip_id = sys.argv[2]
if chip_id in [ '', 'Un-recognized']:
    chip_id = None

hfile = None
if len(sys.argv) > 3:
    hfile = sys.argv[3]

debug_reduced = False
debug = False
if len(sys.argv) > 4:
    debug = sys.argv[4]
    if debug != None:
        debug = True



print '\n[mpy2c] argv=', sys.argv
file = sys.argv[1]
file = os.path.abspath(file)
(fileroot, fileext) = os.path.splitext(file)


script_dir  = os.path.dirname( sys.argv[0] )




fip = open( file, 'rb')
lines = fip.readlines()
fip.close()

# Make the first line non blank.
# we need to do this, becuase I strongly suspect that the python ast module
# starts numbering its lines from the first non-blank line.
# and we need to preserve the real line numbers so that we can do hot-spot debug properly
if lines[0].strip() == '':
    lines[0] = '#' + lines[0]
    

jlines = ''.join(lines)
jlines = re.sub(r'\r','',jlines)



uc = mpy2c( jlines, filename=file, chip_id=chip_id, hfile=hfile )


#uc.write_toks()

fileop = '%s.c' % fileroot
uc.write_op( file=fileop)

if debug or debug_reduced: 
   print 'mpy2c completed debug'
else:
   print 'mpy2c completed'    # print this out so that the calling progrm knows we got to the end with normal completion
