import smartpy as sp

class Test(sp.Contract):
    def __init__(self):
        self.init(value = 0)

    @sp.offchain_view()
    def other(self, x):
        sp.verify(x < self.data.value)
        sp.result(x * x)

    @sp.offchain_view()
    def square_exn(self, x):
        sp.set_type(x, sp.TInt)
        sp.failwith(x * x)

if "templates" not in __name__:
    @sp.add_test(name = "Test")
    def test():
        scenario = sp.test_scenario()
        c = Test()
        scenario += c
        scenario.compute(c.other(-5))
        scenario.verify(sp.is_failing(c.other(5)))
        scenario.verify(~ sp.is_failing(c.other(-5)))
        scenario.verify(sp.catch_exception(c.other(5)) == sp.some("WrongCondition: params < self.data.value"))
        scenario.verify(sp.catch_exception(c.other(5), t = sp.TString) == sp.some("WrongCondition: params < self.data.value"))
        scenario.verify(sp.catch_exception(c.other(-5), t = sp.TString) == sp.none)
        scenario.verify(sp.catch_exception(c.other(-5), t = sp.TInt) == sp.none)
        scenario.verify(sp.catch_exception(c.square_exn(-5), t = sp.TInt) == sp.some(25))
