# Multiple Nim Games - Example for illustrative purposes only.

# Instead of defining a single NimGame per contract,
# we define a contract for multiple games.

import smartpy as sp

def rangeMap(a, b):
   r = sp.local('rangeMap', {})
   sp.for i in sp.range(a, b):
       r.value[i - a] = i
   return r.value

class NimMultipleGame(sp.Contract):
    def __init__(self):
        self.init(games = {}, nbGames = 0)

    @sp.entry_point
    def build(self, params):
        size   = params.size
        bound  = params.bound
        lastWins = False
        game = sp.record(deck       = rangeMap(1, size + 1),
                         size       = size,
                         nextPlayer = 1,
                         claimed    = False,
                         winner     = 0,
                         bound      = bound,
                         lastWins   = lastWins
                        )
        self.data.games[self.data.nbGames] = game
        self.data.nbGames += 1

    @sp.entry_point
    def remove(self, params):
        gameId = params.gameId
        game = self.data.games[gameId]
        cell = params.cell
        k = params.k
        sp.verify(0 <= cell)
        sp.verify(cell < game.size)
        sp.verify(1 <= k)
        sp.verify(k <= game.bound)
        sp.verify(k <= game.deck[cell])
        game.deck[cell] = game.deck[cell] - k
        game.nextPlayer = 3 - game.nextPlayer

    @sp.entry_point
    def claim(self, params):
        gameId = params.gameId
        game = self.data.games[gameId]
        sp.verify(sp.sum(game.deck.values()) == 0)
        game.claimed = True
        sp.if game.lastWins:
            game.winner = 3 - game.nextPlayer
        sp.else:
            game.winner = game.nextPlayer

# Tests
@sp.add_test(name = "NimGames")
def test():
    # define a contract
    c1 = NimMultipleGame()
    # show its representation
    scenario = sp.test_scenario()
    scenario.h1("Nim games")
    scenario.h2("Contract")
    scenario += c1
    scenario.h2("First: define a few games with build")
    for size in range(5, 8):
        result  = c1.build(size = size, bound = 2)
        scenario += result
    scenario.h2("Message execution")
    scenario.h3("A first move")
    result  = c1.remove(gameId = 0, cell = 2, k = 1)
    scenario += result
    scenario.h3("A second move")
    result  = c1.remove(gameId = 0, cell = 2, k = 2)
    scenario += result
    scenario.h3("An illegal move")

    result  = c1.remove(gameId = 0, cell = 2, k = 1).run(valid = False)
    scenario += result
    scenario.h3("Another illegal move")
    result  = c1.claim(gameId=1).run(valid = False)
    scenario += result
    scenario.h3("A third move")
    result  = c1.remove(gameId = 0, cell = 1, k = 2)
    scenario += result
    scenario.h3("More moves")
    c1.remove(gameId = 0, cell = 0, k = 1)
    c1.remove(gameId = 0, cell = 3, k = 1)
    c1.remove(gameId = 0, cell = 3, k = 1)
    c1.remove(gameId = 0, cell = 3, k = 2)
    c1.remove(gameId = 0, cell = 4, k = 1)
    c1.remove(gameId = 0, cell = 4, k = 2)
    scenario.h3("A failed attempt to claim")
    c1.claim(gameId = 0).run(valid = False)
    scenario.h3("A last removal")
    c1.remove(gameId = 0, cell = 4, k = 2)
    scenario.h3("And a final claim")
    c1.claim(gameId = 0)

sp.add_compilation_target("nim", NimMultipleGame())
