# Mini-kitties - Example for illustrative purposes only.

# This small example is loosely inspired by CryptoKitties.

import smartpy as sp

class MiniKitties(sp.Contract):
    def __init__(self, creator, newAuctionDuration, hatchingDuration):
        self.newAuctionDuration = newAuctionDuration
        self.hatchingDuration = hatchingDuration
        self.init(kitties = {}, creator = creator)

    @sp.entry_point
    def build(self, params):
        sp.verify(self.data.creator == sp.sender)
        sp.verify(params.kitty.isNew)
        sp.set_type(params.kitty.kittyId, sp.TInt)
        self.data.kitties[params.kitty.kittyId] = params.kitty

    @sp.entry_point
    def sell(self, params):
        sp.verify(sp.mutez(0) <= params.price)
        self.checkAvailable(self.data.kitties[params.kittyId], params)
        self.data.kitties[params.kittyId].price = params.price

    @sp.entry_point
    def lend(self, params):
        sp.verify(sp.mutez(0) <= params.price)
        self.checkAvailable(self.data.kitties[params.kittyId], params)
        self.data.kitties[params.kittyId].borrowPrice = params.price

    @sp.entry_point
    def buy(self, params):
        kitty = self.data.kitties[params.kittyId]
        sp.verify(sp.mutez(0) < kitty.price)
        sp.verify(kitty.price <= params.price)
        sp.verify(sp.amount == params.price)
        sp.send(kitty.owner, params.price)
        kitty.owner = sp.sender
        sp.if kitty.isNew:
            kitty.isNew = False
            kitty.auction = sp.now.add_seconds(self.newAuctionDuration)
        sp.verify(sp.now <= kitty.auction)
        sp.if sp.now <= kitty.auction:
            kitty.price = params.price + sp.mutez(1)

    def checkAvailable(self, kitty, params, borrow = False):
        sp.if borrow:
            sp.verify(sp.mutez(0) < kitty.borrowPrice)
            borrowPrice = params.borrowPrice
            sp.verify(kitty.borrowPrice < borrowPrice)
            sp.verify(sp.amount == borrowPrice)
            sp.send(kitty.owner, borrowPrice)
        sp.verify(kitty.auction < sp.now)
        sp.verify(kitty.hatching < sp.now)

    def newKitty(self, kittyId, hatching, generation):
        return sp.record(kittyId = kittyId, owner = sp.sender, price = sp.mutez(0), isNew = False, auction = sp.timestamp(0), hatching = hatching, generation = generation, borrowPrice = sp.mutez(0))

    @sp.entry_point
    def breed(self, params):
        parent1 = params.parent1
        parent2 = params.parent2
        kitty1 = self.data.kitties[parent1]
        kitty2 = self.data.kitties[parent2]
        sp.verify(parent1 != parent2)
        self.checkAvailable(kitty1, params)
        self.checkAvailable(kitty2, params, kitty2.owner != sp.sender)
        hatching = sp.now.add_seconds(self.hatchingDuration)
        kitty1.hatching = hatching
        kitty2.hatching = hatching
        kitty = self.newKitty(params.kittyId, hatching, 1 + sp.max(kitty1.generation, kitty2.generation))
        self.data.kitties[kitty.kittyId] = kitty

@sp.add_test(name = "MiniKitties")
def test():
    creator = sp.test_account("Creator")
    alice   = sp.test_account("Alice")
    bob     = sp.test_account("Robert")

    c1 = MiniKitties(creator.address, newAuctionDuration = 10, hatchingDuration = 100)
    scenario  = sp.test_scenario()
    scenario.h1("Mini Kitties")
    scenario += c1
    def newKitty(kittyId, price):
        return sp.record(kittyId = kittyId, owner = creator.address, price = sp.mutez(price), isNew = True, auction = sp.timestamp(0), hatching = sp.timestamp(0), generation = 0, borrowPrice = sp.mutez(0))
    c1.build(kitty = newKitty(0, 10)).run(sender = creator)
    c1.build(kitty = newKitty(1, 10)).run(sender = creator)
    c1.build(kitty = newKitty(2, 10)).run(sender = creator)
    c1.build(kitty = newKitty(3, 10)).run(sender = creator)
    c1.buy(  kittyId = 1, price = sp.mutez(10)).run(sender = alice, amount = sp.mutez(10))
    c1.buy(  kittyId = 2, price = sp.mutez(10)).run(sender = alice, amount = sp.mutez(10))
    c1.buy(  kittyId = 1, price = sp.mutez(11)).run(sender = bob, amount = sp.mutez(11), now = sp.timestamp(3))
    c1.buy(  kittyId = 1, price = sp.mutez(15)).run(sender = alice, amount = sp.mutez(15), now = sp.timestamp(9))
    scenario.h2("A bad execution")
    c1.buy(  kittyId = 1, price = sp.mutez(20)).run(sender = bob, amount = sp.mutez(20), now = sp.timestamp(13), valid = False)
    scenario.h2("Hatching")
    c1.breed(borrowPrice = sp.mutez(10), kittyId = 4, parent1 = 1, parent2 = 2).run(sender = alice, now = sp.timestamp(15))

sp.add_compilation_target("minikitties", MiniKitties(creator = sp.address("tz1M9CMEtsXm3QxA7FmMU2Qh7xzsuGXVbcDr"), newAuctionDuration = 10, hatchingDuration = 100))
