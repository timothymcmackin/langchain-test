# Div - Example for illustrative purposes only.

import smartpy as sp

class TestDiv(sp.Contract):
    def __init__(self):
        self.init(a = sp.none,
                  b = sp.none,
                  c = sp.none,
                  d = sp.none,
                  e = sp.none,
                  f = sp.none,
                  g = sp.none,
                  h = sp.none,
                  i = sp.none,
                  j = sp.none,
                  k = sp.none,
                  l = sp.none,
                  m = sp.none
        )

    @sp.entry_point
    def test(self, params):
        self.data.a = sp.ediv(1, 0)
        self.data.b = sp.ediv(-1, 0)
        self.data.c = sp.ediv(1, 12)
        self.data.d = sp.ediv(-1, 12)
        self.data.e = sp.ediv(-1, -12)
        self.data.f = sp.ediv(15, 12)
        self.data.g = sp.ediv(-15, 12)
        self.data.h = sp.ediv(-15, -12)
        self.data.i = sp.ediv(sp.tez(2), sp.mutez(100))
        self.data.j = sp.ediv(sp.tez(2), sp.mutez(101))
        self.data.k = sp.ediv(sp.tez(2), sp.tez(100))
        self.data.l = sp.ediv(sp.tez(2), 15)
        self.data.m = sp.ediv(sp.amount, sp.set_type_expr(params, sp.TNat))

@sp.add_test(name = "Div")
def test():
    c1 = TestDiv()
    scenario = sp.test_scenario()
    scenario.h1("Division")
    scenario += c1
    c1.test(2000).run(amount = sp.tez(2))
    scenario.show(c1.data)
    scenario.verify_equal(c1.data, sp.record(a = sp.none, b = sp.none, c = sp.some((0, 1)), d = sp.some((-1, 11)), e = sp.some((1, 11)), f = sp.some((1, 3)), g = sp.some((-2, 9)), h = sp.some((2, 9)), i = sp.some((20000, sp.tez(0))), j = sp.some((19801, sp.mutez(99))), k = sp.some((0, sp.tez(2))), l = sp.some((sp.mutez(133333), sp.mutez(5))), m = sp.some((sp.mutez(1000), sp.tez(0)))))

sp.add_compilation_target("testDiv", TestDiv())
