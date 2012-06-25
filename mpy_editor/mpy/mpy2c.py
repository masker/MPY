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
    def __init__(self, code, full_conversion=True, filename=None ):
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

        if full_conversion:
            self.micro_name = None        


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
 
        self.code_ast = ast.parse(code)
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
        

        self.walk_node( None, self.code_ast, None, None, None, 'TOP', filename=filename)  
                
        
        if full_conversion:
            self.setup_standard_variables_list()        
            
        self.convert_for_statements()
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
    def setup_standard_variables_list(self):

        self.standard_var_list = [ 'WDTCTL', 'WDTPW', 'WDTHOLD', 
        'CCTL1', 'CCR0', 'CCR1', 'CCR1', 'TACTL', 'TAR', 
        'TA0CCTL0', 'TA0CCTL1', 'TA0CCTL2', 'TA0CCR0', 'TA0CCR1', 'TA0CCR2', 'TA0CTL', 'TA0R', 
        'TA1CCTL0', 'TA1CCTL1', 'TA1CCTL2', 'TA1CCR0', 'TA1CCR1', 'TA1CCR2', 'TA1CTL', 'TA1R',
        'CACTL1', 'CACTL2', 'MC_1',
        'ADC10SHT_0', 'ADC10SHT_1', 'ADC10SHT_2', 'ENC', 'ADC10ON', 
        'ADC10CTL0', 'ADC10CTL1', 'ADC10AE0', 'ADC10MEM', 
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
                opstr += '\n'
                opstr += '  ' * t[6]
            lineno = t[4]
            
            
            # Put a space after the element, but not if the element ends with a \n 
            if len(t[0]) > 0 and t[0][-1] != '\n':
                suffix = ' '
            else:
                suffix = ''
                
            opstr += '%s%s' % (t[0], suffix)

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
        
        # Look for all elements where the vardef is True
        # and add the element text to the var_d dict
        for t in self.op:
            if t[1] == True:
                scope = t[2]
                if scope not in self.var_d:
                    self.var_d[scope] = {}
                if t[0] not in self.standard_var_list:
                    # to start lets assume that 'all' variables are int's
                    # this will be upgraded later to add strings and lists (hopefully)
                    #                             typename  done_flag
                    if self.is_var_num_str( t[0] ) == 'variable':
                        self.var_d[scope][ t[0] ]  = [ 'int',    None ]
#                    self.var_d[scope][ t[0] ]  = [ 'unsigned int',    None ]
                
        opn = []
        
                
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
                if self.var_d[scope][v][1] == None:
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
                    print 'found body_start for ', scope
                if scope in self.var_d:
                    for v in self.var_d[scope]:
                    
                        # Skip this variable definition if a global ('main') variable of the same name has been defined 
                        if scope != 'main' and v in  self.var_d['main']:
                            continue
                    
                        typ = self.var_d[scope][v][0]
                        if self.var_d[scope][v][1] == None:
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
    def replace_define_micro(self):
        '''Look for the define_micro_() If found then replace the call with 
            #include <io.h>
            #include "msp430g2231.h"
        '''

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
                self.add_element_opn( opn, t,  '#include "%s.h"\n' % micro_name )
                
                file = os.path.join( script_dir, 'mpy_functions.c' ) 
                self.add_element_opn( opn, t,  '#include "%s"\n' % file ) 





                print '%s  %s' % ( '@@MMCU@@:', micro_name )


        if replace_state != 'done':
            print "*** ERROR *** (mpy2c failed) define_micro line missing. eg. define_micro('msp430g2553')"

 
        self.op = opn    


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

                
            if t[5] in ['body_end', 'define_micro_end'] and idx < len(self.op) - 3:
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
                t[4] = main_insert_tok[4] - 1
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
                t[4] = main_insert_tok[4] - 1
                t[6] = 0
                t[0] = ''
                t[5] = 'body_start'
                opn.append(t)
                t = main_insert_tok[:]
                t[2] = 'main'
                t[4] = main_insert_tok[4] - 1
                t[6] = indent                
                t[0] = '\n'
                t[5] = ''
                opn.append(t)
                t[2] = 'main'
                t[4] = main_insert_tok[4] - 1
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
                
                duc = mpy2c( mpy_value_sub, full_conversion=False)
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
        for i in range(len(self.op)):

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
                        
                    if not line_offset: 
                        line_offset = linenum_start
                    tr[4] =  linenum_start
                    tr[6] =  indent
                    tr[2] =  scope
                    
                    vns =  self.is_var_num_str(tr[0], tr[7])
                    if vns == 'variable':
                        tr[1] = True
 
                    opn.append(tr)
                      
                params_in_code = None
                 
                if params_in_prototype != None:
                    end_i = end_of_call_idx          
            else:
              if i >= end_i:  
                opn.append(t)
                
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
        
        uc_inc = mpy2c( jlines, filename=fullfile , full_conversion=False)
        
        self.op.extend( uc_inc.op )
    
        self.add_marker( 'INCLUDE_%s  end' % file )

        
    ########################################################################    
    def walk_node( self, parent_node_name, node,  parent_arg_name, arg_name, first_node_name, node_or_field, filename=None):
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


        if debug : print '(walk_node) ', pfx, node_or_field, parent_node_name, node_name, parent_arg_name, arg_name, node0_name, first_node_name, node, typ




        # Update the scope
        if parent_node_name == 'FunctionDef' and node_name == 'str' and arg_name == 'name':
            scope      = node
            self.scope = node

        if node_name == 'FunctionDef':
            self.add_marker('FunctionDef')


        ##### mark the element as a variable ######
        if node_name == 'str' and parent_arg_name in [None, 'target', 'value'] and arg_name == 'id':
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

        if parent_node_name in ['Call', ] and node_name == 'Name':
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
            

        
        ######  RECURSION  LOOPS  ##############################
        
#        pfx = '.   ' * self.level  
        
        if isinstance( node, types.ListType ):
            done = False
            node_len = len(node)
            node_count = 1
            for nd in node:
 #                           parent_node_name, node,  parent_arg_name, arg_name, first_node_name, node_or_field):
                self.walk_node(  node_name,     nd,      arg_name,       None,   parent_node_name, 'NOD', filename=filename )

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
                    self.walk_node(  node_name , field[1],  arg_name,     field[0], first_node_nm, 'FLD', filename=filename)
                     
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

        # when we encounter the define_micro command then we will be adding the main() function
        if self.define_micro_flag == True and node_name == 'str' and self.scope == '__top_level__':
            self.micro_name = node.lower()


        # when we encounter the define_micro command then we will be adding the main() function
        if parent_arg_name in ['func'] and node == 'define_micro' and self.scope == '__top_level__':
            self.define_micro_flag = True
            
        
        self.level -= 1

#########################################################################

     

debug = False
if len(sys.argv) > 2:
    debug = sys.argv[2]
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


uc = mpy2c( jlines, filename=file )


#uc.write_toks()

fileop = '%s.c' % fileroot
uc.write_op( file=fileop)

