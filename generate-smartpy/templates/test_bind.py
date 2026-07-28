import smartpy as sp

class MyContract(sp.Contract):
    def __init__(self, **kargs):
        self.init(x = 12, y = 0)

    def f(self, params):
        b = sp.bind_block()
        with b:
            sp.result(self.data.x + params)
        return b.value

    @sp.inline_result
    def g(self, params):
        sp.result(self.data.x + params)

    @sp.entry_point
    def call_f(self, params):
        self.data.x = self.f(params)
        self.data.x = self.f(5)
        self.data.x = self.g(32)

@sp.add_test(name = "Bind")
def test():
    scenario = sp.test_scenario()
    c1 = MyContract()
    scenario += c1
