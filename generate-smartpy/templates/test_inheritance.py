import smartpy as sp

# Various technics to edit entry points


class MyContract(sp.Contract):
    def __init__(self, x, y):
        self.init(x = x,
                  y = y,
                  t = 0)

    @sp.entry_point
    def myEntryPoint(self, params):
        sp.verify(self.data.x <= 100)
        self.data.x += params

    @sp.entry_point
    def myEntryPointOther(self):
        self.data.x += 10

    @sp.entry_point
    def myEntryPointXXX(self, params):
        sp.verify(self.data.x <= 1000)
        self.data.x += params

    def some_helper(self):
        pass

class MyContract2(MyContract):
    def __init__(self, x, y):
        self.myEntryPointXXX = None # Removed even before the self.init is called.
        MyContract.__init__(self, 1, 2)
        self.update_initial_storage(z = 42, t = None)

    # removal of entry point, called within another entry point
    def myEntryPointOther(self):
        super().myEntryPointOther.f(self)

    @sp.entry_point
    def myEntryPoint(self, params):
        super().myEntryPoint.f(self, params)
        self.data.y = 12345
        self.some_helper(params + 2)
        self.myEntryPointOther()

    def some_helper(self, params):
        self.data.y += params

    @sp.entry_point
    def myEntryPoint2(self):
         pass

# Tests
@sp.add_test(name = "Inheritance")
def test():
    scenario = sp.test_scenario()
    c1 = MyContract2(12, 15)
    scenario += c1
