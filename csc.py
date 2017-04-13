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


##############################################################
#                                                            #
#         Global data declarations and definitions           #
#                                                            #
##############################################################

lineno   = charno = -1  # Current line and character number of input file
token    = Token(None, None, None, None)
in_function = []
in_dowhile  = []
have_return = [] # have return statement at specific nested level
nextlabel   = 1
tmpvars     = dict()
next_tmpvar = 1
quad_code   = list()
tokens   = {
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
def open_files(input_file, output_file):
    global infile, outfile, lineno, charno
    lineno = 1
    charno = 0
    try:
        infile = open(input_file, 'r', encoding='utf-8')
#       outfile = open(output_file, 'w', encoding='utf-8') # TODO uncomment later
    except OSError as oserr:
        if oserr.filename != None:
            perror_exit(oserr.errno, oserr.filename + ':', oserr.strerror)
        else:
            perror_exit(oserr.errno, oserr)


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
#           Syntax analyzer related functions                #
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


def print_int_code():
    for quad in quad_code:
        print(quad)


# Performs syntax analysis
def syntax_analyzer():
    global token
    token = lex()
    program()
    # At this point syntax analysis has succeeded
    # but we should check for stray tokens.
    if token.tktype != TokenType.EOF:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected \'EOF\' but found \'%s\' instead' % token.tkval)
    print_int_code() # TODO remove


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
            block(name);
        else:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected program name but found \'%s\' instead' % token.tkval)
    else:
        perror_exit(3, 'Missing \'program\' keyword')


def block(name):
    global token
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
    global token
    if token.tktype == TokenType.IDENT:
        name = token.tkval
        token = lex()
        funcbody(name)
    else:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected procedure/function name but found \'%s\' instead' % token.tkval)


def funcbody(name):
    formalpars()
    block(name)


def formalpars():
    global token
    if token.tktype == TokenType.LPAREN:
        token = lex()
        if token.tktype == TokenType.INSYM or token.tktype == TokenType.INOUTSYM:
            formalparlist()
        if token.tktype != TokenType.RPAREN:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected \')\' but found \'%s\' instead' % token.tkval)
        token = lex()
    else:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected \'(\' but found \'%s\' instead' % token.tkval)


def formalparlist():
    global token
    formalparitem()
    while token.tktype == TokenType.COMMA:
        token = lex()
        if token.tktype != TokenType.INSYM and token.tktype != TokenType.INOUTSYM:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected formal parameter declaration but found \'%s\' instead'
                % token.tkval)
        formalparitem()


def formalparitem():
    global token
    if token.tktype == TokenType.INSYM or token.tktype == TokenType.INOUTSYM:
        token = lex()
        if token.tktype != TokenType.IDENT:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected formal parameter name but found \'%s\' instead'
                % token.tkval)
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
        if_list = make_list(next_quad())
        gen_quad('jump')
        backpatch(b_false, next_quad())
        elsepart()
        backpatch(if_list, next_quad())
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
            token = lex()
            if token.tktype == TokenType.RPAREN:
                token = lex()
                const = 1
                while token.tktype == TokenType.NUMBER:
                    if int(token.tkval) != const:
                        perror_line_exit(3, token.tkl, token.tkc,
                            'Expected \'%d\' as case constant but found \'%s\' instead'
                            % (const,token.tkval))
                    const += 1
                    token = lex()
                    if token.tktype == TokenType.COLON:
                        token = lex()
                        brack_or_stat()
                    else:
                        perror_line_exit(3, token.tkl, token.tkc,
                            'Expected \':\' after case constant but found \'%s\' instead'
                            % token.tkval)
                if token.tktype == TokenType.DEFAULTSYM:
                    token = lex()
                    if token.tktype == TokenType.COLON:
                        token = lex()
                        brack_or_stat()
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
    global token, in_dowhile
    in_dowhile.append(True)
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
            backpatch(c_false, s_quad)
            backpatch(c_true, next_quad())
            token = lex()
        else:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected \'(\' after \'while\' but found \'%s\' instead'
                % token.tkval)
    else:
        perror_line_exit(3, token.tkl, token.tkc,
            'Expected \'while\' token but found \'%s\' instead' % token.tkval)
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
        gen_quad('par', exp, 'cv')
    elif token.tktype == TokenType.INOUTSYM:
        token = lex()
        parid = token.tkval
        if token.tktype != TokenType.IDENT:
            perror_line_exit(3, token.tkl, token.tkc,
                'Expected variable identifier but found \'%s\' instead' % token.tkval)
        token = lex()
        gen_quad('par', parid, 'ref')
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
    while token.tktype == TokenType.PLUS or token.tktype == TokenType.MINUS:
        op     = add_oper()
        term2  = term()
        tmpvar = new_temp()
        gen_quad(op, term1, term2, tmpvar)
        term1 = tmpvar
    # unary minus
    if opsign != None:
        signtmp = new_temp()
        gen_quad('-', 0, term1, signtmp)
        term1 = signtmp
    # print("retval = ", term1) # TODO remove
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
            gen_quad('par', funcret, 'ret')
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
    input_file  = ''
    output_file = ''

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
            input_file = arg
        elif opt in ("-o", "--output"):
            output_file = arg
        elif opt in ("-I", "--interm", "-C", "--c-equiv", "--save-temps"):
            pwarn("%s: Currently unavailable option" % opt)

    if input_file == '':
        perror('Option {-i|--input} is required')
        print_usage(1)
    elif input_file[-4:] != '.csc':
        perror(input_file + ': invalid file type')
        perror_exit(1, 'INFILE should have a \'.csc\' extension')

    if output_file == '':
        output_file = input_file[:-4] + '.asm'

    if os.path.isfile(output_file):
        pwarn(output_file + ': exists and will be overwritten!')

    open_files(input_file, output_file)
    syntax_analyzer()


if __name__ == "__main__":
    main(sys.argv[1:])

