import smartpy as sp

class C1(sp.Contract):
    pass

class C2(sp.Contract):
    @sp.entry_point
    def ep(self):
        pass

@sp.add_test(name = "Void")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Void / Unit")
    scenario += C1()
    scenario += C2()

sp.add_compilation_target("testVoid", C1())
