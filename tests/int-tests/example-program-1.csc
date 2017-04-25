program exams {
	declare
		a, b
	enddeclare
	function P1(in x, inout y) {
		declare
			c, d
		enddeclare
		function P11(in w, inout z) {
			declare
				e
			enddeclare
			function P21(in x) {
				e := x;
				z := w;
				e := P21(in a);
				return (e);
			}
			e := z;
			z := w;
			e := P21(in c);
			return (e);
		}
		function P12(in c) {
			declare
				e
			enddeclare
			e := P11(in e);
			return (e);
		}
		b := 100;
		c := P11(in b, inout c);
		y := b + c;
		return (a);
	}
	a := P1(in a, inout b);
}
