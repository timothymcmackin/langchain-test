# Check Language Constructions - Example for illustrative purposes only.

# This contract is only for test purposes.
# It tests two things against each other:
# - regular Python computations
# - SmartPy / SmartML computations

# Please see corresponding Medium post:
# https://smartpy-io.medium.com/basic-computations-in-smartpy-python-and-michelson-bb69dccddaf2

import smartpy as sp

class CheckOperator(sp.Contract):
    def __init__(self, all_tests):
        self.all_tests = all_tests
        self.init()

    @sp.entry_point
    def run(self):
        for my_tests, xs, ys in self.all_tests:
            tests = []
            for name, op in my_tests:
                op_ = lambda x, op = op: op(sp.fst(x), sp.snd(x))
                l = []
                for x in xs:
                    for y in ys:
                        l.append((x, y, op(x, y)))
                tests.append((name, op_, l))
            sp.for test in tests:
                name, loc_op, loc_tests = sp.match_tuple(test, "name", "loc_op", "loc_tests")
                sp.for test_ in loc_tests:
                    x, y, res = sp.match_tuple(test_, "x", "y", "res")
                    z = sp.local("z", loc_op((x, y))).value
                    sp.verify(z == res, message = (name, (x, (y, z, res))))

@sp.add_test(name = "Operators")
def test():
    int_tests = [('+' , lambda x, y: x + y),
                 ('-' , lambda x, y: (0 + x) - y),
                 ('*' , lambda x, y: x * y)]

    nat_tests = [('%' , lambda x, y: x % y),
                 ('//', lambda x, y: x // y)]

    bool_tests = [('&', lambda x, y: x & y),
                  ('|', lambda x, y: x | y)]

    scenario = sp.test_scenario()

    c1 = CheckOperator([
        (int_tests, [11, 123, -15], [22, 28, -47, -2]),
        (nat_tests, [11, 123], [22, 28]),
        (bool_tests, [True, False], [True, False])])

    scenario.register(c1)
    c1.run().run(show = False)
