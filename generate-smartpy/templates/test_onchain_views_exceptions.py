import smartpy as sp

class Test(sp.Contract):
    def __init__(self):
        self.init(value = 0)

    @sp.offchain_view()
    def other(self, x):
        sp.result(1 + x)

if "templates" not in __name__:
    @sp.add_test(name="Test")
    def test():
        scenario = sp.test_scenario()
        provider = sp.address("KT1")
        scenario.verify(sp.catch_exception(sp.view("a_view", provider, 0, t = sp.TNat)) == sp.some("Missing contract for view"))
        c1 = Test()
        scenario += c1
        scenario.verify(c1.other(42) == 43)
        scenario.verify(sp.view("other", c1.address, 1, t = sp.TIntOrNat) == sp.some(2))
        scenario.verify(sp.catch_exception(sp.view("other", c1.address, 1, t = sp.TInt) == sp.some(2)) == sp.some("Type error in view"))
        scenario.verify(sp.catch_exception(sp.view("missing_view", c1.address, 1)) == sp.some("Missing view missing_view in contract KT1TezoooozzSmartPyzzSTATiCzzzwwBFA1"))

    @sp.add_test(name="Test_view_no_exception")
    def test2():
        scenario = sp.test_scenario()
        scenario.add_flag("no-view-check-exception")
        provider = sp.address("KT1")
        scenario.verify(sp.view("a_view", provider, 0, t = sp.TNat) == sp.none)
        c1 = Test()
        scenario += c1
        scenario.verify(c1.other(42) == 43)
        scenario.verify(sp.view("other", c1.address, 1, t = sp.TIntOrNat) == sp.some(2))
        scenario.verify(sp.view("other", c1.address, 1) == sp.some(2))
        scenario.verify(sp.view("missing_view", c1.address, 1) == sp.none)
        scenario.verify(sp.view("other", c1.address, 1, t = sp.TInt) == sp.none)
