\* test-function-2.csc *\

program myProg {
	declare
		a, b, x
	enddeclare

	function f(in a, inout b) {
		b := b + 1;
		a := a + 1;
		return (a*10);
	}

	a := 2;
	b := 4;
	x := f(in a, inout b);
	print(a);
	print(b);
	print(x);
}
