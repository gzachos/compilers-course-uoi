\* test-dowhile-2.csc *\

program MyProg {
	declare
		a, b, c
	enddeclare

	a := 0;
	b := 100;
	c := 4;	

	do {
		do {
			a := a + 1;
			if (a >= b) {
				a := a - 2;
				if (a < b) {
					exit;
				}
			}
		}
		while(a < c);

		if (a = b) {
			b := 100;
			exit;
		};
		a := a + 1;
	}
	while(10 = 10);
}
