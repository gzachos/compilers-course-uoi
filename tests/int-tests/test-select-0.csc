\* test-select-0.csc *\

program MyProg {
	declare
		a, myvar
	enddeclare

	myvar := 8;
	
	select(myvar)
		1: a:= 2;
		2: a:= 3;
		3: a:= 4;
        default: a:= 5;

}
