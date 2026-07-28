"""
    A realistic scenario where Alice and Opponent play tictactoe on the gamePlatform.

    They exchange their addresses, public_key, and the running game via an
    unknown medium, possibly public medium.

    Alice scenario is a bit more complex. She originates a gamePlatform
    contract on the interpreter. This way she can verify what would occur if
    every exchange would be pushed onchain.

    Bob is doing something lighter: he only uses the offchain view
    Bob doesn't verify opponnent countersign of his moves.

    In a perfect world, only steps marked as ONCHAIN need to be pushed on-chain.
    Everything else only exists on the interpreter.
"""

import smartpy as sp

gp         = sp.io.import_template("state_channel_games/game_platform.py")
Tictactoe  = sp.io.import_template("state_channel_games/models/tictactoe.py")
model_wrap = sp.io.import_template("state_channel_games/model_wrap.py")
lgr        = sp.io.import_template("state_channel_games/ledger.py")
FA2        = sp.io.import_template("FA2.py")

if "templates" not in __name__:
    me = sp.record(
        address    = sp.address("tz1bQx5gL9WLBsc9qyxKj7wGiit78A7frBmK"),
        public_key = sp.key("edpkv3regPfkqjzWuD29P4tq1zkKokRQnGGpg5UMMvvXnCkXNoRqY2"),
        secret_key = sp.secret_key("edskRtPDyFcuEVeZ2tK7xu2jKGFUgvfvLP7gWB8QvFmBv84Z9MhErHps65MNr1RdL5Qh3Uii6CDhymhoPFEee3TykXPpaWPUWU"),
    )
    opponent = sp.record(
        address    = sp.address("tz1dtXJpDg4e8tYcGE5b7dzStfvHGyVZivaY"),
        public_key = sp.key("edpkuTgJuK2tK5pixWA27bMZ3JHybicPr6Uy6ang9GWbGvFV4eAPXb"),
    )
    players = {me.address: me.public_key, opponent.address: opponent.public_key}
    admin = me

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


    tictactoe = Tictactoe.Tictactoe()
    play_delay = 3600 * 24

    @sp.add_test(name="Bob")
    def test():
        data = {}
        sc = sp.test_scenario()
        sc.table_of_contents()
        def get_state(testView):
            return sc.compute(testView.data.result.open_some())
        sc.h1("Transfers")
        sc.h2("Contracts")
        sc.h3("Ledger")
        ledger = lgr.Ledger(ledger_config, admin = ledger_admin.address, metadata = ledger_metadata)
        sc += ledger
        platform_addr = sp.address("KT1LX9dx1MMSBbG3seX7DHC7kd2tuKUmwyZs")
        c1 = gp.GamePlatform(admins = sp.set([admin.address]), ledger = ledger.address, self_addr = platform_addr)
        sc += c1
        platform_sc_addr = c1.address
        c1.address = platform_addr
        sc.h2("Ledger: XTZ configuration")
        ledger.set_token_info(token_id = 0, token_info = wXTZ_metadata).run(sender = ledger_admin)
        ledger.update_token_permissions(token_id = 0, token_permissions = wXTZ_permissions).run(sender = ledger_admin)
        # -- New channel --
        sc.h2("New channel")
        channelParams = sp.record(players = players, nonce = "1", withdraw_delay = 60 * 10)
        channel_id = sp.blake2b(sp.pack((c1.address, channelParams.players, channelParams.nonce)))
        c1.new_channel(channelParams)

        # -- Push bonds --
        sc.h2("ONCHAIN: Push bonds {0: 100_000000}")
        ledger.mint(token_id = 0, amount = 100_000000, address = me.address).run(sender = me.address, amount = sp.tez(100))
        ledger.push_bonds(platform = platform_sc_addr, channel_id = channel_id, player_addr = me.address, bonds = {0: 100_000000}).run(sender = me.address)

        # -- New model --
        sc.h2("New model: TicTacToe")
        model = model_wrap.model_wrap(tictactoe)
        model = sc.compute(model)
        model_id = sc.compute(model_wrap.model_id(model))
        sc.show(sp.record(model_id = model_id))
        sc.verify_equal(model_id, sp.bytes("0xd8d896739d4ffdb8900ced61865e19eda69fef8b8cc9f08e5908596eef057a89"))
        c1.admin_new_model(model).run(sender = admin.address)
        sc.verify(c1.data.models.contains(model_id))

        # -- Game constants --
        settlements = sp.map({
            sp.variant("player_inactive",      1)      : [gp.transfer(1, 2, {0: 15_000000})],
            sp.variant("player_inactive",      2)      : [gp.transfer(2, 1, {0: 15_000000})],
            sp.variant("player_double_played", 1)      : [gp.transfer(1, 2, {0: 20_000000})],
            sp.variant("player_double_played", 2)      : [gp.transfer(2, 1, {0: 20_000000})],
            sp.variant("game_finished", "player_1_won"): [gp.transfer(2, 1, {0: 10_000000})],
            sp.variant("game_finished", "player_2_won"): [gp.transfer(1, 2, {0: 10_000000})],
            sp.variant("game_finished", "draw")        : [],
            sp.variant("game_aborted", sp.unit)        : [],
        })
        constants = sp.record(model_id = model_id, channel_id = channel_id, players_addr = {2:me.address, 1:opponent.address},
                              game_nonce = "game2", play_delay = play_delay, settlements = settlements, bonds = {1:{0:20_000000}, 2:{0:20_000000}})
        game_id = gp.compute_game_id(constants)
        sc.show(game_id)

        # -- New game --
        sc.h2("New game")
        new_game_action = gp.action_new_game(constants, sp.pack(sp.unit))
        my_new_game_sig = sc.compute(sp.make_signature(me.secret_key, new_game_action))

        # Replace by opponent signature
        opponent_new_game_sig = sp.signature('edsigtmDn3a8tqvCt8XPwrCx8k2AbNAMbv44aYgvCjJRGZKuKeqqwRFsRP55ysg3k1TBgW1Cp4gpBEQoJPabj9gMUhPdZH9bCQc')
        new_game_signatures = sp.map({me.public_key: my_new_game_sig, opponent.public_key: opponent_new_game_sig})

        game = sc.compute(c1.offchain_new_game(sp.record(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_signatures)))
        sc.show(game)

        sc.p('After verification of opponent bonds and game constants.<br/>We sign the new game.')
        sc.show(my_new_game_sig)

        # -- Move 0 --
        move_nb = 0
        sc.h2(f"Move {move_nb}")

        # Replace by opponent move
        move_data = sp.record(i = 1, j = 1)
        move_data = sp.set_type_expr(move_data, tictactoe.t_move_data)

        sc.p('Game structure modifications')
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(move_data), sender = opponent.address)))
        sc.p('Action play')
        action_play = sc.compute(gp.action_play(game_id, game.current, game.state.open_some(), sp.pack(move_data)))
        sc.show(action_play)
        sc.p("My play sig")
        my_play_sig = sp.make_signature(me.secret_key, action_play)
        sc.show(my_play_sig)

        # Replace by opponent signature
        opponent_play_sig = sp.signature('edsigtyre4mtVm3k7ssRYJGeUSCMo1N2Tz4szdsndmxoRbFLFKJxjrQbjC9Xues31h2SfDfmTYoGUD4CbQLoEi6uGZy8itYJVnB')

        sc.verify(sp.check_signature(
            opponent.public_key,
            opponent_play_sig,
            action_play
        ))

        data[move_nb] = (game, action_play, {me.public_key: my_play_sig, opponent.public_key: opponent_play_sig}, sp.pack(move_data))

        # -- Move 1 --
        move_nb = 1
        sc.h2(f"Move {move_nb}")

        move_data = sp.record(i = 0, j = 0)
        move_data = sp.set_type_expr(move_data, tictactoe.t_move_data)
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(move_data), sender = me.address)))
        sc.p('Action play')
        action_play = sc.compute(gp.action_play(game_id, game.current, game.state.open_some(), sp.pack(move_data)))
        sc.show(action_play)
        sc.p("My play sig")
        my_play_sig = sp.make_signature(me.secret_key, action_play)
        sc.show(my_play_sig)

        data[move_nb] = (game, action_play, {me.public_key: my_play_sig}, sp.pack(move_data))

        # -- Move 2 --
        move_nb = 2
        sc.h2(f"Move {move_nb}")

        move_data = sp.record(i = 0, j = 1)
        move_data = sp.set_type_expr(move_data, tictactoe.t_move_data)
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(move_data), sender = opponent.address)))
        sc.p('Action play')
        action_play = sc.compute(gp.action_play(game_id, game.current, game.state.open_some(), sp.pack(move_data)))
        sc.show(action_play)
        sc.p("My play sig")
        my_play_sig = sp.make_signature(me.secret_key, action_play)
        sc.show(my_play_sig)

        opponent_play_sig = sp.signature('edsigtZMMJwy2m6fGR4dYFtbdBjdADK2qVJtncsZpoM4vJZAuwGkXXTHAUVs1dnSCDUHLRbcepBLEt7ocmsAGj5Ntwot6s75ruy')

        sc.verify(sp.check_signature(
            opponent.public_key,
            opponent_play_sig,
            action_play
        ))

        data[move_nb] = (game, action_play, {me.public_key: my_play_sig, opponent.public_key: opponent_play_sig}, sp.pack(move_data))

        # -- Move 3 --
        move_nb = 3
        sc.h2(f"Move {move_nb}")

        move_data = sp.record(i = 2, j = 1)
        move_data = sp.set_type_expr(move_data, tictactoe.t_move_data)
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(move_data), sender = me.address)))
        sc.p('Action play')
        action_play = sc.compute(gp.action_play(game_id, game.current, game.state.open_some(), sp.pack(move_data)))
        sc.show(action_play)
        sc.p("My play sig")
        my_play_sig = sp.make_signature(me.secret_key, action_play)
        sc.show(my_play_sig)

        data[move_nb] = (game, action_play, {me.public_key: my_play_sig}, sp.pack(move_data))

        # -- Move 4 --
        move_nb = 4
        sc.h2(f"Move {move_nb}")

        move_data = sp.record(i = 2, j = 0)
        move_data = sp.set_type_expr(move_data, tictactoe.t_move_data)
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(move_data), sender = opponent.address)))
        sc.p('Action play')
        action_play = sc.compute(gp.action_play(game_id, game.current, game.state.open_some(), sp.pack(move_data)))
        sc.show(action_play)
        sc.p("My play sig 4")
        my_play_sig = sp.make_signature(me.secret_key, action_play)
        sc.show(my_play_sig)

        opponent_play_sig = sp.signature('edsigtq3vCxkKe3ZnyrvxxoR9GGeWeRKUYdAku4uodubkHvFaqE4S1RwxK8G3UWAy2whacREXiABdtCqkEKHxsLtmw3g4LLp9uw')

        sc.verify(sp.check_signature(
            opponent.public_key,
            opponent_play_sig,
            action_play
        ))

        data[move_nb] = (game, action_play, {me.public_key: my_play_sig, opponent.public_key: opponent_play_sig}, sp.pack(move_data))

        # -- Move 5 --
        move_nb = 5
        sc.h2(f"Move {move_nb}")

        move_data = sp.record(i = 0, j = 2)
        move_data = sp.set_type_expr(move_data, tictactoe.t_move_data)
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(move_data), sender = me.address)))
        sc.p('Action play')
        action_play = sc.compute(gp.action_play(game_id, game.current, game.state.open_some(), sp.pack(move_data)))
        sc.show(action_play)
        sc.p("My play sig 5")
        my_play_sig = sp.make_signature(me.secret_key, action_play)
        sc.show(my_play_sig)

        data[move_nb] = (game, action_play, {me.public_key: my_play_sig}, sp.pack(move_data))

        # -- Move 6 --
        move_nb = 6
        sc.h2(f"Move {move_nb}")

        move_data = sp.record(i = 1, j = 2)
        move_data = sp.set_type_expr(move_data, tictactoe.t_move_data)
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(move_data), sender = opponent.address)))
        sc.p('Action play')
        action_play = sc.compute(gp.action_play(game_id, game.current, game.state.open_some(), sp.pack(move_data)))
        sc.show(action_play)
        sc.p("My play sig 6")
        my_play_sig = sp.make_signature(me.secret_key, action_play)
        sc.show(my_play_sig)

        opponent_play_sig = sp.signature('edsigtutPy6aRGx1B4MiPGXgbFtApXKjTH9wwUyirGyyCCKbupbh4mD4Sff89Uzf9xciGU78vaRVKXifx4vCjLyjMH6c8Jq8Rj1')

        sc.verify(sp.check_signature(
            opponent.public_key,
            opponent_play_sig,
            action_play
        ))

        data[move_nb] = (game, action_play, {me.public_key: my_play_sig, opponent.public_key: opponent_play_sig}, sp.pack(move_data))

        # -- Move 7 --
        move_nb = 7
        sc.h2(f"Move {move_nb}")

        move_data = sp.record(i = 2, j = 2)
        move_data = sp.set_type_expr(move_data, tictactoe.t_move_data)
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(move_data), sender = me.address)))
        sc.p('Action play')
        action_play = sc.compute(gp.action_play(game_id, game.current, game.state.open_some(), sp.pack(move_data)))
        sc.show(action_play)
        sc.p("My play sig 7")
        my_play_sig = sp.make_signature(me.secret_key, action_play)
        sc.show(my_play_sig)

        data[move_nb] = (game, action_play, {me.public_key: my_play_sig}, sp.pack(move_data))

        # -- Move 8 --
        move_nb = 8
        sc.h2(f"Move {move_nb}")

        move_data = sp.record(i = 1, j = 0)
        move_data = sp.set_type_expr(move_data, tictactoe.t_move_data)
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(move_data), sender = opponent.address)))
        sc.p('Action play')
        action_play = sc.compute(gp.action_play(game_id, game.current, game.state.open_some(), sp.pack(move_data)))
        sc.show(action_play)
        sc.p("My play sig 8")
        my_play_sig = sp.make_signature(me.secret_key, action_play)
        sc.show(my_play_sig)

        opponent_play_sig = sp.signature('edsigthhBHKixGPbQSFgtJHg4xzstEFR4oHv48AXhpxNAcRUidC2udgGibmT1nmaocLn7QixhyQKa3zBtnUonAbwJfgitnuJy5Q')

        sc.verify(sp.check_signature(
            opponent.public_key,
            opponent_play_sig,
            action_play
        ))

        data[move_nb] = (game, action_play, {me.public_key: my_play_sig, opponent.public_key: opponent_play_sig}, sp.pack(move_data))
