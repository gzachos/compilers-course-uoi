\* test-function-1.csc *\

program myProg {
	declare
		a, x
	enddeclare

	function f(in a) {
		return (a*10);
	}

	x := 4;
	a := f(in 10*x);
	print(a);
}
