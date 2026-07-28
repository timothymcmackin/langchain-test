# Flags - Example for illustrative purposes only.

import smartpy as sp

class Test(sp.Contract):
    def __init__(self, flags):
        self.init(x = 1, y = 2)
        for flag in flags:
            self.add_flag(flag)

@sp.add_test(name = "Flags")
def test():
    scenario = sp.test_scenario()

    scenario += Test([])

    scenario.add_flag("no-initial-cast")
    scenario += Test([])

    scenario.add_flag("initial-cast")
    scenario += Test([])

    scenario += Test(["no-initial-cast"])

    scenario += Test([])

    scenario += Test(["initial-cast"])

    scenario += Test([])

sp.add_compilation_target("zero", Test([]))

sp.add_compilation_target("cast", Test(["initial-cast"]))

sp.add_compilation_target("no-cast", Test(["no-initial-cast"]))
