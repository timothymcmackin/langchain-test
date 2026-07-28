# Inner operation is invalid, calling other contracts - Example for illustrative purposes only.

import smartpy as sp

class Test(sp.Contract):
    def __init__(self):
        self.init(counter = 0)

    @sp.entry_point
    def run(self, n):
        sp.verify(self.data.counter * n != 9)
        sp.if n > 1:
            self.data.counter += 1
            sp.transfer(n - 1, sp.mutez(0), sp.self_entry_point("run"))

    @sp.entry_point
    def reset(self):
        self.data.counter = 0

    @sp.entry_point
    def compute(self, n):
        sp.transfer(n, sp.mutez(0), sp.self_entry_point("run"))

@sp.add_test(name = "Test")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Test template - Inter-Contract Calls")
    test = Test()
    scenario += test
    for i in range(0, 20):
        valid = i not in [6, 10]
        test.reset()
        test.compute(i).run(valid = valid)
        scenario.verify(test.data.counter == (max(0, i - 1) if valid else 0))
