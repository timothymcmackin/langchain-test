import smartpy as sp

class Calculator(sp.Contract):
    def __init__(self, exception_optimization_level, no_comment = False):
        self.exception_optimization_level = exception_optimization_level
        if no_comment:
            self.add_flag("erase-comments")
        self.init(value = 0)

    @sp.entry_point
    def multiply(self, x, y):
        self.data.value = x * y

    @sp.entry_point
    def add(self, x, y):
        self.data.value = x + y

    @sp.entry_point
    def square(self, x):
        self.data.value = x * x

    @sp.entry_point
    def squareRoot(self, x):
        sp.verify(x >= 0)
        y = sp.local('y', x)
        sp.while y.value * y.value > x:
            y.value = (x // y.value + y.value) // 2
        sp.verify((y.value * y.value <= x) & (x < (y.value + 1) * (y.value + 1)))
        self.data.value = y.value

    @sp.entry_point
    def factorial(self, x):
        self.data.value = 1
        sp.for y in sp.range(1, x + 1):
            self.data.value *= y

    @sp.entry_point
    def log2(self, x):
        self.data.value = 0
        y = sp.local('y', x)
        sp.while 1 < y.value:
            self.data.value += 1
            y.value //= 2

    @sp.entry_point
    def other(self, x):
        c = sp.compute({1:2, 2: 3})
        self.data.value = c[x]
        self.data.value += c.get(x, 12)
        self.data.value += c.get(x, message = "not here")


if "templates" not in __name__:
    @sp.add_test(name = "Test")
    def test():
        scenario = sp.test_scenario()
        scenario.h1("Levels")
        scenario.p('; '.join(sp.exception_optimization_levels))
        for exception_optimization_level in sp.exception_optimization_levels:
            scenario.h2("Level: %s" % exception_optimization_level)
            scenario += Calculator(exception_optimization_level)
        scenario.h2("Level: FullDebug - No comment")
        scenario += Calculator("full-debug", no_comment = True)
