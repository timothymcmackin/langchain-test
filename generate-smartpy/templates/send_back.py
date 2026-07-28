import smartpy as sp

class MyContract(sp.Contract):
    def __init__(self, flag = [], **kargs):
        if flag:
            self.add_flag(*flag)
        self.init(**kargs)

    @sp.entry_point
    def bounce(self):
        sp.send(sp.source, sp.amount)

    @sp.entry_point
    def bounce2(self):
        sp.send(sp.source, sp.tez(1))
        sp.send(sp.source, sp.amount - sp.tez(1))

@sp.add_test(name = "Test")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Send Back")
    scenario += MyContract()
    scenario += MyContract(flag = ["lazy-entry-points"])

sp.add_compilation_target("send_back", MyContract())
