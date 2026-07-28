# Shuffle - Example for illustrative purposes only.

import smartpy as sp

class Shuffle(sp.Contract):
    def __init__(self):
        self.init(a = sp.record(x1 = -1, x2 = -2), b = sp.record(x1 = -3, x2 = -4))

    @sp.entry_point
    def swap(self):
        x = sp.local("x", self.data.a.x1)
        self.data.a.x1 = self.data.a.x2
        self.data.a.x2 = x.value

        self.data.b.x1 = self.data.b.x2
        # self.data.b.x1 += 1
        self.data.b.x2 *= 2

# Tests
@sp.add_test(name = "Shuffle")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Shuffle")
    c = Shuffle()
    scenario += c

sp.add_compilation_target("shuffle", Shuffle())
