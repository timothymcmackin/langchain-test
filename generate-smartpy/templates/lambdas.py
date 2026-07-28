import smartpy as sp

class Created(sp.Contract):
    def __init__(self):
        self.init_type(sp.TRecord(a = sp.TInt, b = sp.TNat))

    @sp.entry_point
    def myEntryPoint(self, params):
        self.data.a += params.x
        self.data.b += params.y

class MyContract(sp.Contract):
    def __init__(self):
        self.created = Created()
        self.init(value = 0, ggg = sp.some(42), fff = sp.none, abcd = 0, f = lambda x: x+1)

    @sp.entry_point
    def f(self):
        toto = sp.local('toto', lambda x: sp.fst(x) + sp.snd(x))
        titi = sp.local('titi', toto.value.apply(5))
        self.data.value = titi.value(8)

    @sp.entry_point
    def flambda(self):
        self.data.value = self.flam(self.flam(15)) + self.square_root(12345)

    @sp.private_lambda()
    def flam(self, params):
        sp.result(322 * params)

    @sp.private_lambda()
    def square_root(self, x):
        sp.verify(x >= 0)
        y = sp.local('y', x)
        sp.while y.value * y.value > x:
            y.value = (x // y.value + y.value) // 2
        sp.verify((y.value * y.value <= x) & (x < (y.value + 1) * (y.value + 1)))
        sp.result(y.value)

    @sp.private_lambda()
    def comp(self, params):
        sp.result(params.f(params.x))

    @sp.entry_point
    def comp_test(self):
        self.data.abcd = self.comp(sp.record(f = lambda x: x + 3, x = 2))

    @sp.private_lambda()
    def abs(self, x):
        sp.if x > 0:
            sp.result(x)
        sp.else:
            sp.result(-x)

    @sp.entry_point
    def abs_test(self, x):
        self.data.abcd = self.abs(x)

    @sp.entry_point
    def h(self):
        def sqrt(x):
            sp.verify(x >= 0)
            y = sp.local('y', x)
            sp.while y.value * y.value > x:
                y.value = (x // y.value + y.value) // 2
            sp.verify((y.value * y.value <= x) & (x < (y.value + 1) * (y.value + 1)))
            sp.result(y.value)
        self.data.fff = sp.some(sqrt)

    @sp.entry_point
    def hh(self, params):
        self.data.value = self.data.fff.open_some()(params)

    @sp.entry_point
    def i(self):
        def check1(x):
            sp.verify(x >= 0)
        def check2(x):
            sp.verify(x >= 0)
            sp.result(x - 2)
        def check3(x):
            sp.verify(x >= 0)
            sp.result(True)
        def check4(x):
            def check3bis(x):
                sp.verify(x >= 0)
                sp.result(False)
            sp.local('ch3b', check3bis)
            sp.verify(x >= 0)
            sp.result(3 * x)
        sp.local('ch1', check1)
        sp.local('ch2', check2)
        sp.local('ch3', check3)
        ch4 = sp.local('ch4', check4)
        self.data.value = ch4.value(12)
        sp.verify(self.not_pure(()) == self.data.value)

    @sp.entry_point
    def operation_creation(self):
        def test(x):
            sp.create_contract(storage = sp.record(a = x, b = 15), contract = self.created)
            sp.create_contract(storage = sp.record(a = 2 * x, b = 15), contract = self.created)
        f = sp.local('f', sp.utils.lambda_operations_only(test)).value
        sp.add_operations(f(12345001))
        sp.add_operations(f(12345002))

    @sp.entry_point
    def operation_creation_result(self):
        def test(x):
            sp.create_contract(storage = sp.record(a = x, b = 15), contract = self.created)
            sp.result(4)
        f = sp.local('f', sp.utils.lambda_with_operations(test))
        x = sp.local('x', f.value(12345001)).value
        y = sp.local('y', f.value(12345002)).value
        sp.add_operations(sp.fst(x))
        sp.add_operations(sp.fst(y))
        sp.local('sum', sp.snd(x) + sp.snd(y))

    @sp.private_lambda()
    def oh_no(self, params):
        with sp.set_result_type(sp.TInt):
           sp.if params > 0:
              sp.failwith("too big")
           sp.else:
              sp.failwith("too small")

    @sp.private_lambda(with_storage="read-write", wrap_call=True)
    def not_pure(self, x):
        sp.result(self.data.value)

    @sp.entry_point
    def fact(self, n):
        fact = sp.compute(sp.build_lambda((lambda n, fact: sp.eif(n<=1,1,n*fact(n-1))), recursive=True))
        self.data.abcd = fact(n)

@sp.add_test(name = "Lambdas")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Lambdas")
    c1 = MyContract()
    scenario += c1
    c1.f()
    c1.flambda()
    c1.i()
    c1.comp_test()
    c1.abs_test(5)
    scenario.verify(c1.data.abcd == 5)
    c1.abs_test(-42)
    scenario.verify(c1.data.abcd == 42)
    c1.fact(3)
    scenario.verify(c1.data.abcd == 6)
    c1.fact(5)
    scenario.verify(c1.data.abcd == 120)

sp.add_compilation_target("lambdas", MyContract())

# ----------------------------------------------------------------

def dummy_lambda_function(params):
    sp.set_type(params, sp.TUnit)
    dummyContractHandle = sp.contract(sp.TUnit, sp.self_address).open_some()
    sp.transfer(sp.unit, sp.mutez(0), dummyContractHandle)

class MyContract2(sp.Contract):
    def __init__(self):
        self.init(result = sp.none)
        self.init_type(sp.TRecord(result = sp.TOption(sp.TLambda(sp.TUnit, sp.TUnit, with_operations = True))))

    @sp.entry_point
    def exec_lambda(self, params):
        self.data.result = sp.some(params)

class MyContract3(sp.Contract):
    def __init__(self):
        self.init(result = sp.none)
        self.init_type(sp.TRecord(result = sp.TOption(sp.TLambda(sp.TUnit, sp.TUnit, with_operations = True))))

    @sp.entry_point
    def exec_lambda(self, params):
        self.data.result = sp.some(params)

    @sp.entry_point
    def nothing(self):
        pass

if "templates" not in __name__:
    @sp.add_test(name="Lambdas type with effect")
    def test():
        scenario = sp.test_scenario()
        c1 = MyContract2()
        scenario += c1
        c1.exec_lambda(sp.build_lambda(dummy_lambda_function, with_operations=True))
        c2 = MyContract3()
        scenario += c2
        c2.exec_lambda(sp.build_lambda(dummy_lambda_function, with_operations=True))

