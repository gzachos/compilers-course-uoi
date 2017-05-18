\* test-function-0.csc *\

program myProg {
	declare
		a, x
	enddeclare

	function f(in a) {
		return (a*10);
	}

	x := 4;
	a := func(in x);
	print(a);
}
