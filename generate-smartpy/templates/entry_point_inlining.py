import smartpy as sp

class MyContract(sp.Contract):
    def __init__(self, **kargs):
        #self.verbose = True
        self.init(**kargs)

    @sp.entry_point
    def entry_point_1(self):
        self.f.f(self, 12)
        self.g.f(self, 15)

    @sp.entry_point(private = True)
    def f(self, params):
        self.data.x += params

    @sp.entry_point
    def g(self, params):
        self.data.x += params

class M2(MyContract):
    @sp.entry_point(private = True)
    def f(self, params):
        super().f.f(self, params + 1000)
        self.data.x += 3

@sp.add_test(name = "entry_point_inlining")
def test():
    scenario = sp.test_scenario()
    c = MyContract(x=11)
    scenario += c
    c.g(1)
    c2 = M2(x=12)
    scenario += c2
