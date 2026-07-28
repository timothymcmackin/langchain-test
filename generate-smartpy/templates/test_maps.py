# Maps - Example for illustrative purposes only.

import smartpy as sp

class Test_maps(sp.Contract):
    def __init__(self):
        self.init(x = "a", y = sp.none, z = sp.some("na"), m = {})

    @sp.entry_point
    def test_map_get(self, params):
        sp.set_type(params, sp.TMap(sp.TInt, sp.TString))
        self.data.x = params.get(12)

    @sp.entry_point
    def test_map_get2(self, params):
        sp.set_type(params, sp.TMap(sp.TInt, sp.TString))
        self.data.x = params[12]


    @sp.entry_point
    def test_map_get_opt(self, params):
        sp.set_type(params, sp.TMap(sp.TInt, sp.TString))
        self.data.y = params.get_opt(12)

    @sp.entry_point
    def test_map_get_default_values(self, params):
        sp.set_type(params, sp.TMap(sp.TInt, sp.TString))
        self.data.x = params.get(12, default_value = "abc")

    @sp.entry_point
    def test_map_get_missing_value(self, params):
        sp.set_type(params, sp.TMap(sp.TInt, sp.TString))
        self.data.x = params.get(12, message = "missing 12")

    @sp.entry_point
    def test_map_get_missing_value2(self, params):
        sp.set_type(params, sp.TMap(sp.TInt, sp.TString))
        self.data.x = params.get(12, message = 1234)

    @sp.entry_point
    def test_update_map(self):
        self.data.m = sp.update_map(self.data.m, 1, sp.some("one"))

    @sp.entry_point
    def test_get_and_update(self):
        (previous_value, new_map) = sp.get_and_update(self.data.m, 1, sp.some("one"))
        self.data.z = previous_value

@sp.add_test(name = "Maps")
def test():
    c1 = Test_maps()
    scenario = sp.test_scenario()
    scenario.h1("Maps")
    scenario += c1
    c1.test_map_get_opt({})
    c1.test_map_get_opt({12: "A"})

sp.add_compilation_target("test_maps", Test_maps())
