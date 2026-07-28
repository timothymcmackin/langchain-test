import smartpy as sp

class Test(sp.Contract):
    def __init__(self):
        self.init(a = sp.nat(1234567))

    @sp.entry_point
    def test_and(self, x):
        self.data.a = self.data.a & x

    @sp.entry_point
    def test_or(self, x):
        self.data.a = self.data.a | x

    @sp.entry_point
    def test_exclusive_or(self, x):
        self.data.a = self.data.a ^ x

    @sp.entry_point
    def test_shift_right(self, x):
        self.data.a = self.data.a >> x

    @sp.entry_point
    def test_shift_left(self, x):
        self.data.a = self.data.a << x

@sp.add_test(name = "test")
def test():
    scenario = sp.test_scenario()
    c1 = Test()
    scenario += c1
    c1.test_and(10)
    scenario.verify(c1.data.a == 2)
    c1.test_or(10)
    scenario.verify(c1.data.a == 10)
    c1.test_exclusive_or(9)
    scenario.verify(c1.data.a == 3)
    c1.test_shift_left(10)
    scenario.verify(c1.data.a == 3072)
    c1.test_shift_right(10)
    scenario.verify(c1.data.a == 3)

sp.add_compilation_target("compilation", Test())
