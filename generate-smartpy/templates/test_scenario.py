import smartpy as sp

class C(sp.Contract):
    def __init__(self, x):
        self.init(x = x)

    @sp.entry_point
    def ep(self, x):
        self.data.x = sp.some(x)

class C2(sp.Contract):
    def __init__(self, sv):
        self.sv = sv
        self.init()

    @sp.entry_point
    def ep2(self):
        f = sp.local("f", sp.build_lambda(lambda _: self.sv))
        sp.verify(f.value(0) == 43)

@sp.add_test(name = "Test")
def test():
    s = sp.test_scenario()

    c = C(sp.none)
    s += c
    s.verify(c.data.x == sp.none)
    v1 = s.compute(421)
    v2 = s.compute(43)
    s += C(sp.some(v1))
    c.ep(v1)

    c2 = C2(v2)
    s += c2
    c2.ep2()
