import smartpy as sp

class TestAddressComparison(sp.Contract):
    @sp.entry_point
    def test(self, x):
        sp.verify(sp.utils.mutez_to_nat(sp.amount) == x)
        sp.verify(sp.utils.nat_to_mutez(x) == sp.amount)

    @sp.entry_point
    def test_diff(self, x, y):
        sp.compute(x - y)

@sp.add_test(name = "Test")
def test():
    scenario = sp.test_scenario()
    c1 = TestAddressComparison()

    scenario.register(c1)

    c1.test(10).run(amount = sp.mutez(10))
    c1.test(10000000).run(amount = sp.tez(10))
    c1.test_diff(x=sp.mutez(100), y=sp.mutez(50))
    c1.test_diff(x=sp.mutez(70), y=sp.mutez(100)).run(valid=False)


class MyContract(sp.Contract):
    def __init__(self):
        self.init(result = sp.none)

    @sp.entry_point
    def store(self, params):
        self.data.result = sp.some(params)

    @sp.entry_point
    def decrease(self, params):
        self.data.result = sp.some(self.data.result.open_some() - params)

    @sp.entry_point
    def sub(self, params):
        self.data.result = sp.sub_mutez(params.x, params.y)

if "templates" not in __name__:
    @sp.add_test(name="Test2")
    def test():
        scenario = sp.test_scenario()
        c1 = MyContract()
        scenario += c1
        c1.store(sp.mutez(42))
        c1.decrease(sp.mutez(22))
        c1.decrease(sp.mutez(22)).run(valid=False)
        c1.sub(sp.record(x = sp.mutez(1), y = sp.mutez(2)))
        scenario.verify(c1.data.result == sp.none)
        c1.sub(sp.record(x = sp.mutez(100), y = sp.mutez(1)))
        scenario.verify(c1.data.result == sp.some(sp.mutez(99)))
