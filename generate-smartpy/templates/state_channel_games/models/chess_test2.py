import smartpy as sp

cl = sp.io.import_template("chess_logic.py")
chess = sp.io.import_template("state_channel_games/models/chess.py")

# Tests
if "templates" not in __name__:
    GameTester = sp.io.import_template("state_channel_games/game_tester.py")

    player1 = sp.test_account('player1')
    player2 = sp.test_account('player2')
    p1 = sp.record(addr = player1.address, pk = player1.public_key)
    p2 = sp.record(addr = player2.address, pk = player2.public_key)

    class GameTesterChess(GameTester.GameTester):
        @sp.offchain_view(pure = True)
        def build_fen(self):
            sp.result(
                cl.Lambda_ready.build_fen(self.data.state.board_state)
            )

    def play(f, t, promotion = sp.none, claim_repeat = sp.none):
        return sp.variant("play", sp.record(f = f, t = t, promotion = promotion, claim_repeat = claim_repeat))

    @sp.add_test(name = "Chess - Promotion")
    def test():
        scenario = sp.test_scenario()
        c1 = GameTesterChess(chess.Chess(), p1, p2)
        scenario += c1
        c1.play(move_data = play(f = sp.record(i = 1, j = 6), t = sp.record(i = 3, j = 6)), move_nb = 0).run(sender = player1)
        c1.play(move_data = play(f = sp.record(i = 6, j = 1), t = sp.record(i = 4, j = 1)), move_nb = 1).run(sender = player2)
        c1.play(move_data = play(f = sp.record(i = 3, j = 6), t = sp.record(i = 4, j = 6)), move_nb = 2).run(sender = player1)
        c1.play(move_data = play(f = sp.record(i = 4, j = 1), t = sp.record(i = 3, j = 1)), move_nb = 3).run(sender = player2)
        c1.play(move_data = play(f = sp.record(i = 4, j = 6), t = sp.record(i = 5, j = 6)), move_nb = 4).run(sender = player1)
        c1.play(move_data = play(f = sp.record(i = 3, j = 1), t = sp.record(i = 2, j = 1)), move_nb = 5).run(sender = player2)
        c1.play(move_data = play(f = sp.record(i = 5, j = 6), t = sp.record(i = 6, j = 7)), move_nb = 6).run(sender = player1)
        c1.play(move_data = play(f = sp.record(i = 2, j = 1), t = sp.record(i = 1, j = 0)), move_nb = 7).run(sender = player2)
        c1.play(move_data = play(f = sp.record(i = 6, j = 7), t = sp.record(i = 7, j = 6), promotion = sp.some(5)), move_nb = 8).run(sender = player1)
        c1.play(move_data = play(f = sp.record(i = 1, j = 0), t = sp.record(i = 0, j = 1), promotion = sp.some(3)), move_nb = 9).run(sender = player2)
        scenario.show(c1.build_fen())
        scenario.verify(c1.build_fen() == 'rnbqkbQr/p1ppppp1/8/8/8/8/1PPPPP1P/RnBQKBNR w KQkq - 0 6')
