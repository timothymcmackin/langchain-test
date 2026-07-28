import smartpy as sp

class Nim:
    def __init__(self):
        self.name = "Nim"
        self.t_move_data = sp.TRecord(
            heapId = sp.TInt,
            size = sp.TInt)
        self.t_initial_config = sp.TRecord(
            numberOfHeaps = sp.TInt,
            bound         = sp.TOption(sp.TInt),
            misere        = sp.TBool)
        self.t_game_state = sp.TRecord(
            heaps  = sp.TMap(sp.TInt, sp.TInt),
            bound  = sp.TOption(sp.TInt),
            misere = sp.TBool)
        self.t_outcome = ["player_1_won", "player_2_won"]

    def init(self, config):
        heaps = sp.local('heaps', {})
        with sp.for_("i", sp.range(0, config.numberOfHeaps)) as i:
            heaps.value[i] = 3 + i
        sp.result(sp.record(heaps = heaps.value, bound = config.bound, misere = config.misere))

    def apply_(self, move_data, move_nb, player, state):
        s  = sp.local('s', state)

        sp.verify(s.value.heaps.contains(move_data.heapId), "unknown heap")
        heap = sp.local('heap', s.value.heaps[move_data.heapId])

        sp.verify(s.value.bound.is_none() | (move_data.size <= s.value.bound.open_some()), "bound exceeded")
        sp.verify(move_data.size >= 1, "must take at least one")
        sp.verify(move_data.size <= heap.value, "heap too small")
        s.value.heaps[move_data.heapId] -= move_data.size

        outcome = sp.local('outcome', sp.some(sp.bounded("player_1_won")))

        with sp.if_(s.value.misere == (player == 1)):
            outcome.value = sp.some(sp.bounded("player_2_won"))

        with sp.for_("x", s.value.heaps.values()) as x:
            with sp.if_(x > 0):
                outcome.value = sp.none

        sp.result(sp.pair(s.value, outcome.value))

# Tests
if "templates" not in __name__:
    GameTester = sp.io.import_template("state_channel_games/game_tester.py")

    player1 = sp.test_account('player1')
    player2 = sp.test_account('player2')
    p1 = sp.record(addr = player1.address, pk = player1.public_key)
    p2 = sp.record(addr = player2.address, pk = player2.public_key)

    @sp.add_test(name="Nim - 1")
    def test():
        scenario = sp.test_scenario()
        scenario.h1("Nim")
        scenario.h2("Contract")

        params = sp.record(
            numberOfHeaps = 5,
            bound         = sp.none,
            misere        = True)

        c1 = GameTester.GameTester(Nim(), p1, p2, params)
        scenario += c1
        scenario.h2("A sequence of interactions with a winner")
        c1.play(move_nb = 0, move_data = sp.record(heapId = 0, size = 3)).run(sender = player1)
        c1.play(move_nb = 1, move_data = sp.record(heapId = 1, size = 4)).run(sender = player2)
        c1.play(move_nb = 2, move_data = sp.record(heapId = 2, size = 5)).run(sender = player1)
        c1.play(move_nb = 3, move_data = sp.record(heapId = 3, size = 6)).run(sender = player2)
        c1.play(move_nb = 4, move_data = sp.record(heapId = 4, size = 7)).run(sender = player1)
        scenario.verify(c1.data.current.outcome == sp.some("player_2_won"))