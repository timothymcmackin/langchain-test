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
        address    = sp.address("tz1dtXJpDg4e8tYcGE5b7dzStfvHGyVZivaY"),
        public_key = sp.key("edpkuTgJuK2tK5pixWA27bMZ3JHybicPr6Uy6ang9GWbGvFV4eAPXb"),
        secret_key = sp.secret_key("edskRhyHJmHpNZagdYET8zkQob6whvb8tJ2tEp2r3ugx7LzH4kEHRgp3tSiBZLw445CdLjXsasDGt4G2DR4b8RUr5shnF4DZDf"),
    )
    opponent = sp.record(
        address    = sp.address("tz1bQx5gL9WLBsc9qyxKj7wGiit78A7frBmK"),
        public_key = sp.key("edpkv3regPfkqjzWuD29P4tq1zkKokRQnGGpg5UMMvvXnCkXNoRqY2"),
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

    @sp.add_test(name="Alice")
    def test():
        data = {}
        sc = sp.test_scenario()
        sc.table_of_contents()
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
        sc.h2("ONCHAIN: New channel")
        channelParams = sp.record(players = players, nonce = "1", withdraw_delay = 60 * 10)
        channel_id = sp.blake2b(sp.pack((c1.address, channelParams.players, channelParams.nonce)))
        c1.new_channel(channelParams)
        sc.p('Channel id. Transmit this to Opponent:')
        sc.show(channel_id)

        # -- Push bonds --
        sc.h2("ONCHAIN: Push bonds {0: 50_000_000}")
        ledger.mint(token_id = 0, amount = 50_000_000, address = me.address).run(sender = me.address, amount = sp.tez(50))
        ledger.push_bonds(platform = platform_sc_addr, channel_id = channel_id, player_addr = me.address, bonds = {0: 50*10**6}).run(sender = me.address)
        sc.h2("Push opponent bonds {0: 100_000_000}")
        ledger.mint(token_id = 0, amount = 100_000_000, address = opponent.address).run(sender = opponent.address, amount = sp.tez(100))
        ledger.push_bonds(platform = platform_sc_addr, channel_id = channel_id, player_addr = opponent.address, bonds = {0: 100*10**6}).run(sender = opponent.address)

        # -- New model --
        sc.h2("New model: TicTacToe")
        model = model_wrap.model_wrap(tictactoe)
        model = sc.compute(model)
        model_id = sc.compute(model_wrap.model_id(model))
        sc.verify_equal(model_id, sp.bytes("0xd8d896739d4ffdb8900ced61865e19eda69fef8b8cc9f08e5908596eef057a89"))
        c1.admin_new_model(model).run(sender = admin.address)

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
        constants = sp.record(model_id = model_id, channel_id = channel_id, players_addr = {1:me.address, 2:opponent.address},
                              game_nonce = "game2", play_delay = play_delay, settlements = settlements, bonds = {1:{0:20*10**6}, 2:{0:20*10**6}})
        game_id = gp.compute_game_id(constants)
        sc.show(game_id)

        # -- New game --
        sc.h2("New game")
        new_game_action = gp.action_new_game(constants, sp.pack(sp.unit))
        sc.p('New game action.')
        sc.show(new_game_action)
        my_new_game_sig = sc.compute(sp.make_signature(me.secret_key, new_game_action))
        sc.p('New game signature.<br/>Transmit this to Opponent:')
        sc.show(my_new_game_sig)

        # Replace by opponent signature
        opponent_new_game_sig = sp.signature('edsigtyAW4H2U7Jpbtxfy8qYDgDnQ9Fatjq6xmb185ohE4Suuh9AZti6ShKw9zgX4rvacaJ3fVjNx5gr4MBfF55Q8yUxHAPc328')
        new_game_signatures = sp.map({me.public_key: my_new_game_sig, opponent.public_key: opponent_new_game_sig})

        game = sc.compute(c1.offchain_new_game(sp.record(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_signatures)))

        c1.new_game(constants = constants, initial_config = sp.pack(sp.unit), signatures = new_game_signatures).run(sender = me.address)

        # -- Move 0 --
        move_nb = 0
        sc.h2(f"Move {move_nb}")

        move_data = sp.record(i = 1, j = 1)
        move_data = sp.set_type_expr(move_data, tictactoe.t_move_data)
        sc.p('Move data. Transmit this to Opponent:')
        sc.show(move_data)
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(move_data), sender = me.address)))
        sc.p('Action play')
        action_play = gp.action_play(game_id, game.current, game.state.open_some(), sp.pack(move_data))
        sc.show(action_play)
        sc.p("My play sig. Transmit this to Opponent:")
        my_play_sig = sp.make_signature(me.secret_key, action_play)
        sc.show(my_play_sig)

        # Replace by opponent signature
        opponent_play_sig = sp.signature('edsigu6j3AJgvREiCqtmpDTtJVMxvZwtvZ8AVudo1V3YbsVWD6waBWeS7jqkCXLR9k6PFGgHnrjmJGJtoHcprh6C48qAVBpa6m7')
        data[move_nb] = (game, action_play, {me.public_key: my_play_sig, opponent.public_key: opponent_play_sig}, sp.pack(move_data))

        sc.h3("push move 0 onchain")
        c1.game_play(
            game_id = game_id,
            new_current = data[move_nb][0].current,
            new_state = data[move_nb][0].state.open_some(),
            move_data = data[move_nb][3],
            signatures = data[move_nb][2]
        ).run(sender = me.address)

        # -- Move 1 --
        move_nb += 1
        sc.h2(f"Move {move_nb}")

        # Replace by opponent move
        move_data = sp.record(i = 0, j = 0)
        move_data = sp.set_type_expr(move_data, tictactoe.t_move_data)
        sc.show(move_data)
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(move_data), sender = opponent.address)))
        sc.p('Action play')
        action_play = gp.action_play(game_id, game.current, game.state.open_some(), sp.pack(move_data))
        sc.show(action_play)
        sc.p("My play sig. Transmit this to Opponent:")
        my_play_sig = sp.make_signature(me.secret_key, action_play)
        sc.show(my_play_sig)

        # Replace by opponent signature
        opponent_play_sig = sp.signature('edsigu6mhWR6qctdRNBuW6ugBRbQhnWtwByLvPh1iDs2BTWnj8qh2p4dbmH8UHRkwxEWmhYhrYAP9hDjukN7ZNpAU9aUUPdNrmG')
        data[move_nb] = (game, action_play, {me.public_key: my_play_sig, opponent.public_key: opponent_play_sig}, sp.pack(move_data))

        sc.h3("push move onchain")
        c1.game_play(
            game_id = game_id,
            new_current = data[move_nb][0].current,
            new_state = data[move_nb][0].state.open_some(),
            move_data = data[move_nb][3],
            signatures = data[move_nb][2]
        ).run(sender = me.address)

        # -- Move 2 --
        move_nb += 1
        sc.h2(f"Move {move_nb}")

        move_data = sp.record(i = 0, j = 1)
        move_data = sp.set_type_expr(move_data, tictactoe.t_move_data)
        sc.p('Move data. Transmit this to Opponent:')
        sc.show(move_data)
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(move_data), sender = me.address)))
        sc.p('Action play')
        action_play = gp.action_play(game_id, game.current, game.state.open_some(), sp.pack(move_data))
        sc.show(action_play)
        sc.p("My play sig. Transmit this to Opponent:")
        my_play_sig = sp.make_signature(me.secret_key, action_play)
        sc.show(my_play_sig)

        # Replace by opponent signature
        opponent_play_sig = sp.signature('edsigtrbsm7CoGd23drEv6t1jUekMvP4uJYdfZaijrNKQPaQrpHpCu2DFamkJnHNFXxDkRD1HGAQRtFmFmuTKSH663jWQANnnfH')
        data[move_nb] = (game, action_play, {me.public_key: my_play_sig, opponent.public_key: opponent_play_sig}, sp.pack(move_data))

        sc.h3("push move onchain")
        c1.game_play(
            game_id = game_id,
            new_current = data[move_nb][0].current,
            new_state = data[move_nb][0].state.open_some(),
            move_data = data[move_nb][3],
            signatures = data[move_nb][2]
        ).run(sender = me.address)

        # -- Move 3 --
        move_nb += 1
        sc.h2(f"Move {move_nb}")

        # Replace by opponent move
        move_data = sp.record(i = 2, j = 1)
        move_data = sp.set_type_expr(move_data, tictactoe.t_move_data)
        sc.show(move_data)
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(move_data), sender = opponent.address)))
        sc.p('Action play')
        action_play = gp.action_play(game_id, game.current, game.state.open_some(), sp.pack(move_data))
        sc.show(action_play)
        sc.p("My play sig. Transmit this to Opponent:")
        my_play_sig = sp.make_signature(me.secret_key, action_play)
        sc.show(my_play_sig)

        opponent_play_sig = sp.signature('edsigtxsNxAjonJZ3EMhjS4xWhxCdpcBJcaxsgxKKZ25MihcZtfCM7vX76DNeWrga3ZwC5Pr5QXM7CTBer66TZ45kkxqp9pG3St')
        data[move_nb] = (game, action_play, {me.public_key: my_play_sig, opponent.public_key: opponent_play_sig}, sp.pack(move_data))

        sc.h3("push move onchain")
        c1.game_play(
            game_id = game_id,
            new_current = data[move_nb][0].current,
            new_state = data[move_nb][0].state.open_some(),
            move_data = data[move_nb][3],
            signatures = data[move_nb][2]
        ).run(sender = me.address)

        # -- Move 4 --
        move_nb += 1
        sc.h2(f"Move {move_nb}")

        move_data = sp.record(i = 2, j = 0)
        move_data = sp.set_type_expr(move_data, tictactoe.t_move_data)
        sc.p('Move data. Transmit this to Opponent:')
        sc.show(move_data)
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(move_data), sender = me.address)))
        sc.p('Action play')
        action_play = gp.action_play(game_id, game.current, game.state.open_some(), sp.pack(move_data))
        sc.show(action_play)
        sc.p("My play sig. Transmit this to Opponent:")
        my_play_sig = sp.make_signature(me.secret_key, action_play)
        sc.show(my_play_sig)

        opponent_play_sig = sp.signature('edsigtyQBBwMwxPB5bb7SuWpKHE9AT9Fxf6K3kRjKLaFZMfriwbLYZUsz3zyxyM9p4huzvocuXuGJu48x66eCgrao8VWGZreuxW')
        data[move_nb] = (game, action_play, {me.public_key: my_play_sig, opponent.public_key: opponent_play_sig}, sp.pack(move_data))

        sc.h3("push move onchain")
        c1.game_play(
            game_id = game_id,
            new_current = data[move_nb][0].current,
            new_state = data[move_nb][0].state.open_some(),
            move_data = data[move_nb][3],
            signatures = data[move_nb][2]
        ).run(sender = me.address)

        # -- Move 5 --
        move_nb += 1
        sc.h2(f"Move {move_nb}")

        # Replace by opponent move
        move_data = sp.record(i = 0, j = 2)
        move_data = sp.set_type_expr(move_data, tictactoe.t_move_data)
        sc.show(move_data)
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(move_data), sender = opponent.address)))
        sc.p('Action play')
        action_play = gp.action_play(game_id, game.current, game.state.open_some(), sp.pack(move_data))
        sc.show(action_play)
        sc.p("My play sig. Transmit this to Opponent:")
        my_play_sig = sp.make_signature(me.secret_key, action_play)
        sc.show(my_play_sig)

        opponent_play_sig = sp.signature('edsigtvAkLU3CtNeZxMtdtjhRxvKGUR4gxm4xmmVWedJwY3QgYL1f99NmTFMAHwnurMTvbZ9VXiFtHPQ8LF2WNMy5eCFWRPcqFV')
        data[move_nb] = (game, action_play, {me.public_key: my_play_sig, opponent.public_key: opponent_play_sig}, sp.pack(move_data))

        sc.h3("push move onchain")
        c1.game_play(
            game_id = game_id,
            new_current = data[move_nb][0].current,
            new_state = data[move_nb][0].state.open_some(),
            move_data = data[move_nb][3],
            signatures = data[move_nb][2]
        ).run(sender = me.address)

        # -- Move 6 --
        move_nb += 1
        sc.h2(f"Move {move_nb}")

        move_data = sp.record(i = 1, j = 2)
        move_data = sp.set_type_expr(move_data, tictactoe.t_move_data)
        sc.p('Move data. Transmit this to Opponent:')
        sc.show(move_data)
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(move_data), sender = me.address)))
        sc.p('Action play')
        action_play = gp.action_play(game_id, game.current, game.state.open_some(), sp.pack(move_data))
        sc.show(action_play)
        sc.p("My play sig. Transmit this to Opponent:")
        my_play_sig = sp.make_signature(me.secret_key, action_play)
        sc.show(my_play_sig)

        opponent_play_sig = sp.signature('edsigu56jhd9UFbAienYn2oaFHYd7e5LbX7h85uCGoKP1J3zc5tsMR14Ywb2YZAjvZTHoSEP15h7JiXDCGWKwFko8yZVN92oiiJ')
        data[move_nb] = (game, action_play, {me.public_key: my_play_sig, opponent.public_key: opponent_play_sig}, sp.pack(move_data))

        sc.h3("push move onchain")
        c1.game_play(
            game_id = game_id,
            new_current = data[move_nb][0].current,
            new_state = data[move_nb][0].state.open_some(),
            move_data = data[move_nb][3],
            signatures = data[move_nb][2]
        ).run(sender = me.address)

        # -- Move 7 --
        move_nb += 1
        sc.h2(f"Move {move_nb}")

        # Replace by opponent move
        move_data = sp.record(i = 2, j = 2)
        move_data = sp.set_type_expr(move_data, tictactoe.t_move_data)
        sc.show(move_data)
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(move_data), sender = opponent.address)))
        sc.p('Action play')
        action_play = gp.action_play(game_id, game.current, game.state.open_some(), sp.pack(move_data))
        sc.show(action_play)
        sc.p("My play sig. Transmit this to Opponent:")
        my_play_sig = sp.make_signature(me.secret_key, action_play)
        sc.show(my_play_sig)

        opponent_play_sig = sp.signature('edsigteqF3hSy1gsszEXTBycFaFM894rqK9nfMTwZWSdEHCMCZSs4z5PaWABwDb3FSwQ28Uvv1yW5RdyRDtEmmK5Am9rG8Ru1LG')
        data[move_nb] = (game, action_play, {me.public_key: my_play_sig, opponent.public_key: opponent_play_sig}, sp.pack(move_data))

        sc.h3("push move onchain")
        c1.game_play(
            game_id = game_id,
            new_current = data[move_nb][0].current,
            new_state = data[move_nb][0].state.open_some(),
            move_data = data[move_nb][3],
            signatures = data[move_nb][2]
        ).run(sender = me.address)

        # -- Move 8 --
        move_nb += 1
        sc.h2(f"Move {move_nb}")

        move_data = sp.record(i = 1, j = 0)
        move_data = sp.set_type_expr(move_data, tictactoe.t_move_data)
        sc.p('Move data. Transmit this to Opponent:')
        sc.show(move_data)
        game = sc.compute(c1.offchain_compute_game_play(sp.record(game = game, move_data = sp.pack(move_data), sender = me.address)))
        sc.p('Action play')
        action_play = gp.action_play(game_id, game.current, game.state.open_some(), sp.pack(move_data))
        sc.show(action_play)
        sc.p("My play sig. Transmit this to Opponent:")
        my_play_sig = sp.make_signature(me.secret_key, action_play)
        sc.show(my_play_sig)

        opponent_play_sig = sp.signature('edsigtd8mNQ4JLPQTiHVya2HkBC3RKAyHNDxg34YhYktantC4C3ZxSa2MAtb69UzLnwwS793LjJju8gqSZ8EwEDfF1JXF6oMpkR')
        data[move_nb] = (game, action_play, {me.public_key: my_play_sig, opponent.public_key: opponent_play_sig}, sp.pack(move_data))

        sc.h2("ONCHAIN: push last state onchain")
        c1.game_play(
            game_id = game_id,
            new_current = data[move_nb][0].current,
            new_state = data[move_nb][0].state.open_some(),
            move_data = data[move_nb][3],
            signatures = data[move_nb][2]
        ).run(sender = me.address)

        # -- Settle --
        sc.h2("ONCHAIN: Settle")
        c1.game_settle(game_id).run(sender = me.address)

        sc.h2("Resume of my signatures")
        sc.p("New Game Signature")
        sc.show(my_new_game_sig)
        sc.p("Move_nb - Play Signature")
        sc.show({move_nb: d[2][me.public_key] for move_nb, d in data.items()})
