import smartpy as sp

class Transfer:
    def __init__(self):
        self.name = "Transfer"
        self.t_initial_config  = sp.TUnit
        self.t_game_state = sp.TUnit
        self.t_move_data  = sp.TUnit
        self.t_outcome    = ["transferred"]

    def apply_(self, move_data, move_nb, player, state):
        sp.result( (sp.unit, sp.some(sp.bounded("transferred"))) )

    def init(self, params):
        sp.result(sp.unit)

# Tests
if "templates" not in __name__:
    GameTester = sp.io.import_template("state_channel_games/game_tester.py")

    player1 = sp.test_account('player1')
    player2 = sp.test_account('player2')
    p1 = sp.record(addr = player1.address, pk = player1.public_key)
    p2 = sp.record(addr = player2.address, pk = player2.public_key)

    @sp.add_test(name="Transfer")
    def test():
        scenario = sp.test_scenario()
        c1 = GameTester.GameTester(Transfer(), p1, p2)
        scenario += c1
        c1.play(move_data = (), move_nb = 0).run(sender = player1)
        scenario.verify(c1.data.current.outcome == sp.some("transferred"))
