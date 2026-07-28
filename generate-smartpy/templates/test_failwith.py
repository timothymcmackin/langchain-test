import smartpy as sp

class C1(sp.Contract):
    def __init__(self):
        self.init(f = sp.none)

    @sp.entry_point
    def ep(self):
        def f(x):
            sp.if x == 0:
                sp.failwith("zero")
            sp.else:
                sp.result(1)
        self.data.f = sp.some(f)

class C2(sp.Contract):
    @sp.entry_point
    def ep(self, params):
        sp.if params == 0:
            sp.failwith("zero")
        sp.else:
            sp.failwith("non-zero")

class C3(sp.Contract):
    def __init__(self):
        self.init(x = 1)

    @sp.entry_point
    def ep1(self):
        sp.failwith("A")
        sp.failwith("B")

    @sp.entry_point
    def ep2(self):
        sp.failwith("A")
        self.data.x = 2

@sp.add_test(name = "Test")
def test():
    scenario = sp.test_scenario()
    scenario += C1()
    scenario += C2()
    scenario += C3()
