program a {
	declare
		A, b, g, f
	enddeclare

	function P1(in X, inout Y) {
		declare
			e, f
		enddeclare

		function P11(inout X) {
			declare
				e
			enddeclare

			e := A;
			X := Y;
			f := b;
			return (e);
		}
		b := X;
		e := P11(inout X);
		e := P1(in X, inout Y);
		X := b;
		return (e);
	}

	if (b>1 and f<2 or g+1<f+b) {
		f := P1(in g);
	}
	else {
		f := 1;
	}
}
