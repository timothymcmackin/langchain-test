import smartpy as sp

cl = sp.io.import_template("chess_logic.py")

class Chess:
    def __init__(self):
        self.name = "Chess"
        self.t_initial_config  = sp.TUnit
        self.t_game_state = sp.TRecord(
            board_state = cl.Types.t_board_state,
            status = sp.TVariant(
                play = sp.TUnit,
                force_play = sp.TUnit,
                claim_stalemate = sp.TUnit
            )
        )
        self.t_move_data  = sp.TVariant(
            play = cl.Types.t_move,
            claim_stalemate = sp.TUnit,
            answer_stalemate = sp.TVariant(
                accept = sp.TUnit,
                answer = cl.Types.t_move,
            ),
        )
        self.t_outcome    = ["player_1_won", "player_2_won", "draw"]

    def init(self, params):
        sp.set_type(params, self.t_initial_config)
        sp.result(sp.set_type_expr(sp.record(
            board_state = cl.initial_board_state(),
            status = sp.variant("play", sp.unit)
        ), self.t_game_state))

    # Standard
    def apply_(self, move_data, move_nb, player, state):
        move_piece = sp.build_lambda(self.move_piece)
        get_movable_to = sp.build_lambda(self.get_movable_to)

        with move_data.match_cases() as arg:
            with arg.match("play") as move:
                sp.verify(
                    state.status.is_variant("play") |
                    state.status.is_variant("force_play"),
                    message = "Opponent claimed stalemate, you must answer it"
                )
                sp.result(self.play(move, state.board_state, move_piece, get_movable_to))
            with arg.match("claim_stalemate"):
                sp.verify(state.status.is_variant("play"))
                new_state = sp.record(board_state = state.board_state, status = sp.variant("claim_stalemate", sp.unit))
                sp.result(self.claim_stalemate(state))
            with arg.match("answer_stalemate") as answer_stalemate:
                sp.verify(state.status.is_variant("claim_stalemate"))
                sp.result(self.answer_stalemate(answer_stalemate, state, move_piece, get_movable_to))

    # Entry points

    def play(self, move, board_state, move_piece, get_movable_to):
        board_state, is_draw = sp.match_pair(
            move_piece(
                sp.record(
                    board_state = board_state,
                    get_movable_to = get_movable_to,
                    move = move,
                )
            )
        )
        state = sp.compute(sp.record(board_state = board_state, status = sp.variant("play", sp.unit)))
        state.board_state.nextPlayer *= -1
        outcome = sp.local("outcome", sp.none)
        with sp.if_(is_draw):
            outcome.value = sp.some(sp.bounded("draw"))
        with sp.else_():
            with sp.if_(cl.is_checkmate(board_state, get_movable_to)):
                outcome.value = sp.eif(board_state.nextPlayer == 1, sp.some(sp.bounded("player_2_won")), sp.some(sp.bounded("player_1_won")))

        return (state, outcome.value)

    def claim_stalemate(self, state):
        return (
            sp.record(board_state = state.board_state, status = sp.variant("claim_stalemate", sp.unit)),
            sp.none
        )

    def answer_stalemate(self, answer, state, move_piece, get_movable_to):
        outcome = sp.local("outcome", sp.none)
        state = sp.local("state", state).value

        with answer.match_cases() as arg:
            with arg.match("accept"):
                outcome.value = sp.some(sp.bounded("draw"))
            with arg.match("answer") as refuse_move:
                state.board_state.nextPlayer *= -1
                # Verify if the refuse move is valid
                move_piece(sp.record(move = refuse_move, get_movable_to = get_movable_to))
                state.board_state.nextPlayer *= -1
                state.status = sp.variant("force_play", sp.unit)

        return (state, outcome.value)

    # Lambdas

    def get_movable_to(self, params):
        sp.result(cl.Lambda_ready.get_movable_to(params))

    def move_piece(self, params):
        board_state, is_draw = cl.Lambda_ready.move_piece(params.board_state, params.move, params.get_movable_to)
        sp.result((board_state, is_draw))
