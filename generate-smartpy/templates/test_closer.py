import smartpy as sp

class C(sp.Contract):
    @sp.entry_point
    def test_none(self, p):
        sp.verify(p.is_none())

    @sp.entry_point
    def test_some(self, p):
        sp.verify(p.is_some())

@sp.add_test(name = "Test")
def test():
    s = sp.test_scenario()
    s.add_flag("no-initial-cast")
    s.register(C(), accept_unknown_types = True, show = True)
