\* test-function-1.csc *\

program MyProg {
	declare
		a, b, res
	enddeclare

	function myFunc1(inout a, in b) {

		procedure proc11() {

			function nestedFunct111() {
				return (1);
			}			

			function nestedFunct112() {
				function nestedFunct1121() {
					return (2); 
				}

				procedure proc1122() {
				}		
				a := 10;
				return(3);
			}			

			function nestedFunct113() {
				return (4);
			}			

			k := 10;
		}	
	
		function nestedFunct12() {
			return (5); 
		}			

		if (a < b) {
			a := 8;
			return (0);
		}
	}

	a   := 3;
	b   := 5;
	res := myFunc1(inout a, in b);

}
