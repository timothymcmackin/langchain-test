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

    @sp.add_test(name="Simple transfers")
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
        sc.h2("Simple transfer")
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

        sc.h3("Play transfer")
        c1.game_play(play_transfer(game_id)).run(sender = player1)
        sc.verify(gp.finished_outcome(c1, game_id) == "transferred")

        sc.h3("Settle game")
        sc.verify( gp.player_bonds(c1, channel_id, player1.address)[0] == 10)
        sc.verify(~gp.player_bonds(c1, channel_id, player2.address).contains(0))
        c1.game_settle(game_id).run(sender = player1)
        sc.verify(~gp.player_bonds(c1, channel_id, player1.address).contains(0))
        sc.verify( gp.player_bonds(c1, channel_id, player2.address)[0] == 10)
        sc.p("P2 received 10 tokens 0")

        ############
        #  Test 2  #
        ############
        sc.h2("Transfer back")
        game_num += 1
        sc.h3("P1 and P2 inverted. Player 1 will transfer 10 to Player 2")
        settlements, bonds = h.transfer_settlements(p1_to_p2 = {0:10})
        settlements = sc.compute(settlements)
        sc.show(settlements)

        sc.h3("P2 Instanciate new game : Transfer")
        constants = sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player2.address, 2:player1.address},
                              game_nonce = "game"+str(game_num), play_delay = play_delay, bonds = bonds, settlements = settlements)
        game_id = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player2)

        sc.h3("(Onchain) play transfer")
        c1.game_play(play_transfer(game_id)).run(sender = player2)
        sc.verify(gp.finished_outcome(c1, game_id) == "transferred")

        sc.verify(~gp.player_bonds(c1, channel_id, player1.address).contains(0))
        sc.verify( gp.player_bonds(c1, channel_id, player2.address)[0] == 10)
        c1.game_settle(game_id).run(sender = player1)
        sc.verify( gp.player_bonds(c1, channel_id, player1.address)[0] == 10)
        sc.verify(~gp.player_bonds(c1, channel_id, player2.address).contains(0))
        sc.p("P2 (player 1 of previous game) received 10 tokens 0")

        ###########
        #  Test 3 #
        ###########
        sc.h2("Multiple transfers")
        game_num += 1
        sc.h3("Admin setup free tokens")
        ledger.set_token_info(token_id = 1, token_info = h.free_metadata).run(sender = ledger_admin)
        ledger.set_token_info(token_id = 2, token_info = h.free_metadata).run(sender = ledger_admin)
        ledger.update_token_permissions(token_id = 1, token_permissions = h.free_permissions).run(sender = ledger_admin)
        ledger.update_token_permissions(token_id = 2, token_permissions = h.free_permissions).run(sender = ledger_admin)

        sc.h3("Player 1 transfers 10 token_1 to Player 2 and 10 token_2 ")
        settlements, bonds = h.transfer_settlements(p1_to_p2 = {1:10, 2:10})
        settlements = sc.compute(settlements)
        sc.show(settlements)
        sc.h3("Player 1 push {1: 10, 2: 10}")
        ledger.mint(token_id = 1, amount = 10, address = player1.address).run(sender = player1)
        ledger.mint(token_id = 2, amount = 10, address = player1.address).run(sender = player1)
        ledger.push_bonds(platform = c1.address, channel_id = channel_id, player_addr = player1.address, bonds = {1: 10, 2 : 10}).run(sender = player1)

        sc.h3("P1 Instanciate new game : Transfer")
        constants = sc.compute(sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                              game_nonce = "game"+str(game_num), play_delay = play_delay, bonds = bonds, settlements = settlements))
        game_id = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)

        sc.h3("(Onchain) play transfer")
        c1.game_play(play_transfer(game_id)).run(sender = player1)
        sc.verify(gp.finished_outcome(c1, game_id) == "transferred")

        sc.h3("Settle game")
        sc.verify( gp.player_bonds(c1, channel_id, player1.address)[1] == 10)
        sc.verify( gp.player_bonds(c1, channel_id, player1.address)[2] == 10)
        sc.verify(~gp.player_bonds(c1, channel_id, player2.address).contains(1))
        sc.verify(~gp.player_bonds(c1, channel_id, player2.address).contains(2))
        c1.game_settle(game_id).run(sender = player1)
        sc.verify(~gp.player_bonds(c1, channel_id, player1.address).contains(1))
        sc.verify(~gp.player_bonds(c1, channel_id, player1.address).contains(2))
        sc.verify( gp.player_bonds(c1, channel_id, player2.address)[1] == 10)
        sc.verify( gp.player_bonds(c1, channel_id, player2.address)[2] == 10)
        sc.p("P1 received 10 token_1 and 10 token_2")

        ###########
        #  Test 4 #
        ###########
        sc.h2("Self transfer")
        game_num += 1
        sc.h3("Player 1 transfers 5 tokens to himself")
        settlements, bonds = h.transfer_settlements(p1_to_p1 = {0:5})
        settlements = sc.compute(settlements)
        sc.show(settlements)

        sc.h3("P1 Instanciate new game : Transfer")
        constants = sc.compute(sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                              game_nonce = "game"+str(game_num), play_delay = play_delay, bonds = bonds, settlements = settlements))
        game_id = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)

        sc.h3("(Onchain) play transfer")
        c1.game_play(play_transfer(game_id)).run(sender = player1)
        sc.verify(gp.finished_outcome(c1, game_id) == "transferred")

        sc.h3("Settle game")
        sc.verify(gp.player_bonds(c1, channel_id, player1.address)[0] == 10)
        c1.game_settle(game_id).run(sender = player1)
        sc.verify(gp.player_bonds(c1, channel_id, player1.address)[0] == 10)
        sc.p("P1 tokens didn't changed")

        ###########
        #  Test 5 #
        ###########
        sc.h2("Transfer in both direction")
        game_num += 1
        sc.h3("Player 1 transfers 5 tokens 0 to player 2, 2 tokens to himself, Player 2 transfer 4 tokens 0 to player 1")
        settlements, bonds = h.transfer_settlements(p1_to_p2 = {0:5}, p1_to_p1 = {0:2}, p2_to_p1 = {0: 4})
        settlements = sc.compute(settlements)
        sc.show(settlements)

        sc.h3("Player 2 push {0: 10}")
        ledger.mint(token_id = 0, amount = 10, address = player2.address).run(sender = player1, amount = sp.mutez(10))
        ledger.push_bonds(platform = c1.address, channel_id = channel_id, player_addr = player2.address, bonds = {0: 10}).run(sender = player2)

        sc.h3("P1 Instanciate new game : Transfer")
        constants = sc.compute(sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                              game_nonce = "game"+str(game_num), play_delay = play_delay, bonds = bonds, settlements = settlements))
        game_id = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)

        sc.h3("(Onchain) play transfer")
        c1.game_play(play_transfer(game_id)).run(sender = player1)
        sc.verify(gp.finished_outcome(c1, game_id) == "transferred")

        sc.h3("Player 2 settle the game")
        sc.verify(gp.player_bonds(c1, channel_id, player1.address)[0] == 10)
        sc.verify(gp.player_bonds(c1, channel_id, player2.address)[0] == 10)
        c1.game_settle(game_id).run(sender = player2)
        sc.verify(gp.player_bonds(c1, channel_id, player1.address)[0] == 9)
        sc.verify(gp.player_bonds(c1, channel_id, player2.address)[0] == 11)
        sc.p("P1 lost 1 token, P2 won 1 token")

        ###########
        #  Test 6 #
        ###########
        sc.h2("Simple withdraw")
        sc.h3("Player 1 request withdraw 5 tokens")
        c1.withdraw_request(channel_id = channel_id, tokens = sp.map({0: 5})).run(sender = player1)
        sc.p("Player 1 channel bonds")
        sc.show(c1.data.channels[channel_id].players[player1.address])
        sc.h3("Player 2 request leave empty challenge")
        c1.withdraw_challenge(channel_id = channel_id, withdrawer = player1.address, game_ids = sp.set([])).run(sender = player2)
        sc.h3("Player 1 finalize withdraw request")
        sc.verify(gp.player_bonds(c1, channel_id, player1.address)[0] == 9)
        c1.withdraw_finalize(channel_id).run(sender = player1)
        sc.verify(gp.player_bonds(c1, channel_id, player1.address)[0] == 4)
        sc.verify(lgr.fa2_balance(player1.address, ledger, token_id = 0) == 5)

    @sp.add_test(name="Withdraw challenges - set_outcome")
    def test():
        sc = sp.test_scenario()
        sc.table_of_contents()
        sc.h1("Withdraw challenges")
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

        sc.h2("Player 1 push {0: 10}")
        ledger.mint(token_id = 0, amount = 10, address = player1.address).run(sender = player1, amount = sp.mutez(10))
        ledger.push_bonds(platform = c1.address, channel_id = channel_id, player_addr = player1.address, bonds = {0: 10}).run(sender = player1)

        sc.h2("P1 Instanciate new game : Transfer")
        settlements, bonds = h.transfer_settlements(p1_to_p2 = {0:5})
        settlements = sc.compute(settlements)
        constants = sc.compute(sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                                game_nonce = "game", play_delay = play_delay, bonds = bonds, settlements = settlements))
        game_id = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)

        ###########
        #  Test 1 #
        ###########
        sc.h2("Challenged withdraw")
        sc.h3("Player 1 request withdraw 8 tokens")
        c1.withdraw_request(channel_id = channel_id, tokens = sp.map({0: 8})).run(sender = player1)
        sc.h3("Player 2 challenge by pushing a game_id")
        c1.withdraw_challenge(channel_id = channel_id, withdrawer = player1.address, game_ids = sp.set([game_id])).run(sender = player2)
        sc.h3("Player 1 can't finalize withdraw")
        c1.withdraw_finalize(channel_id).run(sender = player1, valid = False, exception = "Platform_TokenChallenged")
        sc.h3("Player 1 proposes an abort outcome for running transfer and Player 2 accepts")
        proposed_outcome = gp.action_new_outcome(game_id, gp.abort, sp.timestamp(3600 * 24))
        outcome_sigs = h.make_signatures(player1, player2, proposed_outcome)
        c1.game_set_outcome(game_id = game_id, outcome = gp.abort, timeout = sp.timestamp(3600 * 24), signatures = outcome_sigs).run(sender = player1)
        c1.game_settle(game_id).run(sender = player1)
        sc.h3("Player 1 resolve challenge")
        c1.withdraw_challenge(channel_id = channel_id, withdrawer = player1.address, game_ids = sp.set([game_id])).run(sender = player1)
        sc.h3("Player 1 finalize withdraw request")
        c1.withdraw_finalize(channel_id).run(sender = player1)

        ###########
        #  Test 2 #
        ###########
        sc.h2("Multi challenged withdraw")
        sc.h3("Admin setup free tokens")
        ledger.set_token_info(token_id = 1, token_info = h.free_metadata).run(sender = ledger_admin)
        ledger.update_token_permissions(token_id = 1, token_permissions = h.free_permissions).run(sender = ledger_admin)
        sc.p("3 running transfers: 1 with low money, 2 with high money.<br/>\
              Player 1 resolves game 1 but it's not sufficient to withdraw and then resolve game 2, that become sufficient to withdraw")
        sc.h2("Player 1 push {1: 100}")
        ledger.mint(token_id = 1, amount = 100, address = player1.address).run(sender = player1)
        ledger.push_bonds(platform = c1.address, channel_id = channel_id, player_addr = player1.address, bonds = {1: 100}).run(sender = player1)
        sc.h2("Instanciate new transfers games")
        sc.h3("Game 1: 5 tokens 1")
        settlements, bonds = h.transfer_settlements(p1_to_p2 = {1:5})
        settlements = sc.compute(settlements)
        constants = sc.compute(sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                                game_nonce = "game_1", play_delay = play_delay, bonds = bonds, settlements = settlements))
        game_id_1 = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)
        sc.h3("Game 2: 40 tokens 1")
        settlements, bonds = h.transfer_settlements(p1_to_p2 = {1:40})
        settlements = sc.compute(settlements)
        constants = sc.compute(sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                                game_nonce = "game_2", play_delay = play_delay, bonds = bonds, settlements = settlements))
        game_id_2 = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)
        sc.h3("Game 3: 40 tokens 1")
        constants = sc.compute(sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                                game_nonce = "game_3", play_delay = play_delay, bonds = bonds, settlements = settlements))
        game_id_3 = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)

        sc.h3("Player 1 request withdraw 50 tokens 1")
        c1.withdraw_request(channel_id = channel_id, tokens = sp.map({1: 50})).run(sender = player1)
        sc.h3("Player 2 challenge by pushing 3 game ids")
        c1.withdraw_challenge(channel_id = channel_id, withdrawer = player1.address, game_ids = sp.set([game_id_1, game_id_2, game_id_3])).run(sender = player2)
        sc.h3("Player 1 can't finalize withdraw")
        c1.withdraw_finalize(channel_id).run(sender = player1, valid = False, exception = "Platform_TokenChallenged")

        sc.h3("Player 1 proposes an abort outcome for game_id_1 running transfer and Player 2 accepts")
        proposed_outcome = gp.action_new_outcome(game_id_1, gp.abort, sp.timestamp(3600 * 24))
        outcome_sigs = h.make_signatures(player1, player2, proposed_outcome)
        c1.game_set_outcome(game_id = game_id_1, outcome = gp.abort, timeout = sp.timestamp(3600 * 24), signatures = outcome_sigs).run(sender = player1)
        c1.game_settle(game_id_1).run(sender = player1)
        sc.h3("Player 1 tries to resolve challenge but still doesn't have resolved enough challenge")
        c1.withdraw_challenge(channel_id = channel_id, withdrawer = player1.address, game_ids = sp.set([game_id_1])).run(sender = player1)
        c1.withdraw_finalize(channel_id).run(sender = player1, valid = False, exception = "Platform_TokenChallenged")

        sc.h3("Player 1 proposes an abort outcome for game_id_2 running transfer and Player 2 accepts")
        proposed_outcome = gp.action_new_outcome(game_id_2, gp.abort, sp.timestamp(3600 * 24))
        outcome_sigs = h.make_signatures(player1, player2, proposed_outcome)
        c1.game_set_outcome(game_id = game_id_2, outcome = gp.abort, timeout = sp.timestamp(3600 * 24), signatures = outcome_sigs).run(sender = player1)
        c1.game_settle(game_id_2).run(sender = player1)
        sc.h3("Player 1 resolves challenge")
        c1.withdraw_challenge(channel_id = channel_id, withdrawer = player1.address, game_ids = sp.set([game_id_2])).run(sender = player1)
        sc.h3("Player 1 finalizes withdraw request")
        c1.withdraw_finalize(channel_id).run(sender = player1)

    @sp.add_test(name="Withdraw timeout and not enough tokens")
    def test():
        sc = sp.test_scenario()
        sc.table_of_contents()
        sc.h1("Expected withdraw errors")
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

        sc.h2("New channel")
        channelParams = sp.record(players = players, nonce = "Channel 1", withdraw_delay = 3600*24)
        channel_id = sp.blake2b(sp.pack((c1.address, channelParams.players, channelParams.nonce)))
        c1.new_channel(channelParams)

        sc.h2("Player 1 push {0: 10}")
        ledger.mint(token_id = 0, amount = 10, address = player1.address).run(sender = player1, amount = sp.mutez(10))
        ledger.push_bonds(platform = c1.address, channel_id = channel_id, player_addr = player1.address, bonds = {0: 10}).run(sender = player1)

        sc.h2("Not enough tokens")
        sc.h3("Player 1 request withdraw 50 tokens")
        c1.withdraw_request(channel_id = channel_id, tokens = sp.map({0: 50})).run(sender = player1)
        sc.h3("Player 1 fails to withdraw 50 tokens")
        c1.withdraw_finalize(channel_id).run(sender = player1, now = sp.timestamp(3600 * 24 + 1), valid = False, exception = "Platform_NotEnoughTokens")

        sc.h3("Player 1 can't open another request")
        c1.withdraw_request(channel_id = channel_id, tokens = sp.map({0: 5})).run(sender = player1, now = sp.timestamp(3600 * 24 + 1), valid = False, exception = "Platform_AnotherWithdrawIsRunning")
        sc.h3("Player 1 cancels its request")
        c1.withdraw_cancel(channel_id).run(sender = player1, now = sp.timestamp(3600 * 24 + 1))

        sc.h3("Player 1 request withdraw 5 tokens")
        c1.withdraw_request(channel_id = channel_id, tokens = sp.map({0: 5})).run(sender = player1, now = sp.timestamp(3600 * 24 + 1))
        sc.h3("Player 1 can't finalize before timeout")
        c1.withdraw_finalize(channel_id).run(sender = player1, valid = False, exception = "Platform_ChallengeDelayNotOver")
        sc.h3("Player 1 finalize after timeout")
        c1.withdraw_finalize(channel_id).run(sender = player1, now = sp.timestamp(3600 * 24 * 2 + 2))
        sc.verify(gp.player_bonds(c1, channel_id, player1.address)[0] == 5)
        sc.verify(lgr.fa2_balance(player1.address, ledger, token_id = 0) == 5)
