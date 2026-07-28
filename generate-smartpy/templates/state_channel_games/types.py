import smartpy as sp

class BytesModel:
    t_initial_config = sp.TBytes
    t_game_state = sp.TBytes
    t_move_data  = sp.TBytes

class Types:
    def __init__(self, model = BytesModel):
        self.t_initial_config   = model.t_initial_config
        self.t_game_state   = model.t_game_state
        self.t_move_data    = model.t_move_data

        self.t_nonce          = sp.TString
        self.t_model_id       = sp.TBytes
        self.t_token_map      = sp.TMap(sp.TNat, sp.TNat)
        self.t_game_bonds     = sp.TMap(sp.TInt, self.t_token_map)
        self.t_players_addr   = sp.TMap(sp.TInt, sp.TAddress)
        self.t_metadata       = sp.TMap(sp.TString, sp.TBytes)
        self.t_permissions    = sp.TMap(sp.TString, sp.TBytes)

        self.t_transfer       = sp.TRecord(
            sender = sp.TInt,
            receiver = sp.TInt,
            bonds = self.t_token_map
        )

        self.t_outcome        = sp.TVariant(
            game_finished         = sp.TString,
            game_aborted          = sp.TUnit,
            player_inactive       = sp.TInt,
            player_double_played  = sp.TInt
        ).right_comb()

        self.t_proposed_outcome = sp.TVariant(
            game_finished = sp.TString,
            game_aborted  = sp.TUnit
        )

        self.t_settlements  = sp.TMap(self.t_outcome, sp.TList(self.t_transfer))

        ######
        # FA #
        ######

        self.t_tx = sp.TRecord(amount = sp.TNat, to_ = sp.TAddress, token_id = sp.TNat).layout(("to_", ("token_id", "amount")))
        self.t_txs = sp.TList(self.t_tx)
        self.t_fa2_transfer = sp.TList(sp.TRecord(from_ = sp.TAddress, txs = self.t_txs).layout(("from_", "txs")))

        self.t_callback = sp.TRecord(amount = sp.TNat, data = sp.TBytes, receiver = sp.TAddress, sender = sp.TAddress, token_id = sp.TNat).right_comb()
        self.t_on_receive_bonds_data = sp.TRecord(channel_id = sp.TBytes, player_addr = sp.TAddress)

        #########
        # Games #
        #########

        self.t_player = sp.TRecord(addr = sp.TAddress, pk = sp.TKey)

        self.t_constants = sp.TRecord(
            bonds        = self.t_game_bonds,
            channel_id   = sp.TBytes,
            game_nonce   = self.t_nonce,
            model_id     = self.t_model_id,
            play_delay   = sp.TInt,
            players_addr = self.t_players_addr,
            settlements  = self.t_settlements
        ).right_comb()

        self.t_current = sp.TRecord(
            move_nb = sp.TNat,
            player  = sp.TInt,
            outcome = sp.TOption(sp.TVariant(final = self.t_outcome, pending = self.t_outcome)),
        ).right_comb()

        self.t_timeouts = sp.TMap(sp.TInt, sp.TTimestamp)

        self.t_game = sp.TRecord(
            addr_players    = sp.TMap(sp.TAddress, sp.TInt),
            constants       = self.t_constants,
            current         = self.t_current,
            initial_config  = self.t_initial_config,
            permissions     = self.t_permissions,
            state           = sp.TOption(self.t_game_state),
            settled         = sp.TBool,
            timeouts        = self.t_timeouts,
        ).right_comb()

        ##########
        # Models #
        ##########

        self.t_model_outcomes   = sp.TList(sp.TString)

        self.t_apply_input = sp.TRecord(
            move_data = self.t_move_data,
            move_nb   = sp.TNat,
            player    = sp.TInt,
            state     = self.t_game_state,
        ).right_comb()

        self.t_apply_result = sp.TPair(
            self.t_game_state,
            sp.TOption(sp.TString),
        )

        self.t_init   = sp.TLambda(self.t_initial_config, self.t_game_state)
        self.t_apply_ = sp.TLambda(self.t_apply_input, self.t_apply_result)

        self.t_model = sp.TRecord(
            init     = self.t_init,
            apply_   = self.t_apply_,
            outcomes = self.t_model_outcomes,
        ).right_comb()

        self.t_model_lambdas = sp.TRecord(
            apply_   = self.t_apply_,
            init     = self.t_init,
            outcomes = self.t_model_outcomes,
        ).right_comb()

        self.t_model_wrap = sp.TRecord(
            model = sp.TBytes,
            metadata = sp.TMap(sp.TString, sp.TBytes),
            permissions = sp.TMap(sp.TString, sp.TBytes),
            rewards = self.t_txs
        ).right_comb()

        ############
        # Channels #
        ############

        self.t_channel_player = sp.TRecord(
            bonds    = self.t_token_map,
            pk       = sp.TKey,
            withdraw = sp.TOption(
                sp.TRecord(
                    challenge        = sp.TSet(sp.TBytes),
                    challenge_tokens = sp.TMap(sp.TNat, sp.TInt),
                    timeout          = sp.TTimestamp,
                    tokens           = self.t_token_map,
                )
            ),
            withdraw_id = sp.TNat
        ).right_comb()

        self.t_channel = sp.TRecord(
            closed   = sp.TBool,
            nonce    = self.t_nonce,
            players  = sp.TMap(sp.TAddress, self.t_channel_player),
            withdraw_delay = sp.TInt,
        ).right_comb()