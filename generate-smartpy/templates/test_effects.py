import smartpy as sp

class Sub(sp.Contract):
    def __init__(self):
        self.init(a = sp.nat(0))

    @sp.entry_point
    def sub_incr(self):
        self.data.a = self.data.a + 1

    @sp.entry_point
    def sub_double(self):
        self.data.a = 2 * self.data.a

class Main(sp.Contract):
    def __init__(self, sub):
        self.sub = sub
        self.init(a = sp.nat(0))

    @sp.private_lambda(with_storage="read-write")
    def incr(self, x):
        self.data.a = self.data.a + 1
        sp.result(x + 1)

    @sp.private_lambda(with_storage="read-write")
    def double(self, x):
        self.data.a = 2 * self.data.a
        sp.result(2 * x)

    @sp.private_lambda(with_operations=True)
    def sub_incr(self, x):
        sub_incr = sp.compute(sp.contract(address=self.sub, t = sp.TUnit, entry_point="sub_incr").open_some())
        sp.transfer((), sp.tez(0), sub_incr)
        sp.result(x + 1)

    @sp.private_lambda(with_operations=True)
    def sub_double(self, x):
        sub_double = sp.compute(sp.contract(address=self.sub, t = sp.TUnit, entry_point="sub_double").open_some())
        sp.transfer((), sp.tez(0), sub_double)
        sp.result(2 * x)

    @sp.private_lambda(with_storage="read-write", with_operations=True)
    def sub_incr_both(self, x):
        sub_incr = sp.compute(sp.contract(address=self.sub, t = sp.TUnit, entry_point="sub_incr").open_some())
        sp.transfer((), sp.tez(0), sub_incr)
        self.data.a = self.data.a + 1
        sp.result(x + 1)

    @sp.entry_point
    def test_with_storage(self):
        self.data.a = 0
        sp.verify(self.incr(100) == 101)
        sp.verify(self.data.a == 1)

        self.data.a = 10
        sp.verify(self.double(100) == 200)
        sp.verify(self.data.a == 20)

        self.data.a = 10
        sp.verify(self.double(self.incr(100)) == 202)
        sp.verify(self.data.a == 22)

        self.data.a = 10
        sp.verify(self.double(100) + self.incr(1000) == 1201)
        sp.verify(self.data.a == 22)

        self.data.a = 10
        sp.verify(self.incr(1000) + self.double(100) == 1201)
        sp.verify(self.data.a == 21)

    @sp.entry_point
    def test_sub_incr(self):
        self.data.a = 0
        sp.verify(self.sub_incr(100) == 101)

    @sp.entry_point
    def test_sub_incr_both(self):
        self.data.a = 0
        sp.verify(self.sub_incr_both(100) == 101)
        sp.verify(self.data.a == 1)

    @sp.entry_point
    def test_sub_incr_store(self):
        self.data.a = self.sub_incr_both(100)


@sp.add_test(name = "Effects")
def test():
    s = sp.test_scenario()
    sub = Sub()
    s += sub
    main = Main(sub.address)
    s += main
    main.test_with_storage()

    s.verify(sub.data.a == 0)

    main.test_sub_incr()
    s.verify(sub.data.a == 1)

    main.test_sub_incr_both()
    s.verify(sub.data.a == 2)

    main.test_sub_incr_store()
    s.verify(sub.data.a == 3)
    s.verify(main.data.a == 101)
