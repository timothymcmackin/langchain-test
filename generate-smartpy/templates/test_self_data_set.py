import smartpy as sp

t = sp.TRecord(address = sp.TOption(sp.TInt))

class Test(sp.Contract):
    def __init__(self):
        self.init_type(t)
    @sp.entry_point
    def a(self, params):
        self.data = params
    @sp.entry_point
    def b(self, params):
        self.data.address = params

@sp.add_test(name = "Tests")
def test():
    scenario = sp.test_scenario()
    scenario.add_flag("no-initial-cast")
    scenario += Test()
