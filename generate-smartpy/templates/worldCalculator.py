# World Calculator - Example for illustrative purposes only.

import smartpy as sp

class WorldCalculator(sp.Contract):
    def __init__(self):
        self.init(Help = ["SmartPy Reverse Polish Calculator Template", "Operations: +, -, *, ^", "Example: 2 3 4 * - 3 ^"],
                  formula = "",
                  operations = [],
                  result = 0,
                  summary = "")

    @sp.private_lambda()
    def nat_of_string(self, params):
        c   = sp.map({str(x) : x for x in range(0, 10)})
        result = sp.local('result', 0)
        sp.for idx in sp.range(0, sp.len(params)):
            result.value = 10 * result.value + c[sp.slice(params, idx, 1).open_some()]
        sp.result(result.value)

    @sp.private_lambda()
    def string_of_nat(self, params):
        c   = sp.map({x : str(x) for x in range(0, 10)})
        x   = sp.local('x', params)
        res = sp.local('string_res', [])
        sp.if x.value == 0:
            res.value.push('0')
        sp.while 0 < x.value:
            res.value.push(c[x.value % 10])
            x.value //= 10
        sp.result(sp.concat(res.value))

    @sp.private_lambda()
    def string_split(self, params):
        s = sp.set_type_expr(params.s, sp.TString)
        sep = params.sep
        prev_idx = sp.local('prev_idx', 0)
        res = sp.local('res', [])
        sp.for idx in sp.range(0, sp.len(s)):
            sp.if sp.slice(s, idx, 1).open_some() == sep:
                res.value.push(sp.slice(s, prev_idx.value, sp.as_nat(idx - prev_idx.value)).open_some())
                prev_idx.value = idx + 1
        sp.if sp.len(s) > 0:
            res.value.push(sp.slice(s, prev_idx.value, sp.as_nat(sp.len(s) - prev_idx.value)).open_some())
        sp.result(res.value.rev())

    def pow(self, x):
        result = sp.local('result', 1)
        sp.for i in sp.range(0, sp.fst(x)):
            result.value *= sp.snd(x)
        sp.result(result.value)

    @sp.entry_point
    def compute(self, params):
        bin_ops = sp.local('bin_ops',
                    sp.map({'+' : sp.build_lambda(lambda x:(sp.fst(x) + sp.snd(x))),
                            '*' : sp.build_lambda(lambda x:(sp.fst(x) * sp.snd(x))),
                            '-' : sp.build_lambda(lambda x:(sp.snd(x) - sp.fst(x))),
                            '^' : sp.build_lambda(self.pow),
                    }))
        elements = sp.local('elements', self.string_split(sp.record(s = params, sep = ' ')))
        stack = sp.local('stack', [], sp.TList(sp.TInt))
        formula = sp.local('formulas', [])
        sp.for element in elements.value:
            sp.if element != "":
                sp.if bin_ops.value.contains(element):
                    with sp.match_cons(stack.value) as x1:
                        with sp.match_cons(x1.tail) as x2:
                            stack.value = x2.tail
                            stack.value.push(bin_ops.value[element]((x1.head, x2.head)))
                        sp.else:
                            sp.failwith("Bad formula: too many operators")
                    sp.else:
                        sp.failwith("Bad formula: too many operators")
                    with sp.match_cons(formula.value) as x1:
                        with sp.match_cons(x1.tail) as x2:
                            formula.value = x2.tail
                            formula.value.push(sp.concat(["(", x2.head, element, x1.head, ")"]))
                sp.else:
                    stack.value.push(self.nat_of_string(element))
                    formula.value.push(element)
        self.data.formula = params
        self.data.operations = elements.value
        length = sp.local('length', sp.len(stack.value))
        sp.verify(length.value == 1, message = ("Bad stack at the end of the computation. Length = " + self.string_of_nat(length.value), stack.value))
        with sp.match_cons(stack.value) as x1:
            with sp.match_cons(formula.value) as f1:
                self.data.result = x1.head
                sp.if 0 <= x1.head:
                    self.data.summary = f1.head + " = " + self.string_of_nat(sp.as_nat(x1.head))
                sp.else:
                    self.data.summary = f1.head + " = -" + self.string_of_nat(sp.as_nat(-x1.head))

@sp.add_test(name = "World Calculator")
def test():
    scenario = sp.test_scenario()
    scenario.h1("World Calculator")
    c1 = WorldCalculator()
    scenario += c1
    c1.compute("1 2 3 + +")
    c1.compute("1 2 + 3 4 + * 12 - 3 ^")
    c1.compute("1 2 + 3 4 + * 12 - 3 ^ 5").run(valid = False)
    c1.compute("-").run(valid = False)
    c1.compute("1 2 3 + + + +").run(valid = False)
    scenario.simulation(c1)

sp.add_compilation_target("worldCalculator", WorldCalculator())
