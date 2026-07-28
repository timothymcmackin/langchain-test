import smartpy as sp

class Receiver(sp.Contract):
    @sp.entry_point
    def receive_and_check(self, sender_balance, receiver_balance):
        sp.verify(sender_balance == sp.view("get_balance", sp.sender, sp.unit, sp.TMutez).open_some())
        sp.verify(receiver_balance == sp.balance)

class Sender(sp.Contract):
    @sp.entry_point
    def send(self, a):
        c = sp.contract(sp.TRecord(sender_balance=sp.TMutez, receiver_balance=sp.TMutez), a, entry_point = "receive_and_check").open_some()
        sp.transfer(sp.record(sender_balance=sp.tez(110), receiver_balance=sp.tez(1)), sp.tez(1) , c)
        sp.transfer(sp.record(sender_balance=sp.tez(100), receiver_balance=sp.tez(11)), sp.tez(10), c)

    @sp.onchain_view()
    def get_balance(self):
        sp.result(sp.balance)

if "templates" not in __name__:
    @sp.add_test(name="Test")
    def test():
        sc = sp.test_scenario()

        sender = Sender()
        sender.set_initial_balance(sp.tez(111))
        sc += sender

        receiver = Receiver()
        sc += receiver

        sender.send(receiver.address)
