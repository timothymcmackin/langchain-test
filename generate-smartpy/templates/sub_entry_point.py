import smartpy as sp

class MyContract(sp.Contract):
    def __init__(self):
        self.init(x = 2, y = "aaa", z = 0)

    @sp.private_lambda(with_storage="read-write", with_operations=True, wrap_call=True)
    def a(self, params):
        sp.set_type(params, sp.TNat)
        sp.send(sp.test_account("alice").address, sp.mul(params, sp.tez(1)))
        sp.send(sp.test_account("bob").address, sp.tez(2))
        self.data.x += 1
        sp.result(params  * self.data.x)

    @sp.sub_entry_point
    def b(self, params):
        sp.set_type(params, sp.TNat)
        sp.send(sp.test_account("alice").address, sp.mul(params, sp.tez(1)))
        sp.send(sp.test_account("bob").address, sp.tez(2))
        self.data.x += 1
        sp.result(params  * self.data.x)

    @sp.entry_point
    def f(self):
        self.data.z = self.a(5) + self.a(10)

    @sp.entry_point
    def g(self):
        self.data.z = self.a(6)

@sp.add_test(name = "Sub")
def test():
    scenario = sp.test_scenario()
    c1 = MyContract()
    c1.set_initial_balance(sp.tez(1000))
    scenario += c1
    c1.f()
    scenario.verify(c1.data == sp.record(x = 4, z = 55, y = "aaa"))

sp.add_compilation_target("sub_entry_point", MyContract())
