import smartpy as sp

class ArgumentOrderOfEntryPoints(sp.Contract):
    def __init__(self):
        self.init(a = 1, b = "", c = True)

    @sp.entry_point(
        parameter_type = sp.TRecord(a = sp.TNat, b = sp.TString, c = sp.TBool).layout(("a", ("c", "b")))
    )
    def ep1(self, a, c, b):
        self.data.b = b
        self.data.a = a
        self.data.c = c

    @sp.entry_point
    def ep2(self, c, a, b):
        sp.set_type(a, sp.TInt)
        sp.set_type(c, sp.TBool)
        sp.set_type(b, sp.TString)

    @sp.entry_point(parameter_type = sp.TString)
    def ep3(self, param):
        self.data.b = param

@sp.add_test(name = "ArgumentOrderOfEntryPoints_test")
def test():
    scenario = sp.test_scenario()
    c1 = ArgumentOrderOfEntryPoints()
    scenario += c1
    c1.ep1(a = 1, c = True, b = "")
    c1.ep2(a = 1, c = True, b = "")
    c1.ep3("test")

sp.add_compilation_target("ArgumentOrderOfEntryPoints_compilation", ArgumentOrderOfEntryPoints())
