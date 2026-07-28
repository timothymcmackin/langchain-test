import smartpy as sp

class InitialBalance(sp.Contract):
    def __init__(self):
        self.init(x = 2)

    @sp.private_lambda(with_storage="read-write", wrap_call=True)
    def sub(self, params):
        self.data.x = 3

class InitialBalance2(sp.Contract):
    def __init__(self):
        self.set_initial_balance(sp.tez(2))
        self.init(x = 2)

    @sp.private_lambda(with_storage="read-write", wrap_call=True)
    def sub(self, params):
        self.data.x = 3

class InitialBalance3(sp.Contract):
    def __init__(self):
        self.init(x = 3)
        self.set_initial_balance(sp.tez(3))

    @sp.private_lambda(with_storage="read-write", wrap_call=True)
    def sub(self, params):
        self.data.x = 3

@sp.add_test(name = "Sub")
def test():
    scenario = sp.test_scenario()

    initialBalance = sp.mutez(123)

    c1 = InitialBalance()
    c1.set_initial_balance(initialBalance)
    scenario += c1
    scenario.verify(c1.balance == initialBalance)

    c2 = InitialBalance2()
    scenario += c2
    scenario.verify(c2.balance == sp.tez(2))

    c3 = InitialBalance3()
    scenario += c3
    scenario.verify(c3.balance == sp.tez(3))
