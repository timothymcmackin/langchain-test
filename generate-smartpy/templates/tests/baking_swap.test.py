import smartpy as sp

BakingSwap = sp.io.import_template("baking_swap.py").BakingSwap

if "templates" not in __name__:
    admin = sp.test_account("Admin")
    notAdmin = sp.test_account("notAdmin")
    voting_powers = {
        admin.public_key_hash: 0,
    }
    class Receiver(sp.Contract):
        @sp.entry_point
        def default(self):
            pass

    @sp.add_test(name="Full", is_default=True)
    def test():
        sc = sp.test_scenario()
        sc.h1("Full test")
        sc.table_of_contents()
        sc.h2("Origination")
        c = BakingSwap(admin.address, 0, 10000)
        sc += c
        sc.h2("Delegator")
        delegator = Receiver()
        sc += delegator
        sc.h2("Admin receiver")
        admin_receiver = Receiver()
        sc += admin_receiver

        sc.h2('delegate')
        c.delegate(admin.public_key_hash).run(sender=admin, voting_powers=voting_powers)
        sc.verify(c.baker == sp.some(admin.public_key_hash))
        sc.h3('Failures')
        c.delegate(admin.public_key_hash).run(
            sender=notAdmin,
            voting_powers=voting_powers,
            valid=False,
            exception="WrongCondition: sp.sender == self.data.admin")
        c.delegate(admin.public_key_hash).run(
            sender=admin,
            amount=sp.mutez(1),
            voting_powers=voting_powers,
            valid=False,
            exception="WrongCondition: sp.amount == sp.tez(0)")
        c.delegate(notAdmin.public_key_hash).run(
            sender=admin,
            voting_powers=voting_powers,
            valid=False,
            exception="WrongCondition: sp.sender == sp.to_address(sp.implicit_account(params))")

        sc.h2('collateralize')
        c.collateralize().run(sender=admin, amount=sp.tez(500))
        sc.verify(c.data.collateral == sp.tez(500))
        sc.h3('Failures')
        c.collateralize().run(
            sender=notAdmin,
            amount=sp.tez(500),
            valid=False,
            exception="WrongCondition: sp.sender == self.data.admin")

        sc.h2('set_offer')
        c.set_offer(rate=1000, duration=365).run(sender=admin)
        sc.h3('Failures')
        c.set_offer(rate=1000, duration=365).run(
            sender=notAdmin,
            valid=False,
            exception="WrongCondition: sp.sender == self.data.admin")
        c.set_offer(rate=1000, duration=365).run(
            sender=admin,
            amount=sp.mutez(1),
            valid=False,
            exception="WrongCondition: sp.amount == sp.tez(0)")

        sc.h2('deposit')
        c.deposit(rate=1000, duration=365).run(sender=delegator.address, amount=sp.tez(100))
        sc.verify(c.data.collateral == sp.tez(490))
        sc.verify(c.data.ledger[delegator.address] == sp.record(
            amount=sp.tez(110),
            due=sp.timestamp(365*24*3600)))
        sc.h3('Failures')
        c.deposit(rate=1001, duration=365).run(
            sender=delegator.address,
            amount=sp.tez(100),
            valid=False,
            exception="WrongCondition: self.data.rate >= params.rate")
        c.deposit(rate=1000, duration=364).run(
            sender=delegator.address,
            amount=sp.tez(100),
            valid=False,
            exception="WrongCondition: self.data.duration <= params.duration")
        c.deposit(rate=1000, duration=365).run(
            sender=delegator.address,
            amount=sp.tez(100),
            valid=False,
            exception="WrongCondition: ~ (self.data.ledger.contains(sp.sender))")

        sc.h2('uncollateralize')
        sc.h3('Failures')
        c.uncollateralize(amount=sp.tez(500), receiver=admin_receiver.address).run(
            sender=admin,
            valid=False,
            exception="insufficient collateral")
        c.uncollateralize(amount=sp.tez(490), receiver=admin_receiver.address).run(
            sender=notAdmin,
            valid=False,
            exception="WrongCondition: sp.sender == self.data.admin")
        sc.h3('Valid')
        c.uncollateralize(amount=sp.tez(490), receiver=admin_receiver.address).run(sender=admin)
        sc.verify(c.data.collateral == sp.tez(0))
        sc.verify(admin_receiver.balance == sp.tez(490))

        sc.h2('withdraw')
        sc.h3('Failures')
        c.withdraw(delegator.address).run(
            sender=delegator.address,
            amount=sp.mutez(1),
            now=sp.timestamp(365*24*3600),
            valid=False,
            exception="WrongCondition: sp.amount == sp.tez(0)")
        c.withdraw(delegator.address).run(
            sender=delegator.address,
            now=sp.timestamp(365*24*3600-1),
            valid=False,
            exception="WrongCondition: sp.now >= compute_baking_swap_118.value.due")
        sc.h3('Valid')
        c.withdraw(delegator.address).run(sender=delegator.address, now=sp.timestamp(365*24*3600))
        sc.verify(delegator.balance == sp.tez(110))
        sc.verify(~c.data.ledger.contains(delegator.address))
        sc.h3('Failures')
        c.withdraw(delegator.address).run(
            sender=delegator.address,
            valid=False,
            now=sp.timestamp(365*24*3600),
            exception="NoDeposit")

    @sp.add_test(name="Mutation", is_default=False)
    def test():
        s = sp.test_scenario()
        with s.mutation_test() as mt:
            mt.add_scenario("Full")