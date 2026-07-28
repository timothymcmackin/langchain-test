# Store Value - Example for illustrative purposes only.

import smartpy as sp

class Onchain_views(sp.Contract):
    @sp.onchain_view()
    def get_value(self):
        sp.result(self.data.storedValue)

class StoreValue(Onchain_views):
    def __init__(self, value):
        self.init(storedValue = value)

    @sp.entry_point
    def replace(self, params):
        self.data.storedValue = params.value

class StoreValue2(Onchain_views):
    def __init__(self, value):
        #self.verbose = True
        self.init(storedValue = value)

    @sp.entry_point
    def add(self, params):
        self.data.storedValue += params.value

class StoreValue3(StoreValue2):
    @sp.onchain_view(name="new_name")
    def get_value(self):
        sp.result(self.data.storedValue)

if "templates" not in __name__:
    @sp.add_test(name = "StoreValue")
    def test():
        c1 = StoreValue(12)
        sc = sp.test_scenario()
        sc += c1
        c2 = StoreValue2(14)
        sc += c2
        c3 = StoreValue3(14)
        sc += c3
        sc.verify(c2.get_value() == 14)
        sc.verify(c1.get_value() == 12)
        sc.verify(c3.get_value() == 14)

    sp.add_compilation_target("storeValue", StoreValue(12))
