import smartpy as sp

class MyContract(sp.Contract):
    def __init__(self):
        self.init_type(sp.TRecord(
            x = sp.TRecord(a = sp.TInt, b = sp.TInt).right_comb(),
            y = sp.TVariant(A = sp.TInt, B = sp.TInt).right_comb()))
        self.init(x = sp.record(a = 1, b = 2), y = sp.variant("A", 42))

    @sp.entry_point
    def test_record(self):
        x = sp.set_type_expr(
               sp.record(c = 3, d = 4),
               sp.TRecord(c = sp.TInt, d = sp.TInt).right_comb())
        self.data.x = sp.convert(x)
        sp.verify(self.data.x == sp.record(a = 3, b = 4))

    @sp.entry_point
    def test_pair(self):
        self.data.x = sp.convert((5,6))
        sp.verify(self.data.x == sp.record(a = 5, b = 6))

    @sp.entry_point
    def test_variant(self):
        y = sp.set_type_expr(
               sp.variant("C", 43),
               sp.TVariant(C = sp.TInt, D = sp.TInt).right_comb())
        self.data.y = sp.convert(y)
        sp.verify(self.data.y == sp.variant("A", 43))


@sp.add_test(name = "Test_Convert")
def test():
    scenario = sp.test_scenario()

    c = MyContract()
    scenario += c

    c.test_record()
    c.test_pair()
    c.test_variant()


sp.add_compilation_target("test_convert", MyContract())
