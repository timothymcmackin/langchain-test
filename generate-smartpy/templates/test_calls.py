import smartpy as sp

class Default1(sp.Contract):
    @sp.entry_point
    def default(self):
        self.update_initial_storage(x = sp.tez(0))
        self.data.x = sp.amount

class Default2(sp.Contract):
    @sp.entry_point
    def default(self):
        self.update_initial_storage(x = sp.tez(0))
        self.data.x = sp.amount

    @sp.entry_point
    def other(self):
        pass

class Regular_annotation1(sp.Contract):
    @sp.entry_point
    def reg_annot(self):
        self.update_initial_storage(x = sp.tez(0))
        self.data.x = sp.amount

class Regular_annotation2(sp.Contract):
    @sp.entry_point
    def reg_annot(self):
        self.update_initial_storage(x = sp.tez(0))
        self.data.x = sp.amount

    @sp.entry_point
    def other(self):
        pass

class No_annotation(sp.Contract):
    def __init__(self):
        self.add_flag("no-single-entry-point-annotation")
        self.init(x=sp.tez(0))

    @sp.entry_point
    def no_annot(self):
        self.data.x = sp.amount

class Test(sp.Contract):
    @sp.entry_point
    def send(self, address, amount):
        sp.send(address, amount)

@sp.add_test(name = "Test")
def test():
    scenario = sp.test_scenario()
    target_default1 = Default1()
    target_default2 = Default2()
    target_regular1 = Regular_annotation1()
    target_regular2 = Regular_annotation2()
    target_no_annot = No_annotation()

    test = Test()
    test.set_initial_balance(sp.tez(1))

    scenario += target_default1
    scenario += target_default2
    scenario += target_regular1
    scenario += target_regular2
    scenario += target_no_annot
    scenario += test

    test.send(address=target_default1.address, amount=sp.mutez(1))
    test.send(address=target_default2.address, amount=sp.mutez(2))
    test.send(address=target_regular1.address, amount=sp.mutez(3))
    test.send(address=target_regular2.address, amount=sp.mutez(4)).run(valid = False, exception="Missing entry point target in contract")
    test.send(address=target_no_annot.address, amount=sp.mutez(5))

    test.send(address=sp.to_address(target_default1.typed.default), amount=sp.mutez(6))
    test.send(address=sp.to_address(target_default2.typed.default), amount=sp.mutez(7))
    test.send(address=sp.to_address(target_regular1.typed.reg_annot), amount=sp.mutez(8))
    test.send(address=sp.to_address(target_regular2.typed.reg_annot), amount=sp.mutez(9))
    test.send(address=sp.to_address(target_no_annot.typed.no_annot), amount=sp.mutez(10)).run(valid = False, exception="No annotation in contract")

@sp.add_test(name = "Test_option")
def test_option():
    scenario = sp.test_scenario()

    target_default1 = Default1()
    target_default2 = Default2()
    target_regular1 = Regular_annotation1()
    target_regular2 = Regular_annotation2()
    target_no_annot = No_annotation()

    test = Test()
    test.set_initial_balance(sp.tez(1))

    scenario.add_flag("no-contract-check-exception")

    scenario += target_default1
    scenario += target_default2
    scenario += target_regular1
    scenario += target_regular2
    scenario += target_no_annot
    scenario += test

    test.send(address=target_default1.address, amount=sp.mutez(1))
    test.send(address=target_default2.address, amount=sp.mutez(2))
    test.send(address=target_regular1.address, amount=sp.mutez(3))
    test.send(address=target_regular2.address, amount=sp.mutez(4)).run(valid = False, exception="Not the proper variant constructor [Some] != [None]")
    test.send(address=target_no_annot.address, amount=sp.mutez(5))

    test.send(address=sp.to_address(target_default1.typed.default), amount=sp.mutez(6))
    test.send(address=sp.to_address(target_default2.typed.default), amount=sp.mutez(7))
    test.send(address=sp.to_address(target_regular1.typed.reg_annot), amount=sp.mutez(8))
    test.send(address=sp.to_address(target_regular2.typed.reg_annot), amount=sp.mutez(9))
    test.send(address=sp.to_address(target_no_annot.typed.no_annot), amount=sp.mutez(10)).run(valid = False, exception="Not the proper variant constructor [Some] != [None]")
