# Fibonacci, calling other contracts - Example for illustrative purposes only.

import smartpy as sp

class Fibonacci(sp.Contract):
    def __init__(self):
        self.init(counter = 0, steps = [])

    @sp.entry_point
    def run(self, n):
        self.data.steps.push(n)
        sp.if n > 1:
            sp.transfer(n - 2, sp.mutez(0), sp.self_entry_point("run"))
            sp.transfer(n - 1, sp.mutez(0), sp.self_entry_point("run"))
        sp.else:
            self.data.counter += 1

    @sp.entry_point
    def compute(self, n):
        self.data.counter = 0
        self.data.steps = []
        sp.transfer(n, sp.mutez(0), sp.self_entry_point("run"))

def fibo(n):
    if n < 2:
        return 1
    return fibo(n - 1) + fibo(n - 2)

@sp.add_test(name = "Fibonacci")
def test():
    scenario = sp.test_scenario()
    scenario.h2("Fibonacci")
    fibonacci = Fibonacci()
    scenario += fibonacci
    for i in range(0, 10):
        fibonacci.compute(i)
        scenario.verify(fibonacci.data.counter == fibo(i))
    scenario.show(fibonacci.data.steps.rev())
    scenario.verify_equal(fibonacci.data.steps.rev(), [9, 7, 5, 3, 1, 2, 0, 1, 4, 2, 0, 1, 3, 1, 2, 0, 1, 6, 4, 2, 0, 1, 3, 1, 2, 0, 1, 5, 3, 1, 2, 0, 1, 4, 2, 0, 1, 3, 1, 2, 0, 1, 8, 6, 4, 2, 0, 1, 3, 1, 2, 0, 1, 5, 3, 1, 2, 0, 1, 4, 2, 0, 1, 3, 1, 2, 0, 1, 7, 5, 3, 1, 2, 0, 1, 4, 2, 0, 1, 3, 1, 2, 0, 1, 6, 4, 2, 0, 1, 3, 1, 2, 0, 1, 5, 3, 1, 2, 0, 1, 4, 2, 0, 1, 3, 1, 2, 0, 1])

sp.add_compilation_target("fibonacci_comp", Fibonacci())
