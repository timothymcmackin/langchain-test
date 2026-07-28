import smartpy as sp

class Lib(sp.Contract):
    @sp.private_lambda()
    def f(self, x):
        sp.result(x * 2)

    @sp.private_lambda()
    def g(self, x):
        sp.result(x * 2)

    @sp.private_lambda()
    def factorial(self, x):
        r = sp.local('r', 1)
        sp.for y in sp.range(2, x + 1):
            r.value *= y
        sp.result(r.value)

    @sp.private_lambda(recursive=True)
    def factorial_rec(self, n, factorial_rec):
        sp.if n <= 1:
             sp.result(n)
        sp.else:
             sp.result(n * factorial_rec(n-1))

    @sp.private_lambda()
    def factorial_five(self, params):
        sp.set_type(params, sp.TUnit)
        r = sp.local('r', 1)
        sp.for y in sp.range(2, 6):
           r.value *= y
        sp.result(r.value)

    @sp.entry_point
    def test_factorial(self):
        sp.verify(self.factorial(5) == 120)
        sp.verify(self.factorial_rec(5) == 120)
        sp.verify(self.factorial_five() == 120)

    @sp.private_lambda()
    def failing(self, x):
        with sp.set_result_type(sp.TInt):
            sp.failwith("Aaa" + x)

    @sp.entry_point
    def test_failing(self):
        sp.local("aaa", self.failing(""))

class Tester(sp.Contract):
    def __init__(self, f):
        self.f = f
        self.init(x = sp.none)

    @sp.entry_point
    def update(self, params):
        self.data.x = sp.some(self.f(params))

    @sp.entry_point
    def check(self, params, result):
        sp.verify(self.f(params) == result)

@sp.add_test(name = "Bind")
def test():
    s = sp.test_scenario()
    l = Lib()
    s += l
    l.test_factorial()
    tester = Tester(l.f)
    s += tester
    tester.update(12)
    s.verify(tester.data.x.open_some() == 24)
    tester.check(params = 12, result = 24)
    tester.check(params = 11, result = 22)
