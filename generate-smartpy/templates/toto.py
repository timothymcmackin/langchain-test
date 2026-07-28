import smartpy as sp
class C(sp.Contract):
    @sp.entry_point
    def ep(self, params):
        sp.set_type(params, sp.TList(sp.TVariant(V1 = sp.TRecord(b = sp.TString, a = sp.TBool).layout(("b", "a")), V2 = sp.TNat).layout(("V2", "V1"))))
@sp.add_test(name = "C")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Toto")
    c = C()
    scenario += c
    c.ep([ sp.variant("V1", sp.record(a = False, b = "BBB")) ])
