import smartpy as sp

class MyContract(sp.Contract):
    def __init__(self, **kargs):
        self.init(x = 0)

    @sp.entry_point
    def entry_point_1(self, params):
        a, b = sp.match_pair(params)
        c, d  = sp.match_pair(b)
        self.data.x += a * c * d

@sp.add_test(name = "Minimal")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Minimal")
    c1 = MyContract()
    scenario += c1
