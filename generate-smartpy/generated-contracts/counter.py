import smartpy as sp

@sp.module 
def main():
    class Counter(sp.Contract):
        def __init__(self):
            self.data.value=0

        @sp.entrypoint
        def add_one(self):
            self.data.value += 1

        @sp.entrypoint
        def subtract_one(self):
            self.data.value -= 1

@sp.add_test()
def test():
    scenario = sp.test_scenario("Counter")
    c = main.Counter()
    scenario += c
    
    # Initial value should be 0
    scenario.verify(c.data.value == 0)
    
    # Add one
    c.add_one()
    scenario.verify(c.data.value == 1)
    
    # Subtract one
    c.subtract_one()
    scenario.verify(c.data.value == 0)

    # sp.add_compilation_target("Counter", Counter())
