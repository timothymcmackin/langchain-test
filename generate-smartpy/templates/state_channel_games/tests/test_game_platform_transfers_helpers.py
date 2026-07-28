import smartpy as sp

gp         = sp.io.import_template("state_channel_games/game_platform.py")
lgr        = sp.io.import_template("state_channel_games/ledger.py")
Transfer   = sp.io.import_template("state_channel_games/models/transfer.py")
model_wrap = sp.io.import_template("state_channel_games/model_wrap.py")
types      = sp.io.import_template("state_channel_games/types.py").Types()
FA2        = sp.io.import_template("FA2.py")


def transfer_settlements(
        p1_to_p2 = {}, p2_to_p1 = {},
        p1_to_p1 = {}, p2_to_p2 = {},
        p0_to_p1 = {}, p0_to_p2 = {}
    ):
    transfers = []
    if len(p1_to_p2) > 0:
        transfers.append(gp.transfer(1, 2, p1_to_p2))
    if len(p2_to_p1) > 0:
        transfers.append(gp.transfer(2, 1, p2_to_p1))
    if len(p1_to_p1) > 0:
        transfers.append(gp.transfer(1, 1, p1_to_p1))
    if len(p2_to_p2) > 0:
        transfers.append(gp.transfer(2, 2, p2_to_p2))
    if len(p0_to_p1) > 0:
        transfers.append(gp.transfer(0, 1, p0_to_p1))
    if len(p0_to_p2) > 0:
        transfers.append(gp.transfer(0, 2, p0_to_p2))
    settlements = sp.map({
        sp.variant("player_double_played", 1)     : transfers,
        sp.variant("player_double_played", 2)     : transfers,
        sp.variant("player_inactive",      1)     : transfers,
        sp.variant("player_inactive",      2)     : transfers,
        sp.variant("game_finished", "transferred"): transfers,
        sp.variant("game_aborted", sp.unit)       : []
    })
    bonds = {1: p1_to_p2, 2: p2_to_p1}
    bonds = sp.set_type_expr(bonds, gp.types.t_game_bonds)
    settlements = sp.set_type_expr(settlements, gp.types.t_settlements)
    return settlements, bonds

def make_signatures(p1, p2, x):
    sig1 = sp.make_signature(p1.secret_key, x)
    sig2 = sp.make_signature(p2.secret_key, x)
    return sp.map({p1.public_key: sig1, p2.public_key: sig2})

wXTZ_metadata = FA2.FA2.make_metadata(
    name     = "Wrapped XTZ",
    symbol   = "WXTZ",
    decimals = 6,
)

wXTZ_permissions = lgr.build_token_permissions({
        "type"            : "NATIVE",
        "mint_cost"       : sp.mutez(1),
        "mint_permissions": sp.variant("allow_everyone", sp.unit)
})

free_metadata = FA2.FA2.make_metadata(
    name     = "Free tokens",
    symbol   = "FREE",
    decimals = 6,
)

free_permissions = lgr.build_token_permissions({
    "type"            : "NATIVE",
    "mint_cost"       : sp.mutez(0),
    "mint_permissions": sp.variant("allow_everyone", sp.unit)
})

reputation_metadata = FA2.FA2.make_metadata(
    name     = "Reputation",
    symbol   = "R",
    decimals = 0,
)

class DummyFA2(FA2.FA2, FA2.FA2_mint):
    @sp.private_lambda(with_storage="read-write", with_operations=True, wrap_call=True)
    def _transfer(self, params):
        super().transfer.f(self, params)

    @sp.entry_point
    def transfer(self, params):
        self._transfer(params)

    @sp.entry_point
    def transfer_and_call(self, batchs):
        sp.set_type(batchs, lgr.t_transfer_and_call)

        # Transfer
        with sp.for_('batchs', batchs) as batch:
            with sp.for_('transaction', batch.txs) as tx:
                self._transfer([
                    sp.record(
                        from_=batch.from_,
                        txs=[
                            sp.record(
                                to_=tx.to_,
                                token_id=tx.token_id,
                                amount=tx.amount
                            )
                        ]
                    )
                ])

                # Callback
                callback = sp.contract(types.t_callback, tx.callback).open_some("FA2_WRONG_CALLBACK_INTERFACE")
                args = sp.record(
                    amount   = tx.amount,
                    data     = tx.data,
                    sender   = batch.from_,
                    receiver = tx.to_,
                    token_id = tx.token_id,
                )
                sp.transfer(args, sp.tez(0), callback)
