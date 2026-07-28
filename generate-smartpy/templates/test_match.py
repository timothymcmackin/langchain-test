import smartpy as sp

class C(sp.Contract):
    def __init__(self):
        self.init(m = {"abc": sp.record(a = 10, b = 20)}, out = "z")

    @sp.entry_point
    def ep1(self, params):
        x, y = sp.match_pair(params)
        sp.verify(x == "x")
        sp.verify(y == 2)

    @sp.entry_point
    def ep2(self, params):
        x, y, z = sp.match_tuple(params, "my_x", "my_y", "my_z")
        sp.verify(x == "x")
        sp.verify(y == 2)
        sp.verify(z)

    @sp.entry_point
    def ep3(self, params):
        sp.set_type(params, sp.TRecord(x = sp.TString, y = sp.TInt, z = sp.TBool))
        x, z = sp.match_record(params, "x", "z")
        sp.verify(x == "x")
        sp.verify(z)

    @sp.entry_point
    def ep4(self, params):
        sp.set_type(params.x01, sp.TInt)
        sp.set_type(params.x02, sp.TKey)
        sp.set_type(params.x03, sp.TString)
        sp.set_type(params.x04, sp.TTimestamp)
        sp.set_type(params.x05, sp.TBytes)
        sp.set_type(params.x06, sp.TAddress)
        sp.set_type(params.x07, sp.TBool)
        sp.set_type(params.x08, sp.TKeyHash)
        sp.set_type(params.x09, sp.TSignature)
        sp.set_type(params.x10, sp.TMutez)
        x07, x03 = sp.match_record(params, "x07", "x03")
        sp.verify(x03 == "x")
        sp.verify(x07)

    @sp.entry_point
    def ep5(self, params):
        a, b, c, d = sp.match_tuple(params, "a", "b", "c", "d")
        sp.verify(a * b + c * d == 12)

    @sp.entry_point
    def ep6(self, params):
        a, b, c, d = sp.match_tuple(params, "a", "b", "c", "d")
        sp.set_type(c, sp.TInt)
        sp.verify(a * b + d == 12)

    @sp.entry_point
    def ep7(self):
       k = sp.local('k', "abc")
       with sp.modify_record(self.data.m[k.value], "data") as data:
           k.value.set("xyz" + k.value)
       self.data.out = k.value

@sp.add_test(name = "Match")
def test():
    s = sp.test_scenario()
    c = C()
    s += c
    c.ep1(("x", 2))
    c.ep2(("x", 2, True))
    c.ep3(x="x", y=2, z=True)
    c.ep5((1,6,2,3))
    c.ep6((1,6,2,6))
    c.ep7()
