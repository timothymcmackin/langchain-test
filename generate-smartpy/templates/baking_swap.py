import smartpy as sp


class BakingSwap(sp.Contract):
    """A contract that takes tez deposits and pays interest.

    The deposited funds cannot leave the contract, but the administrator can
    delegate them for baking.

    In more detail:

    - The administrator funds the contract with collateral.

    - The administrator publishes an offer: a rate (in basis points) and a
    duration (in days).

    - For each deposit the amount to be paid out and the due date are recorded.
    The corresponding amount of collateral is locked up.

    - At maturity the deposit plus interest can be withdrawn.
    """

    def __init__(self, admin, initialRate, initialDuration):
        """Constructor

        Args:
            admin (sp.TAddress): admin of the contract.
            initialRate (sp.TNat): Basis points to compute the interest.
            initialDuration (sp.TNat): Number of days before a deposit can be
                withdrawn.
        """
        self.init(
            admin=admin,
            collateral=sp.mutez(0),
            ledger={},
            rate=initialRate,
            duration=initialDuration,
        )

    # Admin-only entrypoints

    @sp.entry_point
    def delegate(self, public_key_hash):
        """Admin-only. Delegate the contract's balance to the admin.

        Args:
            public_key_hash (sp.TKeyHash): public key hash of the admin.
        """
        sp.verify(sp.sender == self.data.admin)
        sp.verify(sp.amount == sp.mutez(0))
        sp.verify(sp.sender == sp.to_address(sp.implicit_account(public_key_hash)))
        sp.set_delegate(sp.some(public_key_hash))

    @sp.entry_point
    def collateralize(self):
        """Admin-only. Provide tez as collateral for interest to be paid."""
        sp.verify(sp.sender == self.data.admin)
        self.data.collateral += sp.amount

    @sp.entry_point
    def uncollateralize(self, amount, receiver):
        """Admin-only. Withdraw collateral.

        Transfer `amount` mutez to admin if it doesn't exceed collateral.

        Args:

            amount (sp.TMutez): Amount to be removed from the collateral.
        """
        sp.verify(sp.sender == self.data.admin)
        # Explicitly fails for insufficient collateral.
        sp.verify(amount <= self.data.collateral, "insufficient collateral")
        self.data.collateral -= amount
        sp.send(receiver, amount)

    @sp.entry_point
    def set_offer(self, rate, duration):
        """Admin-only. Set the current offer: interest rate (in basis points)
        and duration.

        Args:
            rate (sp.TNat): Basis points to compute the interest.
            duration (sp.TNat): Number of days before a deposit can be withdrawn.
        """
        sp.verify(sp.sender == self.data.admin)
        sp.verify(sp.amount == sp.mutez(0))
        self.data.rate = rate
        self.data.duration = duration

    # Permissionless entrypoints

    @sp.entry_point
    def deposit(self, rate, duration):
        """Deposit tez. The current offer has to be repeated in the parameters.

        Args:
            rate (sp.TNat): Basis points to compute the interest.
            duration (sp.TNat): Number of days before a deposit can be withdrawn.
        """
        sp.verify(self.data.rate >= rate)
        sp.verify(self.data.duration <= duration)
        sp.verify(~self.data.ledger.contains(sp.sender))

        # Compute interest to be paid.
        interest = sp.compute(sp.split_tokens(sp.amount, self.data.rate, 10_000))
        self.data.collateral -= interest

        # Record the payment to be made.
        self.data.ledger[sp.sender] = sp.record(
            amount=sp.amount + interest,
            due=sp.now.add_days(self.data.duration),
        )

    @sp.entry_point
    def withdraw(self, receiver):
        """Withdraw tez at maturity."""
        sp.verify(sp.amount == sp.mutez(0))
        entry = sp.compute(self.data.ledger.get(sp.sender, message="NoDeposit"))
        sp.verify(sp.now >= entry.due)
        sp.send(receiver, entry.amount)
        del self.data.ledger[sp.sender]


if "templates" not in __name__:
    admin = sp.test_account("Admin")
    voting_powers = {
        admin.public_key_hash: 0,
    }

    @sp.add_test(name="Baking")
    def test():
        scenario = sp.test_scenario()
        scenario.h1("Baking Swap")
        c = BakingSwap(admin.address, 700, 365)
        scenario += c

        c.delegate(admin.public_key_hash).run(sender=admin, voting_powers=voting_powers)

sp.add_compilation_target(
    "bakingSwap", BakingSwap(sp.test_account("admin").address, 700, 365)
)
