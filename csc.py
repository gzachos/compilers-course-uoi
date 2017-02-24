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

keywords = ['and','declare','do','else','enddeclare','exit','procedure',\
	'function','print','call','if','in','inout','not','select','program',\
	'or','return','while','default']
buffer   = []

class TokenType(Enum):
	IDENT      = 0 
	NUMDER     = 1
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
	ELSESIM    = 29
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


# Perform lexical analysis
def lex(input_file):
	try:
		infile = open(input_file,'r')
	except OSError as oserr:
		if oserr.filename != None:
			perror_exit(oserr.errno, oserr.filename + ':', oserr.strerror)
		else:
			perror_exit(oserr.errno, oserr)

	state = 0
	ERROR = -1
	OK    = -2
	c = infile.read(1)
	buffer.append(c)
	while state != ERROR and state != OK:
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
			else:
				state = ERROR
		elif state == 1:
			if c.isalnum():
				state = 1
			else:
				state = OK
		elif state == 2:
			if c.isdigit():
				state = 2
			else:
				state = OK
		elif state == 3:
			if c == '=':
				state = OK
			elif c == '>':
				state = OK
			else:
				state = OK
		elif state == 4:
			if c == '=':
				state = OK
			else:
				state = OK
		elif state == 6:
			if c == '*':
				state = 7
			else:
				state = ERROR
		elif state == 7:
			if c == '': # EOF
				state = ERROR
			elif c == '*':
				state = 8
		elif state == 8:
			if c == '\\':
				state = 0
			else:
				state = ERROR
		c = infile.read(1)
		buffer.append(c)


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

	lex(input_file)


if __name__ == "__main__":
	main(sys.argv[1:])


