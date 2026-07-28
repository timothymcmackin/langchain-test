import smartpy as sp

t = sp.TRecord(a = sp.TNat, b = sp.TInt, c = sp.TBool, d = sp.TString)

class C1(sp.Contract):
    def __init__(self):
        self.init(x1 = sp.record(a = sp.nat(0), b = sp.int(1), c = True, d = "abc")
                , x2 = sp.record(a = sp.nat(0), b = sp.int(1), c = True, d = "abc")
                , x3 = sp.record(a = sp.nat(0), b = sp.int(1), c = True, d = "abc")
                , x4 = sp.record(a = sp.nat(0), b = sp.int(1), c = True, d = "abc")
                , y = (sp.nat(0), sp.int(1), True, "abc")
                , z = sp.record(a = sp.nat(0), b = sp.int(1), c = True, d = sp.record(e = 1, f = "x"))
                )

    @sp.entry_point
    def ep1(self):
        sp.set_type(self.data.x2, t.layout(("a",("b",("c","d")))))
        sp.set_type(self.data.x3, t.layout(((("a","b"),"c"),"d")))
        sp.set_type(self.data.x4, t.layout((("a","b"),("c","d"))))
        with sp.modify_record(self.data.x1) as data:
            sp.verify(abs(data.b) == data.a + 1)
        with sp.modify_record(self.data.x2) as data:
            sp.verify(abs(data.b) == data.a + 1)
            data.d = "xyz"
        with sp.modify_record(self.data.x3) as data:
            sp.verify(abs(data.b) == data.a + 1)
            data.d.set("xyz")
        with sp.modify_record(self.data.x4) as data:
            sp.verify(abs(data.b) == data.a + 1)
            data.d.set("xyz")

    @sp.entry_point
    def ep2(self):
        with sp.modify_record(self.data.x1) as data:
            sp.verify(abs(data.b) == data.a + 1)
            data.d.set("xyz")

    @sp.entry_point
    def ep3(self):
        with sp.modify_tuple(self.data.y, "a", "b", "c", "d") as data:
            (a,b,c,d) = data
            sp.verify(abs(b) == a + 1)
            d.set("xyz")
            sp.result((a,b,c,d))

    @sp.entry_point
    def ep4(self):
        with sp.modify_record(self.data.x1) as data:
            data.a

    @sp.entry_point
    def ep5(self):
        with sp.modify_record(self.data.x1) as data:
            sp.verify(abs(data.b) == data.a + 1)
            data.d.set("xyz")
        self.data.x1.a += 5

    @sp.entry_point
    def ep5(self, alice):
        with sp.modify_record(self.data.x1) as data:
            sp.send(alice, sp.tez(0))
            data.d.set("xyz")
        self.data.x1.a += 5

    @sp.entry_point
    def ep6(self):
        with sp.modify_record(self.data.z) as outter:
            with sp.modify_record(outter.d) as inner:
                outter.b.set(100)
                inner.e.set(2)
                inner.f.set("y")

    @sp.entry_point
    def ep7(self):
        sp.verify(self.data.z.d.e == 2)
        with sp.modify_record(self.data.z.d) as z_d:
            sp.verify(z_d.e == 2)
            z_d.e.set(3)
            z_d.f.set("z")
            sp.verify(z_d.e == 3)
            z_d.e = 4
            sp.verify(z_d.e == 4)
        sp.verify(self.data.z.d.e == 4)

class C2(sp.Contract):
    def __init__(self):
        self.init(a = sp.nat(0), b = sp.int(1), c = True, d = "abc")

    @sp.entry_point
    def ep1(self):
        with sp.modify_record(self.data) as data:
            sp.verify(abs(data.b) == data.a + 1)
            data.d.set("xyz")

    @sp.entry_point
    def ep2(self):
        with sp.modify_record(self.data) as data:
            data.d = "abc"

class C3(sp.Contract):
    def __init__(self):
        self.init(42)
    @sp.entry_point
    def ep1(self):
        with sp.modify(self.data, 'x') as x:
            sp.result(x + 1)

@sp.add_test(name = "Match")
def test():
    alice = sp.test_account("Alice")
    s = sp.test_scenario()
    c1 = C1()
    s += c1
    s += c1.ep1()
    s += c1.ep2()
    s += c1.ep3()
    s += c1.ep4()
    # s += c1.ep5(alice.address)
    s += c1.ep6()
    s += c1.ep7()

    s += C2()

    s += C3()
