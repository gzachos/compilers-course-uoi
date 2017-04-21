\* test-expression-4.csc *\

program MyProg {
	
	\* The following statement should trigger a syntax error.
	 * The minus sign is not a unary operator but an optional
	 * sign to the whole expression. That expression is the
	 * positive number constant: 32768 > MAX_INT = 32767.
	 *\
	a := -32768;

}
