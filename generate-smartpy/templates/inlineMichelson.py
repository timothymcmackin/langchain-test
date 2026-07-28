import smartpy as sp

class C(sp.Contract):
    def __init__(self):
        self.init(value = 0, s = '')

    @sp.entry_point
    def arith(self):
        add = sp.michelson("ADD", [sp.TInt, sp.TInt], [sp.TInt])
        sp.verify(add(1,  2) == 3)
        sp.verify(add(1, -2) == -1)
        sub = sp.michelson("SUB", [sp.TInt, sp.TInt], [sp.TInt])
        sp.verify(sub(1, -2) == 3)
        sp.verify(sub(1,  2) == -1)

    @sp.entry_point
    def prim0(self):
        unit = sp.michelson("UNIT", [], [sp.TUnit])
        sp.verify(unit() == ())
        none = sp.michelson("NONE unit", [], [sp.TOption(sp.TUnit)])
        sp.verify(none() == sp.none)
        pair12 = sp.michelson("PUSH int 2; PUSH int 1; PAIR", [], [sp.TPair(sp.TInt,sp.TInt)])
        sp.verify(pair12() == (1,2))
        nil = sp.michelson("NIL unit", [], [sp.TList(sp.TUnit)])
        sp.verify(sp.len(nil()) == 0)
        empty_set = sp.michelson("EMPTY_SET unit", [], [sp.TSet(sp.TUnit)])
        sp.verify(sp.len(empty_set()) == 0)
        empty_map = sp.michelson("EMPTY_MAP unit unit", [], [sp.TMap(sp.TUnit, sp.TUnit)])
        sp.verify(sp.len(empty_map()) == 0)
        empty_big_map = sp.michelson("EMPTY_BIG_MAP unit unit", [], [sp.TBigMap(sp.TUnit, sp.TUnit)])
        # sp.verify(sp.len(empty_big_map()) == 0)

    @sp.entry_point
    def overflow_add(self):
        add = sp.michelson("ADD", [sp.TMutez, sp.TMutez], [sp.TMutez])
        sp.compute(add(sp.mutez(9223372036854775807), sp.mutez(1)))

    @sp.entry_point
    def overflow_mul(self):
        mul = sp.michelson("MUL", [sp.TMutez, sp.TNat], [sp.TMutez])
        sp.compute(mul(sp.mutez(4611686018427387904), 2))

    @sp.entry_point
    def underflow(self):
        sub = sp.michelson("SUB_MUTEZ", [sp.TMutez, sp.TMutez], [sp.TOption(sp.TMutez)])
        sp.verify(sub(sp.mutez(0), sp.mutez(1)) == sp.none)

    @sp.entry_point
    def concat1(self):
        concat = sp.michelson("CONCAT", [sp.TList(sp.TString)], [sp.TString])
        sp.verify(concat(["a", "b", "c"]) == "abc")

    @sp.entry_point
    def concat2(self):
        concat = sp.michelson("CONCAT", [sp.TString, sp.TString], [sp.TString])
        sp.verify(concat("a", "b") == "ab")

    @sp.entry_point
    def seq(self):
        f = sp.michelson("DIP {SWAP}; ADD; MUL; DUP; MUL;", [sp.TInt, sp.TInt, sp.TInt], [sp.TInt])
        sp.verify(f(15, 16, 17) == 262144)

    @sp.entry_point
    def lambdas(self):
        f = sp.michelson("PUSH (lambda int int) {DUP; ADD}; SWAP; EXEC;", [sp.TInt], [sp.TInt])
        sp.verify(f(100) == 200)

        # f = sp.michelson("PUSH (lambda (pair int int) int) {UNPAIR; PUSH int 10; MUL; ADD;}; SWAP; EXEC;", [sp.TInt, sp.TInt], [sp.TInt])
        # sp.verify(f(2,5) == 25)
        # TODO Why does this not fail during type checking?

        f = sp.michelson("PAIR; PUSH (lambda (pair int int) int) { UNPAIR; PUSH int 10; MUL; ADD;}; SWAP; EXEC;", [sp.TInt, sp.TInt], [sp.TInt])
        sp.verify(f(2,5) == 25)

        f = sp.michelson("PAIR 3; PUSH (lambda (pair int int int) int) { UNPAIR 3; PUSH int 10; MUL; ADD; PUSH int 10; MUL; ADD;}; SWAP; EXEC;", [sp.TInt, sp.TInt, sp.TInt], [sp.TInt])
        sp.verify(f(2,5,7) == 257)

        f = sp.michelson("PUSH (lambda (pair int int int) int) { UNPAIR 3; PUSH int 10; MUL; ADD; PUSH int 10; MUL; ADD;}; PUSH int 2; APPLY; PUSH int 5; APPLY; PUSH int 7; EXEC;", [], [sp.TInt])
        sp.verify(f() == 257)

        # TODO lambda that traverses the SmartPy-Michelson barrier

        f = sp.michelson("LAMBDA_REC int int                { DUP; PUSH int 1; COMPARE; GE; IF { DROP 2; PUSH int 1; } { DUP; PUSH int 1; SWAP; SUB; DIG 2; SWAP; EXEC; MUL; }; }; SWAP; EXEC;", [sp.TInt], [sp.TInt])
        sp.verify(f(5) == 120)

        f = sp.michelson("PUSH (lambda int int) (Lambda_rec { DUP; PUSH int 1; COMPARE; GE; IF { DROP 2; PUSH int 1; } { DUP; PUSH int 1; SWAP; SUB; DIG 2; SWAP; EXEC; MUL; }; }); SWAP; EXEC;", [sp.TInt], [sp.TInt])
        sp.verify(f(5) == 120)

    @sp.entry_point
    def test_operations(self):
        op1 = sp.michelson("NONE key_hash; SET_DELEGATE;", [], [sp.TOperation]);
        sp.add_operations([op1()])

        c = sp.michelson("PUSH int 123; PUSH mutez 0; NONE key_hash; CREATE_CONTRACT { parameter int; storage int; code { UNPAIR; ADD; NIL operation; PAIR } }; PAIR", [], [sp.TPair(sp.TOperation, sp.TAddress)]);
        op,address = sp.match_pair(c())
        sp.add_operations([sp.fst(c())])

@sp.add_test(name = "Inline Michelson")
def test():
    scenario = sp.test_scenario()
    c = C()
    scenario += c
    c.prim0()
    c.arith()
    c.overflow_add().run(valid = False, exception = "ADD: mutez overflow")
    c.overflow_mul().run(valid = False, exception = "MUL: mutez overflow")
    c.underflow()
    c.seq()
    c.lambdas()
    c.test_operations()

sp.add_compilation_target("inlineMichelson", C())
