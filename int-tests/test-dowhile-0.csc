\* test-dowhile-0.csc *\

program MyProg {
	declare
		a, b
	enddeclare

	a := 0;
	b := 10;	

	do {
		a := a + 1;
	}
	while(a < b);
}
