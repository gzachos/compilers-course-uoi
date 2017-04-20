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

__version__='0.0.1'


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
    def __init__(self, nested_level=1, enclosing_scope=None):
        self.entities, self.nested_level = list(), nested_level
        self.enclosing_scope = enclosing_scope

    def setNestedLevel(self, nested_level): # TODO remove (?)
        self.nested_level = nested_level

    def setStackPtr(self, stack_ptr):
        self.stack_ptr = stack_ptr

    def addEntity(self, entity):
        self.entities.append(entity)

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

    def set_next(self, next_entity):
        self.next = next_entity

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
    def __init__(self, name, ret_type, start_quad):
        super().__init__(name, "FUNCTION")
        self.ret_type, self.start_quad = ret_type, start_quad
        self.args, self.framelength = list(), -1

    def add_arg(self, arg):
        self.args.append(arg)

    def set_framelen(self, framelength):
        self.framelength = framelength

    def __str__(self):
        return super().__str__() + ', retv: ' + self.ret_type \
            + ', squad: ' + str(self.start_quad)


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


##############################################################
#                                                            #
#         Global data declarations and definitions           #
#                                                            #
##############################################################

lineno   = charno = -1  # Current line and character number of input file
token    = Token(None, None, None, None)
in_function  = []
in_dowhile   = []
exit_dowhile = []
have_return  = [] # have return statement at specific nested level
nextlabel    = 0
tmpvars      = dict()
next_tmpvar  = 1
quad_code    = list()
scopes       = list()
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


# Print error message to stderr and exit
def perror_exit(ec, *args, **kwargs):
    print('[' + clr.ERR + 'ERROR' + clr.END + ']', *args, file=sys.stderr, **kwargs)
    sys.exit(ec)


# Print error message to stderr
def perror(*args, **kwargs):
    print('[' + clr.ERR + 'ERROR' + clr.END + ']', *args, file=sys.stderr, **kwargs)


# Print warning to stderr
def pwarn(*args, **kwargs):
    print('[' + clr.WRN + 'WARNING' + clr.END + ']', *args, file=sys.stderr, **kwargs)


# Print line #lineno to stderr with character charno highlighted
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
    infile.seek(currchar)
    sys.exit(ec)


# Open files
def open_files(input_filename, interm_filename, cequiv_filename, output_filename):
    global infile, int_file, ceq_file, outfile, lineno, charno
    lineno = 1
    charno = 0
    try:
        infile   = open(input_filename,  'r', encoding='utf-8')
        int_file = open(interm_filename, 'w', encoding='utf-8')
#       ceq_file = open(cequiv_filename, 'w', encoding='utf-8')
#       outfile  = open(output_filename, 'w', encoding='utf-8')
    except OSError as oserr:
        if oserr.filename != None:
            perror_exit(oserr.errno, oserr.filename + ':', oserr.strerror)
        else:
            perror_exit(oserr.errno, oserr)


def close_files():
    global infile
    infile.close()


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
    scopes[-1].addEntity(TmpVar(key))
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


def generate_int_code_file():
    for quad in quad_code:
        int_file.write(quad.tofile() + '\n')
    int_file.close()


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
        else:
            retval = 'int ' + quad.arg1 + '()\n{' # FIXME return type & params
        vars = find_var_decl(quad)
        retval += transform_decls(vars)
    elif quad.op == 'call':
        retval = quad.arg1 + '();'
    elif quad.op == 'end_block':
        addlabel = False
        retval = '\tL_' + str(quad.label) + ': {}\n'
        retval += '}\n'
    elif quad.op == 'halt':
        retval = 'return 0;' # change to exit() if arbitrary
                             # halt statements are enabled.
    else:
        return None
    if addlabel == True:
        retval = '\tL_' + str(quad.label) + ': ' + retval
    return retval


def generate_c_code_file():
    print('#include <stdio.h>\n')
    print('/* This file was automatically generated by:')
    print(' *     CiScal Compiler', __version__)
    print(' */\n')
    for quad in quad_code:
        tmp = transform_to_c(quad)
        if tmp != None:
            print(tmp)


##############################################################
#                                                            #
#             Symbol table related functions                 #
#                                                            #
##############################################################


def add_new_scope():
    enclosing_scope = scopes[-1]
    curr_scope = Scope(enclosing_scope.nested_level + 1, enclosing_scope)
    scopes.append(curr_scope)


def print_scopes():
    print('* main scope\n|')
    for scope in scopes:
        level = scope.nested_level
    #   print('    ' * level + str(scope))
        for entity in scope.entities:
            print('|    ' * level + str(entity))
            if isinstance(entity, Function):
                for arg in entity.args:
                    print('|    ' * level + '|    ' + str(arg))
    print('\n')


def print_entity(entity):
    level = scopes[-1].nested_level - 1
    if level == 1:
        print('* main scope\n|')
    print('|    ' * level + str(entity))
    if isinstance(entity, Function):
        for arg in entity.args:
            print('|    ' * level + '|   ' + str(arg))


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
    scopes[-2].addEntity(Function(name, ret_type, next_quad()))


def add_param_entity(name, par_mode):
    nested_level = scopes[-1].nested_level
    if not unique_entity(name, "PARAMETER", nested_level):
        perror_line_exit(5, token.tkl, token.tkc,
            'Redefinition of \'%s\'' % name)
    scopes[-1].addEntity(Parameter(name, par_mode))


def add_func_arg(func_name, par_mode):
    if (par_mode == 'in'):
        new_arg = Argument('CV')
    else:
        new_arg = Argument('REF')
    func_entity = search_entity(func_name, "FUNCTION")
    if func_entity == None:
        perror_line_exit(5, token.tkl, token.tkc,
            'No definition of \'%s\' was not found' % func_name)
    if func_entity.args != list():
        func_entity.args[-1].set_next(new_arg)
    func_entity.add_arg(new_arg)


def search_entity(name, etype):
    if scopes == list():
        return
    tmp_scope = scopes[-1]
    while tmp_scope != None:
        for entity in tmp_scope.entities:
#           print_entity(entity)
            if entity.name == name and entity.etype == etype:
                return entity
        tmp_scope = tmp_scope.enclosing_scope


def unique_entity(name, etype, nested_level):
    if scopes[-1].nested_level < nested_level:
        return
    scope = scopes[nested_level-1]
#   print('ABOUT TO ADD: ', name)
    list_len = len(scope.entities)
    for i in range(list_len):
#       print(scope.entities[i].name)
        for j in range(list_len):
            e1 = scope.entities[i]
            e2 = scope.entities[j]
#           print(i,j)
#           print(e1.name, e2.name, '\n')
            if e1.name == e2.name and e1.etype == e2.etype \
                    and e1.name == name and e1.etype == etype:
#               print('SAME: ' ,e1.name, e2.name)
                return False
    return True


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
    # generate_c_code_file()


# The following functions implement the syntax rules of CiScal grammar rev.3
# (as of March 3, 2017) and no further documentation is necessary other than
# the one found in ciscal-grammar.pdf.


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
    global token, scopes
    if token.tktype == TokenType.LBRACE:
        token = lex()
        declarations()
        subprograms()
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
        gen_quad('halt')
    gen_quad('end_block', name)
#   print_scopes()
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
        token = lex()
        while token.tktype == TokenType.COMMA:
            token = lex()
            if token.tktype != TokenType.IDENT:
                perror_line_exit(3, token.tkl, token.tkc,
                    'Expected variable declaration but found \'%s\' instead'
                    % token.tkval)
            token = lex()


def subprograms():
    global token, have_return, in_function
    while token.tktype == TokenType.PROCSYM or token.tktype == TokenType.FUNCSYM:
        in_function.append(False)
        have_return.append(False)
        if (token.tktype == TokenType.FUNCSYM):
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
    #func_entity = search_entity(name, "FUNCTION")
    #print_entity(func_entity) # TODO remove
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


# Print program usage and exit
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


# Print program version and exit
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
            pwarn("%s: Currently unavailable option" % opt)

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

