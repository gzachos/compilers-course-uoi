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


keywords = [
	'and','declare','do','else','enddeclare','exit','procedure',
	'function','print','call','if','in','inout','not','select','program',
	'or','return','while','default']
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
	'default':TokenType.DEFAULTSYM}
buffer   = []


# Print message to stderr and exit
def perror_exit(ec, *args, **kwargs):
	print('[ERROR]', *args, file=sys.stderr, **kwargs)
	sys.exit(ec)


# Print error message to stderr
def perror(*args, **kwargs):
	print('[ERROR]', *args, file=sys.stderr, **kwargs)


# Print warning to stderr
def pwarn(*args, **kwargs):
	print('[WARNING]', *args, file=sys.stderr, **kwargs)


# Open files
def open_files(input_file, output_file):
	global infile, outfile, lineno, charno
	lineno = 1
	charno = 0
	try:
		infile = open(input_file, 'r', encoding='utf-8')
		outfile = open(output_file, 'w', encoding='utf-8')
	except OSError as oserr:
		if oserr.filename != None:
			perror_exit(oserr.errno, oserr.filename + ':', oserr.strerror)
		else:
			perror_exit(oserr.errno, oserr)


# Perform lexical analysis
def lex():
	global lineno, charno
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
				return None
			elif c.isspace():
				state = 0
			else:
				perror_exit(2, '%s:%d:%d: Invalid character \'%c\' in program' %
					(infile.name, lineno, charno, c))
		elif state == 1:
			if not c.isalnum():
				unget = True
				state = OK
		elif state == 2:
			if not c.isdigit():
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
				perror_exit(2, '%s:%d:%d: Expected \'*\' after \'\\\'' %
					(infile.name, lineno, charno, c))
		elif state == 7:
			if c == '': # EOF
				perror_exit(2, '%s:%d:%d: Unterminated comment' %
					(infile.name, cl, cc))
			elif c == '*':
				state = 8
		elif state == 8:
			if c == '\\':
				del buffer[:]
				state = 0
			else:
				state = 7
		if c.isspace():
			del buffer[-1]
			unget = False
			if c == '\n':
				lineno += 1
				charno = 0

	if unget == True:
		del buffer[-1]
		infile.seek(infile.tell() - 1)
		charno -= 1

	buff_cont = ''.join(buffer)
	if buff_cont not in tokens.keys():
		if buff_cont.isdigit():
			retval = (TokenType.NUMBER, int(buff_cont))
		else:
			retval = (TokenType.IDENT, buff_cont[:30])
	else:
		retval = (tokens[buff_cont],)
	del buffer[:]
	return retval


# Print program usage and exit with exit code: ec
def print_usage(ec=0):
	print('Usage:  %s [OPTIONS] {-i|--input} INFILE' % __file__)
	print('Available options:')
	print('        -h, --help                Display this information')
	print('        -v, --version             Output version information')
	print('        -o, --output OUTFILE      Place output in file: OUTFILE\n')
	sys.exit(ec)


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
			print('CiScal Compiler ', __version__)
			print('Copyright (C) 2017 George Z. Zachos, Andrew Konstantinidis')
			print('This is free software; see the source for copying conditions.')
			print('There is NO warranty to the extent permitted by law.\n')
			sys.exit()
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
	while True:
		tk = lex()
		if tk == None:
			break
		if len(tk) == 1:
			print(tk[0])
		else:
			print(tk[1])


if __name__ == "__main__":
	main(sys.argv[1:])


