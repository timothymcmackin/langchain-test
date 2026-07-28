import smartpy as sp

nats = [
    0,
    1,
    2,
    3,
    10,
    10000,
    1000000,
    1000000000000
    ]

implicit_accounts = ['tz1fextP23D6Ph2zeGTP8EwkP5Y8TufeFCHA',
                     'tz2FCNBrERXtaTtNX6iimR1UJ5JSDxvdHM93',
                     'tz3WMqdzXqRWXwyvj5Hp2H7QEepaUuS7vd9K'
                     ]

def f1(x):
    sp.if x.a:
        sp.result(123)
    sp.else:
        sp.result(x.b)

def f2(x):
    sp.if x.a:
        sp.result(123)
    sp.else:
        sp.result(x.b + x.c)

def f3(x):
    y = sp.local('y', 0)
    r = sp.local('r', "A")
    sp.if x == 0:
        sp.if x == y.value:
            r.value = "B"
    sp.result(r.value)

with_unpack = ([True, False, ()]
               + [sp.mutez(x) for x in nats]
               + [sp.nat(x) for x in nats]
               + [sp.int(x) for x in nats]
               + [sp.int(-x) for x in nats]
               + ["", "a", "ab", "abc"]
               + [sp.bytes("0x"), sp.bytes("0x00"), sp.bytes("0xab00")]
               + [(1, 2), ("a", True)]
               + [sp.timestamp(123)]
               + [sp.signature("sigTBpkXw6tC72L2nJ2r2Jm5iB6uidTWqoMNd4oEawUbGBf5mHVfKawFYL8X8MJECpL73oBnfujyUZNLK2LQWD1FaCkYMP4j"),
                  sp.signature("spsig1PPUFZucuAQybs5wsqsNQ68QNgFaBnVKMFaoZZfi1BtNnuCAWnmL9wVy5HfHkR6AeodjVGxpBVVSYcJKyMURn6K1yknYLm"),
                  sp.signature("p2sigsceCzcDw2AeYDzUonj4JT341WC9Px4wdhHBxbZcG1FhfqFVuG7f2fGCzrEHSAZgrsrQWpxduDPk9qZRgrpzwJnSHC3gZJ"),
                  sp.make_signature(sp.test_account("keystore").secret_key, sp.pack("value"), message_format = 'Raw')]
               + [sp.address(account) for account in implicit_accounts]
               + [sp.key_hash(account) for account in implicit_accounts]
               + [sp.address('KT1Mpqi89gRyUuoXUPAWjHkqkk1F48eUKUVy'),
                  sp.address('KT1Mpqi89gRyUuoXUPAWjHkqkk1F48eUKUVy%'),
                  sp.address('KT1Mpqi89gRyUuoXUPAWjHkqkk1F48eUKUVy%foo')]
               + [range(0, n) for n in range(1, 8)]
               + [sp.set([1, 2, 3, 4])]
               + [sp.timestamp(123), sp.address('tz1fextP23D6Ph2zeGTP8EwkP5Y8TufeFCHA')]
               + [lambda x: x + 2, f1, f2, sp.lambda_michelson("DUP; PUSH int 42; ADD; MUL", sp.TInt, sp.TInt)]
               )

int_to_string = sp.TLambda(sp.TInt,sp.TString)
int_to_unit = sp.TLambda(sp.TInt,sp.TUnit)
int_to_bool = sp.TLambda(sp.TInt,sp.TBool)
int_to_int = sp.TLambda(sp.TInt,sp.TInt)

class Pack(sp.Contract):
    def __init__(self, l, unpack = True):
        self.l = l
        self.unpack = unpack
        self.init()

    @sp.entry_point
    def run(self):
        for x in self.l:
            packed = sp.resolve(sp.pack(x))
            sp.verify(sp.pack(x) == packed)
            if self.unpack:
                sp.verify_equal(x, sp.resolve(sp.unpack(packed).open_some()))

    @sp.entry_point
    def pack_lambdas(self):
        f1 = sp.local("f1", f3, t = int_to_string)
        p1 = sp.local("p1", sp.pack(f1.value))
        f2 = sp.local("f2", sp.unpack(p1.value).open_some(), t = int_to_string)
        p2 = sp.local("p2", sp.pack(f2.value))
        sp.verify(p1.value == p2.value)
        sp.verify(f1.value(0) == f2.value(0))
        sp.verify(f1.value(1) == f2.value(1))
        sp.verify(f1.value(2) == f2.value(2))

    @sp.entry_point
    def pack_lambdas2(self):
        def f(x):
            sp.result(x > 0)
        f1 = sp.local("f1", f, t = int_to_bool)
        p1 = sp.local("p1", sp.pack(f1.value))
        f2 = sp.local("f2", sp.unpack(p1.value).open_some(), t = int_to_bool)
        sp.verify(f2.value(1))

    @sp.entry_point
    def pack_lambda_record(self):
        f = lambda x: sp.record(a = 1, b = x + 2)
        t = sp.TLambda(sp.TInt, sp.TRecord(a = sp.TInt, b = sp.TInt))
        f2 = sp.unpack(sp.pack(f), t).open_some()
        sp.verify(f2(100).a == 1)

        f = lambda x: sp.record(a = x + 1)
        t = sp.TLambda(sp.TInt, sp.TRecord(a = sp.TInt))
        f2 = sp.unpack(sp.pack(f), t).open_some()
        sp.verify(f2(100).a == 101)

    @sp.entry_point
    def pack_lambda_variant(self):
        tv = sp.TVariant(a = sp.TInt, b = sp.TInt)
        f = lambda x: sp.set_type_expr(sp.variant("a", x + 1),tv)
        t = sp.TLambda(sp.TInt, tv)
        f2 = sp.unpack(sp.pack(f), t).open_some()
        sp.verify(f2(100).open_variant("a") == 101)

        f = lambda x: sp.variant("a", x + 1)
        t = sp.TLambda(sp.TInt, sp.TVariant(a = sp.TInt))
        f2 = sp.unpack(sp.pack(f), t).open_some()
        sp.verify(f2(100).open_variant("a") == 101)

@sp.add_test(name = "Pack")
def test():
    s = sp.test_scenario()

    c = Pack(with_unpack[0:30])
    s.register(c)
    c.run()
    c.pack_lambdas()
    c.pack_lambdas2()
    c.pack_lambda_record()
    c.pack_lambda_variant()

    c = Pack(with_unpack[30:])
    s.register(c)
    c.run()

    s.verify_equal(f3, sp.unpack(sp.pack(f3)).open_some())
    s.verify_equal(                  sp.unpack(sp.pack(f3), t = int_to_string).open_some(),
                   sp.unpack(sp.pack(sp.unpack(sp.pack(f3), t = int_to_string).open_some()), t = int_to_string).open_some())
