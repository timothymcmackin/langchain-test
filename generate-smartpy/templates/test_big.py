import smartpy as sp

class Pack(sp.Contract):
    @sp.entry_point
    def run(self):
        for x in [sp.nat(x) for x in range(1000)]:
            sp.verify(x == x)

@sp.add_test(name = "Big")
def test():
    scenario = sp.test_scenario()
    c1 = Pack()
    scenario += c1
