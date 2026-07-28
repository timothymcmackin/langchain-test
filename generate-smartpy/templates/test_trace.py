import smartpy as sp

class A(sp.Contract):
    @sp.entry_point
    def f(self, x):
        sp.trace(x * 2)
        sp.trace("double")

@sp.add_test(name = "Trace")
def test():
    scenario = sp.test_scenario()
    c1 = A()
    scenario += c1
    c1.f(12)
