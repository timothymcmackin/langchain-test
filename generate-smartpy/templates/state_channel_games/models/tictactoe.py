import smartpy as sp

class Tictactoe:
    def __init__(self):
        self.name = "Tictactoe"
        self.t_initial_config     = sp.TUnit
        self.t_game_state     = sp.TMap(sp.TInt, sp.TMap(sp.TInt, sp.TInt))
        self.t_move_data      = sp.TRecord(i=sp.TInt, j=sp.TInt)
        self.t_outcome        = ["draw", "player_1_won", "player_2_won"]

    def _checkLine(self, line, outcome):
        with sp.if_(~(line[0] == 0) & (line[0] == line[1]) & (line[0] == line[2])):
            with sp.if_(line[0] == 1):
                outcome.value = sp.some(sp.bounded("player_1_won"))
            with sp.else_():
                outcome.value = sp.some(sp.bounded("player_2_won"))

    def apply_(self, move_data, move_nb, player, state):
        deck = sp.local('deck', state)
        sp.verify((move_data.i >= 0) & (move_data.i < 3),    message = "move out of grid")
        sp.verify((move_data.j >= 0) & (move_data.j < 3),    message = "move out of grid")
        sp.verify(deck.value[move_data.i][move_data.j] == 0, message = "move on a non empty cell")

        outcome = sp.local('outcome', sp.none)

        deck.value[move_data.i][move_data.j] = player

        # Check win
        # Line
        self._checkLine(deck.value[move_data.i], outcome)
        # Column
        self._checkLine([deck.value[i][move_data.j] for i in range(0, 3)], outcome)
        # Diagonal Top Left to Bottom Right
        self._checkLine([deck.value[i][i] for i in range(0, 3)], outcome)
        # Diagonal Top right to Bottom Left
        self._checkLine([deck.value[i][2 - i] for i in range(0, 3)], outcome)

        # Check draw
        with sp.if_((move_nb == 8) & (~outcome.value.is_some())):
            outcome.value = sp.some(sp.bounded("draw"))

        sp.result(sp.pair(
            deck.value,
            outcome.value,
        ))

    def init(self, params):
        sp.result(sp.utils.matrix([[0, 0, 0], [0, 0, 0], [0, 0, 0]]))

# Tests
if "templates" not in __name__:
    GameTester = sp.io.import_template("state_channel_games/game_tester.py")

    player1 = sp.test_account('player1')
    player2 = sp.test_account('player2')
    p1 = sp.record(addr = player1.address, pk = player1.public_key)
    p2= sp.record(addr = player2.address, pk = player2.public_key)

    @sp.add_test(name="TicTacToe - Win")
    def test():
        scenario = sp.test_scenario()
        scenario.h1("Tic-Tac-Toe - Win")
        scenario.h2("Contract")
        c1 = GameTester.GameTester(Tictactoe(), p1, p2)
        scenario += c1
        scenario.h2("A sequence of interactions with a winner")
        c1.play(move_data = sp.record(i = 1, j = 1), move_nb = 0).run(sender = player1)
        c1.play(move_data = sp.record(i = 1, j = 2), move_nb = 1).run(sender = player2)
        c1.play(move_data = sp.record(i = 2, j = 1), move_nb = 2).run(sender = player1)
        c1.play(move_data = sp.record(i = 2, j = 2), move_nb = 3).run(sender = player2)
        c1.play(move_data = sp.record(i = 0, j = 1), move_nb = 4).run(sender = player1)
        scenario.p("Player1 has won")

    @sp.add_test(name="TicTacToe - Draw")
    def test():
        scenario = sp.test_scenario()
        scenario.h1("Tic-Tac-Toe - Win")
        scenario.h2("Contract")
        c1 = GameTester.GameTester(Tictactoe(), p1, p2)
        scenario += c1
        scenario.h2("A sequence of interactions with a draw")
        c1.play(move_data = sp.record(i = 1, j = 1), move_nb = 0).run(sender = player1)
        c1.play(move_data = sp.record(i = 1, j = 2), move_nb = 1).run(sender = player2)
        c1.play(move_data = sp.record(i = 2, j = 1), move_nb = 2).run(sender = player1)
        c1.play(move_data = sp.record(i = 2, j = 2), move_nb = 3).run(sender = player2)
        c1.play(move_data = sp.record(i = 0, j = 0), move_nb = 4).run(sender = player1)
        c1.play(move_data = sp.record(i = 0, j = 1), move_nb = 5).run(sender = player2)
        c1.play(move_data = sp.record(i = 0, j = 2), move_nb = 6).run(sender = player1)
        c1.play(move_data = sp.record(i = 2, j = 0), move_nb = 7).run(sender = player2)
        c1.play(move_data = sp.record(i = 1, j = 0), move_nb = 8).run(sender = player1)
        scenario.verify(c1.data.current.outcome == sp.some("draw"))

    @sp.add_test(name="TicTacToe - Errors")
    def test():
        scenario = sp.test_scenario()
        scenario.h1("Tic-Tac-Toe - Errors tests")
        scenario.h2("Contract")
        c1 = GameTester.GameTester(Tictactoe(), p1, p2)
        scenario += c1
        scenario.h3("A first move in the center")
        c1.play(move_data = sp.record(i = 1, j = 1), move_nb = 0).run(sender = player1)
        scenario.h3("Move out of grid")
        c1.play(move_data = sp.record(i = 5, j = 1), move_nb = 1).run(sender = player2, valid = False)
        # scenario.verify(c1.data.error.open_some().error_messages == "move out of grid")
        scenario.h3("Move on an non empty cell")
        c1.play(move_data = sp.record(i = 1, j = 1), move_nb = 1).run(sender = player2, valid = False)
        # scenario.verify(c1.data.error.open_some().error_messages == "move on a non empty cell")
        scenario.h3("Forbidden player")
        c1.play(move_data = sp.record(i = 1, j = 2), move_nb = 1).run(sender = player1, valid = False)
        scenario.h3("A second move")
        c1.play(move_data = sp.record(i = 1, j = 2), move_nb = 1).run(sender = player2)
        scenario.h3("Other moves")
        c1.play(move_data = sp.record(i = 2, j = 1), move_nb = 2).run(sender = player1)
        c1.play(move_data = sp.record(i = 2, j = 2), move_nb = 3).run(sender = player2)
        scenario.verify(c1.data.current.outcome.is_none())
        c1.play(move_data = sp.record(i = 0, j = 1), move_nb = 4).run(sender = player1)
        scenario.verify(c1.data.current.outcome == sp.some("player_1_won"))
        scenario.p("Player1 has won")
        scenario.h3("Move after the end")
        c1.play(move_data = sp.record(i = 0, j = 0), move_nb = 5).run(sender = player2, valid = False)