import smartpy as sp

class A(sp.Contract):
    @sp.entry_point
    def ep1(self, param):
        sp.set_type(param, sp.TUnit)

    @sp.entry_point
    def ep2(self, param):
        sp.set_type(param, sp.TContract(sp.TTimestamp))

class B(sp.Contract):
    def __init__(self, a):
        self.init(a = a)

    @sp.entry_point
    def ep3(self, param):
        sp.set_type(param, sp.TBool)

        ep2 = sp.contract(sp.TContract(sp.TTimestamp),
            self.data.a,
            entry_point = 'ep2'
        ).open_some()

        ep4 = sp.self_entry_point(entry_point = 'ep4')
        sp.set_type(ep4, sp.TContract(sp.TTimestamp))

        sp.transfer(ep4, sp.mutez(0), ep2)

    @sp.entry_point
    def ep4(self, result):
        sp.set_type(result, sp.TTimestamp)

class Unrelated(sp.Contract):
    def __init__(self):
        self.init(x = "abc")

@sp.add_test(name = "test")
def test():
    scenario = sp.test_scenario()

    a = A()
    scenario += a
    b = B(a = a.address)

    scenario += b
    b.ep3(True)
    scenario += Unrelated()

sp.add_compilation_target("self_entry_point", A())
