# Two Level Multisig - Example for illustrative purposes only.

import smartpy as sp

# MultiSigFactory is a two level multisig factory contract
# - two level because to validate a property, we can use several groups of participants and not only one group,
# - and a factory because it can hold several such two level multisig contracts.

class MultiSigFactory(sp.Contract):
    def __init__(self):
        self.init(multisigs = sp.big_map(), nbMultisigs = 0)

    @sp.entry_point
    def build(self, params):
        contract = params.contract
        self.data.multisigs[self.data.nbMultisigs] = contract
        self.data.nbMultisigs += 1

    @sp.entry_point
    def sign(self, id, contractId, contractName):
        sp.verify(id == sp.sender)
        sp.set_type(contractName, sp.TString)
        contract = self.data.multisigs[contractId]
        sp.verify(contractName == contract.name)
        sp.set_type(contract.weight, sp.TInt)
        sp.set_type(contract.groupsOK, sp.TInt)
        with sp.for_("group", contract.groups) as group:
            with sp.for_("participant", group.participants) as participant:
                with sp.if_(participant.id == id):
                    sp.verify(~ participant.hasVoted)
                    participant.hasVoted = True
                    sp.set_type(group.weight, sp.TInt)
                    group.weight += participant.weight
                    group.voters += 1
                    with sp.if_(~group.ok & (group.thresholdVoters <= group.voters) & (group.thresholdWeight <= group.weight)):
                        group.ok = True
                        contract.weight += group.contractWeight
                        contract.groupsOK += 1
                        with sp.if_(~contract.ok & (contract.thresholdGroupsOK <= contract.groupsOK) & (contract.thresholdWeight <= contract.weight)):
                            contract.ok = True
                            self.onOK(contract)

    def onOK(self, contract):
        pass

# MultiSigFactoryWithPayment inherits from MultiSigFactory and adds a
# payment functionality

class MultiSigFactoryWithPayment(MultiSigFactory):
    def onOK(self, contract):
        sp.send(contract.owner, contract.amount)

def addMultiSig(c, thresholdWeight, thresholdGroupsOK):
    # tgroup = c.getStorageType().go('multisigs').go('list').go('groups').go('list')
    # tparticipant = tgroup.go('participants').go('list')
    def group(contractWeight, thresholdWeight, thresholdVoters, participants):
        participants = [sp.record(hasVoted = False, weight = weight, id = id) for (id, weight) in participants]
        return sp.record(weight          = 0,
                         voters          = 0,
                         contractWeight  = contractWeight,
                         thresholdWeight = thresholdWeight,
                         thresholdVoters = thresholdVoters,
                         participants    = participants,
                         ok              = False
        )
    p1 = sp.address("tz1NFevnqBrtcZTZTeKP2YBBjsPs9bih5i3J")
    p2 = sp.address("tz1ZRjMiF9K9n3S9AcUrTGUzR2okS7dn9KXS")
    p3 = sp.address("tz1NLJRAAwYdggijWz9EFtX5Dgs95BLfD6mP")
    g1 = group(5, 5 , 2, [(p1, 2), (p2, 8), (p3, 1)])
    g2 = group(7, 5 , 1, [(p1, 7), (p2, 8)])
    g3 = group(7, 10, 1, [(p3, 10)])
    contract = sp.record(name              = "demo",
                         thresholdGroupsOK = thresholdGroupsOK,
                         groupsOK          = 0,
                         thresholdWeight   = thresholdWeight,
                         weight            = 0,
                         groups            = sp.list([g1, g2, g3]),
                         ok                = False)
    return c.build(contract = contract)

# Tests
@sp.add_test(name = "MultiSig")
def test():
    c1 = MultiSigFactory()

    alice    = sp.test_account("Alice")
    bob      = sp.test_account("Rob")
    charlie  = sp.test_account("Charlie")

    scenario = sp.test_scenario()
    scenario.h1("Multi Sig")
    scenario.h2("Contract")
    scenario.h3("Simple multisig factories")
    scenario += c1
    scenario.h2("First: define a simple multisig")
    scenario += addMultiSig(c1, thresholdWeight = 10, thresholdGroupsOK = 2)
    scenario.h2("Message execution")
    scenario.h3("A first move")
    c1.sign(id = alice.address, contractId = 0, contractName = "demo").run(sender = alice)
    c1.sign(id = bob.address, contractId = 0, contractName = "demo").run(sender = bob)

    scenario.h2("First: define a simple multi-sig")
    scenario += addMultiSig(c1, thresholdWeight = 10, thresholdGroupsOK = 3)
    scenario.h2("Message execution")
    scenario.h3("A first move")
    c1.sign(id = alice.address, contractId = 1, contractName = "demo").run(sender = alice)
    c1.sign(id = bob.address, contractId = 1, contractName = "demo").run(sender = bob)
    scenario.h4("We need a third vote")
    c1.sign(id = charlie.address, contractId = 1, contractName = "demo").run(sender = charlie)
    scenario.h4("Final state")
    scenario.show(c1.data)

    scenario.h3("Multisig factories with payments")
    c2 = MultiSigFactoryWithPayment()
    scenario += c2

sp.add_compilation_target("multisig", MultiSigFactoryWithPayment())
