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

    @sp.add_test(name="Settled game Challenge")
    def test():
        sc = sp.test_scenario()
        sc.table_of_contents()
        sc.h1("Settled game Challenge")
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
        channelParams = sp.record(players = players, nonce = "Channel 1", withdraw_delay = 3600*24)
        channel_id = sp.blake2b(sp.pack((c1.address, channelParams.players, channelParams.nonce)))
        c1.new_channel(channelParams)

        sc.h2("Player 1 and 2 push {0: 10}")
        ledger.mint(token_id = 0, amount = 10, address = player1.address).run(sender = player1, amount = sp.mutez(10))
        ledger.push_bonds(platform = c1.address, channel_id = channel_id, player_addr = player1.address, bonds = {0: 10}).run(sender = player1)

        sc.h2("P1 Instanciate new game : Transfer")
        settlements, bonds = h.transfer_settlements(p1_to_p2 = {0:100})
        settlements = sc.compute(settlements)
        constants = sc.compute(sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                                game_nonce = "game", play_delay = play_delay, bonds = bonds, settlements = settlements))
        game_id = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)

        sc.h3("Player 1 proposes an abort outcome for game_id running transfer and Player 2 accepts")
        proposed_outcome = gp.action_new_outcome(game_id, gp.abort, sp.timestamp(3600 * 24))
        outcome_sigs = h.make_signatures(player1, player2, proposed_outcome)
        c1.game_set_outcome(game_id = game_id, outcome = gp.abort, timeout = sp.timestamp(3600 * 24), signatures = outcome_sigs).run(sender = player1)
        c1.game_settle(game_id).run(sender = player1)

        sc.h2("Player 2 tries to challenge with a settled game")
        sc.h3("Player 1 request withdraw 5 tokens")
        c1.withdraw_request(channel_id = channel_id, tokens = sp.map({0: 5})).run(sender = player1)
        sc.h3("Player 2 fails to push settled game id as a challenge")
        c1.withdraw_challenge(channel_id = channel_id, withdrawer = player1.address, game_ids = sp.set([game_id])).run(
            sender = player2, valid = False, exception = "Platform_GameSettled")

    @sp.add_test(name="Expected errors")
    def test():
        sc = sp.test_scenario()
        sc.table_of_contents()
        sc.h1("Expected transfer errors")
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
        channelParams = sp.record(players = players, nonce = "Channel 1", withdraw_delay = 3600*24)
        channel_id = sp.blake2b(sp.pack((c1.address, channelParams.players, channelParams.nonce)))
        c1.new_channel(channelParams)

        sc.h3("P1 Instanciate new game : Transfer")
        settlements, bonds = h.transfer_settlements(p1_to_p2 = {0:10})
        settlements = sc.compute(settlements)
        constants = sc.compute(sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                                game_nonce = "game1", play_delay = play_delay, bonds = bonds, settlements = settlements))
        game_id = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)

        sc.h3("Player 1 plays")
        c1.game_play(play_transfer(game_id)).run(sender = player1)

        sc.h2("(fail) Settle: Don't own token")
        error_message = sp.pair("Platform_NotEnoughToken:", sp.record(sender = player1.address, token = 0, amount = 10))
        sp.set_type_expr(error_message, sp.TPair(sp.TString, sp.TRecord(sender = sp.TAddress, token = sp.TNat, amount = sp.TNat)))
        c1.game_settle(game_id).run(sender = player1, valid = False, exception = error_message)

        sc.h2("Push 5 tokens 0")
        ledger.mint(token_id = 0, amount = 5, address = player1.address).run(sender = player1, amount = sp.mutez(5))
        ledger.push_bonds(platform = c1.address, channel_id = channel_id, player_addr = player1.address, bonds = {0: 5}).run(sender = player1)

        sc.h2("fail) Settle: No enough tokens")
        error_message = sp.pair("Platform_NotEnoughToken:", sp.record(sender = player1.address, token = 0, amount = 10))
        sp.set_type_expr(error_message, sp.TPair(sp.TString, sp.TRecord(sender = sp.TAddress, token = sp.TNat, amount = sp.TNat, bond = gp.types.t_token_map)))
        c1.game_settle(game_id).run(sender = player1, valid = False, exception = error_message)

        sc.h2("Not enought tez for bonds")
        ledger.mint(token_id = 0, amount = 5, address = player1.address).run(sender = player1, amount = sp.mutez(0),
            valid = False, exception = sp.pair("FA2_WRONG_AMOUNT_expected", sp.utils.nat_to_mutez(5))
        )

        sc.h2("Too much tez for bonds")
        ledger.mint(token_id = 0, amount = 5, address = player1.address).run(sender = player1, amount = sp.mutez(20),
            valid = False, exception = sp.pair("FA2_WRONG_AMOUNT_expected", sp.utils.nat_to_mutez(5))
        )

        sc.h2("Trying to mint not configured token")
        ledger.mint(token_id = 404, amount = 5, address = player1.address).run(sender = player1, amount = sp.mutez(20),
            valid = False, exception = sp.pair("Ledger_token_unpermitted", 404)
        )

        sc.h2("Trying to push bonds for not configured token")
        ledger.push_bonds(platform = c1.address, channel_id = channel_id, player_addr = player1.address, bonds = {404: 5}).run(
            sender = player1, amount = sp.mutez(0), valid = False, exception = sp.pair("Ledger_token_unpermitted", 404)
        )

    @sp.add_test(name="Settlements verification")
    def test():
        sc = sp.test_scenario()
        sc.table_of_contents()
        sc.h1("Settlements verification")
        sc.h2("Contract")
        sc.h3("GamePlatform")
        ledger_address = sp.address("KT1_LEDGER_ADDRESS")
        c1 = gp.GamePlatform(sp.set([admin.address]), ledger_address)
        sc += c1

        sc.h2("New model: Transfer")
        model = sc.compute(model_wrap.model_wrap(transfer))
        model_id = sc.compute(model_wrap.model_id(model))
        c1.admin_new_model(model).run(sender = admin)

        sc.h2("New channel")
        channelParams = sp.record(players = players, nonce = "Channel 1", withdraw_delay = 3600*24)
        channel_id = sp.blake2b(sp.pack((c1.address, channelParams.players, channelParams.nonce)))
        c1.new_channel(channelParams)

        sc.h3("Missing game_finished: transferd in settlements")
        settlements = sp.map({
            sp.variant("player_double_played", 1)     : [],
            sp.variant("player_double_played", 2)     : [],
            sp.variant("player_inactive",      1)     : [],
            sp.variant("player_inactive",      2)     : [],
            sp.variant("game_aborted", sp.unit)       : []
        })
        bonds = {}
        settlements = sc.compute(settlements)
        constants = sc.compute(sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                                game_nonce = "game1", play_delay = play_delay, bonds = bonds, settlements = settlements))
        game_id = sc.compute(gp.compute_game_id(constants))
        c1.new_game(
            constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)
        ).run(sender = player1, valid = False, exception = sp.pair("Platform_MissingSettlement", sp.variant("game_finished", "transferred")))

        sc.h3("Missing game_aborted in settlements")
        settlements = sp.map({
            sp.variant("player_double_played", 1)     : [],
            sp.variant("player_double_played", 2)     : [],
            sp.variant("player_inactive",      1)     : [],
            sp.variant("player_inactive",      2)     : [],
            sp.variant("game_finished", "transferred"): [],
        })

        settlements = sc.compute(settlements)
        constants = sc.compute(sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                                game_nonce = "game1", play_delay = play_delay, bonds = bonds, settlements = settlements))
        game_id = sc.compute(gp.compute_game_id(constants))
        c1.new_game(
            constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)
        ).run(sender = player1, valid = False, exception = sp.pair("Platform_MissingSettlement", sp.variant("game_aborted", sp.unit)))
