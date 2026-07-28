import smartpy as sp

class TestUnification(sp.Contract):
    def __init__(self):
        self.init(x = sp.none)

    @sp.entry_point
    def push(self, params):
        self.data.x = sp.some(params)

if "templates" not in __name__:
    @sp.add_test(name = "TestUnification")
    def test():
        scenario = sp.test_scenario()
        c1 = TestUnification()
        scenario += c1
        c1.push(4)
