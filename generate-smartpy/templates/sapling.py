import smartpy as sp

class MyContract(sp.Contract):
    def __init__(self, **kwargs):
        self.init(**kwargs)

    @sp.entry_point
    def entry_point_1(self, params):
        sp.set_type(params.s, sp.TSaplingState(15))
        self.data.y = sp.sapling_verify_update(params.s, params.t)

@sp.add_test(name = "Sapling")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Sapling")

    def h(x):
        sp.set_type(x.a, sp.TSaplingState(12))
        sp.result(sp.sapling_verify_update(x.a, x.b))

    c1 = MyContract(x=12,
                    y = sp.none,
                    z = lambda x: (x+1, sp.sapling_empty_state(8)),
                    h = h)
    scenario += c1
