import smartpy as sp

types = sp.io.import_template("state_channel_games/types.py").Types()

def _wrap_apply(model):
    def apply_(params):
        move_data = sp.compute(sp.unpack(params.move_data, model.t_move_data).open_some("move_unwrap_err"))
        move_nb   = sp.set_type_expr(params.move_nb, sp.TNat)
        player    = sp.set_type_expr(params.player, sp.TInt)
        state     = sp.compute(sp.unpack(params.state, model.t_game_state).open_some("state_unwrap_err"))
        r = sp.bind_block()
        with r:
            model.apply_(move_data, move_nb, player, state)

        new_state, outcome = sp.match_pair(r.value)
        sp.set_type(outcome, sp.TOption(sp.TBounded(model.t_outcome)))
        with outcome.match_cases() as arg:
            with arg.match("Some") as b_outcome:
                sp.result(sp.pair(
                    sp.pack(new_state),
                    sp.some(sp.unbounded(b_outcome)),
                ))
            with arg.match("None"):
                sp.result(sp.pair(
                    sp.pack(new_state),
                    sp.none,
                ))
    return apply_

def _wrap_init_state(model):
    def init_state(params):
        params = sp.unpack(params, model.t_initial_config).open_some("params_unwrap_err")
        r = sp.bind_block()
        with r:
            model.init(params)
        sp.result(sp.pack(sp.set_type_expr(r.value, model.t_game_state)))
    return init_state

def model_wrap(model, permissions = {}, rewards = []):
    model_record = sp.record(
        init   = sp.build_lambda(_wrap_init_state(model)),
        apply_ = sp.build_lambda(_wrap_apply(model)),
        outcomes = model.t_outcome
    )
    model_record = sp.set_type_expr(model_record, types.t_model_lambdas)
    record = sp.record(
        model = sp.pack(model_record),
        metadata = sp.map({"name": sp.utils.bytes_of_string(model.name)}, tkey = sp.TString, tvalue = sp.TBytes),
        permissions = permissions,
        rewards = rewards
    )
    return sp.set_type_expr(record, types.t_model_wrap)

def model_id(model_wrapped):
    return sp.blake2b(model_wrapped.model)
