import smartpy as sp

gp           = sp.io.import_template("state_channel_games/game_platform.py")
model_wrap   = sp.io.import_template("state_channel_games/model_wrap.py")
Chess        = sp.io.import_template("state_channel_games/models/chess.py")

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

    def new_game_sigs(constants, params = sp.unit):
        new_game = gp.action_new_game(constants, sp.pack(params))
        return make_signatures(player1, player2, new_game)

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

    chess = Chess.Chess()

    @sp.add_test(name="Chess - Game platform")
    def test():
        sc = sp.test_scenario()
        sc.h1("Chess")
        sc.h2("Contract")
        # Ledger
        ledger_address = sp.address("KT1_LEDGER_ADDRESS")
        c1 = gp.GamePlatform(sp.set([admin.address]), ledger_address)
        sc += c1

        sc.h2("New model: Chess")
        model = sc.compute(model_wrap.model_wrap(chess))
        model_id = sc.compute(model_wrap.model_id(model))
        c1.admin_new_model(model).run(sender = admin)
        sc.p("Init type:")
        sc.show(sp.utils.bytes_of_string("{ \"prim\": \"unit\" }"))
        sc.p("Model Id:")
        sc.show(model_id)

        sc.h2("New channel")
        channelParams = sp.record(players = players, nonce = "Channel 1", withdraw_delay = 5)
        channel_id = sp.blake2b(sp.pack((c1.address, channelParams.players, channelParams.nonce)))
        c1.new_channel(channelParams)

        sc.h3("Instanciate new game - Chess")
        constants = sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:player1.address, 2:player2.address},
                              game_nonce = "game1", play_delay = play_delay, settlements = settlements, bonds = {1:{0:20}, 2:{0:20}})
        game_id = sc.compute(gp.compute_game_id(constants))
        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_sigs(constants)).run(sender = player1)
        game = c1.data.games[game_id]

        sc.h2("A single move")
        move_data = sp.pack(
            sp.set_type_expr(
                sp.variant("play", sp.record(f = sp.record(i = 1, j = 4), t = sp.record(i = 3, j = 4), promotion = sp.none, claim_repeat = sp.none)),
                chess.t_move_data
            )
        )
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = move_data, sender = player1.address)))
        play_action = gp.action_play(game_id, game.current, game.state.open_some(), move_data)
        signatures = make_signatures(player1, player2, play_action)
        c1.game_play(game_id = game_id, new_current = game.current, new_state = game.state.open_some(), move_data = move_data, signatures = signatures)