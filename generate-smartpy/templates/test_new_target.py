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

@sp.add_target(name = "orig", kind = "origination")
def origin():
    scenario = sp.test_scenario()
    c1 = MyContract(x=12)
    scenario += c1
