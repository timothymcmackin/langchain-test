import smartpy as sp

gp           = sp.io.import_template("state_channel_games/game_platform.py")
lgr          = sp.io.import_template("state_channel_games/ledger.py")
Tictactoe    = sp.io.import_template("state_channel_games/models/tictactoe.py")
Nim          = sp.io.import_template("state_channel_games/models/nim.py")
model_wrap   = sp.io.import_template("state_channel_games/model_wrap.py")
FA2          = sp.io.import_template("FA2.py")

def make_signatures(p1, p2 = None, x = sp.unit):
    sig1 = sp.make_signature(p1.secret_key, x)
    if p2 is None:
        return sp.map({p1.public_key: sig1})
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
    nim       = Nim.Nim()
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

    @sp.add_test(name="TicTacToe and Nim - everything onchain")
    def test():
        sc = sp.test_scenario()
        sc.table_of_contents()
        sc.h1("Tic-Tac-Toe - Win")
        sc.h2("Contract")
        ledger_address = sp.address("KT1_LEDGER_ADDRESS")
        sc.h3("GamePlatform")
        c1 = gp.GamePlatform(sp.set([admin.address]), ledger_address)
        sc += c1
        sc.h2("New model: TicTacToe")
        model = sc.compute(model_wrap.model_wrap(tictactoe))
        model_id = sc.compute(model_wrap.model_id(model))
        model_nim = sc.compute(model_wrap.model_wrap(nim))
        model_nim_id = sc.compute(model_wrap.model_id(model_nim))
        c1.admin_new_model(model).run(sender = admin)
        sc.h2("New model: Nim")
        c1.admin_new_model(model_nim).run(sender = admin)

        sc.h2("New channel")
        channelParams = sp.record(players = players, nonce = "Channel 1", withdraw_delay = 5)
        channel_id = sp.blake2b(sp.pack((c1.address, channelParams.players, channelParams.nonce)))
        c1.new_channel(channelParams)

        sc.h3("Instanciate new game - TicTacToe")
        constants = sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                              game_nonce = "game1", play_delay = play_delay, settlements = settlements, bonds = {1:{0:10}, 2:{0:10}})
        game_id = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)
        game = c1.data.games[game_id]

        sc.h2("A sequence of interactions with a winner")
        move_data = sp.pack(sp.record(i = 1, j = 1))
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = move_data, sender = player1.address)))
        play_action = gp.action_play(game_id, game.current, game.state.open_some(), move_data)
        signatures = make_signatures(player1, player2, play_action)
        c1.game_play(game_id = game_id, new_current = game.current, new_state = game.state.open_some(), move_data = move_data, signatures = signatures)

        move_data = sp.pack(sp.record(i = 1, j = 2))
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = move_data, sender = player2.address)))
        play_action = gp.action_play(game_id, game.current, game.state.open_some(), move_data)
        signatures = make_signatures(player1, player2, play_action)
        c1.game_play(game_id = game_id, new_current = game.current, new_state = game.state.open_some(), move_data = move_data, signatures = signatures)

        move_data = sp.pack(sp.record(i = 2, j = 1))
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = move_data, sender = player1.address)))
        play_action = gp.action_play(game_id, game.current, game.state.open_some(), move_data)
        signatures = make_signatures(player1, player2, play_action)
        c1.game_play(game_id = game_id, new_current = game.current, new_state = game.state.open_some(), move_data = move_data, signatures = signatures)

        move_data = sp.pack(sp.record(i = 2, j = 2))
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = move_data, sender = player2.address)))
        play_action = gp.action_play(game_id, game.current, game.state.open_some(), move_data)
        signatures = make_signatures(player1, player2, play_action)
        c1.game_play(game_id = game_id, new_current = game.current, new_state = game.state.open_some(), move_data = move_data, signatures = signatures)

        move_data = sp.pack(sp.record(i = 0, j = 1))
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = move_data, sender = player1.address)))
        play_action = gp.action_play(game_id, game.current, game.state.open_some(), move_data)
        signatures = make_signatures(player1, player2, play_action)
        c1.game_play(game_id = game_id, new_current = game.current, new_state = game.state.open_some(), move_data = move_data, signatures = signatures)

        sc.verify(gp.finished_outcome(c1, game_id) == "player_1_won")
        sc.p("Player1 has won")

        sc.h3("Instanciate new game - Nim")
        constants = sp.record(model_id = model_nim_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                              game_nonce = "game2", play_delay = play_delay, settlements = settlements, bonds = {1:{0:10}, 2:{0:10}})
        game_id = sc.compute(gp.compute_game_id(constants))
        nimParams = sp.record(numberOfHeaps = 5, bound = sp.none, misere = True)
        c1.new_game(constants = constants, initial_config = sp.pack(nimParams), signatures = new_game_sigs(constants, nimParams)).run(sender = player1)
        game = c1.data.games[game_id]

        move_data = sp.pack(sp.record(heapId = 0, size = 3))
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = move_data, sender = player1.address)))
        play_action = gp.action_play(game_id, game.current, game.state.open_some(), move_data)
        signatures = make_signatures(player1, player2, play_action)
        c1.game_play(game_id = game_id, new_current = game.current, new_state = game.state.open_some(), move_data = move_data, signatures = signatures)

        move_data = sp.pack(sp.record(heapId = 1, size = 4))
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = move_data, sender = player2.address)))
        play_action = gp.action_play(game_id, game.current, game.state.open_some(), move_data)
        signatures = make_signatures(player1, player2, play_action)
        c1.game_play(game_id = game_id, new_current = game.current, new_state = game.state.open_some(), move_data = move_data, signatures = signatures)

        move_data = sp.pack(sp.record(heapId = 2, size = 5))
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = move_data, sender = player1.address)))
        play_action = gp.action_play(game_id, game.current, game.state.open_some(), move_data)
        signatures = make_signatures(player1, player2, play_action)
        c1.game_play(game_id = game_id, new_current = game.current, new_state = game.state.open_some(), move_data = move_data, signatures = signatures)

        move_data = sp.pack(sp.record(heapId = 3, size = 6))
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = move_data, sender = player2.address)))
        play_action = gp.action_play(game_id, game.current, game.state.open_some(), move_data)
        signatures = make_signatures(player1, player2, play_action)
        c1.game_play(game_id = game_id, new_current = game.current, new_state = game.state.open_some(), move_data = move_data, signatures = signatures)

        move_data = sp.pack(sp.record(heapId = 4, size = 7))
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = move_data, sender = player1.address)))
        play_action = gp.action_play(game_id, game.current, game.state.open_some(), move_data)
        signatures = make_signatures(player1, player2, play_action)
        c1.game_play(game_id = game_id, new_current = game.current, new_state = game.state.open_some(), move_data = move_data, signatures = signatures)

        sc.verify(gp.finished_outcome(c1, game_id) == "player_2_won")

    @sp.add_test(name="TicTacToe_Errors - everything onchain - no countersign")
    def test():
        sc = sp.test_scenario()
        sc.table_of_contents()
        sc.h1("Tic-Tac-Toe - Errors tests")
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

        sc.h3("A first move in the center")
        move_data = sp.pack(sp.record(i = 1, j = 1))
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = move_data, sender = player1.address)))
        play_action = gp.action_play(game_id, game.current, game.state.open_some(), move_data)
        signatures = make_signatures(player1, x = play_action)
        c1.game_play(game_id = game_id, new_current = game.current, new_state = game.state.open_some(), move_data = move_data, signatures = signatures)

        ##########
        # Test 1 #
        ##########
        sc.h3("Move out of grid")
        sc.verify(sp.catch_exception(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(sp.record(i = 1, j = 5)), sender = player2.address))) == sp.some("move out of grid"))

        sc.h3("Move out of grid onchain with a fake game structure")
        fake_move_data = sp.pack(sp.record(i = 1, j = 2))
        fake_game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = fake_move_data, sender = player2.address)))
        play_action = gp.action_play(game_id, fake_game.current, fake_game.state.open_some(), move_data)
        signatures = make_signatures(player2, x = play_action)
        c1.game_play(
            game_id     = game_id,
            new_current = fake_game.current,
            new_state   = fake_game.state.open_some(),
            move_data   = sp.pack(sp.record(i = 1, j = 5)),
            signatures  = signatures
        ).run(valid = False, exception = "move out of grid")

        ##########
        # Test 2 #
        ##########
        sc.h3("Move on a non empty cell")
        sc.verify(sp.catch_exception(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(sp.record(i = 1, j = 1)), sender = player2.address))) == sp.some("move on a non empty cell"))

        sc.h3("Move on a non empty cell onchain with a fake game structure")
        fake_move_data = sp.pack(sp.record(i = 1, j = 2))
        fake_game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = fake_move_data, sender = player2.address)))
        play_action = gp.action_play(game_id, fake_game.current, fake_game.state.open_some(), move_data)
        signatures = make_signatures(player2, x = play_action)
        c1.game_play(
            game_id     = game_id,
            new_current = fake_game.current,
            new_state   = fake_game.state.open_some(),
            move_data   = sp.pack(sp.record(i = 1, j = 1)),
            signatures  = signatures
        ).run(valid = False, exception = "move on a non empty cell")

        ##########
        # Test 3 #
        ##########
        sc.h3("Forbidden player")
        move_data = sp.pack(sp.record(i = 1, j = 2))
        sc.verify(sp.catch_exception(c1.offchain_compute_game_play(sp.record(game = game, move_data = move_data, sender = player1.address))) == sp.some("Platform_WrongPlayer"))
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = move_data, sender = player2.address)))
        play_action = gp.action_play(game_id, game.current, game.state.open_some(), move_data)
        signatures = make_signatures(player1, x = play_action)
        c1.game_play(
            game_id     = game_id,
            new_current = game.current,
            new_state   = game.state.open_some(),
            move_data   = move_data,
            signatures  = signatures
        ).run(valid = False)


        ##########
        # Test 4 #
        ##########
        sc.h3("Play offchain until the end")
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(sp.record(i = 2, j = 1)), sender = player1.address)))
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(sp.record(i = 2, j = 2)), sender = player2.address)))
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(sp.record(i = 0, j = 1)), sender = player1.address)))
        play_action = gp.action_play(game_id, game.current, game.state.open_some(), move_data)
        sc.h3("Player tries to push without player 2's signature")
        signatures = make_signatures(player1, x = play_action)
        c1.game_play(
            game_id = game_id, new_current = game.current, new_state = game.state.open_some(), move_data = move_data, signatures = signatures
        ).run(valid = False)

        ##########
        # Test 5 #
        ##########
        sc.h3("Pushing last play")
        signatures = make_signatures(player1, player2, play_action)
        c1.game_play(game_id = game_id, new_current = game.current, new_state = game.state.open_some(), move_data = move_data, signatures = signatures)
        sc.h3("Move after the end")
        sc.verify(gp.finished_outcome(c1, game_id) == "player_1_won")
        c1.game_play(
            game_id = game_id, new_current = game.current, new_state = game.state.open_some(), move_data = move_data, signatures = signatures
        ).run(valid = False, exception = "Platform_GameNotRunning")
