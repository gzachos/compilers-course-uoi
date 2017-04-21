\* test-dowhile-1.csc *\

program MyProg {
	declare
		a, b
	enddeclare

	a := 0;
	b := 100;

	do {
		if (a = b) {
			b := 10;
			exit;
		};
		a := a + 1;
	}
	while(10 = 10);
}
