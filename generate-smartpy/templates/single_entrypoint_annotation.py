import smartpy as sp

class Contract1(sp.Contract):
    def __init__(self, **kargs):
        self.init(**kargs)
        self.add_flag("no-single-entry-point-annotation")

    @sp.entry_point
    def ep(self, params):
        """
            Default entrypoint with no annotation
        """
        sp.set_type(params, sp.TNat)
        self.data.result = sp.some(params)

class Contract2(sp.Contract):
    def __init__(self, **kargs):
        self.init(**kargs)

    @sp.entry_point
    def ep(self, params):
        """
            Default entrypoint with annotation
        """
        sp.set_type(params, sp.TNat)
        self.data.result = sp.some(params)

class Contract3(sp.Contract):
    def __init__(self):
        self.init()

    @sp.entry_point
    def ep1(self, params):
        c = sp.contract(sp.TNat, params.address1).open_some("WRONG_INTERFACE_Contract1")
        sp.transfer(1, sp.tez(0), c)
        c = sp.contract(sp.TNat, params.address2, "ep").open_some("WRONG_INTERFACE_Contract2")
        sp.transfer(1, sp.tez(0), c)

    @sp.entry_point
    def ep2(self, params):
        c = sp.contract(sp.TNat, params.address1).open_some("WRONG_INTERFACE_Contract1")
        sp.transfer(1, sp.tez(0), c)
        c = sp.contract(sp.TNat, params.address2, "ep").open_some("WRONG_INTERFACE_Contract2")
        sp.transfer(1, sp.tez(0), c)

@sp.add_test(name = "single_entrypoint_annotation_test")
def test():
    scenario = sp.test_scenario()

    c1 = Contract1(result = sp.none)
    scenario += c1

    c2 = Contract2(result = sp.none)
    scenario += c2

    c3 = Contract3()
    scenario += c3

    c3.ep1(address1 = c1.address, address2 = c2.address)
    c3.ep2(address1 = c1.address, address2 = c2.address)

sp.add_compilation_target("single_entrypoint_annotation_compilation1", Contract1(result = sp.none))
sp.add_compilation_target("single_entrypoint_annotation_compilation2", Contract2(result = sp.none))
