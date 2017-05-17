\* test-procedure-0.csc *\

program myProg {
	declare
		a, b
	enddeclare

	procedure proc(in a, inout b) {
		a := a + 1;
		b := b + 1;
	}

	a := 2;
	b := 4;
	call proc(in a, inout b);
	print(a);
	print(b);
}
