import smartpy as sp

class C(sp.Contract):
    def __init__(self):
        self.init(x = sp.some(42))

    @sp.entry_point
    def set(self, x):
        self.data.x = x

    @sp.entry_point
    def map(self, f):
        self.data.x = self.data.x.map(f)

@sp.add_test(name="Test")
def test():
    s = sp.test_scenario()
    c = C()
    s += c
    c.map(lambda x: x+1)
    s.verify(c.data.x == sp.some(43))
    c.map(lambda x: x+2)
    s.verify(c.data.x == sp.some(45))

    c.set(sp.none)
    c.map(lambda x: x-1)
    s.verify(c.data.x == sp.none)
