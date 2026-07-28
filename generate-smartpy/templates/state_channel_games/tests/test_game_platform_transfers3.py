import smartpy as sp

h          = sp.io.import_template("state_channel_games/tests/test_game_platform_transfers_helpers.py")
gp         = sp.io.import_template("state_channel_games/game_platform.py")
lgr        = sp.io.import_template("state_channel_games/ledger.py")
Transfer   = sp.io.import_template("state_channel_games/models/transfer.py")
model_wrap = sp.io.import_template("state_channel_games/model_wrap.py")
types      = sp.io.import_template("state_channel_games/types.py").Types()
FA2        = sp.io.import_template("FA2.py")

if "templates" not in __name__:
    admin = sp.test_account('admin')
    player1 = sp.test_account('player1')
    player2 = sp.test_account('player2')
    players = {player1.address: player1.public_key, player2.address: player2.public_key}

    transfer = Transfer.Transfer()
    play_delay = 3600 * 24

    # Ledger
    ledger_admin = sp.test_account('ledger_admin')
    ledger_config = FA2.FA2_config(single_asset = False)
    ledger_metadata = sp.utils.metadata_of_url("https://example.com")

    def new_game_sigs(constants, params = sp.unit):
        new_game = gp.action_new_game(constants, sp.pack(params))
        return h.make_signatures(player1, player2, new_game)

    def play_transfer(game_id):
        new_current = sp.record(move_nb = 1, player = 2, outcome = sp.some(sp.variant("final", sp.variant("game_finished", "transferred"))))
        signatures = h.make_signatures(player1, player2, gp.action_play(game_id, new_current, sp.pack(sp.unit), sp.pack(sp.unit)))
        return sp.record(game_id = game_id, new_current = new_current, new_state = sp.pack(sp.unit), move_data = sp.pack(sp.unit), signatures = signatures)

    @sp.add_test(name="Platform transfers tokens")
    def test():
        sc = sp.test_scenario()
        sc.table_of_contents()
        sc.h1("Transfers")
        sc.h2("Contracts")
        sc.h3("Ledger")
        ledger = lgr.Ledger(ledger_config, admin = ledger_admin.address, metadata = ledger_metadata)
        sc += ledger
        sc.h3("GamePlatform")
        c1 = gp.GamePlatform(sp.set([admin.address]), ledger.address)
        sc += c1

        sc.h2("Ledger: XTZ configuration")
        ledger.set_token_info(token_id = 0, token_info = h.wXTZ_metadata).run(sender = ledger_admin)
        ledger.update_token_permissions(token_id = 0, token_permissions = h.wXTZ_permissions).run(sender = ledger_admin)

        sc.h2("New model: Transfer")
        model = sc.compute(model_wrap.model_wrap(transfer))
        model_id = sc.compute(model_wrap.model_id(model))
        c1.admin_new_model(model).run(sender = admin)

        sc.h2("New channel")
        channelParams = sp.record(players = players, nonce = "Channel 1", withdraw_delay = 3600 * 24)
        channel_id = sp.blake2b(sp.pack((c1.address, channelParams.players, channelParams.nonce)))
        c1.new_channel(channelParams)

        sc.h2("New token: Reputation")
        reputation_permissions = lgr.build_token_permissions({
            "type"            : "NATIVE",
            "mint_cost"       : sp.mutez(0),
            "mint_permissions": sp.variant("allow_only", sp.set([c1.address]))
        })
        ledger.set_token_info(token_id = 42, token_info = h.reputation_metadata).run(sender = ledger_admin)
        ledger.update_token_permissions(token_id = 42, token_permissions = reputation_permissions).run(sender = ledger_admin)

        sc.h2("Simple transfer")
        game_num = 1
        sc.h3("Platform will mint 10 tokens 0 to Player 2")
        settlements, bonds = h.transfer_settlements(p0_to_p2 = {42:10})
        settlements = sc.compute(settlements)
        sc.show(settlements)

        sc.h3("P1 Instanciate new game : Transfer")
        constants = sc.compute(sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                              game_nonce = "game"+str(game_num), play_delay = play_delay, bonds = bonds, settlements = settlements))
        game_id = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)

        sc.h3("Admin allows reputation transfer in game permissions")
        c1.admin_game_permissions(game_id = game_id, key = "allowed_mint", permission = sp.some(sp.pack(sp.map(l = {sp.nat(42): sp.nat(10)})))).run(sender = admin)

        sc.h3("Play transfer")
        c1.game_play(play_transfer(game_id)).run(sender = player1)
        sc.verify(gp.finished_outcome(c1, game_id) == "transferred")

        sc.h3("Settle game")
        sc.verify(~gp.player_bonds(c1, channel_id, player2.address).contains(42))
        c1.game_settle(game_id).run(sender = player1)
        sc.verify( gp.player_bonds(c1, channel_id, player2.address)[42] == 10)
        sc.p("P2 received 10 tokens 0")

        sc.h2("Admin allow transfer model to mint Reputation token")
        c1.admin_model_permissions(model_id = model_id, key = "allowed_mint", permission = sp.some(sp.pack(sp.map(l = {sp.nat(42): sp.nat(15)})))).run(sender = admin)

        game_num += 1
        sc.h2("Simple transfer that mint Reputation token")
        constants = sc.compute(sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                                         game_nonce = "game"+str(game_num), play_delay = play_delay, bonds = bonds, settlements = settlements))
        game_id = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)

        sc.h3("Play transfer")
        c1.game_play(play_transfer(game_id)).run(sender = player1)
        sc.verify(gp.finished_outcome(c1, game_id) == "transferred")

        sc.h3("Settle game")
        sc.verify(gp.player_bonds(c1, channel_id, player2.address)[42] == 10)
        sc.verify(sp.unpack(c1.data.model_permissions[model_id]["allowed_mint"], sp.TMap(sp.TNat, sp.TNat)).open_some()[42] == 15)
        c1.game_settle(game_id).run(sender = player1)
        sc.verify(gp.player_bonds(c1, channel_id, player2.address)[42] == 20)
        sc.verify(sp.unpack(c1.data.model_permissions[model_id]["allowed_mint"], sp.TMap(sp.TNat, sp.TNat)).open_some()[42] == 5)
        sc.p("P2 received 10 tokens 0")

        game_num += 1
        sc.h2("Simple transfer that mint Reputation token")
        constants = sc.compute(sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                                         game_nonce = "game"+str(game_num), play_delay = play_delay, bonds = bonds, settlements = settlements))
        game_id = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)

        sc.h3("Play transfer")
        c1.game_play(play_transfer(game_id)).run(sender = player1)
        sc.verify(gp.finished_outcome(c1, game_id) == "transferred")

        sc.h3("Settle game cannot be completed because the model is not allowed to mint more")
        c1.game_settle(game_id).run(sender = player1, valid = False)

        sc.h3("Admin allows enough reputation transfer in game permissions")
        c1.admin_game_permissions(game_id = game_id, key = "allowed_mint", permission = sp.some(sp.pack(sp.map(l = {sp.nat(42): sp.nat(6)})))).run(sender = admin)
        sc.h3("Settle game")
        sc.verify(gp.player_bonds(c1, channel_id, player2.address)[42] == 20)
        sc.verify(sp.unpack(c1.data.model_permissions[model_id]["allowed_mint"], sp.TMap(sp.TNat, sp.TNat)).open_some()[42] == 5)
        c1.game_settle(game_id).run(sender = player1)
        sc.verify(gp.player_bonds(c1, channel_id, player2.address)[42] == 30)
        sc.verify(sp.unpack(c1.data.model_permissions[model_id]["allowed_mint"], sp.TMap(sp.TNat, sp.TNat)).open_some()[42] == 1)
        sc.p("P2 received 10 tokens 42")

    @sp.add_test(name="Rewards")
    def test():
        sc = sp.test_scenario()
        sc.table_of_contents()
        sc.h1("Rewards")
        sc.h2("Contracts")
        sc.h3("Ledger")
        ledger = lgr.Ledger(ledger_config, admin = ledger_admin.address, metadata = ledger_metadata)
        sc += ledger
        sc.h3("GamePlatform")
        c1 = gp.GamePlatform(sp.set([admin.address]), ledger.address)
        sc += c1

        sc.h2("Ledger: XTZ configuration")
        ledger.set_token_info(token_id = 0, token_info = h.wXTZ_metadata).run(sender = ledger_admin)
        ledger.update_token_permissions(token_id = 0, token_permissions = h.wXTZ_permissions).run(sender = ledger_admin)

        sc.h2("Ledger: Reputation configuration")
        reputation_permissions = lgr.build_token_permissions({
            "type"            : "NATIVE",
            "mint_cost"       : sp.mutez(0),
            "mint_permissions": sp.variant("allow_only", sp.set([ledger_admin.address]))
        })
        ledger.set_token_info(token_id = 42, token_info = h.reputation_metadata).run(sender = ledger_admin)
        ledger.update_token_permissions(token_id = 42, token_permissions = reputation_permissions).run(sender = ledger_admin)

        sc.h2("Ledger: Mint 1 million reputation tokens for platform")
        ledger.mint(token_id = 42, amount = 1_000_000, address = c1.address).run(sender = ledger_admin)

        sc.h2("New model: Transfer (gives 1000 reputation token to player1)")
        model_rewards = [sp.record(token_id = 42, amount = 1000, to_ = player1.address)]
        model = sc.compute(model_wrap.model_wrap(transfer, rewards = model_rewards))
        model_id = sc.compute(model_wrap.model_id(model))
        c1.admin_new_model(model).run(sender = admin)

        sc.h2("New channel")
        channelParams = sp.record(players = players, nonce = "Channel 1", withdraw_delay = 3600 * 24)
        channel_id = sp.blake2b(sp.pack((c1.address, channelParams.players, channelParams.nonce)))
        c1.new_channel(channelParams)

        sc.h2("Simple transfer")
        game_num = 1
        sc.h3("Transfer of nothing")
        settlements, bonds = h.transfer_settlements()
        settlements = sc.compute(settlements)
        sc.show(settlements)

        sc.h3("P1 Instanciate new game : Transfer")
        constants = sc.compute(sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                              game_nonce = "game"+str(game_num), play_delay = play_delay, bonds = bonds, settlements = settlements))
        game_id = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)
        sc.verify(lgr.fa2_balance(player1.address, ledger, token_id = 42) == 1000)

    @sp.add_test(name="Platform tokens transfers errors")
    def test():
        sc = sp.test_scenario()
        sc.table_of_contents()
        sc.h1("Transfers")
        sc.h2("Contracts")
        sc.h3("Ledger")
        ledger = lgr.Ledger(ledger_config, admin = ledger_admin.address, metadata = ledger_metadata)
        sc += ledger
        sc.h3("GamePlatform")
        c1 = gp.GamePlatform(sp.set([admin.address]), ledger.address)
        sc += c1

        sc.h2("Ledger: XTZ configuration")
        ledger.set_token_info(token_id = 0, token_info = h.wXTZ_metadata).run(sender = ledger_admin)
        ledger.update_token_permissions(token_id = 0, token_permissions = h.wXTZ_permissions).run(sender = ledger_admin)

        sc.h2("New model: Transfer")
        model = sc.compute(model_wrap.model_wrap(transfer))
        model_id = sc.compute(model_wrap.model_id(model))
        c1.admin_new_model(model).run(sender = admin)

        sc.h2("New channel")
        channelParams = sp.record(players = players, nonce = "Channel 1", withdraw_delay = 3600 * 24)
        channel_id = sp.blake2b(sp.pack((c1.address, channelParams.players, channelParams.nonce)))
        c1.new_channel(channelParams)

        sc.h2("Simple transfer")
        sc.h3("Platform will mint 10 tokens 42 to Player 2")
        settlements, bonds = h.transfer_settlements(p0_to_p2 = {42:10})
        settlements = sc.compute(settlements)
        sc.show(settlements)

        sc.h3("P1 Instanciate new game : Transfer")
        constants = sc.compute(sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                              game_nonce = "game1", play_delay = play_delay, bonds = bonds, settlements = settlements))
        game_id = sc.compute(gp.compute_game_id(constants))
        sc.show(game_id)
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)

        sc.h3("(Onchain) play transfer")
        c1.game_play(play_transfer(game_id)).run(sender = player1)
        sc.verify(gp.finished_outcome(c1, game_id) == "transferred")

        sc.h3("Game transfer allowance not configured")
        c1.game_settle(game_id).run(
            sender = player1, valid = False,
            exception =  sp.pair('Platform_NotAllowedMinting', sp.record(amount = 10, game_id = game_id, token = 42))
        )

        sc.h3("Game transfer allowance not configured")
        c1.game_settle(game_id).run(
            sender = player1, valid = False,
            exception = sp.pair("Platform_NotAllowedMinting", sp.record(game_id = game_id, token = 42, amount = 10))
        )

        sc.h3("(Onchain) admin allows reputation transfer in metadata")
        c1.admin_game_permissions(game_id = game_id, key = "allowed_mint", permission = sp.some(sp.pack(sp.map(l = {sp.nat(42): sp.nat(5)})))).run(sender = admin)

        sc.h3("Game transfer allowance is not enough")
        c1.game_settle(game_id).run(
            sender = player1, valid = False,
            exception = sp.pair("Platform_NotAllowedMinting", sp.record(game_id = game_id, token = 42, amount = 10))
        )

        sc.h3("(Onchain) admin set allowed reputation transfer to 10")
        c1.admin_game_permissions(game_id = game_id, key = "allowed_mint", permission = sp.some(sp.pack(sp.map(l = {sp.nat(42): sp.nat(10)})))).run(sender = admin)

        sc.h2("New token: Reputation")
        reputation_permissions = lgr.build_token_permissions({
            "type"            : "NATIVE",
            "mint_cost"       : sp.mutez(0),
            "mint_permissions": sp.variant("allow_only", sp.set([c1.address]))
        })
        ledger.set_token_info(token_id = 42, token_info = h.reputation_metadata).run(sender = ledger_admin)
        ledger.update_token_permissions(token_id = 42, token_permissions = reputation_permissions).run(sender = ledger_admin)

        sc.h3("Valid transfer")
        c1.game_settle(game_id).run(sender = player1)
