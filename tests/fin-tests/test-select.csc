\* test-select.csc *\

program myProg {
	declare
		a, b
	enddeclare

	a := 2;
	b := 5;

	select (a)
		1: print(1);
		2: print(2);
		3: print(3);
		4: print(4);
		default: print(-1);
	;

	select (b)
		1: print(1);
		2: print(2);
		3: print(3);
		4: print(4);
		default: print(-1);
	;
}
