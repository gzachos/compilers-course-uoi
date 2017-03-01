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


##############################################################
#                                                            #
#         Global data declarations and definitions           #
#                                                            #
##############################################################


token    = ()
tokens   = {
	'(':TokenType.LPAREN,
	')':TokenType.RPAREN,
	'{':TokenType.LBRACE,
	'}':TokenType.RBRACE,
	'[':TokenType.LBRACKET,
	']':TokenType.RBRACKET,
	',':TokenType.COMMA,
	':':TokenType.COLON,
	';':TokenType.SEMICOLON,
	'<':TokenType.LSS,
	'>':TokenType.GTR,
	'<=':TokenType.LEQ,
	'>=':TokenType.GEQ,
	'=':TokenType.EQL,
	'<>':TokenType.NEQ,
	':=':TokenType.BECOMES,
	'+':TokenType.PLUS,
	'-':TokenType.MINUS,
	'*':TokenType.TIMES,
	'/':TokenType.SLASH,
	'and':TokenType.ANDSYM,
	'not':TokenType.NOTSYM,
	'or':TokenType.ORSYM,
	'declare':TokenType.DECLARESYM,
	'enddeclare':TokenType.ENDDECLSYM,
	'do':TokenType.DOSYM,
	'if':TokenType.IFSYM,
	'else':TokenType.ELSESYM,
	'exit':TokenType.EXITSYM,
	'procedure':TokenType.PROCSYM,
	'function':TokenType.FUNCSYM,
	'print':TokenType.PRINTSYM,
	'call':TokenType.CALLSYM,
	'in':TokenType.INSYM,
	'inout':TokenType.INOUTSYM,
	'select':TokenType.SELECTSYM,
	'program':TokenType.PROGRAMSYM,
	'return':TokenType.RETURNSYM,
	'while':TokenType.WHILESYM,
	'default':TokenType.DEFAULTSYM,
	'EOF':TokenType.EOF}


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


# Print line #lineno to stderr with character
# charno highlighted
def perror_line(lineno, charno):
	currchar = infile.tell()
	infile.seek(0)
	for index, line in enumerate(infile):
		if index == lineno-1:
			print(" ", line.replace('\t', ' ').replace('\n', ''), file=sys.stderr)
			print(clr.GRN + " " * (charno + 1) + '^' + clr.END, file=sys.stderr)
	infile.seek(currchar)


# Print line #lineno to stderr with character charno
# highlighted along with and error message. Finally exit.
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
#		outfile = open(output_file, 'w', encoding='utf-8') # TODO uncomment later
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
	global lineno, charno, tkl, tkc
	buffer = []
	cc = cl = -1
	state = 0
	OK    = -2
	unget = False
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
			elif c == '+':
				state = OK
			elif c == '-':
				state = OK
			elif c == '*':
				state = OK
			elif c == '/':
				state = OK
			elif c == '=':
				state = OK
			elif c == ',':
				state = OK
			elif c == ';':
				state = OK
			elif c == '{':
				state = OK
			elif c == '}':
				state = OK
			elif c == '(':
				state = OK
			elif c == ')':
				state = OK
			elif c == '[':
				state = OK
			elif c == ']':
				state = OK
			elif c == '': # EOF
				state = OK
				tkl = lineno
				tkc = charno
				return (TokenType.EOF, 'EOF')
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
				#TODO correctly check for {MIN,MAX}_INT violation
				if int(''.join(buffer[:-1])) > 32767:
					perror_line_exit(2, lineno, charno - len(''.join(buffer)) + 1,
						'Number constants should be between -32768 and 32767')
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

	if unget == True:
		del buffer[-1]
		if c != '': # EOF (special case)
			infile.seek(infile.tell() - 1)
		charno -= 1

	buff_cont = ''.join(buffer)
	if buff_cont not in tokens.keys():
		if buff_cont.isdigit():
			retval = (TokenType.NUMBER, int(buff_cont))
		else:
			retval = (TokenType.IDENT, buff_cont[:30])
	else:
		retval = (tokens[buff_cont], buff_cont)
	del buffer[:]
	return retval


##############################################################
#                                                            #
#           Syntax analyzer related functions                #
#                                                            #
##############################################################


# Performs syntax analysis
def syntax_analyzer():
	global token
	token = lex()
	program()
	# At this point syntax analysis has succeeded
	# but we should check for stray tokens.
	if token[0] != TokenType.EOF:
		perror_line_exit(3, tkl, tkc, 'Expected \'EOF\' but \'%s\' was found instead' % token[1])


def program():
	global token
	if token[0] == TokenType.PROGRAMSYM:
		token = lex()
		if token[0] == TokenType.IDENT:
			token = lex()
			block();
		else:
			perror_line_exit(3, tkl, tkc, 'Expected program name but \'%s\' was found instead' % token[1])
	else:
		perror_exit(3, 'Missing \'program\' keyword')


def block():
	global token
	if token[0] == TokenType.LBRACE:
		token = lex()
		declarations()
		subprograms()
		sequence()
		if token[0] != TokenType.RBRACE:
			perror_line_exit(3, tkl, tkc, 'Expected \'}\' but \'%s\' was found instead' % token[1])
		token = lex()
	else:
		perror_line_exit(3, tkl, tkc, 'Expected \'{\' but \'%s\' was found instead' % token[1])


def declarations():
	global token
	if token[0] == TokenType.DECLARESYM:
		token = lex()
		varlist()
		if token[0] != TokenType.ENDDECLSYM:
			perror_line_exit(3, tkl, tkc, 'Expected \'enddeclare\' but \'%s\' was found instead' % token[1])
		token = lex()


def varlist():
	global token
	if token[0] == TokenType.IDENT:
		token = lex()
		while token[0] == TokenType.COMMA:
			token = lex()
			if token[0] != TokenType.IDENT:
				perror_line_exit(3, tkl, tkc, 'Expected variable declaration but \'%s\' was found instead' % token[1])
			token = lex()


def subprograms():
	global token
	while token[0] == TokenType.PROCSYM or token[0] == TokenType.FUNCSYM:
		token = lex()
		func()


def func():
	global token
	if token[0] == TokenType.IDENT:
		token = lex()
		funcbody()
	else:
		perror_line_exit(3, tkl, tkc, 'Expected procedure/function name but \'%s\' was found instead' % token[1])


def funcbody():
	formalpars()
	block()


def formalpars():
	global token
	if token[0] == TokenType.LPAREN:
		token = lex()
		if token[0] == TokenType.INSYM or token[0] == TokenType.INOUTSYM:
			formalparlist()
		if token[0] != TokenType.RPAREN:
			perror_line_exit(3, tkl, tkc, 'Expected \')\' but \'%s\' was found instead' % token[1])
		token = lex()
	else:
		perror_line_exit(3, tkl, tkc, 'Expected \'(\' but \'%s\' was found instead' % token[1])


def formalparlist():
	global token
	formalparitem()
	while token[0] == TokenType.COMMA:
		token = lex()
		if token[0] != TokenType.INSYM and token[0] != TokenType.INOUTSYM:
			perror_line_exit(3, tkl, tkc, 'Expected formal parameter declaration but \'%s\' was found instead' % token[1])
		formalparitem()


def formalparitem():
	global token
	if token[0] == TokenType.INSYM or token[0] == TokenType.INOUTSYM:
		token = lex()
		if token[0] != TokenType.IDENT:
			perror_line_exit(3, tkl, tkc, 'Expected formal parameter name but \'%s\' was found instead' % token[1])
		token = lex()


def sequence():
	global token
	statement()
	while token[0] == TokenType.SEMICOLON:
		token = lex()
		statement();


def brackets_seq():
	global token
	if token[0] == TokenType.LBRACE:
		token = lex()
		sequence()
		if token[0] != TokenType.RBRACE:
			perror_line_exit(3, tkl, tkc, 'Expected \'}\' but \'%s\' was found instead' % token[1])
		token = lex()
	else:
		perror_line_exit(3, tkl, tkc, 'Expected \'{\' but \'%s\' was found instead' % token[1])


def brack_or_stat():
	if token[0] == TokenType.LBRACE:
		brackets_seq()
	else:
		statement()


def statement():
	global token
	if token[0] == TokenType.IDENT:
		token = lex()
		assignment_stat()
	elif token[0] == TokenType.IFSYM:
		token = lex()
		if_stat()
	elif token[0] == TokenType.DOSYM:
		token = lex()
		do_while_stat()
	elif token[0] == TokenType.WHILESYM:
		token = lex()
		while_stat()
	elif token[0] == TokenType.SELECTSYM:
		token = lex()
		select_stat()
	elif token[0] == TokenType.EXITSYM:
		token = lex()
		# No need to define exit_stat()
	elif token[0] == TokenType.RETURNSYM:
		token = lex()
		return_stat()
	elif token[0] == TokenType.PRINTSYM:
		token = lex()
		print_stat()
	elif token[0] == TokenType.CALLSYM:
		token = lex()
		call_stat()


def assignment_stat():
	global token
	if token[0] == TokenType.BECOMES:
		token = lex()
		expression()
	else:
		perror_line_exit(3, tkl, tkc, 'Expected \':=\' but \'%s\' was found instead' % token[1])


def if_stat():
	global token
	if token[0] == TokenType.LPAREN:
		token = lex()
		condition()
		if token[0] != TokenType.RPAREN:
			perror_line_exit(3, tkl, tkc, 'Expected \')\' but \'%s\' was found instead' % token[1])
		token = lex()
		brack_or_stat()
		elsepart()
	else:
		perror_line_exit(3, tkl, tkc, 'Expected \'(\' but \'%s\' was found instead' % token[1])


def elsepart():
	global token
	if token[0] == TokenType.ELSESYM:
		token = lex()
		brack_or_stat


def while_stat():
	global token
	if token[0] == TokenType.LPAREN:
		token = lex()
		condition()
		if token[0] != TokenType.RPAREN:
			perror_line_exit(3, tkl, tkc, 'Expected \')\' but \'%s\' was found instead' % token[1])
		token = lex()
		brack_or_stat()
	else:
		perror_line_exit(3, tkl, tkc, 'Expected \'(\' but \'%s\' was found instead' % token[1])


def select_stat():
	global token
	if token[0] == TokenType.LPAREN:
		token = lex()
		if token[0] == TokenType.IDENT:
			token = lex()
			if token[0] == TokenType.RPAREN:
				token = lex()
				const = 1
				while token[0] == TokenType.NUMBER:
					if token[1] != const:
						perror_line_exit(3, tkl, tkc, 'Expected \'%d\' as case constant but \'%s\' was found instead' % (const,token[1]))
					const += 1
					token = lex()
					if token[0] == TokenType.COLON:
						token = lex()
						brack_or_stat()
					else:
						perror_line_exit(3, tkl, tkc, 'Expected \':\' after case constant but \'%s\' was found instead' % token[1])
				if token[0] == TokenType.DEFAULTSYM:
					token = lex()
					if token[0] == TokenType.COLON:
						token = lex()
						brack_or_stat()
					else:
						perror_line_exit(3, tkl, tkc, 'Expected \':\' after default keyword but \'%s\' was found instead' % token[1])
				else:
					perror_line_exit(3, tkl, tkc, 'Expected \'default\' case but \'%s\' was found instead' % token[1])
			else:
				perror_line_exit(3, tkl, tkc, 'Expected \')\' but \'%s\' was found instead' % token[1])
		else:
			perror_line_exit(3, tkl, tkc, 'Expected variable identifier but \'%s\' was found instead' % token[1])
	else:
		perror_line_exit(3, tkl, tkc, 'Expected \'(\' but \'%s\' was found instead' % token[1])


def do_while_stat():
	global token
	brack_or_stat()
	if token[0] == TokenType.WHILESYM:
		token = lex()
		if token[0] == TokenType.LPAREN:
			token = lex()
			condition()
			if token[0] != TokenType.RPAREN:
				perror_line_exit(3, tkl, tkc, 'Expected \')\' but \'%s\' was found instead' % token[1])
			token = lex()
		else:
			perror_line_exit(3, tkl, tkc, 'Expected \'(\' but \'%s\' was found instead' % token[1])
	else:
		perror_line_exit(3, tkl, tkc, 'Expected \'while\' token but \'%s\' was found instead' % token[1])


def return_stat():
	global token
	if token[0] == TokenType.LPAREN:
		token = lex()
		expression()
		if token[0] != TokenType.RPAREN:
			perror_line_exit(3, tkl, tkc, 'Expected \')\' but \'%s\' was found instead' % token[1])
		token = lex()
	else:
		perror_line_exit(3, tkl, tkc, 'Expected \'(\' but \'%s\' was found instead' % token[1])


def print_stat():
	global token
	if token[0] == TokenType.LPAREN:
		token = lex()
		expression()
		if token[0] != TokenType.RPAREN:
			perror_line_exit(3, tkl, tkc, 'Expected \')\' but \'%s\' was found instead' % token[1])
		token = lex()
	else:
		perror_line_exit(3, tkl, tkc, 'Expected \'(\' but \'%s\' was found instead' % token[1])


def call_stat():
	global token
	if token[0] == TokenType.IDENT:
		token = lex()
		actualpars()
	else:
		perror_line_exit(3, tkl, tkc, 'Expected procedure name but \'%s\' was found instead' % token[1])


def actualpars():
	global token
	if token[0] == TokenType.LPAREN:
		token = lex()
		if token[0] == TokenType.INSYM or token[0] == TokenType.INOUTSYM:
			actualparlist()
		if token[0] != TokenType.RPAREN:
			perror_line_exit(3, tkl, tkc, 'Expected \')\' but \'%s\' was found instead' % token[1])
		token = lex()
	else:
		perror_line_exit(3, tkl, tkc, 'Expected \'(\' but \'%s\' was found instead' % token[1])


def actualparlist():
	global token
	actualparitem()
	while token[0] == TokenType.COMMA:
		token = lex()
		actualparitem()


def actualparitem():
	global token
	if token[0] == TokenType.INSYM:
		token = lex()
		expression()
	elif token[0] == TokenType.INOUTSYM:
		token = lex()
		if token[0] != TokenType.IDENT:
			perror_line_exit(3, tkl, tkc, 'Expected variable identifier but \'%s\' was found instead' % token[1])
		token = lex()
	else:
		perror_line_exit(3, tkl, tkc, 'Expected parameter type but \'%s\' was found instead' % token[1])


def condition():
	global token
	boolterm()
	while token[0] == TokenType.ORSYM:
		token = lex()
		boolterm()


def boolterm():
	global token
	boolfactor()
	while token[0] == TokenType.ANDSYM:
		token = lex()
		boolfactor()


def boolfactor():
	global token
	if token[0] == TokenType.NOTSYM:
		token = lex()
		if token[0] == TokenType.LBRACKET:
			token = lex()
			condition()
			if token[0] != TokenType.RBRACKET:
				perror_line_exit(3, tkl, tkc, 'Expected \']\' but \'%s\' was found instead' % token[1])
			token = lex()
		else:
			perror_line_exit(3, tkl, tkc, 'Expected \'[\' but \'%s\' was found instead' % token[1])
	elif token[0] == TokenType.LBRACKET:
		token = lex()
		condition()
		if token[0] != TokenType.RBRACKET:
			perror_line_exit(3, tkl, tkc, 'Expected \']\' but \'%s\' was found instead' % token[1])
		token = lex()
	else:
		expression()
		relational_oper()
		expression()


def expression():
	optional_sign()
	term()
	while token[0] == TokenType.PLUS or token[0] == TokenType.MINUS:
		add_oper()
		term()


def term():
	factor()
	while token[0] == TokenType.TIMES or token[0] == TokenType.SLASH:
		mul_oper()
		factor()


def factor():
	global token
	if token[0] == TokenType.NUMBER:
		token = lex()
	elif token[0] == TokenType.LPAREN:
		token = lex()
		expression()
		if token[0] != TokenType.RPAREN:
			perror_line_exit(3, tkl, tkc, 'Expected \')\' but \'%s\' was found instead' % token[1])
		token = lex()
	elif token[0] == TokenType.IDENT:
		token = lex()
		idtail()
	else:
		perror_line_exit(3, tkl, tkc, 'Expected factor but \'%s\' was found instead' % token[1])


def idtail():
	if token[0] == TokenType.LPAREN:
		actualpars()


def relational_oper():
	global token
	if token[0] != TokenType.EQL and token[0] != TokenType.LSS and \
			token[0] != TokenType.LEQ and token[0] != TokenType.NEQ and \
			token[0] != TokenType.GEQ and token[0] != TokenType.GTR:
		perror_line_exit(3, tkl, tkc, 'Expected relational operator but \'%s\' was found instead' % token[1])
	token = lex()


def add_oper():
	global token
	if token[0] != TokenType.PLUS and token[0] != TokenType.MINUS:
		perror_line_exit(3, tkl, tkc, 'Expected \'+\' or \'-\' but \'%s\' was found instead' % token[1])
	token = lex()


def mul_oper():
	global token
	if token[0] != TokenType.TIMES and token[0] != TokenType.SLASH:
		perror_line_exit(3, tkl, tkc, 'Expected \'*\' or \'/\' but \'%s\' was found instead' % token[1])
	token = lex()


def optional_sign():
	if token[0] == TokenType.PLUS or token[0] == TokenType.MINUS:
		add_oper()


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
	print('        -o, --output OUTFILE      Place output in file: OUTFILE\n')
	sys.exit(ec)


# Print program version and exit
def print_version():
	print('CiScal Compiler ', __version__)
	print('Copyright (C) 2017 George Z. Zachos, Andrew Konstantinidis')
	print('This is free software; see the source for copying conditions.')
	print('There is NO warranty to the extent permitted by law.\n')
	sys.exit()


def main(argv):
	input_file  = ''
	output_file = ''

	try:
		opts, args = getopt.getopt(argv,"hvo::i:",["help", "version", "input=", "output="])
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

	if input_file == '':
		perror('Option {-i|--input} is required')
		print_usage(1)
	elif input_file[-4:] != '.csc':
		perror(input_file + ': invalid file type')
		perror_exit(1, 'INFILE should have a \'.csc\' extension')

	if output_file == '':
		output_file = input_file[:-4] + '.out'

	if os.path.isfile(output_file):
		pwarn(output_file + ': exists and will be overwritten!')

	open_files(input_file, output_file)
	syntax_analyzer()


if __name__ == "__main__":
	main(sys.argv[1:])


