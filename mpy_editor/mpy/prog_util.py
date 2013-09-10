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
#     along with mpyEditor.  If not, see <http://www.gnu.org/licenses/>.
#
#     (C) Copyright 2013 Mike Asker    mike.asker@gmail.com
#
###########################################################################
#
#   prog_util.py
#
# This is a collection of functions used by the prog and flash modules.
#
############################################################################
  

import subprocess
import sys
import os
import shlex
import time
import re
import glob


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



###############################################################################
def make_include_str(  search_dirs, sub_dirs, file_exts ):
    '''Function to make up an gcc Include option string containing all the
    directories that contain files with file_exts.
    eg. "-I c:\dir1 -I c:\dir2"

    @param search_dirs:   List of root directory names
    @param sub_dirs:      List of subdirectories appended to the search_dirs
    @param file_exts:     List of different file extentions to search
    @return  opstr:       Include format string containing all directories
                              where files were found with matching extentions
    '''

    ilist = []
    for d in search_dirs:
        for sd in sub_dirs:
            for ext in file_exts:
                if sd == '.':
                   files = glob.glob( os.path.join( d, '*' + ext ))
                   dsd = d
                else:
                   files = glob.glob( os.path.join( d, sd, '*' + ext ))
                   dsd = os.path.join( d, sd )
                if len(files) > 0 and dsd not in ilist:
                    ilist.append(dsd)

    opstr = ''
    for i in ilist:
        opstr +=  r' -I "%s"' % i
    return opstr


###############################################################################
def get_src_if_more_recent( src_file, search_dirs, sub_dirs ):
    '''Function that finds the souce file in the search_directories and the
    sub_dirs and returns the full file path for the file. Returns None if not
    or if there is a more recent file.o file in the same directory.
    @param   file:  filename to be searched in the search_dirs and sub_dirs
    @param search_dirs:   List of root directory names to be searched
    @param sub_dirs:      List of subdirectories appended to the search_dirs
    @returns  fullfile:   Full path filename containing the found file
                            Returns None if not found. Or if the file.o exists
                            which is more recent than the file
    '''

    fnd_sfile = find_file(src_file, search_dirs, sub_dirs)

    fnd_sfile_more_recent = 0
    fnd_ofile = []
    if fnd_sfile:
        ofile = os.path.splitext(fnd_sfile)[0] + '.o'
        fnd_ofile = glob.glob( ofile )
        if len(fnd_ofile) == 1:
            fnd_sfile_more_recent = more_recent( fnd_ofile[0], fnd_sfile )

    # If the source is more recent, or we cannot find the .o file
    # then return the full source name so that it can be compiled
    # (or whatever else we want to do with it)
    if fnd_sfile_more_recent or len(fnd_ofile) == 0:
        return fnd_sfile
    else:
        return None

###############################################################################
def more_recent( file0, file1 ):
    '''Find the file with the latest modified timestamp.
    @param   file0:   The first file to be compared
    @param   file1:   The second file to be compared
    @return  file1_more_recent:  Returns 1 if file1 is more recent, or if file0
                   does not exist.
    '''

    m0 = os.path.getmtime(file0)
    m1 = os.path.getmtime(file1)



    if m0 > m1:
        return 0
    else:
        return 1


###############################################################################
def find_file( file, search_dirs, sub_dirs ):
    '''Function that finds the file in the list of search_dirs and sub dirs.
    If multiple matches are found only the first one is returned.
    @param  file:   File to be searched
    @param search_dirs:   List of root directory names to be searched
    @param sub_dirs:      List of subdirectories appended to the search_dirs
    @returns  fullfile:   Full path filename containing the found file
                            Returns None if not found
    '''

    for d in search_dirs:
        for sd in sub_dirs:
             if sd == '.':
                 files = glob.glob( os.path.join( d, file ))
             else:
                 files = glob.glob( os.path.join( d, sd, file ))
             if len(files) > 0:
                break
        if len(files) > 0:
             break

    if len(files) > 0:
        return files[0]
    else:
        return None

