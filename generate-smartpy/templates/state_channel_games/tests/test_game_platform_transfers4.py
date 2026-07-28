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

    @sp.add_test(name="FA2 tokens")
    def test():
        sc = sp.test_scenario()
        sc.table_of_contents()
        FA2_admin = sp.test_account("FA2_admin")
        sc.h1("Transfers")
        sc.h2("Contracts")
        sc.h3("Ledger")
        ledger = lgr.Ledger(ledger_config, admin = ledger_admin.address, metadata = ledger_metadata)
        sc += ledger
        sc.h3("GamePlatform")
        c1 = gp.GamePlatform(sp.set([admin.address]), ledger.address)
        sc += c1
        sc.h3("FA2")
        dummyToken = h.DummyFA2(
            FA2.FA2_config(single_asset = False),
            admin = FA2_admin.address,
            metadata = sp.utils.metadata_of_url("https://example.com")
        )
        sc += dummyToken
        sc.h2("FA2: Initial minting")
        dummy_md = FA2.FA2.make_metadata(
            name     = "Dummy FA2",
            decimals = 0,
            symbol   = "DFA2" )
        dummyToken.mint(
            address  = FA2_admin.address,
            token_id = 0,
            amount   = 100_000_000_000,
            metadata = dummy_md
        ).run(sender = FA2_admin)
        sc.h2("FA2_admin transfer 100 tokens to player1")
        dummyToken.transfer([dummyToken.batch_transfer.item(
            from_ = FA2_admin.address,
            txs = [ sp.record(to_ = player1.address, amount = 100, token_id = 0)])
        ]).run(sender = FA2_admin)
        sc.h2("GamePlatform admin registers FA2 token 0 on platform as token 1")
        wDummy_metadata = FA2.FA2.make_metadata(
            name     = "Wrapped Dummy",
            symbol   = "WD",
            decimals = 6,
        )
        wDummy_permissions = lgr.build_token_permissions({
                "type"            : "FA2",
                "fa_token"        : sp.pair(dummyToken.address, 0),
                "mint_cost"       : sp.mutez(1),
                "mint_permissions": sp.variant("allow_everyone", sp.unit)
        })
        ledger.set_token_info(token_id = 1, token_info = wDummy_metadata).run(sender = ledger_admin)
        ledger.update_token_permissions(token_id = 1, token_permissions = wDummy_permissions).run(sender = ledger_admin)

        sc.h2("Admin set ledger as platform operator for Dummy token")
        c1.admin_update_operators(fa2 = dummyToken.address, operators = [
            sp.variant("add_operator", dummyToken.operator_param.make(
                owner = c1.address,
                operator = ledger.address,
                token_id = 0)),
        ]).run(sender = admin)

        sc.h2("Player1 set ledger as operator")
        dummyToken.update_operators([
                sp.variant("add_operator", dummyToken.operator_param.make(
                    owner = player1.address,
                    operator = ledger.address,
                    token_id = 0)),
        ]).run(sender = player1)

        sc.h2("New channel")
        channelParams = sp.record(players = players, nonce = "Channel 1", withdraw_delay = 3600 * 24)
        channel_id = sp.blake2b(sp.pack((c1.address, channelParams.players, channelParams.nonce)))
        c1.new_channel(channelParams).run(sender = player1)

        sc.h2("Player1 push dummy FA2 tokens as bonds")
        sc.verify(dummyToken.data.ledger[dummyToken.ledger_key.make(player1.address, 0)].balance == 100)
        sc.verify(~dummyToken.data.ledger.contains(dummyToken.ledger_key.make(c1.address, 0)))
        ledger.push_bonds(platform = c1.address, channel_id = channel_id, player_addr = player1.address, bonds = {1: 100}).run(sender = player1)
        sc.verify(dummyToken.data.ledger[dummyToken.ledger_key.make(player1.address, 0)].balance == 0)
        sc.verify(dummyToken.data.ledger[dummyToken.ledger_key.make(c1.address, 0)].balance == 100)

        sc.h2("Withdraw")
        sc.h3("Player 1 request withdraw 50 tokens")
        c1.withdraw_request(channel_id = channel_id, tokens = sp.map({1: 50})).run(sender = player1)
        sc.h3("Player 2 request leave empty challenge")
        c1.withdraw_challenge(channel_id = channel_id, withdrawer = player1.address, game_ids = sp.set([])).run(sender = player2)
        sc.h3("Player 1 finalize withdraw request")
        sc.verify_equal(gp.player_bonds(c1, channel_id, player1.address)[1], 100)
        c1.withdraw_finalize(channel_id).run(sender = player1)
        sc.verify_equal(gp.player_bonds(c1, channel_id, player1.address)[1], 50)
        sc.verify_equal(dummyToken.data.ledger[dummyToken.ledger_key.make(player1.address, 0)].balance, 50)
        sc.verify_equal(dummyToken.data.ledger[dummyToken.ledger_key.make(c1.address, 0)].balance, 50)

        ###################################
        # Test 2 : with transfer_and_call #
        ###################################
        sc.h2("Player1 remove ledger as operator")
        dummyToken.update_operators([
                sp.variant("remove_operator", dummyToken.operator_param.make(
                    owner = player1.address,
                    operator = ledger.address,
                    token_id = 0)),
        ]).run(sender = player1)

        sc.h2("Player1 push dummy FA2 tokens as bonds via transfer and call")
        ledger_on_received_bonds = sp.to_address(sp.contract(types.t_callback, ledger.address, entry_point = "on_received_bonds").open_some())
        sc.verify_equal(dummyToken.data.ledger[dummyToken.ledger_key.make(c1.address, 0)].balance, 50)
        sc.verify_equal(dummyToken.data.ledger[dummyToken.ledger_key.make(player1.address, 0)].balance, 50)
        dummyToken.transfer_and_call([
            sp.record(
                from_ = player1.address,
                txs = [sp.record(
                    to_      = c1.address,
                    callback = ledger_on_received_bonds,
                    data     = sp.pack(sp.record(channel_id = channel_id, player_addr = player1.address)),
                    token_id = 0,
                    amount   = 42
                )]
            )
        ]).run(sender = player1)
        sc.verify_equal(dummyToken.data.ledger[dummyToken.ledger_key.make(c1.address, 0)].balance, 92)
        sc.verify_equal(dummyToken.data.ledger[dummyToken.ledger_key.make(player1.address, 0)].balance, 8)

        sc.h2("Withdraw")
        sc.h3("Player 1 request withdraw 42 tokens")
        c1.withdraw_request(channel_id = channel_id, tokens = sp.map({1: 42})).run(sender = player1)
        sc.h3("Player 2 request leave empty challenge")
        c1.withdraw_challenge(channel_id = channel_id, withdrawer = player1.address, game_ids = sp.set([])).run(sender = player2)
        sc.h3("Player 1 finalize withdraw request")
        sc.verify_equal(gp.player_bonds(c1, channel_id, player1.address)[1], 92)
        c1.withdraw_finalize(channel_id).run(sender = player1)
        sc.verify_equal(gp.player_bonds(c1, channel_id, player1.address)[1], 50)
        sc.verify_equal(dummyToken.data.ledger[dummyToken.ledger_key.make(player1.address, 0)].balance, 50)
        sc.verify_equal(dummyToken.data.ledger[dummyToken.ledger_key.make(c1.address, 0)].balance, 50)

        sc.h2("Expected error on wrong receiver")
        sc.p("This case is never supposed to happen if the ledger is well configured.<br>\
                It should build the callback according to the receiver. \
                But the platform is still responsible for failing if that happens. \
            ")
        c1.on_received_bonds(
            sp.record(
                amount   = 42,
                data = sp.pack(sp.record(channel_id = channel_id, player_addr = player1.address)),
                receiver = player1.address,
                sender = player1.address,
                token_id = 0
            )
        ).run(sender = ledger.address, valid = False, exception = "Platform_NotReceiver")
        # Notice that the sender is a contract of this transction is a contract address,
        # it means we bypass some of the contract logic
        # to test what would happen in the platform if the ledger logic were wrong.

    @sp.add_test(name="transfers - one signature play with outcome")
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

        ###########
        #  Test 1 #
        ###########
        sc.h2("One player signature")
        game_num = 1
        sc.h3("Player 1 will transfer 10 to Player 2")
        settlements, bonds = h.transfer_settlements(p1_to_p2 = {0:10})
        settlements = sc.compute(settlements)
        sc.show(settlements)
        sc.h3("Player 1 push {0: 10}")
        ledger.mint(token_id = 0, amount = 10, address = player1.address).run(sender = player1, amount = sp.mutez(10))
        ledger.push_bonds(platform = c1.address, channel_id = channel_id, player_addr = player1.address, bonds = {0: 10}).run(sender = player1)

        sc.h3("P1 Instanciate new game : Transfer")
        constants = sc.compute(sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                              game_nonce = "game"+str(game_num), play_delay = play_delay, bonds = bonds, settlements = settlements))
        game_id = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)

        sc.h3("Player 1 send transfer with its signature")
        new_current = sp.record(move_nb = 1, player = 2, outcome = sp.some(sp.variant("final", sp.variant("game_finished", "transferred"))))
        player_1_signature = sp.make_signature(player1.secret_key, gp.action_play(game_id, new_current, sp.pack(sp.unit), sp.pack(sp.unit)))
        c1.game_play(game_id = game_id, new_current = new_current, new_state = sp.pack(sp.unit), move_data = sp.pack(sp.unit), signatures = sp.map({player1.public_key: player_1_signature})).run(sender = player1)
        sc.verify(c1.data.games[game_id].current.outcome == sp.some(sp.variant("pending", sp.variant("game_finished", "transferred"))))

        sc.h3("Player 2 countersign")
        player_2_signature = sp.make_signature(player2.secret_key, gp.action_play(game_id, new_current, sp.pack(sp.unit), sp.pack(sp.unit)))
        c1.game_play(game_id = game_id, new_current = new_current, new_state = sp.pack(sp.unit), move_data = sp.pack(sp.unit), signatures = sp.map({player2.public_key: player_2_signature})).run(sender = player2)
        sc.verify(gp.finished_outcome(c1, game_id) == "transferred")

        sc.h3("Settle game")
        sc.verify( gp.player_bonds(c1, channel_id, player1.address)[0] == 10)
        sc.verify(~gp.player_bonds(c1, channel_id, player2.address).contains(0))
        c1.game_settle(game_id).run(sender = player1)
        sc.verify(~gp.player_bonds(c1, channel_id, player1.address).contains(0))
        sc.verify( gp.player_bonds(c1, channel_id, player2.address)[0] == 10)
        sc.p("P2 received 10 tokens 0")

        ###########
        #  Test 2 #
        ###########
        sc.h2("Counter signature starved")
        game_num += 1
        sc.h3("Player 1 will transfer 10 to Player 2")
        settlements, bonds = h.transfer_settlements(p1_to_p2 = {0:10})
        settlements = sc.compute(settlements)
        sc.show(settlements)
        sc.h3("Player 1 push {0: 10}")
        ledger.mint(token_id = 0, amount = 10, address = player1.address).run(sender = player1, amount = sp.mutez(10))
        ledger.push_bonds(platform = c1.address, channel_id = channel_id, player_addr = player1.address, bonds = {0: 10}).run(sender = player1)

        sc.h3("P1 Instanciate new game : Transfer")
        constants = sc.compute(sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                              game_nonce = "game"+str(game_num), play_delay = play_delay, bonds = bonds, settlements = settlements))
        game_id = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)

        sc.h3("Player 1 send transfer with its signature")
        new_current = sp.record(move_nb = 1, player = 2, outcome = sp.some(sp.variant("final", sp.variant("game_finished", "transferred"))))
        player_1_signature = sp.make_signature(player1.secret_key, gp.action_play(game_id, new_current, sp.pack(sp.unit), sp.pack(sp.unit)))
        c1.game_play(game_id = game_id, new_current = new_current, new_state = sp.pack(sp.unit), move_data = sp.pack(sp.unit), signatures = sp.map({player1.public_key: player_1_signature})).run(sender = player1)
        sc.show(c1.data.games[game_id].current.outcome)
        sc.verify(c1.data.games[game_id].current.outcome == sp.some(sp.variant("pending", sp.variant("game_finished", "transferred"))))

        sc.h3("Player 1 starved when pending outcome")
        c1.dispute_starving(game_id = game_id, flag = True).run(sender = player1)
        c1.dispute_starved(game_id = game_id, player_id = 2).run(sender = player1, now = sp.timestamp(3600 * 24 + 1))

        sc.verify(gp.outcome(c1, game_id) == sp.variant("player_inactive", 2))
