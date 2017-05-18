\* test-function-0.csc *\

program myProg {
	declare
		a, x
	enddeclare

	procedure p(inout a) {
		a := a + 1;
	}

	x := 4;
	call proc(inout x);
	print(a);
}
