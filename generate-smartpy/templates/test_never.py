import smartpy as sp

class MyContract(sp.Contract):
    def __init__(self, **kargs):
        self.init(**kargs)

    @sp.entry_point
    def entry_point_1(self, params):
        x = sp.bind_block("x")
        with x:
            with params.match_cases() as p:
                with p.match("A") as arg:
                    sp.result(arg + 12)
                with p.match("B") as arg:
                    sp.never(arg)
        self.data.x = x.value

@sp.add_test(name = "Never")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Never")
    c1 = MyContract(x=0)
    scenario += c1
