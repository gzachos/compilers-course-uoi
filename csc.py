#!/usr/bin/env python3


#+-----------------------------------------------------------------------+
#|       Copyright (C) 2017 George Z. Zachos, Andrew Konstantinidis      |
#+-----------------------------------------------------------------------+
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Contact Information:
# Name: George Z. Zachos
# Email: gzzachos_at_gmail.com


import sys, getopt, os
from enum import Enum
from collections import OrderedDict

__version__='1.0.0'


##############################################################
#                                                            #
#                     Class definitions                      #
#                                                            #
##############################################################


class clr:
    GRN    = '\033[92m'
    WRN    = '\033[95m'
    ERR    = '\033[91m'
    END    = '\033[0m'
    BLD    = '\033[1m'
    UNDRLN = '\033[4m'


class TokenType(Enum):
    IDENT      = 0
    NUMBER     = 1
    # Brackets
    LPAREN     = 2
    RPAREN     = 3
    LBRACE     = 4
    RBRACE     = 5
    LBRACKET   = 6
    RBRACKET   = 7
    # Other punctuation marks
    COMMA      = 8
    COLON      = 9
    SEMICOLON  = 10
    # Relational Operators
    LSS        = 11
    GTR        = 12
    LEQ        = 13
    GEQ        = 14
    EQL        = 15
    NEQ        = 16
    # Assignment
    BECOMES    = 17
    # Arithmetic Operators
    PLUS       = 18
    MINUS      = 19
    TIMES      = 20
    SLASH      = 21
    # Keywords
    ANDSYM     = 22
    NOTSYM     = 23
    ORSYM      = 24
    DECLARESYM = 25
    ENDDECLSYM = 26
    DOSYM      = 27
    IFSYM      = 28
    ELSESYM    = 29
    EXITSYM    = 30
    PROCSYM    = 31
    FUNCSYM    = 32
    PRINTSYM   = 33
    CALLSYM    = 34
    INSYM      = 35
    INOUTSYM   = 36
    SELECTSYM  = 37
    PROGRAMSYM = 38
    RETURNSYM  = 39
    WHILESYM   = 40
    DEFAULTSYM = 41
    # EOF
    EOF        = 42


# What the lexical analyzer returns to the syntax analyzer
#   tktype : TokenType object
#   tkval  : token value
#   tkl    : token start line number
#   tkc    : token start character number
class Token():
    def __init__(self, tktype, tkval, tkl, tkc):
        self.tktype, self.tkval, self.tkl, self.tkc = tktype, tkval, tkl, tkc

    def __str__(self):
        return  '(' + str(self.tktype)+ ', \'' + str(self.tkval) \
            + '\', ' + str(self.tkl) + ', ' + str(self.tkc) + ')'


# The rest of the classes consist the data model required for
# the implementation of the symbol table.


class Quad():
    def __init__(self, label, op, arg1, arg2, res):
        self.label, self.op, self.arg1, self.arg2 = label, op, arg1, arg2
        self.res = res

    def __str__(self):
        return '(' + str(self.label) + ': ' + str(self.op)+ ', ' + \
            str(self.arg1) + ', ' + str(self.arg2) + ', ' + str(self.res) + ')'

    def tofile(self):
        return str(self.label) + ': (' + str(self.op)+ ', ' + \
            str(self.arg1) + ', ' + str(self.arg2) + ', ' + str(self.res) + ')'


class Scope():
    def __init__(self, nested_level=0, enclosing_scope=None):
        self.entities, self.nested_level = list(), nested_level
        self.enclosing_scope = enclosing_scope
        self.tmp_offset = 12

    def addEntity(self, entity):
        self.entities.append(entity)

    def get_offset(self):
        retval = self.tmp_offset
        self.tmp_offset += 4
        return retval

    def __str__(self):
        return self.__repr__() + ': (' + str(self.nested_level) + ', ' + \
            self.enclosing_scope.__repr__() + ')'


class Argument():
    def __init__(self, par_mode, next_arg=None):
        self.par_mode = par_mode
        self.next_arg = next_arg

    def set_next(self, next_arg):
        self.next_arg = next_arg

    def __str__(self):
        return self.__repr__() + ': (' + self.par_mode + ',\t' + \
            self.next_arg.__repr__() + ')'


class Entity():
    def __init__(self, name, etype):
        self.name, self.etype, self.next = name, etype, None

    def __str__(self):
        return self.etype + ': ' + self.name


class Variable(Entity):
    def __init__(self, name, offset=-1):
        super().__init__(name, "VARIABLE")
        self.offset = offset

    def __str__(self):
        return super().__str__() + ', offset: ' + \
            str(self.offset)


class Function(Entity):
    def __init__(self, name, ret_type, start_quad=-1):
        super().__init__(name, "FUNCTION")
        self.ret_type, self.start_quad = ret_type, start_quad
        self.args, self.framelength = list(), -1

    def add_arg(self, arg):
        self.args.append(arg)

    def set_framelen(self, framelength):
        self.framelength = framelength

    def set_start_quad(self, start_quad):
        self.start_quad = start_quad

    def __str__(self):
        return super().__str__() + ', retv: ' + self.ret_type \
            + ', squad: ' + str(self.start_quad) + ', framelen: ' \
            + str(self.framelength)


class Parameter(Entity):
    def __init__(self, name, par_mode, offset=-1):
        super().__init__(name, "PARAMETER")
        self.par_mode, self.offset = par_mode, offset

    def __str__(self):
        return super().__str__() + ', mode: ' + self.par_mode \
            + ', offset: ' + str(self.offset)


class TmpVar(Entity):
    def __init__(self, name, offset=-1):
        super().__init__(name, "TMPVAR")
        self.offset = offset

    def __str__(self):
        return super().__str__() + ', offset: ' + str(self.offset)


##############################################################
#                                                            #
#         Global data declarations and definitions           #
#                                                            #
##############################################################

lineno   = charno = -1  # Current line and character number of input file.
token    = Token(None, None, None, None)
# in_function, in_dowhile, exit_dowhile and have_return are array
# structures and each element corresponds to a nested level in case
# of curly-braced blocks and not function/procedure blocks.
in_function  = []    # currently inside a function (not procedure).
in_dowhile   = []    # currently inside a do-while statement.
exit_dowhile = []    # used to implement exit for a do-while statement.
have_return  = []    # have return statement at specific nested level.
have_subprog = False # True if nested functions are defined in user program.
nextlabel    = 0
tmpvars      = dict() # A dictionary holding temporary variable names
                      # used in intermediate code generation.
next_tmpvar  = 1      # Used to implement the naming convention of
                      # temporary variables.
quad_code    = list() # The main program equivalent in quadruples.
scopes       = list() # The list of currently 'active' scopes.
actual_pars  = list() # holds functions params as discovered
                      # while traversing intermediate code
main_programs_framelength = halt_label = -1
tokens       = {
    '(':          TokenType.LPAREN,
    ')':          TokenType.RPAREN,
    '{':          TokenType.LBRACE,
    '}':          TokenType.RBRACE,
    '[':          TokenType.LBRACKET,
    ']':          TokenType.RBRACKET,
    ',':          TokenType.COMMA,
    ':':          TokenType.COLON,
    ';':          TokenType.SEMICOLON,
    '<':          TokenType.LSS,
    '>':          TokenType.GTR,
    '<=':         TokenType.LEQ,
    '>=':         TokenType.GEQ,
    '=':          TokenType.EQL,
    '<>':         TokenType.NEQ,
    ':=':         TokenType.BECOMES,
    '+':          TokenType.PLUS,
    '-':          TokenType.MINUS,
    '*':          TokenType.TIMES,
    '/':          TokenType.SLASH,
    'and':        TokenType.ANDSYM,
    'not':        TokenType.NOTSYM,
    'or':         TokenType.ORSYM,
    'declare':    TokenType.DECLARESYM,
    'enddeclare': TokenType.ENDDECLSYM,
    'do':         TokenType.DOSYM,
    'if':         TokenType.IFSYM,
    'else':       TokenType.ELSESYM,
    'exit':       TokenType.EXITSYM,
    'procedure':  TokenType.PROCSYM,
    'function':   TokenType.FUNCSYM,
    'print':      TokenType.PRINTSYM,
    'call':       TokenType.CALLSYM,
    'in':         TokenType.INSYM,
    'inout':      TokenType.INOUTSYM,
    'select':     TokenType.SELECTSYM,
    'program':    TokenType.PROGRAMSYM,
    'return':     TokenType.RETURNSYM,
    'while':      TokenType.WHILESYM,
    'default':    TokenType.DEFAULTSYM,
    'EOF':        TokenType.EOF}


##############################################################
#                                                            #
#         Useful error/warning reporting functions           #
#                                                            #
##############################################################


# Print error message to stderr and exit.
def perror_exit(ec, *args, **kwargs):
    print('[' + clr.ERR + 'ERROR' + clr.END + ']', *args, file=sys.stderr, **kwargs)
    sys.exit(ec)


# Print error message to stderr.
def perror(*args, **kwargs):
    print('[' + clr.ERR + 'ERROR' + clr.END + ']', *args, file=sys.stderr, **kwargs)


# Print warning to stderr.
def pwarn(*args, **kwargs):
    print('[' + clr.WRN + 'WARNING' + clr.END + ']', *args, file=sys.stderr, **kwargs)


# Print line #lineno to stderr with character charno highlighted.
def perror_line(lineno, charno):
    currchar = infile.tell()
    infile.seek(0)
    for index, line in enumerate(infile):
        if index == lineno-1:
            print(" ", line.replace('\t', ' ').replace('\n', ''), file=sys.stderr)
            print(clr.GRN + " " * (charno + 1) + '^' + clr.END, file=sys.stderr)
    infile.seek(currchar)


# Print line #lineno to stderr with character charno
# highlighted and along with and error message. Finally exit.
def perror_line_exit(ec, lineno, charno, *args, **kwargs):
    print('[' + clr.ERR + 'ERROR' + clr.END + ']', clr.BLD + '%s:%d:%d:' %
        (infile.name, lineno, charno) + clr.END, *args, file=sys.stderr, **kwargs)
    currchar = infile.tell()
    infile.seek(0)
    for index, line in enumerate(infile):
        if index == lineno-1:
            print(" ", line.replace('\t', ' ').replace('\n', ''), file=sys.stderr)
            print(clr.GRN + " " * (charno + 1) + '^' + clr.END, file=sys.stderr)
    close_files()
    os.remove(int_file.name)
    os.remove(ceq_file.name)
    sys.exit(ec)


# Open files.
def open_files(input_filename, interm_filename, cequiv_filename, output_filename):
    global infile, int_file, ceq_file, outfile, lineno, charno
    lineno = 1
    charno = 0
    try:
        infile   = open(input_filename,  'r', encoding='utf-8')
        int_file = open(interm_filename, 'w', encoding='utf-8')
        ceq_file = open(cequiv_filename, 'w', encoding='utf-8')
        outfile  = open(output_filename, 'w', encoding='utf-8')
    except OSError as oserr:
        if oserr.filename != None:
            perror_exit(oserr.errno, oserr.filename + ':', oserr.strerror)
        else:
            perror_exit(oserr.errno, oserr)


# Close files.
def close_files():
    global infile
    infile.close()
    int_file.close()
    ceq_file.close()
    outfile.close()


##############################################################
#                                                            #
#           Lexical analyzer related functions               #
#                                                            #
##############################################################


# Perform lexical analysis
def lex():
    global lineno, charno

    buffer = []
    tkl = tkc = -1 # token start lineno, charno
    cc = cl = -1   # comment start lineno, charno
    state = 0      # Initial FSM state
    OK    = -2     # Final FSM state
    unget = False  # True if file pointer should be repositioned

    # Lexical analyzer's FSM implementation
    while state != OK:
        c = infile.read(1)
        buffer.append(c)
        charno += 1
        if state == 0:
            if c.isalpha():
                state = 1
            elif c.isdigit():
                state = 2
            elif c == '<':
                state = 3
            elif c == '>':
                state = 4
            elif c == ':':
                state = 5
            elif c == '\\':
                state = 6
            elif c in ('+', '-', '*', '/', '=', ',', ';', '{', '}', '(', ')', '[', ']'):
                state = OK
            elif c == '': # EOF
                state = OK
                return Token(TokenType.EOF, 'EOF', lineno, charno)
            elif c.isspace():
                state = 0
            else:
                perror_line_exit(2, lineno, charno, 'Invalid character \'%c\' in program' % c)
        elif state == 1:
            if not c.isalnum():
                unget = True
                state = OK
        elif state == 2:
            if not c.isdigit():
                if c.isalpha():
                    perror_line_exit(2, lineno, charno - len(''.join(buffer)) + 1,
                        'Variable names should begin with alphabetic character')
                unget = True
                state = OK
        elif state == 3:
            if c != '=' and c != '>':
                unget = True
            state = OK
        elif state == 4:
            if c != '=':
                unget = True
            state = OK
        elif state == 5:
            if c != '=':
                unget = True
            state = OK
        elif state == 6:
            if c == '*':
                state = 7
                cl = lineno
                cc = charno - 1
            else:
                perror_line_exit(2, lineno, charno, 'Expected \'*\' after \'\\\'')
        elif state == 7:
            if c == '': # EOF
                perror_line_exit(2, cl, cc, 'Unterminated comment')
            elif c == '*':
                state = 8
        elif state == 8:
            if c == '\\':
                del buffer[:]
                state = 0
            else:
                state = 7
        if state == OK:
            tkl = lineno
            tkc = charno - len(''.join(buffer)) + 1
        if c.isspace():
            del buffer[-1]
            unget = False
            if c == '\n':
                lineno += 1
                charno = 0

    # Unget last character read
    if unget == True:
        del buffer[-1]
        if c != '': # EOF (special case)
            infile.seek(infile.tell() - 1)
        charno -= 1

    # Empty buffer and return the Token object
    buff_cont = ''.join(buffer)
    if buff_cont not in tokens.keys():
        if buff_cont.isdigit():
            retval = Token(TokenType.NUMBER, buff_cont, tkl, tkc)
        else:
            retval = Token(TokenType.IDENT, buff_cont[:30], tkl, tkc)
    else:
        retval = Token(tokens[buff_cont], buff_cont, tkl, tkc)
    del buffer[:]
    return retval


##############################################################
#                                                            #
#           Intermediate code related functions              #
#                                                            #
##############################################################


def next_quad():
    return nextlabel


def gen_quad(op=None, arg1='_', arg2='_', res='_'):
    global nextlabel
    label = nextlabel
    nextlabel += 1
    newquad  = Quad(label, op, arg1, arg2, res)
    quad_code.append(newquad)


def new_temp():
    global tmpvars, next_tmpvar
    key = 'T_'+str(next_tmpvar)
    tmpvars[key] = None
    offset = scopes[-1].get_offset()
    scopes[-1].addEntity(TmpVar(key, offset))
    next_tmpvar += 1
    return key


def empty_list():
    return list()


def make_list(label):
    newlist = list()
    newlist.append(label)
    return newlist


def merge(list1, list2):
    return list1 + list2


def backpatch(somelist, res):
    global quad_code
    for quad in quad_code:
        if quad.label in somelist:
            quad.res = res


# Generate a file containing the intermediate code
# of the user program.
def generate_int_code_file():
    for quad in quad_code:
        int_file.write(quad.tofile() + '\n')
    int_file.close()


# A naive way to find which variables should be declared.
def find_var_decl(quad):
    vars = dict()
    index = quad_code.index(quad) + 1
    while True:
        q = quad_code[index]
        if q.op == 'end_block':
            break
        if q.arg2 not in ('CV', 'REF', 'RET') and q.op != 'call':
            if isinstance(q.arg1, str):
                vars[q.arg1] = 'int'
            if isinstance(q.arg2, str):
                vars[q.arg2] = 'int'
            if isinstance(q.res, str):
                vars[q.res] = 'int'
        index += 1
    if '_' in vars:
        del vars['_']
    return OrderedDict(sorted(vars.items()))


# Transform variable declarations to ANSI C equivalent.
def transform_decls(vars):
    flag = False
    retval = '\n\tint '
    for var in vars:
        flag = True
        retval += var + ', '
    if flag == True:
        return retval[:-2] + ';'
    else:
        return ''


# Transform a quad to ANSI C code.
def transform_to_c(quad):
    addlabel = True
    if quad.op == 'jump':
        retval = 'goto L_' + str(quad.res) + ';'
    elif quad.op in ('=', '<>', '<', '<=', '>', '>='):
        op = quad.op
        if op == '=':
            op = '=='
        elif op == '<>':
            op = '!='
        retval = 'if (' + str(quad.arg1) + ' ' + op + ' ' + \
            str(quad.arg2) + ') goto L_' + str(quad.res) + ';'
    elif quad.op == ':=':
        retval = quad.res + ' = ' + str(quad.arg1) + ';'
    elif quad.op in ('+', '-', '*', '/'):
        retval = quad.res + ' = ' + str(quad.arg1) + ' ' + \
            str(quad.op) + ' ' + str(quad.arg2) + ';'
    elif quad.op == 'out':
        retval = 'printf("%d\\n", ' + str(quad.arg1) + ');'
    elif quad.op == 'retv':
        retval = 'return (' + str(quad.arg1) + ');'
    elif quad.op == 'begin_block':
        addlabel = False
        if quad.arg1 == mainprog_name:
            retval = 'int main(void)\n{'
        else: # Should never reach else.
            retval = 'int ' + quad.arg1 + '()\n{'
        vars = find_var_decl(quad)
        retval += transform_decls(vars)
        retval += '\n\tL_' + str(quad.label) + ':'
    elif quad.op == 'call':
        # Should never reach this line.
        retval = quad.arg1 + '();'
    elif quad.op == 'end_block':
        addlabel = False
        retval = '\tL_' + str(quad.label) + ': {}\n'
        retval += '}\n'
    elif quad.op == 'halt':
        retval = 'return 0;' # change to exit() if arbitrary
                             # halt statements are enabled
                             # at a later time.
    else:
        return None
    if addlabel == True:
        retval = '\tL_' + str(quad.label) + ': ' + retval
    return retval


# Generate a file containing the ANSI C equivalent code
# of intermediate code. This file is ready to compile.
def generate_c_code_file():
    ceq_file.write('#include <stdio.h>\n\n')
    ceq_file.write('/* This file was automatically generated by:\n')
    ceq_file.write(' *     CiScal Compiler ' + __version__ + '\n')
    ceq_file.write(' */\n\n')
    for quad in quad_code:
        tmp = transform_to_c(quad)
        if tmp != None:
            ceq_file.write(tmp + '\n')
    ceq_file.close()


##############################################################
#                                                            #
#             Symbol table related functions                 #
#                                                            #
##############################################################


# Add a new scope.
def add_new_scope():
    enclosing_scope = scopes[-1]
    curr_scope = Scope(enclosing_scope.nested_level + 1, enclosing_scope)
    scopes.append(curr_scope)


# Print current scope and its enclosing ones.
def print_scopes():
    print('* main scope\n|')
    for scope in scopes:
        level = scope.nested_level + 1
        print('    ' * level + str(scope))
        for entity in scope.entities:
            print('|    ' * level + str(entity))
            if isinstance(entity, Function):
                for arg in entity.args:
                    print('|    ' * level + '|    ' + str(arg))
    print('\n')


# Add a new function entity.
def add_func_entity(name):
    # Function declarations are on the enclosing scope of
    # the current scope.
    nested_level = scopes[-1].enclosing_scope.nested_level
    if not unique_entity(name, "FUNCTION", nested_level):
        perror_line_exit(5, token.tkl, token.tkc,
            'Redefinition of \'%s\'' % name)
    if in_function[-1] == True:
        ret_type = "int"
    else:
        ret_type = "void"
    scopes[-2].addEntity(Function(name, ret_type))


# Update the start quad label of a function entity.
def update_func_entity_quad(name):
    start_quad = next_quad()
    if name == mainprog_name:
        return start_quad
    func_entity = search_entity(name, "FUNCTION")[0]
    func_entity.set_start_quad(start_quad)
    return start_quad


# Update the framelength of a function entity.
def update_func_entity_framelen(name, framelength):
    global main_programs_framelength
    if name == mainprog_name:
        main_programs_framelength = framelength
        return
    func_entity = search_entity(name, "FUNCTION")[0]
    func_entity.set_framelen(framelength)


# Add a new parameter entity.
def add_param_entity(name, par_mode):
    nested_level = scopes[-1].nested_level
    par_offset   = scopes[-1].get_offset()
    if not unique_entity(name, "PARAMETER", nested_level):
        perror_line_exit(5, token.tkl, token.tkc,
            'Redefinition of \'%s\'' % name)
    scopes[-1].addEntity(Parameter(name, par_mode, par_offset))


# Add a new variable entity.
def add_var_entity(name):
    nested_level = scopes[-1].nested_level
    var_offset   = scopes[-1].get_offset()
    if not unique_entity(name, "VARIABLE", nested_level):
        perror_line_exit(5, token.tkl, token.tkc,
            'Redefinition of \'%s\'' % name)
    if var_is_param(name, nested_level):
        perror_line_exit(5, token.tkl, token.tkc,
            '\'%s\' redeclared as different kind of symbol' % name)
    scopes[-1].addEntity(Variable(name, var_offset))


# Add a new function argument to a given function.
def add_func_arg(func_name, par_mode):
    if (par_mode == 'in'):
        new_arg = Argument('CV')
    else:
        new_arg = Argument('REF')
    func_entity = search_entity(func_name, "FUNCTION")[0]
    if func_entity == None:
        perror_line_exit(5, token.tkl, token.tkc,
            'No definition of \'%s\' was not found' % func_name)
    if func_entity.args != list():
        func_entity.args[-1].set_next(new_arg)
    func_entity.add_arg(new_arg)


# Search for an entity named 'name' of type 'etype'.
def search_entity(name, etype):
    if scopes == list():
        return
    tmp_scope = scopes[-1]
    while tmp_scope != None:
        for entity in tmp_scope.entities:
            if entity.name == name and entity.etype == etype:
                return entity, tmp_scope.nested_level
        tmp_scope = tmp_scope.enclosing_scope


# Search for an entity named 'name'.
def search_entity_by_name(name):
    if scopes == list():
        return
    tmp_scope = scopes[-1]
    while tmp_scope != None:
        for entity in tmp_scope.entities:
            if entity.name == name:
                return entity, tmp_scope.nested_level
        tmp_scope = tmp_scope.enclosing_scope


# Check if entity named 'name' of type 'etype' at nested level
# 'nested_level' is redefined.
def unique_entity(name, etype, nested_level):
    if scopes[-1].nested_level < nested_level:
        return
    scope = scopes[nested_level]
    list_len = len(scope.entities)
    for i in range(list_len):
        for j in range(list_len):
            e1 = scope.entities[i]
            e2 = scope.entities[j]
            if e1.name == e2.name and e1.etype == e2.etype \
                    and e1.name == name and e1.etype == etype:
                return False
    return True


# Check if a variable entity named 'name' already exists
# as a parameter entity.
def var_is_param(name, nested_level):
    if scopes[-1].nested_level < nested_level:
        return
    scope = scopes[nested_level]
    list_len = len(scope.entities)
    for i in range(list_len):
        e = scope.entities[i]
        if e.etype == "PARAMETER" and e.name == name:
            return True
    return False


##############################################################
#                                                            #
#               Final code related functions                 #
#                                                            #
##############################################################


# Loads in $t0 the address of a non-local variable
def gnvlcode(v):
    try:
        tmp_entity, elevel  = search_entity_by_name(v)
    except:
        perror_exit(7, 'Undeclared variable:', v)
    if tmp_entity.etype == 'FUNCTION':
        perror_exit(7, 'Undeclared variable:', v)
    curr_nested_level   = scopes[-1].nested_level
    outfile.write('    lw      $t0, -4($sp)\n')
    n = curr_nested_level - elevel - 1
    while  n > 0:
        outfile.write('    lw      $t0, -4($t0)\n')
        n -= 1
    outfile.write('    addi    $t0, $t0, -%d\n' % tmp_entity.offset)


# Load immediate or data from memory to register $t{r}
def loadvr(v, r):
    if str(v).isdigit():
        outfile.write('    li      $t%s, %d\n' % (r, v))
    else:
        try:
            tmp_entity, elevel = search_entity_by_name(v)
        except:
            perror_exit(7, 'Undeclared variable:', v)
        curr_nested_level  = scopes[-1].nested_level
        if tmp_entity.etype == 'VARIABLE' and elevel == 0:
            outfile.write('    lw      $t%s, -%d($s0)\n' % (r, tmp_entity.offset))
        elif (tmp_entity.etype == 'VARIABLE' and \
                elevel == curr_nested_level) or \
                (tmp_entity.etype == 'PARAMETER' and tmp_entity.par_mode == 'in' \
                and elevel == curr_nested_level) or \
                (tmp_entity.etype == 'TMPVAR'):
            outfile.write('    lw      $t%s, -%d($sp)\n' % (r, tmp_entity.offset))
        elif tmp_entity.etype == 'PARAMETER' and tmp_entity.par_mode == 'inout' \
                and elevel == curr_nested_level:
            outfile.write('    lw      $t0, -%d($sp)\n' % tmp_entity.offset)
            outfile.write('    lw      $t%s, 0($t0)\n' % r)
        elif (tmp_entity.etype == 'VARIABLE' and \
                elevel < curr_nested_level) or \
                (tmp_entity.etype == 'PARAMETER' and tmp_entity.par_mode == 'in' \
                and elevel < curr_nested_level):
            gnvlcode(v)
            outfile.write('    lw      $t%s, 0($t0)\n' % r)
        elif tmp_entity.etype == 'PARAMETER' and tmp_entity.par_mode == 'inout' \
                and elevel < curr_nested_level:
            gnvlcode(v)
            outfile.write('    lw      $t0, 0(%t0)\n')
            outfile.write('    lw      $t%s, 0($t0)\n' % r)
        else:
            perror_exit(6, 'loadvr loads an immediate or data from memory'
                        'to a register')


# Store the contents of register $t{r} to the memory allocated for variable v
def storerv(r, v):
    try:
        tmp_entity, elevel = search_entity_by_name(v)
    except:
        perror_exit(7, 'Undeclared variable:', v)
    curr_nested_level  = scopes[-1].nested_level
    if tmp_entity.etype == 'VARIABLE' and elevel == 0:
        outfile.write('    sw      $t%s, -%d($s0)\n' % (r, tmp_entity.offset))
    elif (tmp_entity.etype == 'VARIABLE' and \
            elevel == curr_nested_level) or \
            (tmp_entity.etype == 'PARAMETER' and tmp_entity.par_mode == 'in' \
            and elevel == curr_nested_level) or \
            (tmp_entity.etype == 'TMPVAR'):
        outfile.write('    sw      $t%s, -%d($sp)\n' % (r, tmp_entity.offset))
    elif tmp_entity.etype == 'PARAMETER' and tmp_entity.par_mode == 'inout' \
            and elevel == curr_nested_level:
        outfile.write('    lw      $t0, -%d($sp)\n' % tmp_entity.offset)
        outfile.write('    sw      $t%s, 0($t0)\n' % r)
    elif (tmp_entity.etype == 'VARIABLE' and \
            elevel < curr_nested_level) or \
            (tmp_entity.etype == 'PARAMETER' and tmp_entity.par_mode == 'in' \
            and elevel < curr_nested_level):
        gnvlcode(v)
        outfile.write('    sw      $t%s, 0($t0)\n' % r)
    elif tmp_entity.etype == 'PARAMETER' and tmp_entity.par_mode == 'inout' \
            and elevel < curr_nested_level:
        gnvlcode(v)
        outfile.write('    lw      $t0, 0(%t0)\n')
        outfile.write('    sw      $t%s, 0($t0)\n' % r)
    else:
        perror_exit(6, 'storerv stores the contents of a register to memory')


def gen_mips_asm(quad, block_name):
    global actual_pars
    if str(quad.label) == '0':
        outfile.write(' ' * 70) # Will be later overwritten
    outfile.write('\nL_' + str(quad.label) + ':   #' + quad.tofile() + '\n')
    csc_relop = ('=', '<>', '<', '<=', '>', '>=')
    asm_relop = ('beq', 'bne', 'blt', 'ble', 'bgt', 'bge')
    csc_op    = ('+', '-', '*', '/')
    asm_op    = ('add', 'sub', 'mul', 'div')
    if quad.op == 'jump':
        outfile.write('    j       L_%d\n' % quad.res)
    elif quad.op in csc_relop:
        relop = asm_relop[csc_relop.index(quad.op)]
        loadvr(quad.arg1, '1')
        loadvr(quad.arg2, '2')
        outfile.write('    %s     $t1, $t2, L_%d\n' % (relop, quad.res))
    elif quad.op == ':=':
        loadvr(quad.arg1, '1')
        storerv('1', quad.res)
    elif quad.op in csc_op:
        op = asm_op[csc_op.index(quad.op)]
        loadvr(quad.arg1, '1')
        loadvr(quad.arg2, '2')
        outfile.write('    %s     $t1, $t1, $t2\n' % op)
        storerv('1', quad.res)
    elif quad.op == 'out':
        loadvr(quad.arg1, '9')
        outfile.write('    li      $v0, 1\n')
        outfile.write('    add     $a0, $zero, $t9\n')
        outfile.write('    syscall   # service code 1: print integer\n')
        outfile.write('    la      $a0, newline\n')
        outfile.write('    li      $v0, 4\n')
        outfile.write('    syscall   # service code 4: print (a null terminated) string\n')
    elif quad.op == 'retv':
        loadvr(quad.arg1, '1')
        outfile.write('    lw      $t0, -8($sp)\n')
        outfile.write('    sw      $t1, 0($t0)\n')
        # Actually return to caller; just like end_block case.
        outfile.write('    lw      $ra, 0($sp)\n')
        outfile.write('    jr      $ra\n')
    elif quad.op == 'halt':
        outfile.write('    li      $v0, 10   # service code 10: exit\n')
        outfile.write('    syscall\n')
    elif quad.op == 'par':
        if block_name == mainprog_name:
            caller_level = 0
            framelength = main_programs_framelength
        else:
            caller_entity, caller_level = search_entity(block_name, 'FUNCTION')
            framelength = caller_entity.framelength
        if actual_pars == []:
            outfile.write('    addi    $fp, $sp, -%d\n' % framelength)
        actual_pars.append(quad)
        param_offset = 12 + 4 * actual_pars.index(quad)
        if quad.arg2 == 'CV':
            loadvr(quad.arg1, '0')
            outfile.write('    sw      $t0, -%d($fp)\n' % param_offset)
        elif quad.arg2 == 'REF':
            try:
                var_entity, var_level = search_entity_by_name(quad.arg1)
            except:
                perror_exit(7, 'Undeclared variable:', quad.arg1)
            if caller_level == var_level:
                if var_entity.etype == 'VARIABLE' or \
                        (var_entity.etype == 'PARAMETER' and \
                        var_entity.par_mode == 'in'):
                    outfile.write('    addi    $t0, $sp, -%s\n' % var_entity.offset)
                    outfile.write('    sw      $t0, -%d($fp)\n' % param_offset)
                elif var_entity.etype == 'PARAMETER' and \
                        var_entity.par_mode == 'inout':
                    outfile.write('    lw      $t0, -%d($sp)\n' % var_entity.offset)
                    outfile.write('    sw      $t0, -%d($fp)\n' % param_offset)
            else:
                if var_entity.etype == 'VARIABLE' or \
                        (var_entity.etype == 'PARAMETER' and \
                        var_entity.par_mode == 'in'):
                    gnvlcode(quad.arg1)
                    outfile.write('    sw      $t0, -%d($fp)\n' % param_offset)
                elif var_entity.etype == 'PARAMETER' and \
                        var_entity.par_mode == 'inout':
                    gnvlcode(quad.arg1)
                    outfile.write('    lw      $t0, 0($t0)\n')
                    outfile.write('    sw      $t0, -%d($fp)\n' % param_offset)
        elif quad.arg2 == 'RET':
            try:
                var_entity, var_level = search_entity_by_name(quad.arg1)
            except:
                perror_exit(7, 'Undeclared variable:', quad.arg1)
            outfile.write('    addi    $t0, $sp, -%d\n' % var_entity.offset)
            outfile.write('    sw      $t0, -8($fp)\n')
    elif quad.op == 'call':
        if block_name == mainprog_name:
            caller_level = 0
            framelength = main_programs_framelength
        else:
            caller_entity, caller_level = search_entity(block_name, 'FUNCTION')
            framelength = caller_entity.framelength
        try:
            callee_entity, callee_level = search_entity(quad.arg1, 'FUNCTION')
        except:
            perror_exit(7, 'Undefined function/procedure:', quad.arg1)
        check_subprog_args(callee_entity.name)
        if caller_level == callee_level:
            outfile.write('    lw      $t0, -4($sp)\n')
            outfile.write('    sw      $t0, -4($fp)\n')
        else:
            outfile.write('    sw      $sp, -4($fp)\n')
        outfile.write('    addi    $sp, $sp, -%d\n' % framelength)
        outfile.write('    jal     L_%s\n' % str(callee_entity.start_quad))
        outfile.write('    addi    $sp, $sp, %d\n' % framelength)
    elif quad.op == 'begin_block':
        outfile.write('    sw      $ra, 0($sp)\n')
        if block_name == mainprog_name:
            outfile.seek(0,0)   # Go to the beginning of the output file
            outfile.write('\n')
            outfile.write('    .globl L_%d\n' % quad.label)
            outfile.write('    .text\n\n')
            outfile.write('    j       L_%d   # main program\n' % quad.label)
            outfile.seek(0,2)   # Go to the end of the output file
            #outfile.write('    addi    $sp, $sp, %d\n' % main_programs_framelength)
            outfile.write('    move    $s0, $sp\n')
    elif quad.op == 'end_block':
        if block_name == mainprog_name:
            outfile.write('    j       L_%d\n' % halt_label)
            # Hack for printing newline character
            outfile.write('\n###########################\n\n')
            outfile.write('    .data\n\n')
            outfile.write('newline:  .asciiz    "\\n"\n\n')
        else:
            outfile.write('    lw      $ra, 0($sp)\n')
            outfile.write('    jr      $ra\n')


def check_subprog_args(name):
    global actual_pars
    entity, level = search_entity_by_name(name)
    if entity.ret_type == 'int':
        actual_pars.pop() # pop parameter of type 'RET'
    if len(entity.args) != len(actual_pars):
        perror_exit(7, '%s: Missmatching subprogram argument number' %
            name)
    #print('\ncheck')
    for arg in entity.args:
        quad = actual_pars.pop(0)
        #print(arg.par_mode, quad.arg2, arg, quad)
        if not (arg.par_mode == quad.arg2):
            if arg.par_mode == 'CV':
                ptype = 'int'
            else:
                ptype = 'int *'
            perror_exit(7,'%s: Expected parameter \'%s\' to be of'
                ' type "%s"' % (name, quad.arg1, ptype))


##############################################################
#                                                            #
#                 Parser related functions                   #
#                                                            #
##############################################################


def parser():
    global token
    token = lex()
    program()
    # At this point syntax analysis has succeeded
    # but we should check for stray tokens.
    if token.tktype != TokenType.EOF:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected \'EOF\' but found \'%s\' instead' % token.tkval)
    generate_int_code_file()
    if have_subprog == False:
        generate_c_code_file()
    else:
        pwarn('Nested functions are defined! Transformation of intermediate\n' \
            + '          code to ANSI C equivalent cannot take place!')
        ceq_file.close()
        os.remove(ceq_file.name)


# The following functions implement the syntax and semantic rules of CiScal grammar
# rev.3 (as of March 3, 2017), including any additional specifications published at
# a later time (as of April 26, 2017). For this reason, no further documentation is
# necessary other than the one found in ciscal-grammar.pdf and the corresponding
# specifications documents.


def program():
    global token, mainprog_name
    if token.tktype == TokenType.PROGRAMSYM:
        token = lex()
        if token.tktype == TokenType.IDENT:
            mainprog_name = name = token.tkval
            token = lex()
            scopes.append(Scope())
            block(name)
        else:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected program name but found \'%s\' instead' % token.tkval)
    else:
        perror_exit(3, 'Missing \'program\' keyword')


def block(name):
    global token, scopes, halt_label
    #print("ENTERING ", name)
    #print_scopes()
    if token.tktype == TokenType.LBRACE:
        token = lex()
        declarations()
        subprograms()
        block_start_quad = update_func_entity_quad(name)
        gen_quad('begin_block', name)
        sequence()
        if token.tktype != TokenType.RBRACE:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected block end (\'}\') but found \'%s\' instead' % token.tkval)
        token = lex()
    else:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected block start (\'{\') but found \'%s\' instead' % token.tkval)
    if name == mainprog_name:
        halt_label = next_quad()
        gen_quad('halt')
    gen_quad('end_block', name)
    update_func_entity_framelen(name, scopes[-1].tmp_offset)
    #print("LEAVING ", name)
    #print_scopes()
    for quad in quad_code[block_start_quad:]:
        s = gen_mips_asm(quad, name)
        if s != None:
            print(s)
    scopes.pop()


def declarations():
    global token
    if token.tktype == TokenType.DECLARESYM:
        token = lex()
        varlist()
        if token.tktype != TokenType.ENDDECLSYM:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected \'enddeclare\' but found \'%s\' instead' % token.tkval)
        token = lex()


def varlist():
    global token
    if token.tktype == TokenType.IDENT:
        add_var_entity(token.tkval)
        token = lex()
        while token.tktype == TokenType.COMMA:
            token = lex()
            if token.tktype != TokenType.IDENT:
                perror_line_exit(3, token.tkl, token.tkc,
                    'Expected variable declaration but found \'%s\' instead'
                    % token.tkval)
            add_var_entity(token.tkval)
            token = lex()


def subprograms():
    global token, have_return, in_function, have_subprog
    while token.tktype == TokenType.PROCSYM or token.tktype == TokenType.FUNCSYM:
        in_function.append(False)
        have_return.append(False)
        have_subprog = True
        if token.tktype == TokenType.FUNCSYM:
            in_function[-1] = True
        token = lex()
        func()
        if in_function.pop() == True:
            if have_return.pop() == False:
                perror_line_exit(4, token.tkl, token.tkc,
                    'Expected return statement in function body')
        else:
            have_return.pop()


def func():
    global token, scopes
    add_new_scope()
    if token.tktype == TokenType.IDENT:
        name = token.tkval
        token = lex()
        add_func_entity(name)
        funcbody(name)
    else:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected procedure/function name but found \'%s\' instead' % token.tkval)


def funcbody(name):
    formalpars(name)
    block(name)


def formalpars(func_name):
    global token
    if token.tktype == TokenType.LPAREN:
        token = lex()
        if token.tktype == TokenType.INSYM or token.tktype == TokenType.INOUTSYM:
            formalparlist(func_name)
        if token.tktype != TokenType.RPAREN:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected \')\' but found \'%s\' instead' % token.tkval)
        token = lex()
    else:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected \'(\' but found \'%s\' instead' % token.tkval)


def formalparlist(func_name):
    global token
    formalparitem(func_name)
    while token.tktype == TokenType.COMMA:
        token = lex()
        if token.tktype != TokenType.INSYM and token.tktype != TokenType.INOUTSYM:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected formal parameter declaration but found \'%s\' instead'
                % token.tkval)
        formalparitem(func_name)


def formalparitem(func_name):
    global token, scopes
    if token.tktype == TokenType.INSYM or token.tktype == TokenType.INOUTSYM:
        par_mode = token.tkval
        token = lex()
        if token.tktype != TokenType.IDENT:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected formal parameter name but found \'%s\' instead'
                % token.tkval)
        par_name = token.tkval
        add_func_arg(func_name, par_mode)
        add_param_entity(par_name, par_mode)
        token = lex()


def sequence():
    global token
    statement()
    while token.tktype == TokenType.SEMICOLON:
        token = lex()
        statement();


def brackets_seq():
    global token
    if token.tktype == TokenType.LBRACE:
        token = lex()
        sequence()
        if token.tktype != TokenType.RBRACE:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected end of bracket sequence (\'}\') but found \'%s\' instead'
                % token.tkval)
        token = lex()
    else:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected start of bracket sequence (\'{\') but found \'%s\' instead'
            % token.tkval)


def brack_or_stat():
    global token
    if token.tktype == TokenType.LBRACE:
        brackets_seq()
    else:
        statement()
        if token.tktype != TokenType.SEMICOLON:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected \';\' after single or empty statement but found \'%s\' instead'
                % token.tkval)
        token = lex()


def statement():
    global token, have_return
    if token.tktype == TokenType.IDENT:
        lhand = token.tkval
        token = lex()
        rhand = assignment_stat()
        gen_quad(':=', rhand, '_', lhand)
    elif token.tktype == TokenType.IFSYM:
        token = lex()
        if_stat()
    elif token.tktype == TokenType.DOSYM:
        token = lex()
        do_while_stat()
    elif token.tktype == TokenType.WHILESYM:
        token = lex()
        while_stat()
    elif token.tktype == TokenType.SELECTSYM:
        token = lex()
        select_stat()
    elif token.tktype == TokenType.EXITSYM:
        if in_dowhile == []:
            perror_line_exit(4, token.tkl, token.tkc,
                'Encountered \'exit\' outside of a do-while loop')
        e_list = make_list(next_quad())
        gen_quad('jump')
        exit_dowhile[-1] = e_list
        token = lex()
        # No need to define exit_stat();
        # only to consume token.
    elif token.tktype == TokenType.RETURNSYM:
        if in_function == [] or in_function[-1] == False:
            perror_line_exit(4, token.tkl, token.tkc,
                'Encountered \'return\' outside of function definition')
        else:
            have_return[-1] = True
        token = lex()
        return_stat()
    elif token.tktype == TokenType.PRINTSYM:
        token = lex()
        print_stat()
    elif token.tktype == TokenType.CALLSYM:
        token = lex()
        call_stat()


def assignment_stat():
    global token
    if token.tktype == TokenType.BECOMES:
        token = lex()
        return expression()
    else:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected \':=\' but found \'%s\' instead' % token.tkval)


def if_stat():
    global token
    if token.tktype == TokenType.LPAREN:
        token = lex()
        (b_true, b_false) = condition()
        if token.tktype != TokenType.RPAREN:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected \')\' but found \'%s\' instead' % token.tkval)
        token = lex()
        backpatch(b_true, next_quad())
        brack_or_stat()
        skip_list = make_list(next_quad())
        gen_quad('jump')
        backpatch(b_false, next_quad())
        elsepart()
        backpatch(skip_list, next_quad())
    else:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected \'(\' after \'if\' but found \'%s\' instead' % token.tkval)


def elsepart():
    global token
    if token.tktype == TokenType.ELSESYM:
        token = lex()
        brack_or_stat()


def while_stat():
    global token
    b_quad = next_quad()
    if token.tktype == TokenType.LPAREN:
        token = lex()
        (b_true, b_false) = condition()
        if token.tktype != TokenType.RPAREN:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected \')\' but found \'%s\' instead' % token.tkval)
        token = lex()
        backpatch(b_true, next_quad())
        brack_or_stat()
        gen_quad('jump','_','_',b_quad)
        backpatch(b_false, next_quad())
    else:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected \'(\' after \'while\' but found \'%s\' instead'
            % token.tkval)


def select_stat():
    global token
    if token.tktype == TokenType.LPAREN:
        token = lex()
        if token.tktype == TokenType.IDENT:
            id = token.tkval
            token = lex()
            if token.tktype == TokenType.RPAREN:
                token = lex()
                const = 1
                exit_list = empty_list()
                while token.tktype == TokenType.NUMBER:
                    number = int(token.tkval)
                    if number != const:
                        perror_line_exit(3, token.tkl, token.tkc,
                            'Expected \'%d\' as case constant but found \'%s\' instead'
                            % (const,token.tkval))
                    const += 1
                    token = lex()
                    if token.tktype == TokenType.COLON:
                        true_list = make_list(next_quad())
                        gen_quad('=', id, number)
                        false_list = make_list(next_quad())
                        gen_quad('jump')
                        backpatch(true_list, next_quad())
                        token = lex()
                        brack_or_stat()
                        tmp_list = make_list(next_quad())
                        gen_quad('jump')
                        exit_list = merge(exit_list, tmp_list)
                        backpatch(false_list, next_quad())
                    else:
                        perror_line_exit(3, token.tkl, token.tkc,
                            'Expected \':\' after case constant but found \'%s\' instead'
                            % token.tkval)
                if token.tktype == TokenType.DEFAULTSYM:
                    token = lex()
                    if token.tktype == TokenType.COLON:
                        token = lex()
                        brack_or_stat()
                        backpatch(exit_list, next_quad())
                    else:
                        perror_line_exit(3, token.tkl, token.tkc,
                            'Expected \':\' after default keyword but found \'%s\' instead'
                            % token.tkval)
                else:
                    perror_line_exit(3, token.tkl, token.tkc,
                        'Expected \'default\' case but found \'%s\' instead'
                        % token.tkval)
            else:
                perror_line_exit(3, token.tkl, token.tkc,
                    'Expected \')\' but found \'%s\' instead'
                    % token.tkval)
        else:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected variable identifier but found \'%s\' instead'
                % token.tkval)
    else:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected \'(\' after \'select\' but found \'%s\' instead'
            % token.tkval)


def do_while_stat():
    global token, in_dowhile, exit_dowhile
    in_dowhile.append(True)
    exit_dowhile.append(None)
    s_quad = next_quad()
    brack_or_stat()
    if token.tktype == TokenType.WHILESYM:
        token = lex()
        if token.tktype == TokenType.LPAREN:
            token = lex()
            (c_true, c_false) = condition()
            if token.tktype != TokenType.RPAREN:
                perror_line_exit(3, token.tkl, token.tkc,
                    'Expected \')\' but found \'%s\' instead' % token.tkval)
            backpatch(c_true, s_quad)
            e_quad = next_quad()
            backpatch(c_false, e_quad)
            token = lex()
        else:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected \'(\' after \'while\' but found \'%s\' instead'
                % token.tkval)
    else:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected \'while\' token but found \'%s\' instead' % token.tkval)
    if exit_dowhile[-1] != None:
        backpatch(exit_dowhile[-1], e_quad)
    exit_dowhile.pop()
    in_dowhile.pop()


def return_stat():
    global token
    if token.tktype == TokenType.LPAREN:
        token = lex()
        exp   = expression()
        gen_quad('retv', exp)
        if token.tktype != TokenType.RPAREN:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected \')\' but found \'%s\' instead' % token.tkval)
        token = lex()
    else:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected \'(\' after \'return\' but found \'%s\' instead'
            % token.tkval)


def print_stat():
    global token
    if token.tktype == TokenType.LPAREN:
        token = lex()
        exp   = expression()
        gen_quad('out', exp)
        if token.tktype != TokenType.RPAREN:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected \')\' but found \'%s\' instead' % token.tkval)
        token = lex()
    else:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected \'(\' after \'print\' but found \'%s\' instead'
            % token.tkval)


def call_stat():
    global token
    if token.tktype == TokenType.IDENT:
        procid = token.tkval
        token  = lex()
        actualpars()
        try:
            proce, procl = search_entity_by_name(procid)
        except:
            perror_line_exit(7, token.tkl, token.tkc,
            'Undefined procedure \'%s\'' % procid)
        gen_quad('call', procid)
    else:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected procedure name but found \'%s\' instead' % token.tkval)


def actualpars():
    global token
    if token.tktype == TokenType.LPAREN:
        token = lex()
        if token.tktype == TokenType.INSYM or token.tktype == TokenType.INOUTSYM:
            actualparlist()
        if token.tktype != TokenType.RPAREN:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected \')\' but found \'%s\' instead' % token.tkval)
        token = lex()
        return True
    else:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected \'(\' after procedure/function name but found \'%s\' instead'
            % token.tkval)


def actualparlist():
    global token
    actualparitem()
    while token.tktype == TokenType.COMMA:
        token = lex()
        actualparitem()


def actualparitem():
    global token
    if token.tktype == TokenType.INSYM:
        token = lex()
        exp   = expression()
        gen_quad('par', exp, 'CV')
    elif token.tktype == TokenType.INOUTSYM:
        token = lex()
        parid = token.tkval
        if token.tktype != TokenType.IDENT:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected variable identifier but found \'%s\' instead' % token.tkval)
        token = lex()
        gen_quad('par', parid, 'REF')
    else:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected parameter type but found \'%s\' instead' % token.tkval)


def condition():
    global token
    (b_true, b_false) = (q1_true, q1_false) = boolterm()
    while token.tktype == TokenType.ORSYM:
        backpatch(b_false, next_quad())
        token = lex()
        (q2_true, q2_false) = boolterm()
        b_true  = merge(b_true, q2_true)
        b_false = q2_false
    return (b_true, b_false)


def boolterm():
    global token
    (q_true, q_false) = (r1_true, r1_false) = boolfactor()
    while token.tktype == TokenType.ANDSYM:
        backpatch(q_true, next_quad())
        token = lex()
        (r2_true, r2_false) = boolfactor()
        q_false = merge(q_false, r2_false)
        q_true  = r2_true
    return (q_true, q_false)


def boolfactor():
    global token
    if token.tktype == TokenType.NOTSYM:
        token = lex()
        if token.tktype == TokenType.LBRACKET:
            token = lex()
            retval = condition()
            retval = retval[::-1] # reverse lists
            if token.tktype != TokenType.RBRACKET:
                perror_line_exit(3, token.tkl, token.tkc,
                    'Expected \']\' but found \'%s\' instead' % token.tkval)
            token = lex()
        else:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected \'[\' after \'not\' but found \'%s\' instead'
                % token.tkval)
    elif token.tktype == TokenType.LBRACKET:
        token = lex()
        retval = condition()
        if token.tktype != TokenType.RBRACKET:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected \']\' but found \'%s\' instead' % token.tkval)
        token = lex()
    else:
        exp1   = expression()
        op     = relational_oper()
        exp2   = expression()
        r_true = make_list(next_quad())
        gen_quad(op, exp1, exp2)
        r_false = make_list(next_quad())
        gen_quad('jump')
        retval = (r_true, r_false)
    return retval


def expression():
    opsign = optional_sign()
    term1  = term()
    # unary minus
    if opsign != None:
        signtmp = new_temp()
        gen_quad('-', 0, term1, signtmp)
        term1 = signtmp
    while token.tktype == TokenType.PLUS or token.tktype == TokenType.MINUS:
        op     = add_oper()
        term2  = term()
        tmpvar = new_temp()
        gen_quad(op, term1, term2, tmpvar)
        term1 = tmpvar
    return term1


def term():
    factor1 = factor()
    while token.tktype == TokenType.TIMES or token.tktype == TokenType.SLASH:
        op      = mul_oper()
        factor2 = factor()
        tmpvar  = new_temp()
        gen_quad(op, factor1, factor2, tmpvar)
        factor1 = tmpvar
    return factor1


def factor():
    global token
    if token.tktype == TokenType.NUMBER or token.tktype == TokenType.PLUS or \
            token.tktype == TokenType.MINUS:
        retval = number_const()
    elif token.tktype == TokenType.LPAREN:
        token  = lex()
        retval = expression()
        if token.tktype != TokenType.RPAREN:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected \')\' but found \'%s\' instead' % token.tkval)
        token = lex()
    elif token.tktype == TokenType.IDENT:
        retval = token.tkval
        token  = lex()
        tail   = idtail()
        if tail != None:
            funcret = new_temp()
            gen_quad('par', funcret, 'RET')
            try:
                funce, funcl = search_entity_by_name(retval)
            except:
                perror_line_exit(7, token.tkl, token.tkc,
                'Undefined function \'%s\'' % retval)
            gen_quad('call', retval)
            retval = funcret
    else:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected factor but found \'%s\' instead' % token.tkval)
    return retval


# Custom function that returns the numeric value
# of a constant. Optional sign is taken into account.
def number_const():
    global token
    sign = '+'
    if token.tktype == TokenType.PLUS or token.tktype == TokenType.MINUS:
        sign = token.tkval
        token = lex()
    if token.tktype == TokenType.NUMBER:
        numval = int(''.join((sign, token.tkval)))
        # MIN_INT= -32768, MAX_INT= 32767
        if numval < -32768 or numval > 32767:
            perror_line_exit(3, token.tkl, token.tkc,
               'Number constants should be between -32768 and 32767')
    else:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected number constant but found \'%s\' instead' % token.tkval)
    token = lex()
    return numval


def idtail():
    if token.tktype == TokenType.LPAREN:
        return actualpars()


def relational_oper():
    global token
    op = token.tkval
    if token.tktype != TokenType.EQL and token.tktype != TokenType.LSS and \
            token.tktype != TokenType.LEQ and token.tktype != TokenType.NEQ and \
            token.tktype != TokenType.GEQ and token.tktype != TokenType.GTR:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected relational operator but found \'%s\' instead' % token.tkval)
    token = lex()
    return op


def add_oper():
    global token
    op = token.tkval
    if token.tktype != TokenType.PLUS and token.tktype != TokenType.MINUS:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected \'+\' or \'-\' but found \'%s\' instead' % token.tkval)
    token = lex()
    return op


def mul_oper():
    global token
    op = token.tkval
    if token.tktype != TokenType.TIMES and token.tktype != TokenType.SLASH:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected \'*\' or \'/\' but found \'%s\' instead' % token.tkval)
    token = lex()
    return op


def optional_sign():
    if token.tktype == TokenType.PLUS or token.tktype == TokenType.MINUS:
        return add_oper()


##############################################################
#                                                            #
#        Functions related to the main CSC program           #
#                                                            #
##############################################################


# Print program usage and exit.
def print_usage(ec=0):
    print('Usage:  %s [OPTIONS] {-i|--input} INFILE' % __file__)
    print('Available options:')
    print('        -h, --help                Display this information')
    print('        -v, --version             Output version information')
    print('        -I, --interm              Keep intermediate code (IC) file')
    print('        -C, --c-equiv             Keep IC equivalent in C lang file')
    print('        --save-temps              Equivalent to -IC option')
    print('        -o, --output OUTFILE      Place output in file: OUTFILE\n')
    sys.exit(ec)


# Print program version and exit.
def print_version():
    print('CiScal Compiler ', __version__)
    print('Copyright (C) 2017 George Z. Zachos, Andrew Konstantinidis')
    print('This is free software; see the source for copying conditions.')
    print('There is NO warranty to the extent permitted by law.\n')
    sys.exit()


# Implements the command line interface and triggers the
# different stages of the compilation process.
def main(argv):
    input_filename  = ''
    interm_filename = ''
    cequiv_filename = ''
    output_filename = ''

    try:
        opts, args = getopt.getopt(argv,"hvICo::i:",["help", "version", "interm",
                                    "c-equiv", "save-temps", "input=", "output="])
    except getopt.GetoptError as err:
        perror(err)
        print_usage(1)

    if not opts:
        print_usage(1)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_usage()
        elif opt in ("-v", "--version"):
            print_version()
        elif opt in ("-i", "--input"):
            input_filename = arg
        elif opt in ("-o", "--output"):
            output_filename = arg
        elif opt in ("-I", "--interm", "-C", "--c-equiv", "--save-temps"):
            pwarn("%s: Enabled by default option" % opt)

    if input_filename == '':
        perror('Option {-i|--input} is required')
        print_usage(1)
    elif input_filename[-4:] != '.csc':
        perror(input_filename + ': invalid file type')
        perror_exit(1, 'INFILE should have a \'.csc\' extension')

    interm_filename = input_filename[:-4] + '.int'
    cequiv_filename = input_filename[:-4] + '.c'
    if output_filename == '':
        output_filename = input_filename[:-4] + '.asm'

    if os.path.isfile(output_filename):
        pwarn(output_filename + ': exists and will be overwritten!')

    open_files(input_filename, interm_filename, cequiv_filename, output_filename)
    parser()
    close_files()


if __name__ == "__main__":
    main(sys.argv[1:])

