import smartpy as sp

##########################################################
# Upgradable Contract that uses lambdas
# https://tezos.gitlab.io/michelson-reference/#type-lambda
##########################################################

class Upgradable(sp.Contract):
    def __init__(self, **kargs):
        self.init(**kargs)

    @sp.entry_point
    def calc(self, data):
        self.data.value = self.data.logic(data)

    @sp.entry_point
    def updateLogic(self, logic):
        self.data.logic = logic

# Logic Version 1 (x, y)
def logic1(data):
    t = sp.TRecord(x = sp.TNat, y = sp.TNat)
    unpacked = sp.unpack(data, t).open_some(message = "Cannot UNPACK")

    sp.result(unpacked.x + unpacked.y)

# Logic Version 2 (x, y, z)
def logic2(data):
    t = sp.TRecord(x = sp.TNat, y = sp.TNat, z = sp.TNat)
    unpacked = sp.unpack(data, t).open_some(message = "Cannot UNPACK")

    sp.result(unpacked.x + unpacked.y + unpacked.z)

@sp.add_test(name = "Upgradable")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Upgradable")

    c1 = Upgradable(value = 0, logic = sp.build_lambda(logic1))
    scenario += c1

    # Use logic version 1
    c1.calc(sp.pack(sp.record(x = 1, y = 2)))

    # Update logic to version 2
    c1.updateLogic(sp.build_lambda(logic2))

    # Use logic version 2
    c1.calc(sp.pack(sp.record(x = 1, y = 2, z = 3)))
