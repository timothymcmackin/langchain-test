import smartpy as sp

class C(sp.Contract):
    def __init__(self, flag):
        if flag: self.add_flag(flag)
        self.init(x = sp.map(tkey = sp.TRecord(a = sp.TNat, b = sp.TAddress, c = sp.TNat), tvalue = sp.TUnit))

    @sp.entry_point
    def ep(self):
        sp.verify(self.data.x.contains(sp.record(a = 0, b = sp.sender, c = 0)))

@sp.add_test(name = "annots")
def test():
        scenario = sp.test_scenario()
        scenario += C("initial-cast")
        scenario += C("erase-var-annots")
        scenario += C("no-pairn")
        scenario += C(None)
