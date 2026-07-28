import smartpy as sp

class TestContract(sp.Contract):
    @sp.entry_point
    def deposit(self):
        pass

    @sp.entry_point
    def withdraw(self, address, quantity):
        sp.send(address, quantity)

    @sp.entry_point
    def withdraw_all(self, address):
        sp.send(address, sp.balance)

@sp.add_test(name="Test")
def test():
    sc = sp.test_scenario()
    account = sp.test_account("test")
    c = TestContract()
    c.set_initial_balance(sp.mutez(100))
    sc += c
    c.deposit().run(amount = sp.mutez(1000))
    sc.verify(c.balance == sp.mutez(1100))
    c.withdraw(address=account.address, quantity=sp.mutez(200))
    c.withdraw(address=account.address, quantity=sp.mutez(2000)).run(valid=False, exception="Negative balance for KT1TezoooozzSmartPyzzSTATiCzzzwwBFA1")
    sc.verify(c.balance == sp.mutez(900))
    c.withdraw_all(account.address)
    sc.verify(c.balance == sp.mutez(0))
