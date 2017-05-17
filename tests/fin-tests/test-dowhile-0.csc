\* test-dowhile-0.csc  *\

program MyProg {
	declare
		a, b
	enddeclare

	a := 0;
	b := 100;
	do {
		a := a + 2;
		print(a);
		if (a = 50) {
			exit
		}
	}
	while (a <= b);
}
