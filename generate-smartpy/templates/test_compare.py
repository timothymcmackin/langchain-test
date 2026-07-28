import smartpy as sp

class C(sp.Contract):

    @sp.entry_point
    def compare_inferior(self):
        sp.verify(sp.compare(sp.nat(1), sp.nat(5)) == -1)
        sp.verify(sp.compare(sp.int(1), sp.int(5)) == -1)
        sp.verify(sp.compare(sp.timestamp(1), sp.timestamp(5)) == -1)
        sp.verify(sp.compare(sp.address("KT18amZmM5W7qDWVt2pH6uj7sCEd3kbzLrHT"), sp.address("KT1XvNYseNDJJ6Kw27qhSEDF8ys8JhDopzfG")) == -1)
        sp.verify(sp.compare(False, True) == -1)
        sp.verify(sp.compare(sp.bytes("0x00"), sp.bytes("0x01")) == -1)
        sp.verify(sp.compare(sp.chain_id_cst("0x00"), sp.chain_id_cst("0x01")) == -1)
        sp.verify(sp.compare(sp.key("edpkuBknW28nW72KG6RoH"), sp.key("edpkuJqtDcA2m2muMxViS")) == -1)
        sp.verify(sp.compare(sp.key_hash("tz1KqTpEZ7Yob7QbPE4Hy"), sp.key_hash("tz1XPTDmvT3vVE5Uunngm")) == -1)
        sp.verify(sp.compare(sp.mutez(1), sp.mutez(5)) == -1)
        sp.verify(sp.compare("a", "e") == -1)
        sp.verify(sp.compare(sp.pair(1, 5), sp.pair(5, 1)) == -1)
        sp.verify(sp.compare(sp.none, sp.some(sp.unit)) == -1)
        sp.verify(sp.compare(sp.some(1), sp.some(5)) == -1)
        t = sp.TOr(sp.TNat, sp.TNat)
        sp.verify(sp.compare(sp.set_type_expr(sp.left(5), t), sp.right(1)) == -1)
        sp.verify(sp.compare(sp.set_type_expr(sp.left(1), t), sp.left(5)) == -1)
        sp.verify(sp.compare(sp.set_type_expr(sp.left(1), t), sp.left(5)) == -1)
        sp.verify(sp.compare(sp.set_type_expr(sp.right(1), t), sp.right(5)) == -1)

    @sp.entry_point
    def compare_eq(self):
        sp.verify(sp.compare(sp.unit, sp.unit) == 0)
        sp.verify(sp.compare(sp.set_type_expr(sp.none, sp.TOption(sp.TNat)), sp.set_type_expr(sp.none, sp.TOption(sp.TNat))) == 0)
        sp.verify(sp.compare(sp.nat(2), sp.nat(1)) == 1)

@sp.add_test(name = "Compare")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Compare")
    c = C()
    scenario += c
    c.compare_inferior()
    c.compare_eq()

sp.add_compilation_target("testCompare", C())
