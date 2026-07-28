import smartpy as sp

class MyContract(sp.Contract):
    def __init__(self):
        self.init_type(t = sp.TRecord(a = sp.TInt, b = sp.TBool))

    @sp.entry_point
    def f(self, params):
        self.data.a += params

class MyContract2(sp.Contract):
    @sp.entry_point
    def f(self, params):
        self.data.a = 2 * params

@sp.add_test(name = "TypeOnly")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Init Type Only")
    c1 = MyContract()
    scenario += c1
    c2 = MyContract()
    c2.init_storage(sp.record(a = 12, b = True))
    scenario += c2
    c2.f(5)

    c3 = MyContract2()
    scenario += c3
    c4 = MyContract2()
    c4.init_storage(sp.record(a = 12, b = True))
    scenario += c4
    c4.f(5)

sp.add_compilation_target("type_only", MyContract())

sp.add_compilation_target("type_and_storage", MyContract(), storage = sp.record(a = 12, b = True))

sp.add_compilation_target("type_and_storage_parameters", MyContract(),
               storage = sp.record(a = 12, b = True),
               parameters = [("f", 5),
                             ("f", 12)]
               )
