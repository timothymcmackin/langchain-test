import smartpy as sp

set_f_type = sp.TLambda(sp.TInt, sp.TInt, with_storage="read-write", tstorage=sp.TRecord(x=sp.TInt))

def set_f(self, x):
    self.data.x = x
    sp.result(x * 100)

class Library(sp.Contract):
    def __init__(self):
        self.init(x = 0)

    @sp.onchain_view()
    def get_set_f(self):
        sp.result(sp.build_lambda(set_f, with_storage="read-write"))

# Same as Library, but different storage (hence specified in sp.build_lambda).
class Library2(sp.Contract):
    def __init__(self):
        self.init(y = "abc")

    @sp.onchain_view()
    def get_set_f(self):
        sp.result(sp.build_lambda(set_f, with_storage="read-write", tstorage=sp.TRecord(x=sp.TInt)))

class Main(sp.Contract):
    def __init__(self):
        self.init(x = 0)

    @sp.entry_point
    def run(self, f, x):
        sp.set_type(f, set_f_type)
        sp.compute(f(x))

    @sp.entry_point
    def save(self, f, x):
        sp.set_type(f, set_f_type)
        self.data.x = f(x)

class Remote(sp.Contract):
    @sp.entry_point
    def call(self, lib, main, x):
        t = sp.TLambda(sp.TInt, sp.TInt, with_storage="read-write", tstorage=sp.TRecord(x=sp.TInt))
        set_f = sp.compute(sp.view("get_set_f", lib, (), t)).open_some()
        main_run = sp.compute(sp.contract(sp.TRecord(f = t, x = sp.TInt), main, entry_point = "run")).open_some()
        sp.transfer(sp.record(f = set_f, x = x), sp.mutez(0), main_run)

@sp.add_test(name = "Effects")
def test():
    s = sp.test_scenario()
    lib = Library()
    lib2 = Library2()
    main = Main()
    remote = Remote()
    s += lib
    s += lib2
    s += main
    s += remote

    # Using a storage-modifying lambda from another contract with the
    # same storage:
    main.run(f = lib.get_set_f(), x = 5)
    s.verify(main.data.x == 5)
    s.verify(lib.data.x == 0)

    # Same, but with Library2:
    main.run(f = lib2.get_set_f(), x = 5)
    s.verify(main.data.x == 5)
    s.verify(lib.data.x == 0)

    # Same, but overwrite the storage immediately:
    main.save(f = lib.get_set_f(), x = 5)
    s.verify(main.data.x == 500)
    s.verify(lib.data.x == 0)

    # Complicate things a little by doing it via a remote contract
    # that doesn't have any state:
    remote.call(lib = lib.address, main = main.address, x = 7)
    s.verify(main.data.x == 7)
    s.verify(lib.data.x == 0)

    # We can also define effectful lambdas outside contracts, but then
    # we have to specify a tstorage:
    def f(self, x):
        self.data.x = 2 * x
        sp.result(0)
    my_f = sp.build_lambda(f, with_storage = "read-write", tstorage = sp.TRecord(x = sp.TIntOrNat))
    main.run(f = my_f, x = 42)
    s.verify(main.data.x == 84)
