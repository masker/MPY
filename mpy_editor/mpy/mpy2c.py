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

        # Change the print statements to a print_mpy function call
        # this is most easily done before we pass the code to the ast parser
        code = self.replace_print( code ) 

        if full_conversion:
            self.micro_name = chip_id   
            

        

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

            
        if debug:
             self.output_toks()
 
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
            
        return (opline, quoted_strings)

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
            if re.match(r'^\s*print[(|\s]', line):
#                print '(replace_print) found print line = ', line
                (blanked_line, quoted_strings) = self.blank_strings_and_comments(line)
#                print '(replace_print) blanked_line = ', blanked_line, quoted_strings
                cmds = blanked_line.split(';')
                new_cmds = []
                for cmd in cmds:
                    new_cmd = cmd
                    # Looking for " print(..." or " print X..."
                    if re.match(r'^\s*print[(|\s]', cmd):
#                        print '(replace_print) found print ', cmd

                                                
                        # Check to see if it is  function or a statement by looking for an openning bracket
                        if re.match(r'^\s*print\s*\(', cmd):
                            fnd_function = True
                        else:
                            fnd_function = False
                        pars = cmd.split(',')
#                        print '(replace_print) pars=', pars
                        
                        # Change the command from 'print' to 'print___mpy__' 
                        if fnd_function:
                            pars[0] = re.sub('print', 'print__mpy__', pars[0])
                        else:
                            pars[0] = re.sub('print', 'print__mpy__(', pars[0])
 
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
                         
#                        print '(replace_print) found print   fnd_function=', fnd_function, '  do_nl=', do_nl
                        
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

#                       print '(replace_print) new pars=', pars
                        
                           
                        new_cmd = ','.join(pars)
                        
                    new_cmds.append(new_cmd)
                
                blanked_line = ';'.join(new_cmds)
                new_line = self.reinsert_strings_and_comments(blanked_line, quoted_strings)
#                print '(replace_print) reinserted line = ', new_line
            new_lines.append(new_line)
            

        
        return '\n'.join(new_lines)


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
    
        # go through all the toks and build a dict of variables
        
        
        self.var_d = {}
        in_args = False
        
        # Look for all elements where the vardef is True
        # and add the element text to the var_d dict
        for t in self.op:

            scope = t[2]
            if t[5] == 'func_args_start':
                in_args = True
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
                            self.var_d[scope][ t[0] ]  = [ 'int',    None ]

            # add the function arguments as variables to be declared
            if in_args == True:
                if scope not in self.var_d:
                    self.var_d[scope] = {}
                if t[0] not in self.standard_var_list:
                    if self.is_var_num_str( t[0] ) == 'variable':
                        self.var_d[scope][ t[0] ]  = [ 'int',    None ]
                        t[1] = True
                
        opn = []
        
        
        # Add any global variable definition to the __top_level__ (if they are not already present)
        print '(add_variable_definitions) global_vars=', self.global_vars
        for k in self.global_vars:
            gvl = self.global_vars[k]
            if len(gvl) > 0:
                for gv in gvl:
                     scope = 'main'
                     if scope not in self.var_d:
                         self.var_d[scope] = {}
                     if gv not in self.var_d[scope]:
                         self.var_d[scope][ gv ]  = [ 'int',    None ]
        
        if debug:
            print 'var_d 1 =', self.var_d
                
        # Then add the variable declaration to the body_start or to the function definition arguments
        in_funct_def = False
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
                    tv = t[:]
                    tv[0] = '%s ' % typ
                    tv[1] = False
                    opn.append(tv)
                    self.var_d[scope][v][1] = 'done'
        
            opn.append(t)
            scope = t[2]
#            if t[5] == 'body_start':
            # Add the variable declarations at the start of each function definition
            # but if we are in the the top_level do the  main then add the main variables as globals
            # in the __top_level__ at the define_micro_end position
            if t[5] == 'body_start'       and scope != '__top_level__' and scope != 'main' or \
               t[5] == 'define_micro_end' and scope == '__top_level__' :
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
                        # check the token v is not a function definition name and check that it has not been done already
                        if v not in self.var_d and self.var_d[scope][v][1] == None:
                            if debug:
                                  print '  adding var definition for ', v 
                            tv = t[:]
                            tv[0] = '%s' % ( typ)
                            tv[5] = 'var_type'
                            opn.append(tv)
                            tv = t[:]
                            tv[0] = '%s' % (v)
                            tv[5] = 'var_def'
                            opn.append(tv)
                            tv = t[:]
                            tv[0] = ';'
                            tv[5] = None
                            opn.append(tv)                            
                            self.var_d[scope][v][1] = 'done'

                # pretend we are in the main scope when we are actually in the top_level
                if t[5] == 'define_micro_end' and scope == 'main' : 
                    opn.append(t_newline)

        self.op = opn
        
        if debug:
            print 'var_d=', self.var_d
        
        
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

            if t[5] == 'for_list' and for_state == 'call':
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
                    
                if inc > 0:
                    comp = '<'
                else:
                    comp = '>'
                    
                txt = '  %s=%s; %s%s%s;  %s=%s+%s ) {' % (
                        lv, min,
                        lv, comp, max, 
                        lv, lv, inc    )
                
                i = 0
                for txt in [ lv, '=', min, ';',    lv, comp, max, ';',   lv, '=', lv, '+', inc, ')', '{' ]:
                    tn = t[:]
                    tn[0] = str(txt) 
                    if i == 0:
                        tn[1] = True # set the vardef flag for the loop variable
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
           print( 'X=', x, 'Y=', y )  -> print__mpy__( "sdsd", "X=", x, "Y=", y )
        This function inserts an extra format aguement at the beginning of the list.
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
            if not state and t[5] == 'Call' :
                state = 'Call'
                print_level = t[3]
            if state == 'Call' and t[5] == 'Call_end' :    
                state = None
            if state == 'arg_end' and t[5] == 'Call_end' and t[3] == print_level:
                state = None
                first_tok[0] = '"%s"' % fmt
                first_tok[1] = None
                first_tok[5] = None
                first_tok[7] = 'Str'
#                 print "first_tok=" , first_tok
#                 print "opn_pr=" , opn_pr
                opn.append( first_tok )
                second_tok = first_tok[:]
                second_tok[0] = ','
                opn.append( second_tok )
                
                opn.extend( opn_pr )
                
#                 # If the last_tok was NOT a ',' character then add an extra newline parameter
#                 # a trailing ',' will cause no newline
#                 print 'last_tok=', last_tok
#                 if last_tok[0] != ',':
#                     tn = last_tok[:]
#                     tn[0] = ','
#                     opn.append( tn )
#                     tn = last_tok[:]
#                     tn[0] = '\n'
#                     opn.append( tn )
                    
                
            if state == 'Call' and t[0] == 'print__mpy__':
                state = 'pr'
            
                
                            
            
                
            if state == 'pr' and t[5] == 'arg_start':
                first_pram = tn 
                # start a new list for the print parameters   
                first_tok = t[:]
                opn_pr = []
                state = 'arg_start'
                fmt = ''
                
            if state in ['arg_start', 'arg_done'] and t[5] == 'arg_end':
                state = 'arg_end'
            if state == 'arg_end'   and t[5] == 'arg_start':
                state = 'arg_start'
                
            # when we and arg at the correct level we need to determine it's type
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
                
                
            if state not in ['arg_start', 'arg_end', 'arg_done']:
                opn.append(t)
            else:
                opn_pr.append(t)
                
#            if state: print print_level, state, t
                
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
            self.add_element( '#include "%s.h"\n' % self.micro_name )
            file = os.path.join( script_dir, 'mpy_functions.c' ) 
            self.add_element('#include "%s"\n' % file ) 
            self.add_marker('define_micro_end')
            self.add_mpy_include( '%s\mpy_macros_common.mpy' % script_dir )
            self.add_mpy_include( '%s\mpy_macros_%s.mpy' % (script_dir, self.micro_name) )

            for t in opt:
               self.op.append( t )
            replace_state = 'done'
        
        

        if replace_state != 'done':
            print '*** ERROR *** (mpy2c failed) Cannot identify MSP430 chip'

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
            
#             if found:
#                 main_insert_idx = idx
#                 main_insert_tok = t[:]
#                 found = None

                
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
        self.add_element( '}' )
        self.add_marker(  'body_end' )
            
                
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
    
        fip = open( fullfile, 'rb')
        lines = fip.readlines()
        fip.close()
        jlines = ''.join(lines)
        jlines = re.sub(r'\r','',jlines)
        
        uc_inc = mpy2c( jlines, filename=fullfile , full_conversion=False, vlist=self.standard_var_list)
        
        self.op.extend( uc_inc.op )
    
        self.add_marker( 'INCLUDE_%s  end' % file )

        
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
        if debug : print '(walk_node) ', pfx, node_or_field, parent_node_name, node_name, parent_arg_name, arg_name, node0_name, first_node_name, parent_first_node_name, node, typ




        # Update the scope
        if parent_node_name == 'FunctionDef' and node_name == 'str' and arg_name == 'name':
            scope      = node
            self.scope = node

        if node_name == 'FunctionDef':
            self.add_marker('FunctionDef')


        ##### mark the element as a variable ######
#        if node_name == 'str' and parent_arg_name in [None, 'target', 'value'] and arg_name == 'id':
        if node_name == 'str' and parent_arg_name in [None, 'target'] and arg_name == 'id' and parent_first_node_name == 'Assign' and str(node) not in self.standard_var_list:
            vardef = True
        else:
            vardef = False
        
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
                self.add_element( r'"%s"' % node_str)
            elif arg_name == 'n':
                self.add_element( '%s'   % str(node))
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





        ######   FUNCTION    ########
#        if node_name in ['While', 'For', 'FunctionDef', 'Return', 'Print' ]:
        if node_name in ['While', 'For', 'Return', 'Print', 'Break', 'Continue' ]:
            self.add_element( '%s' % node_name.lower() )
            
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

        if parent_node_name in ['list'] and parent_arg_name in [ 'args'] and first_node_name in ['Call']:
            self.add_marker('arg_start')


        if parent_node_name in ['For']:
            if node_name == 'Name':
                self.add_marker('for_name')
            if node_name == 'Call':
                self.add_marker('for_call')
            if node_name == 'list':
                self.add_marker('for_list')
            
            
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
                    self.add_mpy_include( '%s\mpy_macros_common.mpy' % script_dir )
                    self.add_mpy_include( '%s\mpy_macros_%s.mpy' % (script_dir, self.micro_name) )

                
                if node_count < node_len and parent_node_name == 'BoolOp' and node_name in ['list'] and parent_arg_name in ['test', None] and node0_name in ['Compare', 'Num']:
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
jlines = ''.join(lines)
jlines = re.sub(r'\r','',jlines)


uc = mpy2c( jlines, filename=file, chip_id=chip_id, hfile=hfile )


#uc.write_toks()

fileop = '%s.c' % fileroot
uc.write_op( file=fileop)

if not debug: 
    print 'mpy2c completed'