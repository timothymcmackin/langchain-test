# Nim Game, https://en.wikipedia.org/wiki/Nim - Example for illustrative purposes only.

import smartpy as sp

class NimGame(sp.Contract):
    def __init__(self, size, bound = None, winnerIsLast = False):
        self.bound        = bound
        self.winnerIsLast = winnerIsLast
        self.init(deck       = sp.utils.vector(range(1, size + 1)),
                  size       = size,
                  nextPlayer = 1,
                  claimed    = False,
                  winner     = 0)

    @sp.entry_point
    def remove(self, params):
        sp.verify(0 <= params.cell)
        sp.verify(params.cell < self.data.size)
        sp.verify(1 <= params.k)
        if self.bound is not None:
            sp.verify(params.k <= self.bound)
        sp.verify(params.k <= self.data.deck[params.cell])
        self.data.deck[params.cell] = self.data.deck[params.cell] - params.k
        self.data.nextPlayer = 3 - self.data.nextPlayer

    @sp.entry_point
    def claim(self, params):
        sp.verify(sp.sum(self.data.deck.values()) == 0)
        sp.verify(~ self.data.claimed)
        self.data.claimed = True
        if self.winnerIsLast:
            self.data.winner = 3 - self.data.nextPlayer
        else:
            self.data.winner = self.data.nextPlayer
        sp.verify(params.winner == self.data.winner)

# Tests
if "templates" not in __name__:
    @sp.add_test(name = "Nim")
    def test():
        scenario = sp.test_scenario()
        scenario.h1("Nim game")
        # define a contract
        c1 = NimGame(size = 5, bound = 2)
        # show its representation
        scenario.h2("Contract")
        scenario += c1
        scenario.h2("Message execution")
        scenario.h3("A first move")
        c1.remove(cell = 2, k = 1)
        scenario.h3("A second move")
        c1.remove(cell = 2, k = 2)
        scenario.h3("An illegal move")
        c1.remove(cell = 2, k = 1).run(valid = False)
        scenario.h3("Another illegal move")

        c1.claim(winner=1).run(valid = False)
        scenario.h3("A third move")
        c1.remove(cell = 1, k = 2)
        scenario.h3("More moves")
        c1.remove(cell = 0, k = 1)
        c1.remove(cell = 3, k = 1)
        c1.remove(cell = 3, k = 1)
        c1.remove(cell = 3, k = 2)
        c1.remove(cell = 4, k = 1)
        c1.remove(cell = 4, k = 2)
        scenario.h3("A failed attempt to claim")
        c1.claim(winner=1).run(valid = False)
        scenario.h3("A last removal")
        c1.remove(cell = 4, k = 2)
        scenario.h3("And a final claim")
        c1.claim(winner=1)
        scenario.p("The winner is").show(c1.data.winner)

    sp.add_compilation_target("nim", NimGame(size = 5, bound = 2))
