\* test-procedure-0.csc *\

program MyProg {
	declare
		a, b
	enddeclare

	procedure p1(in a, inout b) {
		b := a * 10;
	}

	a := 4;
	call p1(in a, inout b);

}
