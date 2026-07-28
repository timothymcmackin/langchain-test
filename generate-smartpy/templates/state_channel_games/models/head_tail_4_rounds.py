import smartpy as sp

class HeadTail:
    def __init__(self):
        self.name = "Head and Tail"
        self.t_initial_config = sp.TUnit
        self.t_game_state = sp.TRecord(hash1 = sp.TOption(sp.TBytes), revealed1 = sp.TOption(sp.TNat), hash2 = sp.TOption(sp.TBytes), revealed2 = sp.TOption(sp.TNat))
        self.t_move_data  = sp.TVariant(hash = sp.TBytes, revealed = sp.TNat)
        self.t_outcome    = ["player_1_won", "player_2_won"]

    def result(self, state, outcome):
        res = state.value.revealed1.open_some() +  state.value.revealed2.open_some()
        with sp.if_(res % 2 == 0):
            outcome.value = sp.some(sp.bounded("player_1_won"))
        with sp.else_():
            outcome.value = sp.some(sp.bounded("player_2_won"))

    def apply_(self, move_data, move_nb, player, state):
        state = sp.local('state', state)
        outcome = sp.local('outcome', sp.none)
        with sp.if_(player == 1):
            with sp.if_(state.value.hash1.is_none()):
                state.value.hash1 = sp.some(move_data.open_variant("hash"))
            with sp.else_():
                revealed1 = sp.compute(move_data.open_variant("revealed"))
                sp.verify(sp.blake2b(sp.pack(revealed1)) == state.value.hash1.open_some(), "Invalid Secret")
                state.value.revealed1 = sp.some(revealed1)
        with sp.if_(player == 2):
            with sp.if_(state.value.hash2.is_none()):
                state.value.hash2 = sp.some(move_data.open_variant("hash"))
            with sp.else_():
                revealed2 = sp.compute(move_data.open_variant("revealed"))
                sp.verify(sp.blake2b(sp.pack(revealed2)) == state.value.hash2.open_some(), "Invalid Secret")
                state.value.revealed2 = sp.some(revealed2)
                self.result(state, outcome)

        sp.result(
            sp.pair(
                state.value,
                outcome.value,
            )
        )

    def init(self, params):
        sp.result(
            sp.record(
                hash1=sp.none,
                hash2=sp.none,
                revealed1=sp.none,
                revealed2=sp.none,
            )
        )

# Tests
if "templates" not in __name__:
    GameTester = sp.io.import_template("state_channel_games/game_tester.py")

    player1 = sp.test_account('player1')
    player2 = sp.test_account('player2')
    p1 = sp.record(addr = player1.address, pk = player1.public_key)
    p2 = sp.record(addr = player2.address, pk = player2.public_key)

    @sp.add_test(name="HeadTail - 1")
    def test():
        scenario = sp.test_scenario()
        scenario.h1("HeadTail")
        scenario.h2("Contract")

        secret1 = 1234
        secret2 = 4568
        hash1 = sp.resolve(sp.blake2b(sp.pack(secret1)))
        hash2 = sp.resolve(sp.blake2b(sp.pack(secret2)))

        c1 = GameTester.GameTester(HeadTail(), p1, p2, sp.unit)
        scenario += c1
        scenario.h2("A sequence of interactions with a winner")
        c1.play(move_data = sp.variant("hash", hash1),    move_nb = 0).run(sender = player1)
        c1.play(move_data = sp.variant("hash", hash2),  move_nb = 1).run(sender = player2)
        c1.play(move_data = sp.variant("revealed", 42),   move_nb = 2).run(sender = player1, valid=False)
        c1.play(move_data = sp.variant("revealed", secret1), move_nb = 2).run(sender = player1)
        c1.play(move_data = sp.variant("revealed", 65421), move_nb = 3).run(sender = player2, valid = False)
        c1.play(move_data = sp.variant("revealed", secret2), move_nb = 3).run(sender = player2)
        scenario.verify(c1.data.current.outcome == sp.some("player_1_won"))

    @sp.add_test(name="HeadTail - 2")
    def test():
        scenario = sp.test_scenario()
        scenario.h1("HeadTail")
        scenario.h2("Contract")

        secret1 = 1234
        secret2 = 4567
        hash1 = sp.resolve(sp.blake2b(sp.pack(secret1)))
        hash2 = sp.resolve(sp.blake2b(sp.pack(secret2)))

        c1 = GameTester.GameTester(HeadTail(), p1, p2, sp.unit)
        scenario += c1
        scenario.h2("A sequence of interactions with a winner")
        c1.play(move_data = sp.variant("hash", hash1),    move_nb = 0).run(sender = player1)
        c1.play(move_data = sp.variant("hash", hash2),    move_nb = 1).run(sender = player2)
        c1.play(move_data = sp.variant("revealed", secret1), move_nb = 2).run(sender = player1)
        c1.play(move_data = sp.variant("revealed", secret2), move_nb = 3).run(sender = player2)
        scenario.verify(c1.data.current.outcome == sp.some("player_2_won"))