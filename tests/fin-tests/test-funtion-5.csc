\* test-function-5.csc *\

program myProg {
	declare
		a, x
	enddeclare

	function factorial(in n) {
		if (n <= 1) {
			return (1);
		};
		return (n * factorial(in n-1));
	}

	a := 12;
	x := factorial(in a);
	print(a);
	print(x);
}
