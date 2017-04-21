program MyProgram {

	declare
		a, b, c, d
	enddeclare

	function add(in x, in y) {
		return (x + y)
	}

	procedure p(inout x) {
		declare
			res
		enddeclare

		function f(in x) {
			declare
				i
			enddeclare
			
			i := 10 + x;
			return (i);
		}		

		res := f(in 4);
		if (not [res = 0])
			x := res;
		else
			x := -1; 

	}

	a := 0;
	b := 10;

	while (a <= b) {
		c := add(in a, in b);
		a := a + 1
	};

	do {
		c := c - 5;
		if (c > b)
			exit;
	} while (1 = 1);

	select(c)
		1: d := c * 2;
		2: d := c + 4;
		3: d := c - 8 * 12;
		default: {d := 2; b := 7}
	;

	call p(inout d);
	print(d)

}
