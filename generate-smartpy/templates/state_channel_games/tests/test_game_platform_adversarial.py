import smartpy as sp

gp           = sp.io.import_template("state_channel_games/game_platform.py")
lgr          = sp.io.import_template("state_channel_games/ledger.py")
Tictactoe    = sp.io.import_template("state_channel_games/models/tictactoe.py")
model_wrap   = sp.io.import_template("state_channel_games/model_wrap.py")
FA2          = sp.io.import_template("FA2.py")

def make_signatures(p1, p2, x):
    sig1 = sp.make_signature(p1.secret_key, x)
    sig2 = sp.make_signature(p2.secret_key, x)
    return sp.map({p1.public_key: sig1, p2.public_key: sig2})

if "templates" not in __name__:
    admin = sp.test_account('admin')
    player1 = sp.test_account('player1')
    player2 = sp.test_account('player2')
    players = {player1.address: player1.public_key, player2.address: player2.public_key}

    # Ledger
    ledger_admin = sp.test_account('ledger_admin')
    ledger_config = FA2.FA2_config(single_asset = False)
    ledger_metadata = sp.utils.metadata_of_url("https://example.com")
    wXTZ_metadata = FA2.FA2.make_metadata(
        name     = "Wrapped XTZ",
        symbol   = "WXTZ",
        decimals = 6,
    )
    wXTZ_permissions = lgr.build_token_permissions({
            "type"            : "NATIVE",
            "mint_cost"       : sp.mutez(1),
            "mint_permissions": sp.variant("allow_everyone", sp.unit)
    })

    def new_game_sigs(constants, params = sp.unit):
        new_game = gp.action_new_game(constants, sp.pack(params))
        return make_signatures(player1, player2, new_game)

    tictactoe = Tictactoe.Tictactoe()
    play_delay = 3600 * 24
    settlements = sp.map({
        sp.variant("player_inactive",      1)      : [gp.transfer(1, 2, {0: 15})],
        sp.variant("player_inactive",      2)      : [gp.transfer(2, 1, {0: 15})],
        sp.variant("player_double_played", 1)      : [gp.transfer(1, 2, {0: 20})],
        sp.variant("player_double_played", 2)      : [gp.transfer(2, 1, {0: 20})],
        sp.variant("game_finished", "player_1_won"): [gp.transfer(2, 1, {0: 10})],
        sp.variant("game_finished", "player_2_won"): [gp.transfer(1, 2, {0: 10})],
        sp.variant("game_finished", "draw")        : [],
        sp.variant("game_aborted", sp.unit)        : [],
    })

    @sp.add_test(name="Offchain_TicTacToe_Adversarial - double signed - starved")
    def test():
        sc = sp.test_scenario()
        sc.table_of_contents()
        sc.h1("Offchain - Tic-Tac-Toe - Adversarial Draw")
        sc.h2("Contracts")
        sc.h3("Ledger")
        ledger = lgr.Ledger(ledger_config, admin = ledger_admin.address, metadata = ledger_metadata)
        sc += ledger
        sc.h3("GamePlatform")
        c1 = gp.GamePlatform(sp.set([admin.address]), ledger.address)
        sc += c1
        sc.h2("Ledger: XTZ configuration")
        ledger.set_token_info(token_id = 0, token_info = wXTZ_metadata).run(sender = ledger_admin)
        ledger.update_token_permissions(token_id = 0, token_permissions = wXTZ_permissions).run(sender = ledger_admin)

        sc.h2("New model: TicTacToe")
        model = sc.compute(model_wrap.model_wrap(tictactoe))
        model_id = sc.compute(model_wrap.model_id(model))
        c1.admin_new_model(model).run(sender = admin)
        sc.h2("New channel")
        channelParams = sp.record(players = players, nonce = "Channel 1", withdraw_delay = 5)
        channel_id = sc.compute(sp.blake2b(sp.pack((c1.address, channelParams.players, channelParams.nonce))))
        c1.new_channel(channelParams)
        sc.h2("Push bonds")
        ledger.mint(token_id = 0, amount = 20, address = player1.address).run(sender = player1, amount = sp.mutez(20))
        ledger.mint(token_id = 0, amount = 40, address = player2.address).run(sender = player2, amount = sp.mutez(40))
        ledger.push_bonds(platform = c1.address, channel_id = channel_id, player_addr = player1.address, bonds = {0: 20}).run(sender = player1)
        ledger.push_bonds(platform = c1.address, channel_id = channel_id, player_addr = player2.address, bonds = {0: 40}).run(sender = player2)

        sc.h2("(Offchain) New game")
        constants = sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                              game_nonce = "game1", play_delay = play_delay, settlements = settlements, bonds = {1:{0:20}, 2:{0:20}})
        game_id = sc.compute(gp.compute_game_id(constants))
        game = sc.compute(c1.offchain_new_game(
            sp.record(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants))
        ))

        sc.h3("(Offchain) Move 0")
        move_data_0 = sp.pack(sp.record(i = 1, j = 1))
        game_state_0 = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = move_data_0, sender = player1.address)))
        new_state = gp.action_play(game_id, game_state_0.current, game_state_0.state.open_some(), move_data_0)
        sig_0 = {player1.public_key: sp.make_signature(player1.secret_key, new_state)}

        ###################################
        # Test 1: Go onchain and starving #
        ###################################
        sc.h2("Go onchain and starving")
        sc.p("Player 2 refuses to sign move 1")
        sc.h3("Player 1 forces player 2 to play")
        sc.h4("Push new game")
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)
        sc.h4("Push its move")
        c1.game_play(game_id = game_id, new_current = game_state_0.current, new_state = game_state_0.state.open_some(), move_data = move_data_0, signatures = sig_0)
        sc.h4("Player1 starving")
        c1.dispute_starving(game_id = game_id, flag = True).run(sender = player1)
        ###################################
        # Test 2: Starved on its own turn #
        ###################################
        c1.dispute_starving(game_id = game_id, flag = True).run(sender = player2)
        c1.dispute_starved(game_id = game_id, player_id = 1).run(sender = player2, valid = False, exception = "Platform_NotPlayersTurn")
        c1.dispute_starving(game_id = game_id, flag = False).run(sender = player2)
        ###########################
        # Test 3: new_game replay #
        ###########################
        sc.h2("(fail) New game replay")
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player2, valid = False, exception = "Platform_GameAlreadyExists")
        #############################
        # Test 4: new_game override #
        #############################
        sc.h2("(fail) New game override")
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player2, valid = False, exception = "Platform_GameAlreadyExists")
        #######################
        # Test 5: Settle game #
        #######################
        sc.h2("(fail) Settle game")
        c1.game_settle(game_id).run(sender = player2, valid = False, exception = "Plateform_GameIsntOver")
        #######################################
        # Test 6: Fake new outcome signatures #
        #######################################
        sc.h2("(fail) Push outcome with fake signature")
        new_outcome = gp.action_new_outcome(game_id, gp.game_finished("player_2_won"), sp.timestamp(3600 * 24))
        sigs = make_signatures(player2, player2, new_outcome)
        c1.game_set_outcome(game_id = game_id, outcome = gp.game_finished("player_2_won"), timeout = sp.timestamp(3600 * 24), signatures = sigs).run(sender = player2, valid = False, exception = "Platform_MissingSig")
        ##################################################
        # Test 87: Double sign report with same signature #
        ##################################################
        sc.h2("Player2 tries to report player 1 double sign with same signature")
        statement1 = sp.record(current = game_state_0.current, state = game_state_0.state.open_some(), move_data = move_data_0, sig = sig_0[player1.public_key])
        c1.dispute_double_signed(game_id = game_id, player_id = 1, statement1 = statement1, statement2 = statement1).run(sender = player2, valid = False, exception = "Platform_NotDifferentSignatures")

        sc.h2("(Onchain) move 1")
        move_data_1 = sp.pack(sp.record(i = 1, j = 2))
        game_state_1 = sc.compute(c1.offchain_compute_game_play(sp.record(game = game_state_0, move_data = move_data_1, sender = player2.address)))
        new_state = gp.action_play(game_id, game_state_1.current, game_state_1.state.open_some(), move_data_1)
        sig_1 = {player2.public_key: sp.make_signature(player2.secret_key, new_state)}
        c1.game_play(game_id = game_id, new_current = game_state_1.current, new_state = game_state_1.state.open_some(), move_data = move_data_1, signatures = sig_1)
        ###########################
        # Test 8: Remove starving #
        ###########################
        sc.h2("Player1 remove starving")
        c1.dispute_starving(game_id = game_id, flag = False).run(sender = player1)

        sc.h2("(Offchain) Move 2")
        move_data_2 = sp.pack(sp.record(i = 2, j = 1))
        game_state_2 = sc.compute(c1.offchain_compute_game_play(sp.record(game = c1.data.games[game_id], move_data = move_data_2, sender = player1.address)))
        new_state = gp.action_play(game_id, game_state_2.current, game_state_2.state.open_some(), move_data_2)

        sc.h2("(Offchain) Player 2 sends a wrong move")
        sc.h3("(Offchain) Player 2 tries to craft an invalid move")
        sc.verify(sp.catch_exception(c1.offchain_compute_game_play(sp.record(game = game_state_2, move_data = sp.pack(sp.record(i = 1, j = 1)), sender = player2.address))) == sp.some("move on a non empty cell"))
        sc.h3("(Offchain) Player 2 prepares move 3")
        fake_game = c1.offchain_compute_game_play(sp.record(game = game_state_2, move_data = sp.pack(sp.record(i = 2, j = 2)), sender = player2.address))
        sc.h3("(Offchain) Player 2 craft an invalid signed move and send it to player1")
        player2_move_data = sp.pack(sp.record(i = 1, j = 1))
        fake_state = sp.pack(sp.utils.matrix([[0, 0, 0], [0, 1, 0], [0, 0, 0]]))
        fake_game_state = gp.action_play(game_id, fake_game.current, sp.pack(sp.utils.matrix([[0, 0, 0], [0, 1, 0], [0, 0, 0]])), player2_move_data)
        sig_fake_state = sp.make_signature(player2.secret_key, fake_game_state)
        sc.show(sp.record(fake_state = fake_state, sig_fake_state = sig_fake_state))

        ###############################
        # Test 9: Offchain check move #
        ###############################
        sc.h3("(Offchain) Player 1 discovers that it doesn't pass offchain_check_move")
        sp.catch_exception(c1.offchain_game_play(
            sp.record(
                game        = game_state_2,
                move_data   = player2_move_data,
                new_current = fake_game.current,
                new_state   = fake_game.state.open_some(),
                signatures  = {player2.public_key: sig_fake_state})
        ))

        ################################
        # Test 10: Offchain apply move #
        ################################
        sc.h3("(Offchain) Player 1 tries to find the regular state for player2's move but it's an error")
        sc.verify(sp.catch_exception(c1.offchain_game_apply_move(sp.record(game = game_state_2, move_data = player2_move_data))) == sp.some("move on a non empty cell"))

        sc.h2("(Offchain) Move 2")
        sig_2 = {player1.public_key: sp.make_signature(player1.secret_key, new_state)}

        sc.h2("(Offchain) Move 3")
        move_data_3 = sp.pack(sp.record(i = 2, j = 2))
        game_state_3 = sc.compute(c1.offchain_compute_game_play(sp.record(game = game_state_2, move_data = move_data_3, sender = player2.address)))
        new_state = gp.action_play(game_id, game_state_3.current, game_state_3.state.open_some(), move_data_3)
        state_3_signatures = make_signatures(player1, player2, new_state)
        c1.game_play(game_id = game_id, new_current = game_state_3.current, new_state = game_state_3.state.open_some(), move_data = move_data_3, signatures = state_3_signatures)

        ######################################################
        # Test 11: Double sign report with different move_nb #
        ######################################################
        sc.h2("Player2 tries to report player 1 double sign with different move_nb")
        statement1 = sp.record(current = game_state_0.current, state = game_state_0.state.open_some(), move_data = move_data_0, sig = sig_0[player1.public_key])
        statement2 = sp.record(current = game_state_2.current, state = game_state_2.state.open_some(), move_data = move_data_2, sig = sig_2[player1.public_key])
        c1.dispute_double_signed(game_id = game_id, player_id = 1, statement1 = statement1, statement2 = statement2).run(valid = False, exception = "Platform_MoveNBMismatch")

        #############################################
        # Test 12: Double sign report with dbad sig #
        #############################################
        sc.h2("Player2 tries to report player 1 double sign with bad sig")
        statement1 = sp.record(current = game_state_2.current, state = game_state_0.state.open_some(), move_data = move_data_0, sig = sig_0[player1.public_key])
        statement2 = sp.record(current = game_state_2.current, state = game_state_2.state.open_some(), move_data = move_data_2, sig = sig_2[player1.public_key])
        c1.dispute_double_signed(game_id = game_id, player_id = 1, statement1 = statement1, statement2 = statement2).run(valid = False, exception = "Platform_badSig")

        ##########################################
        # Test 13: Claim starved without timeout #
        ##########################################
        sc.h2("(fail) claim starved without timeout")
        c1.dispute_starved(game_id = game_id, player_id = 1).run(sender = player2, valid = False, exception = "Platform_NoTimeoutSetup")

        ##########################################
        # Test 14: Claim starved without timeout #
        ##########################################
        sc.h2("(fail) claim starved before timeout")
        sc.h3("Player 2 sets starving")
        c1.dispute_starving(game_id = game_id, flag = True).run(sender = player2)
        sc.h3("Player 2 claims starving before timeout")
        c1.dispute_starved(game_id = game_id, player_id = 1).run(sender = player2, valid = False, exception = "Platform_NotTimedOut")

        sc.h2("(Offchain) Move 4")
        move_data_4 = sp.pack(sp.record(i = 0, j = 0))
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game_state_3, move_data = move_data_4, sender = player1.address)))
        new_state = gp.action_play(game_id, game.current, game.state.open_some(), move_data_4)

        sc.h2("(Offchain) Player 2 tries to send a new move 3")
        move_data_3bis = sp.pack(sp.record(i = 0, j = 1))
        game_state_3bis = sc.compute(c1.offchain_compute_game_play(sp.record(game = game_state_2, move_data = move_data_3bis, sender = player2.address)))
        new_state = gp.action_play(game_id, game_state_3bis.current, game_state_3bis.state.open_some(), move_data_3bis)
        sig_1 = sp.make_signature(player2.secret_key, new_state)

        ##########################
        # Test 15: Double signed #
        ##########################
        sc.h2("(Onchain) Player 1 report double signed")
        statement1 = sp.record(current = game_state_3.current, state = game_state_3.state.open_some(), move_data = move_data_3, sig = state_3_signatures[player2.public_key])
        statement2 = sp.record(current = game_state_3bis.current, state = game_state_3bis.state.open_some(), move_data = move_data_3bis, sig = sig_1)
        c1.dispute_double_signed(game_id = game_id, player_id = 2, statement1 = statement1, statement2 = statement2).run(sender = player1)
        sc.verify(gp.outcome(c1, game_id) == sp.variant("player_double_played", 2))

        ###############################
        # Test 16: New channel replay #
        ###############################
        sc.h2("(fail) Player 2 tries to recreate channel")
        c1.new_channel(channelParams).run(sender = player2, valid = False, exception = "Platform_ChannelAlreadyExists")

        ##########################
        # Test 17: Double settle #
        ##########################
        sc.h2("(Onchain) Player 1 settle the game")
        c1.game_settle(game_id).run(sender = player1)
        sc.verify(gp.player_bonds(c1, channel_id, player1.address)[0] == 40)
        sc.verify(gp.player_bonds(c1, channel_id, player2.address)[0] == 20)
        sc.verify(c1.data.games[game_id].settled)
        sc.h2("(Onchain) Player 1 fails to double settle the game")
        c1.game_settle(game_id).run(sender = player1, valid = False, exception = "Plateform_GameSettled")

        ####################
        # Test 18: Starved #
        ####################

        sc.h2("Starving")
        sc.h3("Instanciate new game")
        constants = sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                              game_nonce = "game2", play_delay = play_delay, settlements = settlements, bonds = {1:{0:20}, 2:{0:20}})
        game_id = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)
        sc.h3("A first move in the center")
        move = sp.pack(sp.record(i = 1, j = 1))
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = c1.data.games[game_id], move_data = move, sender = player1.address)))
        new_state = gp.action_play(game_id, game.current, game.state.open_some(), move)
        sig = {player1.public_key: sp.make_signature(player1.secret_key, new_state)}
        c1.game_play(game_id = game_id, new_current = game.current, new_state = game.state.open_some(), move_data = sp.pack(sp.record(i = 1, j = 1)), signatures = sig)
        sc.h2("Player1 starving")
        c1.dispute_starving(game_id = game_id, flag = True).run(sender = player1)
        c1.dispute_starved(game_id = game_id, player_id = 2).run(sender = player1, now = sp.timestamp(3600*24 + 1))
        sc.verify(gp.outcome(c1, game_id) == sp.variant("player_inactive", 2))
        sc.h2("Settle the game")
        c1.game_settle(game_id).run(sender = player1)
        sc.verify(gp.player_bonds(c1, channel_id, player1.address)[0] == 55)
        sc.verify(gp.player_bonds(c1, channel_id, player2.address)[0] ==  5)

    @sp.add_test(name="Offchain_TicTacToe_Adversarial - pending outcome")
    def test():
        sc = sp.test_scenario()
        sc.table_of_contents()
        sc.h1("Offchain - Tic-Tac-Toe - Adversarial Pending outcome")
        sc.h2("Contracts")
        ledger_address = sp.address("KT1_LEDGER_ADDRESS")
        sc.h3("GamePlatform")
        c1 = gp.GamePlatform(sp.set([admin.address]), ledger_address)
        sc += c1
        sc.h2("New channel")
        channelParams = sp.record(players = players, nonce = "Channel 1", withdraw_delay = 5)
        channel_id = sp.blake2b(sp.pack((c1.address, channelParams.players, channelParams.nonce)))
        c1.new_channel(channelParams)
        sc.h2("New model: TicTacToe")
        model = sc.compute(model_wrap.model_wrap(tictactoe))
        model_id = sc.compute(model_wrap.model_id(model))
        c1.admin_new_model(model).run(sender = admin)

        sc.h2("A sequence of interactions with a winner")
        sc.h3("Instanciate new game")
        constants = sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                              game_nonce = "game1", play_delay = play_delay, settlements = settlements, bonds = {1:{0:10}, 2:{0:10}})
        game_id = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants))
        game = c1.data.games[game_id]

        sc.h3("Some moves")
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(sp.record(i = 0, j = 0)), sender = player1.address)))
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(sp.record(i = 1, j = 0)), sender = player2.address)))
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(sp.record(i = 0, j = 1)), sender = player1.address)))
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(sp.record(i = 1, j = 1)), sender = player2.address)))

        move_data = sp.pack(sp.record(i = 1, j = 1))
        play_action = gp.action_play(game_id, game.current, game.state.open_some(), move_data)
        signatures = make_signatures(player1, player2, play_action)

        ###########
        # Moves 5 #
        ###########
        game_5 = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(sp.record(i = 2, j = 0)), sender = player1.address)))
        move_data_5 = sp.pack(sp.record(i = 2, j = 0))
        play_action_5 = gp.action_play(game_id, game_5.current, game_5.state.open_some(), move_data_5)
        signatures_move_5 = {1: sp.make_signature(player1.secret_key, play_action_5), 2: sp.make_signature(player2.secret_key, play_action_5)}
        sc.h3("Move 5:")
        sc.show(sp.record(move_data = move_data_5))
        sc.show(sp.record(signatures = sp.map({player1.public_key: signatures_move_5[1], player2.public_key: signatures_move_5[2]})))

        #################
        # Moves 5 cheat #
        #################
        game_5_cheat = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(sp.record(i = 0, j = 2)), sender = player1.address)))
        move_data_5_cheat = sp.pack(sp.record(i = 0, j = 2))
        play_action_5_cheat = gp.action_play(game_id, game_5_cheat.current, game_5_cheat.state.open_some(), move_data_5_cheat)
        player_1_signature_5_cheat = sp.make_signature(player1.secret_key, play_action_5_cheat)

        sc.h2("Player 1 tries to cheat by pushing state of move 4 and playing something else on-chain with a game outcome")
        sc.h3("Pushing state 4 on-chain")
        c1.game_play(game_id = game_id, new_current = game.current, new_state = game.state.open_some(), move_data = move_data, signatures = signatures).run(sender = player1)
        sc.h3("Playing directly on-chain with an alternative move 5")
        c1.game_play(game_id = game_id, new_current = game_5_cheat.current, new_state = game_5_cheat.state.open_some(), move_data = move_data_5_cheat, signatures = sp.map({player1.public_key: player_1_signature_5_cheat})).run(sender = player1)
        sc.h3("Player 2 reports for double signed")
        statement1 = sp.record(current = game_5.current, state = game_5.state.open_some(), move_data = move_data_5, sig = signatures_move_5[1])
        statement2 = sp.record(current = game_5_cheat.current, state = game_5_cheat.state.open_some(), move_data = move_data_5_cheat, sig = player_1_signature_5_cheat)
        c1.dispute_double_signed(game_id = game_id, player_id = 1, statement1 = statement1, statement2 = statement2).run(sender = player2)