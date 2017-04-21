\* test-function-0.csc *\

program MyProg {

	function p1() {
		return (1);
	}

	function p2() {
		function p21() {
			return (2);
		}

		function p22() {
			return (3);
		}
		return (4);
	}

}
