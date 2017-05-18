\* test-function-4.csc *\

program myProg {
	declare
		a, b, x
	enddeclare

	function f(in a, in b) {
		a := a + 1;
		b := b + 1;
		if (a = 3) {
			return (f(in a, in b));
		};
		return (a*10);
	}

	a := 2;
	b := 4;
	x := f(in a, in b);
	print(a);
	print(b);
	print(x);
}
