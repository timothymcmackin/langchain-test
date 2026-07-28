import smartpy as sp

AdminHandOver = sp.io.import_template("admin_hand_over.py").AdminHandOver

if "templates" not in __name__:
    non_admin = sp.test_account("non_admin")
    first_admin = sp.test_account("first_admin")
    new_admin = sp.test_account("new_admin")

    @sp.add_test(name="Full", is_default=True)
    def test():
        sc = sp.test_scenario()
        sc.h1("Full test")
        sc.table_of_contents()
        sc.h2("Origination")
        c1 = AdminHandOver(admins=sp.set([first_admin.address]))
        sc += c1

        sc.h2("add_admins")
        sc.h3("(Failure) Non admin fails to a new admin.")
        c1.add_admins([new_admin.address]).run(
            sender=non_admin,
            valid=False,
            exception="Only an admin can call this entrypoint.",
        )
        sc.h3("An admin adds a new admin.")
        c1.add_admins([new_admin.address]).run(sender=first_admin)

        sc.h2("remove_admins")
        sc.h3("(Failure) Non admin fails to remove the older admin.")
        c1.remove_admins([first_admin.address]).run(
            sender=non_admin,
            valid=False,
            exception="Only an admin can call this entrypoint.",
        )
        sc.h3("(Failure) Admin tries to remove themselves.")
        c1.remove_admins([first_admin.address]).run(
            sender=first_admin,
            valid=False,
            exception="An admin cannot remove themselves.",
        )
        sc.h3("The new admin removes the older admin.")
        c1.remove_admins([first_admin.address]).run(sender=new_admin)
        sc.verify(~c1.data.admins.contains(first_admin.address))

        sc.h2("protected")
        sc.h3("The new admin calls the protected entrypoint")
        c1.protected().run(sender=new_admin)
        sc.h3("(Failure) Non admin calls the protected entrypoint")
        c1.protected().run(
            sender=non_admin,
            valid=False,
            exception="Only an admin can call this entrypoint.",
        )

    @sp.add_test(name="Mutation", is_default=False)
    def test():
        s = sp.test_scenario()
        with s.mutation_test() as mt:
            mt.add_scenario("Full")
