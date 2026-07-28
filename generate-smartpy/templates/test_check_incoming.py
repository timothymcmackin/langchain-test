import smartpy as sp

class MyContract(sp.Contract):
    def __init__(self, **kargs):
        self.init(**kargs)

    @sp.entry_point(check_no_incoming_transfer=False)
    def transfer_OK(self):
        pass

    @sp.entry_point(check_no_incoming_transfer=True)
    def transfer_KO(self):
        pass

    @sp.entry_point
    def any_ep(self):
        pass

    @sp.entry_point(lazify=True)
    def any_lazy_ep(self):
        pass

@sp.add_test(name = "Minimal")
def test():
    scenario = sp.test_scenario()

    c1 = MyContract(x=12)
    scenario += c1

    scenario.add_flag("default-check-no-incoming-transfer")

    c2 = MyContract(x=12)
    scenario += c2

    c1.transfer_OK().run(amount=sp.mutez(0))
    c1.transfer_KO().run(amount=sp.mutez(0))
    c1.any_ep().run(amount=sp.mutez(0))
    c1.any_lazy_ep().run(amount=sp.mutez(0))

    c2.transfer_OK().run(amount=sp.mutez(0))
    c2.transfer_KO().run(amount=sp.mutez(0))
    c2.any_ep().run(amount=sp.mutez(0))
    c2.any_lazy_ep().run(amount=sp.mutez(0))

    c1.transfer_OK().run(amount=sp.mutez(10))
    c1.transfer_KO().run(amount=sp.mutez(10)).run(valid=False)
    c1.any_ep().run(amount=sp.mutez(10))
    c1.any_lazy_ep().run(amount=sp.mutez(10))

    c2.transfer_OK().run(amount=sp.mutez(10))
    c2.transfer_KO().run(amount=sp.mutez(10)).run(valid=False)
    c2.any_ep().run(amount=sp.mutez(10)).run(valid=False)
    c2.any_lazy_ep().run(amount=sp.mutez(10)).run(valid=False)



sp.add_compilation_target("min_comp", MyContract())
