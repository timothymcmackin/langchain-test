import smartpy as sp

# This contract has nothing to do with inheritance in the Python sense.
# It's about transfers after a person's death.


class Inheritance(sp.Contract):
    """Inheritance contract

    An owner deposits a certain amount of coins into a contract and regularly
    calls the `default` entrypoint to prove that they are still alive.

    If the contract is not called since `alive_delta` seconds (1 years in
    this example), the heir can withdraw the tez by calling `withdraw`.

    At anytime the owner can deposit some tez by using the `default` entrypoint
    (or no entrypoint) or withdraw by calling `withdraw`.
    """

    def __init__(self, owner, heir, alive_delta, now):
        """
        Args:
            owner (address): Address that deposits and prove being alive.
            heir (address): Address that can withdraw if the owner hasn't proved
                being alive.
            alive_delta (int): Maximum number of seconds between two calls to `default`.
        """
        self.init(
            owner=owner,
            heir=heir,
            alive_delta=alive_delta,
            timeout=now.add_seconds(alive_delta),
        )

    @sp.entry_point
    def default(self):
        """Used by the owner to deposit coins and say that they are still alive.

        The `default` entrypoint is also called when doing a transfer without
        specifying an entrypoint. This is useful when using a simple wallet or
        an app without the ability to specify an entrypoint.

        Raises:
            `This entrypoint can only be called by the owner.`
        """
        sp.verify(
            sp.sender == self.data.owner,
            "This entrypoint can only be called by the owner.",
        )
        self.data.timeout = sp.now.add_seconds(self.data.alive_delta)

    @sp.entry_point
    def withdraw(self, receiver, amount):
        """Used by the owner or the heir to withdraw coins.

        The heir can only withdraw if the last call was made more than
        `alive_delta` seconds ago.

        Args:
            receiver (address): Receiver of the withdraw.
            amount (mutez): Amount withdrawn.
        Raises:
            `This entrypoint doesn't accept deposits.`
            `The owner is still considered alive, you cannot withdraw.`
            `Only owner or heir can withdraw.`
        """
        sp.verify(sp.amount == sp.tez(0), "This entrypoint doesn't accept deposits.")
        with sp.if_(sp.sender == self.data.heir):
            sp.verify(
                sp.now > self.data.timeout,
                message="The owner is still considered alive, you cannot withdraw.",
            )
        with sp.else_():
            sp.verify(sp.sender == self.data.owner, "Only owner or heir can withdraw.")
        sp.send(receiver, amount)


owner = sp.test_account("owner").address
heir = sp.test_account("heir").address
ALIVE_DELTA = 366 * 24 * 3600  # 1 leap year

if "templates" not in __name__:

    @sp.add_test(name="Inheritance basic scenario", is_default=True)
    def basic_scenario():
        """Test of:
        - origination.
        - deposit.
        - owner withdrawal.
        - alive confirmation.
        - heir withdrawal before timeout.
        """
        sc = sp.test_scenario()
        sc.h1("Basic scenario.")
        now = sp.timestamp(0)

        sc.h2("Origination.")
        c1 = Inheritance(owner=owner, heir=heir, alive_delta=ALIVE_DELTA, now=now)
        sc += c1

        sc.h2("Deposit.")
        c1.default().run(sender=owner, amount=sp.tez(1200), now=now)
        sc.verify(c1.balance == sp.tez(1200))
        sc.verify(c1.data.timeout == now.add_seconds(ALIVE_DELTA))

        sc.h2("Owner withdraw.")
        now = now.add_minutes(1)
        c1.withdraw(receiver=owner, amount=sp.tez(200)).run(sender=owner, now=now)

        sc.h2("Alive confirmation.")
        now = now.add_days(360)
        c1.default().run(sender=owner, now=now)

        sc.h2("Heir withdraw.")
        now = now.add_days(367)
        c1.withdraw(receiver=heir, amount=c1.balance).run(sender=heir, now=now)

    @sp.add_test(name="Inheritance errors test", is_default=False)
    def errors_test():
        """Test of:
        - `default`: non-owner calling.
        - `withdraw`: not allowed calling.
        - `withdraw`: sending tez.
        - `withdraw`: heir withdraw before timeout.
        """
        sc = sp.test_scenario()
        sc.h1("Errors tests.")
        now = sp.timestamp(0)

        sc.h2("Origination.")
        c1 = Inheritance(owner=owner, heir=heir, alive_delta=ALIVE_DELTA, now=now)
        sc += c1

        sc.h2("Default: non-owner calling.")
        NOT_ALLOWED = sp.test_account("not_allowed").address
        c1.default().run(
            sender=NOT_ALLOWED,
            now=now,
            valid=False,
            exception="This entrypoint can only be called by the owner.",
        )

        sc.h2("Withdraw: not allowed calling.")
        c1.withdraw(receiver=NOT_ALLOWED, amount=c1.balance).run(
            sender=NOT_ALLOWED,
            valid=False,
            exception="Only owner or heir can withdraw.",
        )

        sc.h2("Withdraw: sending tez.")
        c1.withdraw(receiver=owner, amount=c1.balance).run(
            sender=owner,
            amount=sp.tez(100),
            valid=False,
            exception="This entrypoint doesn't accept deposits.",
        )

        sc.h2("Withdraw: heir withdraw before timeout.")
        now = now.add_minutes(5)
        c1.withdraw(receiver=heir, amount=c1.balance).run(
            sender=heir,
            now=now,
            valid=False,
            exception="The owner is still considered alive, you cannot withdraw.",
        )
