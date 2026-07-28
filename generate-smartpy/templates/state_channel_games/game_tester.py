import smartpy as sp

class GameTester(sp.Contract):
    def __init__(self, model, player1, player2, init_params = sp.unit):

        self.model = model
        self.types = sp.io.import_template("state_channel_games/types.py").Types(model)

        self.init(
            current = sp.record(
                player  = 1,
                move_nb = 0,
                outcome = sp.set_type_expr(sp.none, sp.TOption(sp.TString)),
            ),
            constants = sp.record(
                player1        = player1,
                player2        = player2,
                model_id       = sp.bytes("0x"),
                channel_id     = sp.bytes("0x01"),
                game_nonce     = "",
                winner         = sp.tez(0),
                loser          = sp.tez(0),
            ),
            state  = sp.set_type_expr(sp.build_lambda(self.model.init)(init_params), model.t_game_state),
            apply_ = sp.build_lambda(lambda p: self.model.apply_(p.move_data, p.move_nb, p.player, p.state)),
        )

    @sp.entry_point
    def play(self, move_nb, move_data):
        sp.set_type(move_nb, sp.TNat)
        sp.set_type(move_data, self.model.t_move_data)

        with sp.if_(self.data.current.player == 1):
            sp.verify(sp.sender == self.data.constants.player1.addr, message="Game_WrongPlayer")
        with sp.else_():
            sp.verify(sp.sender == self.data.constants.player2.addr, message="Game_WrongPlayer")
        sp.verify(self.data.current.outcome.is_none())
        sp.verify(self.data.current.move_nb == move_nb)

        apply_result = sp.compute(
            self.data.apply_(
                sp.record(
                    move_data = move_data,
                    move_nb   = self.data.current.move_nb,
                    player    = self.data.current.player,
                    state     = self.data.state
                )
            )
        )
        new_state, outcome = sp.match_pair(apply_result)
        sp.set_type(outcome, sp.TOption(sp.TBounded(self.model.t_outcome)))
        with outcome.match_cases() as arg:
            with arg.match("Some") as b_outcome:
                self.data.current.outcome = sp.some(sp.unbounded(b_outcome))
            with arg.match("None"):
                self.data.current.outcome = sp.none

        self.data.current.move_nb    += 1
        self.data.current.player      = 3 - self.data.current.player
        self.data.state               = new_state

if "templates" not in __name__:
    Tictactoe  = sp.io.import_template("state_channel_games/models/tictactoe.py")
    player1_record = sp.record(addr = sp.address('tz1_PLAYER1_ADDRESS'), pk = sp.key('PLAYER1_KEY'))
    player2_record = sp.record(addr = sp.address('tz1_PLAYER2_ADDRESS'), pk = sp.key('PLAYER2_KEY'))
    sp.add_compilation_target("tictactoeGameTester", GameTester(Tictactoe.Tictactoe(), player1_record, player2_record))
