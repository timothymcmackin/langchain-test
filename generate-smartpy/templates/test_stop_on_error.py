import smartpy as sp

class MyContract(sp.Contract):
    def __init__(self, **kargs):
        self.init(**kargs)

    @sp.entry_point
    def entry_point_1(self):
        pass

@sp.add_test(name = "Test")
def test():
    scenario = sp.test_scenario()
    c1 = MyContract(x=12)
    scenario += c1
    scenario.verify(c1.data.x == 12)
    scenario.verify(c1.data.x == 13)
    scenario.verify(c1.data.x == 14)
    scenario.add_flag("stop-on-error")
    scenario.verify(c1.data.x == 12)
    scenario.verify(c1.data.x == 13)
    scenario.verify(c1.data.x == 14)

@sp.add_test(name = "Test2")
def test2():
    scenario = sp.test_scenario()
    c1 = MyContract(x=12)
    scenario += c1
    scenario.add_flag("stop-on-error")
    scenario.verify(c1.data.x == 12)
    scenario.verify(c1.data.x == 13)
    scenario.verify(c1.data.x == 14)

sp.add_compilation_target("comp", MyContract(x = 1))
