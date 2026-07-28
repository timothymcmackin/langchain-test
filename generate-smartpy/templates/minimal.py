import smartpy as sp

class MyContract(sp.Contract):
    def __init__(self, **kargs):
        self.init(**kargs)

    @sp.entry_point
    def entry_point_1(self):
        pass

@sp.add_test(name = "Minimal")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Minimal")
    c1 = MyContract(x=12)
    scenario += c1

# A contract with an empty (unit) storage
sp.add_compilation_target("min_comp", MyContract())

# A contract with a simple int storage
sp.add_compilation_target("min_comp_int", MyContract(x = 1))
