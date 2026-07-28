# Decompilation - Example for illustrative purposes only.

# This example is a toy example on how decompilation can work.
# We show two example templates: Welcome and Fifo.
# It is not finished, not correct in general, and it makes some
# implicit assumptions on the Michelson code.

import smartpy as sp

"""
parameter int;

storage (pair (int %myParameter1) (int %myParameter2));

code
  {
    # Entry point: myEntryPoint # pair(params, storage)
    # sp.verify(self.data.myParameter1 <= 123) # pair(params, storage)
    DUP;        # pair(params, storage).pair(params, storage)
    CDR;        # Rec(myParameter1 = intOrNat, myParameter2 = intOrNat).pair(params, storage)
    CAR;        # intOrNat.pair(params, storage)
    PUSH int 123; # intOrNat.intOrNat.pair(params, storage)
    SWAP;       # intOrNat.intOrNat.pair(params, storage)
    COMPARE;    # int.pair(params, storage)
    LE;         # bool.pair(params, storage)
    IF
      {}
      {
        PUSH string "WrongCondition: self.data.myParameter1 <= 123"; # string.pair(params, storage)
        FAILWITH;   # pair(params, storage)
      }; # pair(params, storage)
    # self.data.myParameter1 += params # pair(params, storage)
    DUP;        # pair(params, storage).pair(params, storage)
    CDR;        # storage.pair(params, storage)
    DUUP;       # pair(params, storage).storage.pair(params, storage)
    CAR;        # params.storage.pair(params, storage)
    DUUP;       # storage.params.storage.pair(params, storage)
    CAR;        # intOrNat.params.storage.pair(params, storage)
    ADD;        # intOrNat.storage.pair(params, storage)
    SWAP;       # storage.intOrNat.pair(params, storage)
    CDR;        # intOrNat.intOrNat.pair(params, storage)
    SWAP;       # intOrNat.intOrNat.pair(params, storage)
    PAIR;       # pair(intOrNat, intOrNat).pair(params, storage)
    SWAP;       # pair(params, storage).storage
    DROP;       # storage
    NIL operation; # operations.storage
    PAIR;       # pair(operations, storage)
  } # pair(operations, storage);
"""

class Decompilation(sp.Contract):
    def getSetList(self, x, v):
        if isinstance(v, sp.record):
            l1 = self.getSetList(x.Left, v.Left)
            l2 = self.getSetList(x.Right, v.Right)
            if len(l1) + len(l2) > 1:
                return [(x, v)]
            else:
                return l1 + l2
        elif id(x) == id(v):
            return []
        else:
            return [(x, v)]

    def deepSet(self, x, v):
        l = self.getSetList(x, v)
        if len(l) == 0:
            pass
        elif len(l) == 1:
            l[0][0].set(l[0][1])
        else:
            x.set(v)
        self.stack = [self.pair(self.stack[0].Left, self.data)]

    def isLocalParams(self, x):
        return id(x) in self.localParamsIds

    def afterMichelson(self):
        # print(self.stack)
        # Somewhat adhoc condition for SmartPy compilation
        if len(self.stack) == 1 and isinstance(self.stack[0], sp.record) and self.isLocalParams(self.stack[0].Left):
            self.deepSet(self.data, self.stack[0].Right)

    def pair(self, x, y):
        return sp.record(Left = x, Right = y)

    def DUPn(self, n):
        self.stack = [self.stack[n - 1]] + self.stack
        self.afterMichelson()

    def DUP(self):
        self.DUPn(1)
        self.afterMichelson()

    def DUUP(self):
        self.DUPn(2)
        self.afterMichelson()

    def CAR(self):
        self.stack[0] = self.stack[0].Left
        self.afterMichelson()
        self.afterMichelson()

    def CDR(self):
        self.stack[0] = self.stack[0].Right
        self.afterMichelson()

    def PUSH(self, x):
        self.stack = [x] + self.stack
        self.afterMichelson()

    def SWAP(self):
        self.stack = [self.stack[1], self.stack[0]] + self.stack[2:]
        self.afterMichelson()

    def COMPARE(self):
        self.stack = [sp.record(x = self.stack[0], y = self.stack[1])] + self.stack[2:]
        self.afterMichelson()

    def LE(self):
        self.stack = [self.stack[0].x <= self.stack[0].y] + self.stack[1:]
        self.afterMichelson()

    def LT(self):
        self.stack = [self.stack[0].x < self.stack[0].y] + self.stack[1:]
        self.afterMichelson()

    def ASSERT(self, x):
        sp.verify(self.stack[0])
        self.stack = self.stack[1:]
        self.afterMichelson()

    def ADD(self):
        self.stack = [self.stack[0] + self.stack[1]] + self.stack[2:]
        self.afterMichelson()

    def PAIR(self):
        self.stack = [self.pair(self.stack[0], self.stack[1])] + self.stack[2:]
        self.afterMichelson()

    def NIL(self):
        self.stack = [[]] + self.stack
        self.afterMichelson()

    def DROP(self):
        self.stack = self.stack[1:]
        self.afterMichelson()

    def NONE(self):
        self.stack = [sp.none] + self.stack
        self.afterMichelson()

    def SOME(self):
        self.stack = [sp.some(self.stack[0])] + self.stack[1:]
        self.afterMichelson()

    def UPDATE(self):
        self.stack = [sp.update_map(self.stack[2], self.stack[0], self.stack[1])] + self.stack[3:]
        self.afterMichelson()

    def access(self, path):
        for c in path[1: -1]:
            if c == 'A':
                self.CAR()
            elif c == 'D':
                self.CDR()
            else:
                raise Exception("Bad path " + path)
        self.afterMichelson()

    def SET_access(self, path):
        if path[0] == 'C':
            path = path[1:-1]
        if path == "A":
            self.CDR()
            self.SWAP()
            self.PAIR()
        elif path == "D":
            self.CAR()
            self.PAIR()
        elif path[0] == "A":
            self.DUP()
            def op():
                self.CAR()
                self.SET_access(path[1:])
            self.DIP(op)
            self.SET_access("A")
        elif path[0] == "D":
            self.DUP()
            def op():
                self.CDR()
                self.SET_access(path[1:])
            self.DIP(op)
            self.SET_access("D")
        self.afterMichelson()

    def DIP(self, f):
        top = self.stack[0]
        self.stack = self.stack[1:]
        f()
        self.stack = [top] + self.stack
        self.afterMichelson()

    def IF_LEFT(self, ifLeft, elseLeft):
        stack2 = [x for x in self.stack]
        sp.if self.stack[0].is_variant('Left'):
            self.stack = [self.stack[0].open_variant('Left')] + self.stack[1:]
            ifLeft()
            assert len(self.stack) == 1
            self.afterMichelson()
            self.deepSet(self.data, self.stack[0].Right)
        sp.else:
            self.stack = stack2
            self.stack = [self.stack[0].open_variant('Right')] + self.stack[1:]
            elseLeft()
            self.afterMichelson()
            assert len(self.stack) == 1
            self.deepSet(self.data, self.stack[0].Right)

class WelcomeDecompilation(Decompilation):
    def __init__(self):
        self.init(Left = 1, Right = 12)

    @sp.entry_point
    def welcome(self, params):
        self.params = params
        self.localParamsIds = [id(self.params)]
        self.stack = [self.pair(params, self.data)]
        self.DUP()
        self.CDR()
        self.CAR()
        self.PUSH(123)
        self.SWAP()
        self.COMPARE()
        self.LE()
        self.ASSERT("WrongCondition: self.data.myParameter1 <= 123")
        self.DUP()
        self.CDR()
        self.DUUP()
        self.CAR()
        self.DUUP()
        self.CAR()
        self.ADD()
        self.SWAP()
        self.CDR()
        self.SWAP()
        self.PAIR()
        self.SWAP()
        self.DROP()
        self.NIL()
        self.PAIR()
        self.deepSet(self.data, self.stack[0].Right)


"""
parameter (or (unit %pop) (nat %push));

storage (pair (pair (int %first) (int %last)) (map %saved int nat));

code
  {
    DUP;        # pair(params, storage).pair(params, storage)
    CDR;        # storage.pair(params, storage)
    SWAP;       # pair(params, storage).storage
    CAR;        # params.storage
    IF_LEFT
      {
        # Entry point: pop # params.storage
        PAIR;       # pair(params, storage)
        # sp.verify(self.data.first < self.data.last) # pair(params, storage)
        DUP;        # pair(params, storage).pair(params, storage)
        CDADR;      # int.pair(params, storage)
        DUUP;       # pair(params, storage).int.pair(params, storage)
        CDAAR;      # int.int.pair(params, storage)
        COMPARE;    # int.pair(params, storage)
        LT;         # bool.pair(params, storage)
        IF
          {}
          {
            PUSH string "WrongCondition: self.data.first < self.data.last"; # string.pair(params, storage)
            FAILWITH;   # pair(params, storage)
          }; # pair(params, storage)
        # del self.data.saved[self.data.first] # pair(params, storage)
        DUP;        # pair(params, storage).pair(params, storage)
        CDR;        # storage.pair(params, storage)
        DUP;        # storage.storage.pair(params, storage)
        CDR;        # Map(int, nat).storage.pair(params, storage)
        DUUP;       # storage.Map(int, nat).storage.pair(params, storage)
        CAAR;       # int.Map(int, nat).storage.pair(params, storage)
        NONE nat;   # Variant(None unit | Some nat).int.Map(int, nat).storage.pair(params, storage)
        SWAP;       # int.Variant(None unit | Some nat).Map(int, nat).storage.pair(params, storage)
        UPDATE;     # Map(int, nat).storage.pair(params, storage)
        SWAP;       # storage.Map(int, nat).pair(params, storage)
        CAR;        # int.Map(int, nat).pair(params, storage)
        PAIR;       # pair(int, Map(int, nat)).pair(params, storage)
        SWAP;       # pair(params, storage).storage
        CAR;        # params.storage
        PAIR;       # pair(params, storage)
        # self.data.first += 1 # pair(params, storage)
        DUP;        # pair(params, storage).pair(params, storage)
        CDR;        # storage.pair(params, storage)
        DUP;        # storage.storage.pair(params, storage)
        CAAR;       # int.storage.pair(params, storage)
        PUSH int 1; # int.int.storage.pair(params, storage)
        ADD;        # int.storage.pair(params, storage)
        SWAP;       # storage.int.pair(params, storage)
        SET_CAAR;   # storage.pair(params, storage)
        SWAP;       # pair(params, storage).storage
        DROP;       # storage
        NIL operation; # operations.storage
        PAIR;       # pair(operations, storage)
      }
      {
        # Entry point: push # params.storage
        PAIR;       # pair(params, storage)
        # self.data.last += 1 # pair(params, storage)
        DUP;        # pair(params, storage).pair(params, storage)
        CDR;        # storage.pair(params, storage)
        DUP;        # storage.storage.pair(params, storage)
        CADR;       # int.storage.pair(params, storage)
        PUSH int 1; # int.int.storage.pair(params, storage)
        ADD;        # int.storage.pair(params, storage)
        SWAP;       # storage.int.pair(params, storage)
        SET_CADR;   # storage.pair(params, storage)
        SWAP;       # pair(params, storage).storage
        CAR;        # params.storage
        PAIR;       # pair(params, storage)
        # self.data.saved[self.data.last] = params # pair(params, storage)
        DUP;        # pair(params, storage).pair(params, storage)
        CDR;        # storage.pair(params, storage)
        DUP;        # storage.storage.pair(params, storage)
        CDR;        # Map(int, nat).storage.pair(params, storage)
        DUUP;       # storage.Map(int, nat).storage.pair(params, storage)
        CADR;       # int.Map(int, nat).storage.pair(params, storage)
        DUUUUP;     # pair(params, storage).int.Map(int, nat).storage.pair(params, storage)
        CAR;        # params.int.Map(int, nat).storage.pair(params, storage)
        SOME;       # option(params).int.Map(int, nat).storage.pair(params, storage)
        SWAP;       # int.option(params).Map(int, nat).storage.pair(params, storage)
        UPDATE;     # Map(int, nat).storage.pair(params, storage)
        SWAP;       # storage.Map(int, nat).pair(params, storage)
        CAR;        # int.Map(int, nat).pair(params, storage)
        PAIR;       # pair(int, Map(int, nat)).pair(params, storage)
        SWAP;       # pair(params, storage).storage
        DROP;       # storage
        NIL operation; # operations.storage
        PAIR;       # pair(operations, storage)
      }; # pair(operations, storage)
  } # pair(operations, storage);
"""

class FifoDecompilation(Decompilation):
    def __init__(self):
        #(Pair (Pair 0 -1) {})
        self.init(Left = sp.record(Left = 0, Right = -1), Right = sp.map(tkey = sp.TInt, tvalue = sp.TInt))

    @sp.entry_point
    def fifo(self, params):
        self.params = params
        self.localParamsIds = [id(self.params), id(self.params.open_variant('Left')), id(self.params.open_variant('Right'))]
        self.stack = [self.pair(params, self.data)]
        sp.set_type(params, sp.TOr(sp.TUnit, sp.TInt))
        self.DUP()
        self.CDR()
        self.SWAP()
        self.CAR()
        def ifLeft():
            self.PAIR()
            self.DUP()
            self.access('CDADR')
            self.DUUP()
            self.access('CDAAR')
            self.COMPARE()
            self.LT()
            self.ASSERT("WrongCondition: self.data.first < self.data.last")
            self.DUP()
            self.CDR()
            self.DUP()
            self.CDR()
            self.DUUP()
            self.access('CAAR')
            self.NONE()
            self.SWAP()
            self.UPDATE()
            self.SWAP()
            self.CAR()
            self.PAIR()
            self.SWAP()
            self.CAR()
            self.PAIR()
            self.DUP()
            self.CDR()
            self.DUP()
            self.access('CAAR')
            self.PUSH(1)
            self.ADD()
            self.SWAP()
            self.SET_access("CAAR")
            self.SWAP()
            self.DROP()
            self.NIL()
            self.PAIR()
        def elseLeft():
            self.PAIR()
            self.DUP()
            self.CDR()
            self.DUP()
            self.access('CADR')
            self.PUSH(1)
            self.ADD()
            self.SWAP()
            self.SET_access('CADR')
            self.SWAP()
            self.CAR()
            self.PAIR()
            self.DUP()
            self.CDR()
            self.DUP()
            self.CDR()
            self.DUUP()
            self.access('CADR')
            self.DUPn(4)
            self.CAR()
            self.SOME()
            self.SWAP()
            self.UPDATE()
            self.SWAP()
            self.CAR()
            self.PAIR()
            self.SWAP()
            self.DROP()
            self.NIL()
            self.PAIR()
        self.IF_LEFT(ifLeft, elseLeft)
        self.deepSet(self.data, self.stack[0].Right)

# Tests
if "templates" not in __name__:
    @sp.add_test(name = "Decompilation")
    def test():
        scenario = sp.test_scenario()
        scenario.h1("Decompilation")
        scenario += WelcomeDecompilation()
        scenario += FifoDecompilation()

    sp.add_compilation_target("decompilation", WelcomeDecompilation())
