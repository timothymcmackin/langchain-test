import smartpy as sp

class Constants(sp.Contract):
    def __init__(self, storage, constant1, constant2):
        self.constant1 = constant1
        self.constant2 = constant2
        self.init(storage)

    @sp.entry_point
    def ep(self, x):
        # Compute the new value from values stored as constants
        self.data = self.constant1(x) + self.constant2

@sp.add_test(name = "Test constants")
def test():
    # Create a scenario
    scenario = sp.test_scenario()

    # Create some lambda
    def some_lambda(x):
        sp.result(x * 10)

    # Create 2 constants from their values
    constant1 = scenario.prepare_constant_value(some_lambda)
    constant2 = scenario.prepare_constant_value(100)
    # Print the constants
    scenario.show(constant1)
    scenario.show(constant2)

    # Create contract
    contract = Constants(0, constant1 = constant1, constant2 = constant2)
    scenario += contract

    # Call the contract
    contract.ep(10)

sp.add_compilation_target(
    "constants_compilation",
    Constants(
        0,
        constant1 = sp.constant("c1", t = sp.TLambda(sp.TNat, sp.TNat)),
        constant2 = sp.constant("c2", t = sp.TNat)
    )
)