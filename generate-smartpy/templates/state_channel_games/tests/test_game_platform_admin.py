import smartpy as sp

gp           = sp.io.import_template("state_channel_games/game_platform.py")
FA2          = sp.io.import_template("FA2.py")
types        = sp.io.import_template("state_channel_games/types.py").Types()

if "templates" not in __name__:
    admin1 = sp.test_account('admin1')
    admin2 = sp.test_account('admin2')
    ledger = sp.test_account('ledger')
    notAdmin = sp.test_account('notAdmin')

    @sp.add_test(name="GamePlatform Change Admin")
    def test():
        sc = sp.test_scenario()

        sc.table_of_contents()
        sc.h1("Change Admin")
        sc.h2("Contract")
        c1 = gp.GamePlatform(sp.set([admin1.address]), ledger.address)
        sc += c1

        def f(self, params):
            sp.set_type(params, types.t_callback)
            sp.send(admin1.address, sp.tez(10))
        ep_update = sp.utils.wrap_entry_point("on_received_bonds", f)

        # Not admin trying to call admin entrypoints

        sc.h2("Not admin admin entrypoints")
        c1.admin_new_model(model = sp.bytes("0x00"), metadata = {}, permissions = {}, rewards = []).run(sender = admin2, valid = False, exception = "Platform_NotAdmin")
        c1.admin_setup(ledger = sp.none, add_admins = sp.list([admin2.address]), remove_admins = sp.set()).run(sender = admin2, valid = False, exception = "Platform_NotAdmin")
        c1.admin_game_permissions(game_id = sp.bytes("0x00"), key = "", permission = sp.some(sp.bytes("0x00"))).run(sender = admin2, valid = False, exception = "Platform_NotAdmin")
        c1.admin_model_metadata(model_id = sp.bytes("0x00"), key = "", metadata = sp.some(sp.bytes("0x00"))).run(sender = admin2, valid = False, exception = "Platform_NotAdmin")
        c1.admin_model_permissions(model_id = sp.bytes("0x00"), key = "", permission = sp.some(sp.bytes("0x00"))).run(sender = admin2, valid = False, exception = "Platform_NotAdmin")
        c1.admin_global_metadata(key = "", metadata = sp.some(sp.bytes("0x00"))).run(sender = admin2, valid = False, exception = "Platform_NotAdmin")
        t_operator_param = sp.TRecord(owner = sp.TAddress, operator = sp.TAddress, token_id = sp.TNat).layout(("owner", ("operator", "token_id")))
        c1.admin_update_operators(fa2 = ledger.address, operators = [
            sp.variant("add_operator", sp.set_type_expr(sp.record(owner = c1.address, operator = ledger.address, token_id = 0,), t_operator_param))
        ]).run(sender = notAdmin, valid = False, exception = "Platform_NotAdmin")
        # c1.admin_update_entrypoints(sp.variant("on_received_bonds", ep_update)).run(sender = admin2, valid = False, exception = "Platform_NotAdmin")

        # # Update entrypoints

        # sc.h2("Update entrypoints")
        # sc.h3("on_received_bonds")
        # sc.verify_equal(c1.balance, sp.tez(0))
        # sc.p("We send 10 tez with the update_entrypoints call")
        # c1.admin_update_entrypoints(sp.variant("on_received_bonds", ep_update)).run(sender = admin1, amount = sp.tez(10))
        # sc.p("We call the entrypoints that we modified to send back 10 tez")
        # c1.on_received_bonds(
        #     sp.record(
        #         amount   = 0,
        #         data = sp.pack(sp.record(channel_id = sp.bytes("0x00"), player_addr = admin1.address)),
        #         receiver = admin1.address,
        #         sender = admin1.address,
        #         token_id = 0
        #     )
        # ).run(sender = ledger.address)
        # sc.p("We verify that the contract balance is back to 0")
        # sc.verify_equal(c1.balance, sp.tez(0))

        # # Verify if all expected entrypoints are lazify
        # sc.verify(c1.on_received_bonds.lazify)
        # sc.verify(c1.withdraw_challenge.lazify)
        # sc.verify(c1.withdraw_finalize.lazify)
        # sc.verify(c1.admin_update_operators.lazify)
        # sc.verify(c1.game_settle.lazify)

        # Setup entrypoint

        sc.h2("Add new admin")
        c1.admin_setup(ledger = sp.none, add_admins = sp.list([admin2.address]), remove_admins = sp.set()).run(sender = admin1)
        sc.verify_equal(c1.data.admins, sp.set([admin1.address, admin2.address]))

        sc.h2("Admin trying to remove itself")
        c1.admin_setup(ledger = sp.none, add_admins = [], remove_admins = sp.set([admin1.address])).run(sender = admin1, valid = False, exception = "Platform_CannotRemoveSelf")

        sc.h2("Remove old admin")
        c1.admin_setup(ledger = sp.none, add_admins = [], remove_admins = sp.set([admin1.address])).run(sender = admin2)
        sc.verify_equal(c1.data.admins, sp.set([admin2.address]))
