# TicTacToe Factory - Example for illustrative purposes only.

import smartpy as sp

class TicTacToe(sp.Contract):
    def __init__(self, admin):
        self.init(admin = admin, paused = False, boards = sp.big_map(tkey = sp.TString), metaData = {})

    @sp.entry_point
    def build(self, params):
        sp.verify((~ self.data.paused) | (sp.sender == self.data.admin))
        sp.verify(~ self.data.boards.contains(params.game))
        self.data.boards[params.game] = sp.record(
            player1    = params.player1,
            player2    = params.player2,
            nbMoves    = 0,
            winner     = 0,
            draw       = False,
            deck       = sp.utils.matrix([[0, 0, 0], [0, 0, 0], [0, 0, 0]]),
            nextPlayer = 1,
            metaData   = {})

    @sp.entry_point
    def deleteGame(self, params):
        sp.verify(sp.sender == self.data.admin)
        del self.data.boards[params.game]

    @sp.entry_point
    def setPause(self, params):
        sp.verify(sp.sender == self.data.admin)
        self.data.paused = params

    @sp.entry_point
    def setMetaData(self, params):
        sp.verify(sp.sender == self.data.admin)
        sp.set_type(params.name, sp.TString)
        sp.set_type(params.value, sp.TString)
        self.data.metaData[params.name] = params.value

    @sp.entry_point
    def setGameMetaData(self, params):
        game = self.data.boards[params.game]
        sp.verify((sp.sender == self.data.admin) | (sp.sender == game.player1))
        sp.set_type(params.name, sp.TString)
        sp.set_type(params.value, sp.TString)
        game.metaData[params.name] = params.value

    @sp.entry_point
    def play(self, params):
        sp.verify(~ self.data.paused)
        game = self.data.boards[params.game]
        sp.verify((game.winner == 0) & ~game.draw)
        sp.verify((params.i >= 0) & (params.i < 3))
        sp.verify((params.j >= 0) & (params.j < 3))
        sp.verify(params.move == game.nextPlayer)
        sp.verify(game.deck[params.i][params.j] == 0)
        sp.if params.move == 1:
            sp.verify(sp.sender == game.player1)
        sp.else:
            sp.verify(sp.sender == game.player2)
        game.nextPlayer = 3 - game.nextPlayer
        game.deck[params.i][params.j] = params.move
        game.nbMoves += 1
        self.checkLine(game, game.deck[params.i])
        self.checkLine(game, [game.deck[i       ][params.j] for i in range(0, 3)])
        self.checkLine(game, [game.deck[i       ][i       ] for i in range(0, 3)])
        self.checkLine(game, [game.deck[i       ][2 - i   ] for i in range(0, 3)])
        sp.if (game.nbMoves == 9) & (game.winner == 0):
            game.draw = True

    def checkLine(self, game, line):
        with sp.if_ ((line[0] != 0) & (line[0] == line[1]) & (line[0] == line[2])):
            game.winner = line[0]

# Tests
if "templates" not in __name__:
    @sp.add_test(name = "TicTacToeFactory")
    def test():
        # define a contract
        admin = sp.test_account("Admin")
        alice = sp.test_account("Alice")
        bob   = sp.test_account("Robert")

        c1 = TicTacToe(admin.address)

        scenario = sp.test_scenario()
        scenario.h1("Tic-Tac-Toe Games")
        # show its representation
        scenario.h2("A sequence of interactions with a winner")
        scenario += c1
        scenario.h2("Message execution")
        scenario.h3("Building a contract")

        g1 = "game 1"
        c1.build(game = g1, player1 = alice.address, player2 = bob.address)

        scenario.h3("A first move in the center")
        c1.play(game = g1, i = 1, j = 1, move = 1).run(sender = alice)

        g2 = "game 2"
        c1.build(game = g2, player1 = alice.address, player2 = bob.address)
        c1.deleteGame(game = g2).run(sender = admin)

        c1.setMetaData(name = "toto", value = "titi").run(sender = admin)

        c1.setGameMetaData(game = g1, name = "toto", value = "titi").run(sender = alice)
        c1.setGameMetaData(game = g1, name = "toto2", value = "titi2").run(sender = admin)

    sp.add_compilation_target("tictactoeFactory", TicTacToe(admin = sp.address("tz1M9CMEtsXm3QxA7FmMU2Qh7xzsuGXVbcDr")))
