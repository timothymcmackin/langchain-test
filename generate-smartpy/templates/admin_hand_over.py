import smartpy as sp


class AdminHandOver(sp.Contract):
    """This contract implements a mechanism to switch administrator (an address
    that with special permission) in a way that prevents the administrator from
    handing over to an address with a typo or a contract without an interaction
    code.

    The problem: An administrator hands the contract over to a new administrator
    and then discovers that they made a typing error in the address.
    In this case, the contract can no longer be administered.

    The solution: The administrator hand over is a two step process:
    1. the current administrator adds a candidate admin.
    2. the new administrator removes the old one.
    """

    def __init__(self, admins):
        """
        Args:
            admins (sp.TSet of sp.TAddress): The contract's administrators.
        """
        self.init(admins=admins)

    @sp.entry_point
    def add_admins(self, admins):
        """Add new administrators.

        Args:
            admins (sp.TList of sp.TAddress): The new admins.
        Raises:
            `Only an admin can call this entrypoint.`
        """
        sp.verify(
            self.data.admins.contains(sp.sender),
            message="Only an admin can call this entrypoint.",
        )
        with sp.for_("admin", admins) as admin:
            self.data.admins.add(admin)

    @sp.entry_point
    def remove_admins(self, admins):
        """Remove administrators.

        An admin cannot remove themselves.

        Args:
            admins (sp.TList of sp.TAddress): The admins to remove.
        Raises:
            `Only an admin can call this entrypoint.`
            `An admin cannot remove themselves.`
        """
        sp.verify(
            self.data.admins.contains(sp.sender),
            message="Only an admin can call this entrypoint.",
        )
        with sp.for_("admin", admins) as admin:
            sp.verify(admin != sp.sender, "An admin cannot remove themselves.")
            self.data.admins.remove(admin)

    @sp.entry_point
    def protected(self):
        """Example of entrypoint reserved to administrators.

        Raises:
            `Only an admin can call this entrypoint.`
        """
        sp.verify(
            self.data.admins.contains(sp.sender),
            message="Only an admin can call this entrypoint.",
        )


# This prevent tests from being executed on importation.
if "templates" not in __name__:

    first_admin = sp.test_account("first_admin")
    new_admin = sp.test_account("new_admin")

    @sp.add_test(name="Admin hand over basic scenario", is_default=True)
    def basic_scenario():
        """Test:
        - Origination
        - An admin adds a new admin.
        - The new admin removes the older admin.
        - The new admin calls the protected entrypoint.
        """
        sc = sp.test_scenario()
        sc.h1("Basic scenario.")

        sc.h2("Origination.")
        c1 = AdminHandOver(admins=sp.set([first_admin.address]))
        sc += c1

        sc.h2("An admin adds a new admin.")
        c1.add_admins([new_admin.address]).run(sender=first_admin)

        sc.h2("The new admin removes the older admin.")
        c1.remove_admins([first_admin.address]).run(sender=new_admin)

        sc.h2("The new admin calls the protected entrypoint")
        c1.protected().run(sender=new_admin)
