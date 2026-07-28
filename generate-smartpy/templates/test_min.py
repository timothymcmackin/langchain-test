import smartpy as sp

class C(sp.Contract):
    def __init__(self): self.init(r = 0)

    @sp.entry_point
    def ep1(self):
        a = sp.local("a", 1)
        b = sp.local("b", 2)
        self.data.r = sp.min(a.value, b.value)

    @sp.entry_point
    def ep2(self):
        a = sp.local("a", 3)
        b = sp.local("b", 4)
        self.data.r = sp.max(a.value, b.value)

    @sp.entry_point
    def ep1b(self, params):
        a = sp.local("a", params)
        b = sp.local("b", 2)
        self.data.r = sp.min(a.value, b.value)

    @sp.entry_point
    def ep2b(self, params):
        a = sp.local("a", params)
        b = sp.local("b", 4)
        self.data.r = sp.max(a.value, b.value)

@sp.add_test(name = "Min")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Min / Max")
    c = C()
    scenario += c
    c.ep1()
    scenario.verify(c.data.r == 1)
    c.ep2()
    scenario.verify(c.data.r == 4)
    c.ep1b(1)
    scenario.verify(c.data.r == 1)
    c.ep2b(3)
    scenario.verify(c.data.r == 4)

sp.add_compilation_target("testMin", C())
