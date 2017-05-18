\* test-function-3.csc *\

program myProg {
	declare
		a, x
	enddeclare

	function f(inout a) {
		return (a*10);
	}

	x := 4;
	a := f(in x);
	print(a);
}
