# Options and Variants - Example for illustrative purposes only.

import smartpy as sp

class TestOptionsAndVariants(sp.Contract):
    def __init__(self):
        self.init(x = sp.variant("A", -1), y = sp.some(-42), z = sp.left(-10), r = 0
                , s = sp.record(x = 0, y = 1))

    @sp.entry_point
    def options(self):
        sp.if self.data.y.is_some():
            self.data.r = 44 + self.data.y.open_some(message = "Not a some!")
            self.data.y = sp.none
        sp.else:
            self.data.r = 3
            self.data.y = sp.some(12)

    @sp.entry_point
    def ep1(self):
        with self.data.x.match("A") as arg:
            self.data.x = sp.variant("B", -2)
            self.data.r = arg
        self.data.x = sp.variant("C", 3)

    @sp.entry_point
    def ep3(self):
        with self.data.z.match("Left") as arg:
            self.data.r = arg

    @sp.entry_point
    def ep4(self):
        with self.data.x.match("A", "a1") as a1:
            with self.data.z.match("Right", "a2") as a2:
                self.data.r = a1 + a2

    @sp.entry_point
    def ep5(self):
        sp.if self.data.x.is_variant("Toto"):
            self.data.r = 42

    @sp.entry_point
    def ep6(self):
        self.data.s = self.data.x.open_variant("Toto", message = "no toto")

    @sp.entry_point
    def ep7(self, params):
        self.data.x = params

    @sp.entry_point
    def ep8(self, params):
        with params.x.match_cases() as arg:
            with arg.match("A"):
                self.data.x = params.x
            with arg.match("B") as arg:
                self.data.y = sp.some(12 + arg + params.y)

    @sp.entry_point
    def ep9(self, params):
        sp.set_type(params.other, sp.TInt)
        with params.z.match_cases() as arg:
            with arg.match("A"):
                self.data.x = params.z

@sp.add_test(name = "variant")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Variants")
    scenario.add_flag("no-initial-cast")
    c = TestOptionsAndVariants()
    scenario += c
    c.options()
    c.ep1()
    c.ep3()
    c.ep4()
    c.ep5()
    c.ep6().run(valid = False)

sp.add_compilation_target("testVariant", TestOptionsAndVariants())
