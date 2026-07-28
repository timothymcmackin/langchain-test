import smartpy as sp

class C(sp.Contract):
    @sp.entry_point
    def ep(self):
        x = sp.local('x', sp.record(a = sp.nat(1), b = sp.nat(2)))
        x.value.a = 15

    @sp.entry_point
    def ep2(self, params):
        sp.set_type(params, sp.TPair(sp.TInt, sp.TNat))

@sp.add_test(name = "LocalRecord")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Local record")
    scenario += C()

sp.add_compilation_target("testLocalRecord", C())
