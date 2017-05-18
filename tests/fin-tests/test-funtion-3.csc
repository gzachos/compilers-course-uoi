\* test-function-3.csc *\

program myProg {
	declare
		a, b, x
	enddeclare

	function f1(in a, inout b) {
		b := b + 1;
		a := a + 1;
		return (a*10);
	}

	function f2(in x, inout y) {
		x := x + 5;
		y := y + 5;
		return (x);
	}

	a := 2;
	b := 4;
	x := f1(in a, inout b);
	print(a);
	print(b);
	print(x);

	x := f2(in a, inout b);
	print(a);
	print(b);
	print(x);
}
