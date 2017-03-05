class Token():
    def __init__(self, tktype, tkval, tkl, tkc):
        self.tktype, self.tkval, self.tkl, self.tkc = tktype, tkval, tkl, tkc

    def __str__(self):
        return  '(' + str(self.tktype)+ ', \'' + str(self.tkval) \
                + '\', ' + str(self.tkl) + ', ' + str(self.tkc) + ')'
