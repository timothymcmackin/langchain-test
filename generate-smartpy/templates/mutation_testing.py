import smartpy as sp

class MyContract(sp.Contract):
    def __init__(self):
        self.init(x = 42)

    @sp.entry_point
    def entry_point_1(self):
        self.data.x += 1

    @sp.entry_point
    def entry_point_2(self, params):
        sp.verify(params < 2)

@sp.add_test(name = "MyTest1")
def test():
    sc = sp.test_scenario()
    c1 = MyContract()
    sc += c1
    sc.verify(c1.data.x == 42)
    c1.entry_point_1()
    sc.verify(c1.data.x == 43)

@sp.add_test(name = "MyTest2")
def test():
    sc = sp.test_scenario()
    c1 = MyContract()
    sc += c1
    c1.entry_point_2(1)
    c1.entry_point_2(4).run(valid = False)

@sp.add_test(name = "Mutation")
def test():
    scenario = sp.test_scenario()
    with scenario.mutation_test() as mt:
        # mt.show_paths(True)
        mt.add_scenario("MyTest1")
        mt.add_scenario("MyTest2")
