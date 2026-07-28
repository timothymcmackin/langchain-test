import smartpy as sp

class C1(sp.Contract):
    def __init__(self):
        self.init(x = sp.bounded("abc"))
        self.init_type(sp.TRecord(x = sp.TBounded(["abc", "def"], t = sp.TString)))

    @sp.entry_point
    def ep(self):
        self.data.x = sp.bounded("abc")

class C2(sp.Contract):
    def __init__(self):
        self.init(x = sp.bounded("abc"))
        self.init_type(sp.TRecord(x = sp.TBounded(["abc", "def"], final=False)))

    @sp.entry_point
    def ep(self):
        self.data.x = sp.bounded("ghi")

    @sp.entry_point
    def ep2(self, params):
        sp.set_type(params, sp.TBounded(["ghi", "jkl", "abc", "def"]))
        self.data.x = params

class C3(sp.Contract):
    def __init__(self):
        self.init(x = sp.bounded(1), y = 0)
        self.init_type(sp.TRecord(x = sp.TBounded([1, 2, 3]), y = sp.TInt))

    @sp.entry_point
    def ep(self):
        self.data.x = sp.bounded(1)

    @sp.entry_point
    def ep2(self):
        self.data.x = sp.bounded(2)

    @sp.entry_point
    def ep3(self):
        self.data.y = sp.unbounded(self.data.x)

class C4(sp.Contract):
    @sp.entry_point
    def ep(self, b):
        sp.set_type(b, sp.TBounded(["abc", "def"]))

    @sp.entry_point
    def ep2(self):
        pass

@sp.add_test(name = "Bounded")
def test():
    scenario = sp.test_scenario()
    scenario += C1()
    scenario += C2()

    c3 = C3()
    scenario += c3
#    c3.ep3()
#    scenario.verify(c3.data.y == 1)

    c4 = C4()
    scenario += c4
    c4.ep(sp.bounded("abc"))
