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

__version__='0.0.1'


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

	c = infile.read(1)
	while c:
		if c != '\n' and not c.isspace():
			print("%c" % c)
		c = infile.read(1)


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


