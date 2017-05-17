\* test-expression-1.csc *\

program myProg {
	declare
		a, x, y, z, w
	enddeclare

	x := 4;
	y := 2;
	z := 1;
	w := 2;
	a := -x + (y + (-z)) * w;
	print(a);
}
