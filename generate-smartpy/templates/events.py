import smartpy as sp

class C(sp.Contract):
    @sp.entry_point
    def ep(self):
        sp.emit("Hello")
        sp.emit("World", tag = "mytag")
        sp.emit(sp.record(a = "ABC", b = "XYZ"), tag = "mytag2")
        sp.emit(sp.record(a = "ABC", b = "XYZ"), tag = "mytag2", with_type = False)

@sp.add_test(name="Events")
def test():
    s = sp.test_scenario()
    c = C()
    s += c
    c.ep()
