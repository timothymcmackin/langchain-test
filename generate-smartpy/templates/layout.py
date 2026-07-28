# Data Layout - Example for illustrative purposes only.

import smartpy as sp

class TestLayout(sp.Contract):
    def __init__(self):
        self.init(a = 1, b = 12)
        self.init_type(sp.TRecord(a = None, b= sp.TNat).layout(("b", "a")))
        self.init_entry_points_layout(((("run_record", "run_record_2"), "run_type_record"), ("run_variant", "run_type_variant")))
        self.add_flag("no-initial-cast")

    @sp.entry_point
    def run_record(self, params):
        sp.set_type(params, sp.TRecord(a = sp.TInt, b = sp.TString, c = sp.TBool).layout(("b", ("a", "c"))))

    @sp.entry_point
    def run_record_2(self, params):
        sp.set_type(params, sp.TRecord(a = sp.TInt, b = sp.TString, c = sp.TBool, d = sp.TNat).right_comb())

    @sp.entry_point
    def run_variant(self, params):
        sp.set_type(params, sp.TVariant(a = sp.TInt, b = sp.TString, c = sp.TBool).layout(("b", ("a", "c"))))

    @sp.entry_point
    def run_type_record(self, params):
        sp.set_type(params, sp.TRecord(a = sp.TInt, b = sp.TString).layout(("b", "a")))

    @sp.entry_point
    def run_type_variant(self, params):
        sp.set_type(params, sp.TVariant(e = sp.TInt, d = sp.TString).layout(("e", "d")))

@sp.add_test(name = "Layout")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Layout")
    scenario += TestLayout()

sp.add_compilation_target("layout", TestLayout())
