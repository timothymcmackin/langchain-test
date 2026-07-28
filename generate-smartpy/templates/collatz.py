# Collatz, calling other contracts - Example for illustrative purposes only.

import smartpy as sp

# Compute the length of the nth Collatz sequence
# (https://oeis.org/A006577) with on-chain continuations

def call(c, x):
    sp.transfer(x, sp.mutez(0), c)

class OnEven(sp.Contract):
    def __init__(self):
        self.init();
        self.add_flag("no-single-entry-point-annotation")

    @sp.entry_point
    def run(self, params):
        call(params.k, params.x / 2)

class OnOdd(sp.Contract):
    def __init__(self):
        self.init();
        self.add_flag("no-single-entry-point-annotation")

    @sp.entry_point
    def run(self, params):
        sp.set_type(params.x, sp.TNat)
        call(params.k, 3 * params.x + 1)

class Collatz(sp.Contract):
    def __init__(self, onEven, onOdd):
        self.init(onEven  = onEven,
                  onOdd   = onOdd,
                  counter = 0)

    @sp.entry_point
    def run(self, x):
        sp.if x > 1:
            self.data.counter += 1
            tk = sp.TRecord(k = sp.TContract(sp.TNat), x = sp.TNat)
            params = sp.record(k = sp.self_entry_point("run"), x = x)
            sp.if x % 2 == 0:
                call(sp.contract(tk, self.data.onEven).open_some(), params)
            sp.else:
                call(sp.contract(tk, self.data.onOdd).open_some(), params)

    @sp.entry_point
    def reset(self):
        self.data.counter = 0

@sp.add_test(name = "Collatz")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Collatz template - Inter-Contract Calls")
    on_even = OnEven()
    scenario += on_even
    on_odd = OnOdd()
    scenario += on_odd
    collatz = Collatz(onEven = on_even.address,
                      onOdd  = on_odd.address)
    scenario += collatz
    # See https://oeis.org/A006577/list
    collatz.run(42)
    scenario.verify(collatz.data.counter == 8)
    collatz.reset()
    collatz.run(5)
    scenario.verify(collatz.data.counter == 5)

sp.add_compilation_target("collatz", Collatz(sp.address("KT1QEaMVhcGvnf31cmWN4YWcujfzwhEQqX8c"),sp.address("KT1CbRd63JiSrZsVEJzmXAmA5ACNvpqYTGbM")))
