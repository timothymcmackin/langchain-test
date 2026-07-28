# State channel game platform (work in progress)
# Version Alpha 0.2
# Documentation can be found at
# https://smartpy.io/docs/guides/state_channels/overview

import smartpy as sp

types = sp.io.import_template("state_channel_games/types.py").Types()

STANDARD_OUTCOMES = [
    sp.variant("player_double_played", 1),
    sp.variant("player_double_played", 2),
    sp.variant("player_inactive", 1),
    sp.variant("player_inactive", 2),
    sp.variant("game_aborted", sp.unit),
]

class GamePlatform_OffChainViews:
    @sp.offchain_view(pure = True)
    def offchain_new_game(self, params):
        """Return a new game structure according to the `constants`

            Params:
                `constants`      (t_constants)        : game constants
                `initial_config` (bytes)              : game config
                `signatures`     (map(key, signature)): player => key: signature of
                    `pack(("New Game", <constants>, <params>))`

            Return:
                game (t_game)
        """
        sp.set_type(params.constants, types.t_constants)
        sp.result(
            self.new_game_(
                compute_game_id(params.constants),
                params.constants,
                params.initial_config,
                params.signatures
            )
        )

    @sp.offchain_view(pure = True)
    def offchain_game_init(self, params):
        """ Return the initial state of a game after it has been initialized by
            the model

            Params:
                `model_id` (bytes): id of the model
                `params`   (bytes): game init params

            Return:
                game_state (bytes)
        """
        model = self.get_model(params.model_id)
        sp.result(model.init(params.params))

    @sp.offchain_view(pure = True)
    def offchain_game_apply_move(self, params):
        """Compute a new state from a move.

            Params:
                game      (t__game): game structure
                move_data (bytes)  : player move's data

            Return:
                game_state (bytes)
        """
        sp.set_type(params.game, types.t_game)
        game      = params.game
        move_data = params.move_data
        model     = self.get_model(game.constants.model_id)
        sp.verify(game.current.outcome == sp.none, "Platform_GameNotRunning")

        with sp.if_(~game.state.is_some()):
            game.state = sp.some(model.init(game.initial_config))
        apply_input = sp.record(
            move_data = move_data,
            move_nb   = game.current.move_nb,
            player    = game.current.player,
            state     = game.state.open_some()
        )
        apply_input = sp.set_type_expr(apply_input, types.t_apply_input)
        sp.result(model.apply_(apply_input))

    @sp.offchain_view(pure = True)
    def offchain_game_play(self, params):
        """Simulate a call to game_play entrypoint.

            Params:
                game        (t_game)         : game structure
                new_current (t_current)      : new current as given by the player
                new_state   (option(t_bytes)): new state as given by the player
                move_data   (bytes)          : player move's data
                signatures  (map(key, signature)): player => key: signature of
                    `pack((
                        "Play",
                        <game_id>,
                        <new_current>,
                        <new_state>,
                        <move_data>
                    ))`

            Return:
                game (t_game)

        """
        sp.set_type(params.game, types.t_game)
        sp.verify(params.game.current.outcome == sp.none, "Platform_GameNotRunning")
        game = sp.local('game', params.game).value
        sp.result(
            self.game_play_(
                compute_game_id(game.constants),
                game,
                params.new_current,
                params.new_state,
                params.move_data,
                params.signatures
            )
        )

    @sp.offchain_view(pure = True)
    def offchain_compute_game_play(self, params):
        """ Return what a move_data would do to a game.

            Params:
                game        (t_game)         : game structure
                move_data   (bytes)          : player move's data
                sender      (address)        : player that do the move

            Return:
                game (t_game)
        """
        sp.set_type(params.game, types.t_game)
        game = sp.local('game', params.game).value
        sp.verify(params.sender == game.constants.players_addr[game.current.player], "Platform_WrongPlayer")
        sp.result(self.compute_game_play(game, params.move_data))

class GamePlatform(sp.Contract, GamePlatform_OffChainViews):
    def __init__(self, admins, ledger, self_addr = None, storage_overrides = {}):
        """ Game Platform contract

            Params:
                admins    (set(address))  : set of admins
                ledger    (address)       : address of the ledger contract
                self_addr (None | address): only set when doing tests.
                    The platform will simulate having a different address
                storage_overrides         : dict of extra storage parameters
        """
        self.init_type(sp.TRecord(
            admins            = sp.TSet(sp.TAddress),
            channels          = sp.TBigMap(sp.TBytes, types.t_channel),
            games             = sp.TBigMap(sp.TBytes, types.t_game),
            ledger            = sp.TAddress,
            models            = sp.TBigMap(sp.TBytes, types.t_model),
            model_metadata    = sp.TBigMap(sp.TBytes, sp.TMap(sp.TString, sp.TBytes)),
            model_permissions = sp.TBigMap(sp.TBytes, sp.TMap(sp.TString, sp.TBytes)),
            metadata          = sp.TBigMap(sp.TString, sp.TBytes),
        ).right_comb())

        self.init(
            admins            = admins,
            channels          = sp.big_map(),
            games             = sp.big_map(),
            ledger            = ledger,
            models            = sp.big_map(),
            model_metadata    = sp.big_map(),
            model_permissions = sp.big_map(),
            metadata          = sp.big_map(),
        )
        self.self_addr = self_addr
        self.update_initial_storage(**storage_overrides)

        # Metadata
        list_of_views = [
            self.offchain_new_game,
            self.offchain_game_init,
            self.offchain_game_play,
            self.offchain_game_apply_move,
            self.offchain_compute_game_play
        ]
        metadata_base = {
            "version": "alpha 0.2",
            "description" : (
                """Example of a state channel based game platform templates (work in progress).\n
                   Documentation is available at https://smartpy.io/docs/guides/state_channels/overview
                """
            ),
            "interfaces": ["TZIP-016"],
            "authors": [
                "SmartPy <https://smartpy.io>"
            ],
            "homepage": "https://smartpy.io",
            "views": list_of_views,
            "source": {
                "tools": ["SmartPy"],
                "location": "https://gitlab.com/SmartPy/smartpy/-/blob/master/python/templates/state_channel_games/game_platform.py"
            },
        }
        self.init_metadata("metadata_base", metadata_base)

    def self_address(self):
        """Simulate an alternative address (used when doing tests)

            Every modifications of this contract consider using self.address()
            instead of sp.self_address
        """
        if self.self_addr is None:
            return sp.self_address
        else:
            return self.self_addr

    ##############################
    # Meta-programmation methods #
    ##############################

    # Getters #

    def get_player(self, constants, player_id):
        """Return a local of the player structure from the channel according to game constants

            Params:
                constants (types.t_constants): game constants
                player_id (sp.TInt)          : the player id in the game constants

            Return:
                player (local(types.t_channel_player)): channel's player structure
        """
        sp.set_type(constants, types.t_constants)
        player = self.data.channels[constants.channel_id].players[constants.players_addr[player_id]]
        player = sp.local('player', player).value
        return player

    def get_running_game(self, game_id, verify_running = True):
        """ Return a local of a game.

            If verify_running is True:
                verify if `game.current.outcome` is None or some(pending).
            Else:
                simply return the game

            Params:
                game_id (bytes): game id
                verify_running (python boolean): meta-programmation boolean
                    to indicate if the game should be running

            Return:
                game (local(types.t_game)): local of the game

        """
        game = self.data.games.get(game_id, message = sp.pair("Platform_GameNotFound: ", game_id))
        game = sp.local('game', game).value
        if verify_running:
            with game.current.outcome.match("Some") as outcome:
                sp.verify(
                    outcome.is_variant("pending"),
                    message = "Platform_GameNotRunning"
                )
        return game

    def get_opened_channel(self, channel_id):
        """ Return a local of an opened channel. Fails if the channel is closed.

            Params:
                channel_id (bytes): channel id

            Return:
                channel (local(types.t_game)): local of the channel
        """
        channel = self.data.channels.get(channel_id, message = sp.pair("Platform_ChannelNotFound: ", channel_id))
        channel = sp.local('channel', channel).value
        sp.verify(~channel.closed, "Platform_ChannelClosed")
        return channel

    def get_model(self, model_id):
        """ Return a local of a model.

            Params:
                model_id (bytes): model id

            Return:
                model (local(types.t_game)): local of the model
        """
        model = self.data.models.get(model_id, message = sp.pair("Platform_ModelNotFound: ", model_id))
        model = sp.local('model', model).value
        return model

    # Setters #

    def game_set_outcome_(self, game, outcome, final = True):
        """ Set game final outcome by default or pending outcome if not `final`

            params:
                game      (local(types.t_game)): local of the game
                move_data (bytes)              : move played

            return:
                game (local(types.t_game)): local of the game
        """
        if final:
            game.current.outcome = sp.some(sp.variant("final", outcome))
        else:
            game.current.outcome = sp.some(sp.variant("pending", outcome))

    def update_metadata(self, metadata_map, key, metadata):
        sp.set_type(metadata, sp.TOption(sp.TBytes))
        sp.set_type(key, sp.TString)
        with sp.if_(metadata.is_some()):
            metadata_map[key] = metadata.open_some()
        with sp.else_():
            del metadata_map[key]

    # Game computation #

    def compute_timeouts(self, game):
        """ Update the timeout value of the current_player if setted
            (setted = other is starving)

            params:
                game (local(types.t_game)): local of the game

            return:
                game (local(types.t_game)): local of the game
        """
        with sp.if_(game.timeouts.contains(game.current.player)):
            game.timeouts[game.current.player] = sp.now.add_seconds(game.constants.play_delay)
        return game

    def compute_game_play(self, game, move_data):
        """ Update game state and current after a move

            params:
                game      (local(types.t_game)): local of the game
                move_data (bytes)              : move played

            return:
                game (local(types.t_game)): local of the game
        """
        model = self.get_model(game.constants.model_id)
        with sp.if_(~game.state.is_some()):
            game.state = sp.some(model.init(game.initial_config))
        params = sp.record(
            move_data = move_data,
            move_nb   = game.current.move_nb,
            player    = game.current.player,
            state     = game.state.open_some()
        )
        apply_result = sp.compute(model.apply_(params))
        game.current = sp.record(
            move_nb        = game.current.move_nb + 1,
            player         =  3 - game.current.player,
            outcome        = sp.eif(
                sp.snd(apply_result).is_some(),
                sp.some(sp.variant("final", sp.variant("game_finished", sp.snd(apply_result).open_some()))),
                sp.none
            ),
        )
        game.state = sp.some(sp.fst(apply_result))
        return game

    def _one_play_sig(self, signers, game, new_current, new_state, move_data):
        """ Two players' signatures on `game_play` entry point

            Set `signers` to current player.
            If game has a pending outcome:
                Set the outcome as final
                Compare new_current and new_state to game.current and game.state
            Else:
                Compute game play
                Compare new_current and new_state to computed game.current and game.state
                If apply returns an outcome:
                    set game outcome as pending
        """
        # sp.verify(game.current.move_nb + 1 == new_current.move_nb) is implicit
        pending = sp.local("pending", False)
        signers.value = [self.get_player(game.constants, game.current.player)]
        with game.current.outcome.match_cases() as arg:
            # Current player play
            with arg.match("None"):
                # self.compute_game_play will set the outcome to a final state
                # or the new_current will mismatch.
                self.compute_game_play(game, move_data)
                with sp.if_(game.current.outcome.is_some()):
                    pending.value = True
            # Other player counter-signature
            with arg.match("Some") as pending_outcome:
                self.game_set_outcome_(game, pending_outcome.open_variant("pending"))

        sp.verify(game.current == new_current, "Platform_CurrentMismatch")
        sp.verify(game.state.open_some() == new_state, "Platform_StateMismatch")
        with sp.if_(pending.value):
            # The outcome was temporarily set final by compute_game_play
            # It was necessary for the verification of current match
            # But now set it as pending, waiting for the counter signature
            self.game_set_outcome_(game, game.current.outcome.open_some().open_variant("final"), final = False)

    def _two_play_sig(self, signers, game, new_current, new_state):
        """ Two players' signatures on `game_play` entry point.

            Verifies if (new_current.move_nb > game.current.move_nb) or
                        (
                            (new_current.move_nb == game.current.move_nb) and
                            (game.current.outcome is pending)
                        )
        """
        equal_move_nb = sp.local("equal_move_nb", False)
        with sp.if_(game.current.outcome.is_some()):
            with sp.if_(game.current.outcome.open_some().is_variant("pending")):
                with sp.if_(new_current.move_nb == game.current.move_nb):
                    equal_move_nb.value = True
        sp.verify( (new_current.move_nb > game.current.move_nb) |
                   (equal_move_nb.value),
                   message = "Platform_OutdatedMoveNB")
        signers.value = self.get_opened_channel(game.constants.channel_id).players.values()
        game.current  = new_current
        game.state = sp.some(new_state)

    # Entry point logic #

    def game_play_(self, game_id, game, new_current, new_state, move_data, signatures):
        """ `game_play` entrypoint's logic without storage update

            Verifies signatures, update timeouts

            If one signature:
                verifies sender is `game.current.player`
                compute apply and compare with new_current and new_state.

            Return:
                game (local(types.t_game)): local of the game
        """

        sp.set_type(signatures, sp.TMap(sp.TKey, sp.TSignature))
        signers = sp.local('signers', [])

        with sp.if_(sp.len(signatures) == 1):
            self._one_play_sig(signers, game, new_current, new_state, move_data)

        with sp.else_():
            self._two_play_sig(signers, game, new_current, new_state)

        to_sign = sp.compute(action_play(game_id, new_current, new_state, move_data))
        with sp.for_('player', signers.value) as player:
            sp.verify(
                sp.check_signature(player.pk, signatures[player.pk], to_sign),
                message = sp.pair("Platform_badSig", player.pk)
            )
        self.compute_timeouts(game)
        return game

    def new_game_(self, game_id, constants, initial_config, signatures):
        """ `new_game` entrypoint's logic without storage update

            Return:
                game (types.t_game): structure of the game
        """
        sp.set_type(constants, types.t_constants)
        sp.set_type(initial_config, types.t_initial_config)
        sp.set_type(signatures, sp.TMap(sp.TKey, sp.TSignature))
        sp.verify(~self.data.games.contains(game_id), message = "Platform_GameAlreadyExists")
        sp.verify(sp.len(constants.players_addr) == 2, message = "Platform_Only2PlayersAllowed")
        channel = self.get_opened_channel(constants.channel_id)

        addr_players = sp.local('addr_players', sp.map()).value
        with sp.for_("addr_player", constants.players_addr.items()) as addr_player:
            addr_players[addr_player.value] = addr_player.key
            sp.verify(channel.players.contains(addr_player.value), message = "Platform_GamePlayerNotInChannel")

        with sp.for_('player', channel.players.values()) as player:
            sp.verify(signatures.contains(player.pk), "Platform_MissingSig")
            sp.verify(
                sp.check_signature(player.pk, signatures[player.pk], action_new_game(constants, initial_config)),
                message = sp.pair("Platform_BadSig", sp.record(player = player.pk, signature = signatures[player.pk]))
            )

        model = self.get_model(constants.model_id)
        self.verify_settlements(constants.settlements, model)

        return sp.set_type_expr(
            sp.record(
                addr_players   = addr_players,
                constants      = constants,
                current        = sp.record(
                    move_nb = 0,
                    player  = 1,
                    outcome = sp.none
                ),
                initial_config  = initial_config,
                permissions     = sp.map(),
                settled         = False,
                state           = sp.none,
                timeouts        = sp.map(),
            ), types.t_game
        )

    # Transfers #

    def platform_transfer(self, game_id, players_addr, players, transfer, allowed_mint_model, allowed_mint_game):
        """ Perform token transfers between the platform and the receiver

            Update the allowed_mint local.
        """
        receiver_addr = sp.compute(players_addr[transfer.receiver])
        receiver = sp.local('receiver', players[receiver_addr]).value
        with sp.for_("tokens", transfer.bonds.items()) as token:
            allowed = allowed_mint_game.get(token.key, 0)
            delta = sp.local('delta', allowed - token.value)
            allowed_mint_game[token.key] = sp.eif(delta.value > 0, sp.as_nat(delta.value), 0)
            with sp.if_(delta.value < 0):
                allowed_model = allowed_mint_model.get(token.key, 0)
                allowed_mint_model[token.key] = sp.as_nat(
                    sp.to_int(allowed_model) + delta.value,
                    sp.pair("Platform_NotAllowedMinting", sp.record(game_id = game_id, token = token.key, amount = token.value))
            )
            receiver.bonds[token.key] = receiver.bonds.get(token.key, 0) + token.value
        players[receiver_addr] = receiver

    def sender_transfer(self, players_addr, players, transfer):
        """ Perform token transfers between two players"""
        def bond_transfer(sender, sender_addr, receiver, token, amount):
            with sp.if_(~(amount == 0)):
                error_message = sp.pair("Platform_NotEnoughToken:", sp.record(sender = sender_addr, token = token, amount = amount))
                sp.verify(sender.bonds.contains(token), message = error_message)
                sender.bonds[token] = sp.as_nat(sender.bonds[token] - amount, message = error_message)
                with sp.if_(sender.bonds[token] == 0):
                    del sender.bonds[token]
                receiver.bonds[token] = receiver.bonds.get(token, 0) + amount

        # We don't need to do anything if sender == receiver
        sender_addr   = sp.compute(players_addr[transfer.sender])
        receiver_addr = sp.compute(players_addr[transfer.receiver])
        with sp.if_(~(sender_addr == receiver_addr)):
            sender   = sp.local('sender',   players[sender_addr]).value
            receiver = sp.local('receiver', players[receiver_addr]).value
            with sp.for_("bond", transfer.bonds.items()) as bond:
                bond_transfer(sender, sender_addr, receiver, bond.key, bond.value)
            players[sender_addr]   = sender
            players[receiver_addr] = receiver

    def rewards_transfer(self, permissions, players_addr, outcome):
        with sp.if_(outcome.is_variant("game_finished")):
            with sp.if_(permissions.contains("game_finished_rewards")):
                settle_rewards = sp.compute(sp.unpack(permissions["game_finished_rewards"], types.t_rewards).open_some())
                txs = sp.compute(sp.list(t = types.t_tx))
                with sp.for_("reward", settle_rewards) as reward:
                    txs.push(sp.record(amount = reward.amount, token_id = reward.token_id, to_ = players_addr[reward.to_]))
                self.ledger_transfer(txs)

    def verify_settlements(self, settlements, model):
        """ Verifies if every `model.outcomes` are in `settlements`.
            Verifies if every standard outcomes are in `settlements`
        """
        with sp.for_("outcome", model.outcomes) as outcome:
            sp.verify(settlements.contains(sp.variant("game_finished", outcome)),
                      message = sp.pair("Platform_MissingSettlement", sp.variant("game_finished", outcome))
            )
        for standard_outcome in STANDARD_OUTCOMES:
            sp.verify(settlements.contains(standard_outcome), message = sp.pair("Platform_MissingSettlement", standard_outcome))

    ###############
    # Entrypoints #
    ###############

    @sp.entry_point
    def new_channel(self, players, withdraw_delay, nonce):
        """ Create a new channel

            Channel id: `blake2b(pack((self_address, players, nonce)))`

            Params:
                players (map(address, public_key)): 2 players key => addresses
                withdraw_delay (nat):
                    number of seconds a player need to wait between a withdraw
                    request and its finalization
                nonce (string): string that will discriminate two channels
                    with identical players
        """
        channel_id = sp.compute(sp.blake2b(sp.pack((self.self_address(), players, nonce))))
        sp.verify(~self.data.channels.contains(channel_id), message = "Platform_ChannelAlreadyExists")
        sp.verify(sp.len(players) == 2, message = "Platform_Only2PlayersAllowed")
        players_map = sp.local('players_map', sp.map()).value
        with sp.for_("player", players.items()) as player:
            players_map[player.key] = sp.record(
                bonds       = {},
                pk          = player.value,
                withdraw    = sp.none,
                withdraw_id = 0,
            )
        self.data.channels[channel_id] = sp.record(
            closed         = False,
            nonce          = nonce,
            players        = players_map,
            withdraw_delay = withdraw_delay,
        )

    @sp.entry_point
    def new_game(self, constants, initial_config, signatures):
        """ Create a new game

            game id: `blake2b(pack((constants.channel_id, pair(constants.model_id, constants.game_nonce)))`
        """
        game_id = compute_game_id(constants)
        self.data.games[game_id] = self.new_game_(game_id, constants, initial_config, signatures)

    # Game #

    @sp.entry_point
    def game_play(self, game_id, new_current, new_state, move_data, signatures):
        game = self.get_running_game(game_id)
        self.game_play_(game_id, game, new_current, new_state, move_data, signatures)
        self.data.games[game_id] = game

    @sp.entry_point
    def game_set_outcome(self, game_id, outcome, timeout, signatures):
        sp.set_type(outcome, types.t_proposed_outcome)
        sp.set_type(signatures, sp.TMap(sp.TKey, sp.TSignature))
        sp.verify(sp.now <= timeout, message = "Platform_OutcomeTimedout")
        game = self.get_running_game(game_id)
        to_sign = sp.compute(action_new_outcome(game_id, outcome, timeout))
        channel = self.get_opened_channel(game.constants.channel_id)
        players = sp.local('players', channel.players).value
        with sp.for_('player', players.values()) as player:
            sp.verify(signatures.contains(player.pk), "Platform_MissingSig")
            sp.verify(sp.check_signature(player.pk, signatures[player.pk], to_sign), message = "Platform_badSig")
        with sp.if_(outcome.is_variant("game_aborted")):
            self.game_set_outcome_(game, sp.variant("game_aborted", sp.unit))
        with sp.else_():
            self.game_set_outcome_(game, sp.variant("game_finished", outcome.open_variant("game_finished")))
        self.data.games[game_id] = game

    @sp.entry_point(lazify = True)
    def game_settle(self, game_id):
        """ Set game to settled and update channel bonds depending on outcome.

            4 Types of outcomes exist:
                - `player_double_played`: set by `dispute_double_signed`
                - `player_inactive`     : set by `starved` entrypoint
                - `game_finished`       : set by `apply_` lambda after a `play`
                                           or by `game_set_outcome`
                - `game_aboorted`       : set by `game_set_outcome`

            The value of `player_double_played` and `player_inactive`
            represents the id of the player associated with the fault.
            The value of `game_finished` is freely defined by the game.

            Transfers are defined by the game constant `settlements`.
            Each outcome and outcome value is associated with a list of transfers.

            No transfer occurs if the outcome + value aren't in `settlements`.

            Transfer decreases bonds of the sender and increases bonds of the receiver.

            If the sender doesn't own enough in the channel to perform the transfer,
            the WHOLE settle FAILS.
        """
        game = self.get_running_game(game_id, verify_running = False)

        # Verify if outcome is valid
        outcome = sp.compute(game.current.outcome.open_some(message = "Plateform_GameIsntOver"))
        transfers = game.constants.settlements.get(
            outcome.open_variant(
                "final",
                message = "Plateform_OutcomeNotFinalized"
            ),
            message = sp.pair("Platform_UnknownOutcome", outcome)
        )

        model_id = game.constants.model_id
        model_permissions = sp.local('model_permissions',
            sp.eif(
                self.data.model_permissions.contains(model_id),
                sp.some(self.data.model_permissions[model_id]),
                sp.none
            )
        ).value
        players = self.get_opened_channel(game.constants.channel_id).players
        sp.verify(~game.settled, message = "Plateform_GameSettled")

        allowed_mint_model = sp.local("allowed_mint_model", {})
        allowed_mint_game  = sp.local("allowed_mint_game", {})
        with sp.if_(model_permissions.is_some()):
            with sp.if_(model_permissions.open_some().contains("allowed_mint")):
                allowed_mint_model.value = sp.unpack(model_permissions.open_some()["allowed_mint"], types.t_token_map).open_some()
        with sp.if_(game.permissions.contains("allowed_mint")):
            allowed_mint_game.value = sp.unpack(game.permissions["allowed_mint"], types.t_token_map).open_some()
            # Allowed mint is not updated in the game storage after all the transfers
            # That's not needed because the game is settled.

        with sp.for_("transfer", transfers) as transfer:
            with sp.if_(transfer.sender == 0):
                self.platform_transfer(game_id, game.constants.players_addr, players, transfer, allowed_mint_model.value, allowed_mint_game.value)
            with sp.else_():
                self.sender_transfer(game.constants.players_addr, players, transfer)

        self.data.channels[game.constants.channel_id].players = players

        game.settled = True
        self.data.games[game_id] = game
        with sp.if_(sp.len(allowed_mint_model.value) > 0):
            self.data.model_permissions[game.constants.model_id]["allowed_mint"] = sp.pack(allowed_mint_model.value)
        with sp.else_():
            with sp.if_(model_permissions.is_some()):
                del self.data.model_permissions[game.constants.model_id]["allowed_mint"]

    # Dispute #

    @sp.entry_point
    def dispute_starving(self, game_id, flag):
        """ Manages the game dispute timeout.

            If flag is True: indicates that the other player no longer has
            sender's confidence.

            Params:
                game_id (bytes): the game id
                flag    (bool) : if True the opponent must play on-chain
                                 if False remove the on-chain requirement

            Example:
                `game.timeouts`: { '<tz1_PLAYER1_ADDRESS>': <timeout>}
                Means that `<tz1_PLAYER1_ADDRESS>` should play on-chain before the
                timeout expires or its opponent may call `dispute_starved` entry
                point.

        """
        game = self.get_running_game(game_id)
        sender_id = game.addr_players[sp.sender]
        with sp.if_(flag):
            game.timeouts[3-sender_id] = sp.now.add_seconds(game.constants.play_delay)
        with sp.else_():
            del game.timeouts[3-sender_id]
        self.data.games[game_id] = game

    @sp.entry_point
    def dispute_starved(self, game_id, player_id):
        """ Indicates that the other player hasn't played on-chain.

            If `player_id`'s timeout expired, the outcome is set to
            `("player_inactive", <player_id>)`
        """
        game = self.get_running_game(game_id)
        sp.verify(game.current.player == player_id, message = "Platform_NotPlayersTurn")
        sp.verify(game.timeouts.contains(player_id), message = "Platform_NoTimeoutSetup")
        sp.verify(sp.now > game.timeouts[player_id], message = "Platform_NotTimedOut")
        self.game_set_outcome_(game, sp.variant("player_inactive", player_id))
        self.data.games[game_id] = game

    @sp.entry_point
    def dispute_double_signed(self, game_id, player_id, statement1, statement2):
        """ Verify if a player produced two different "Play" action signature
            for the same `current.move_nb`

            If the verification passes the game outcome becomes
            `("player_double_played", <player_id>)`

            Params:
                game_id: the game id
                player_id: the player who produced the statements
                statement1 `( current = t_current, state = bytes, move_data = bytes, sig = signature)`:
                    First statement corresponding to the "play" action signature
                statement2 (same type):
                    Second statement with same <move_nb> and different but
                    valid signature.
        """
        # The verification that both signatures come from the same game_id is implicit
        # Because game_id is included in the Play action
        game = self.get_running_game(game_id)
        player = self.get_player(game.constants, player_id)

        # Verification of 1st statement
        to_sign1 = action_play(game_id, statement1.current, statement1.state, statement1.move_data)
        sp.verify(sp.check_signature(player.pk, statement1.sig, to_sign1), message = "Platform_badSig")
        # Verification of 2nd statement
        to_sign2 = action_play(game_id, statement2.current, statement2.state, statement2.move_data)
        sp.verify(sp.check_signature(player.pk, statement2.sig, to_sign2), message = "Platform_badSig")

        # Comparing statement1 with statement2
        sp.verify(statement1.current.move_nb == statement2.current.move_nb, "Platform_MoveNBMismatch")
        sp.verify(statement1.sig != statement2.sig, message = "Platform_NotDifferentSignatures")

        self.game_set_outcome_(game, sp.variant("player_double_played", player_id))
        self.data.games[game_id] = game

    # Channel #

    @sp.entry_point(lazify = True)
    def on_received_bonds(self, params):
        """ Receive entrypoint implementing the "transfer and call" standard.

            Receive bonds from a ledger.

            Params:
                amount   (nat)    : amount of token transferred
                data     (bytes)  : `pack(record(channel_id, player_addr))`
                    channel_id  (bytes)  : id of the channel where the bonds are pushed
                    player_addr (address): address of player which will receive
                        the bonds on the channel
                receiver (address): address of the game platform
                sender   (address): address of the sender
                token_id (nat)    : token_id as represented by the ledger contract

        """
        sp.set_type(params, types.t_callback)
        sp.verify(self.data.ledger == sp.sender, "Platform_NotLedger")
        # Here we use sp.self_address and not self.self_address() because
        # sp.self_address() is only used when comparing signatures
        sp.verify(sp.self_address == params.receiver, "Platform_NotReceiver")
        data = sp.compute(sp.unpack(params.data, types.t_on_receive_bonds_data).open_some("Platform_UnpackErr"))

        channel = self.get_opened_channel(data.channel_id)
        player = channel.players.get(data.player_addr, message = "Platform_NotChannelPlayer")
        player = sp.local('player', player).value
        player.bonds[params.token_id] = player.bonds.get(params.token_id, 0) + params.amount
        self.data.channels[data.channel_id].players[data.player_addr] = player

    @sp.entry_point
    def withdraw_request(self, channel_id, tokens):
        """ Withdraw is the process by which a player can take
            bounds outside of a channel.

            The withdrawal is a three-step process:
                Step 1: `withdraw_request`
                Step 2: `withdraw_challenge`
                Step 3: `withdraw_finalize`

            Bonds can be withdrawn if one of the following conditions is met:
                The other parties don’t respond `withdraw_delay` seconds after a call to `withdraw_request`.
                A player can prove that your channel bonds exceeds his running game bonds - withdraw.

            Params:
                channel_id (bytes): ID of the channel from which the bonds are withdrawed
                tokens (map(token_id, amount)): All tokens requested and their amount
        """
        channel = self.get_opened_channel(channel_id)
        player = channel.players.get(sp.sender, message = "Platform_SenderNotInChannel")
        player = sp.local("player", player).value
        sp.verify(player.withdraw.is_none(), message = "Platform_AnotherWithdrawIsRunning")
        player.withdraw_id += 1
        player.withdraw = sp.some(
            sp.record(
                challenge        = sp.set(),
                challenge_tokens = sp.map(),
                timeout          = sp.now.add_seconds(channel.withdraw_delay),
                tokens           = tokens,
            )
        )
        channel.players[sp.sender] = player
        self.data.channels[channel_id] = channel

    @sp.entry_point(lazify = True)
    def withdraw_challenge(self, channel_id, withdrawer, game_ids):
        """ Step 2 of the `withdraw_request` process. Players send sets of
            `game_ids` that must be examined.

            To challenge: push non-settled games on-chain and calls
            `withdraw_challenge` with the non-settled game ids.

            To answer: same process as the challenge but the games must
            be settled.

            Params:
                channel_id (bytes)     : id of the channel where the withdraw request has been made
                withdrawer (address)   : Address of the player who asked the withdraw
                game_ids   (set(bytes)): List of games that must be inspected to modify the challenge

            ----

            Challenge is fullfiled if: `total bonds of non-settled games < withdraw tokens`

            After someone else than the withdrawer call this entrypoint the
            challenge period instantly timeout.

                - NEVER accept a new game that would unfulfill the challenge.
                - NEVER challenge without all the game_ids that may unfulfill the challenge except if you agree the request.
        """
        sp.set_type(game_ids, sp.TSet(sp.TBytes))
        channel = self.get_opened_channel(channel_id)
        sp.verify(channel.players.contains(sp.sender), "Platform_SenderNotInChannel")
        sp.verify(channel.players.contains(withdrawer), "Platform_WithdrawerNotInChannel")
        sp.verify(channel.players[withdrawer].withdraw.is_some(), "Platform_NoWithdrawRequestOpened")
        withdraw = sp.local('withdraw', channel.players[withdrawer].withdraw.open_some()).value
        with sp.for_('game_id', game_ids.elements()) as game_id:
            game = self.get_running_game(game_id, verify_running = False)
            sp.verify(game.constants.channel_id == channel_id, "Platform_ChannelIdMismatch")
            with sp.if_(game.settled):
                sp.verify(withdraw.challenge.contains(game_id), "Platform_GameSettled")
                withdraw.challenge.remove(game_id)
                minus_tokens(withdraw.challenge_tokens, game.constants.bonds[game.addr_players[withdrawer]])
            with sp.else_():
                with sp.if_(~withdraw.challenge.contains(game_id)):
                    withdraw.challenge.add(game_id)
                    add_tokens(withdraw.challenge_tokens, game.constants.bonds[game.addr_players[withdrawer]])
        with sp.if_(withdrawer != sp.sender):
            withdraw.timeout = sp.now
        channel.players[withdrawer].withdraw = sp.some(withdraw)
        self.data.channels[channel_id] = channel

    def ledger_transfer(self, txs):
        ledger = sp.contract(types.t_fa2_transfer, self.data.ledger, entry_point = "transfer").open_some("Platform_LedgerNotFound")
        arg = sp.list([sp.record(from_ = self.self_address(), txs = txs)])
        sp.transfer(arg, sp.tez(0), ledger)

    @sp.entry_point(lazify = True)
    def withdraw_finalize(self, channel_id):
        """ Step 3 of the `withdraw_request` process. Finalize the sender's withdraw process.

            Params:
                channel_id (bytes): id of the channel where the withdraw request has been made

            Requirements:
            - the `timeout` timed out
            - challenge_tokens doesn't contain positive value (i.e. `total bonds of non-settled games < withdraw tokens`)
        """
        channel = self.get_opened_channel(channel_id)
        sp.verify(channel.players.contains(sp.sender), "Platform_SenderNotInChannel")
        player = sp.local('player', channel.players[sp.sender]).value
        sp.verify(player.withdraw.is_some(), "Platform_NoWithdrawOpened")
        withdraw = sp.local('withdraw', player.withdraw.open_some()).value
        sp.verify(sp.now >= withdraw.timeout, message = "Platform_ChallengeDelayNotOver")
        txs = sp.local('txs', sp.list()).value

        with sp.for_('token', withdraw.challenge_tokens.items()) as token:
            with sp.if_((token.value > 0) & player.bonds.contains(token.key)):
                sp.verify((player.bonds[token.key]-withdraw.tokens[token.key]) > token.value, "Platform_TokenChallenged")

        # Transfer withdraw
        with sp.for_('token', withdraw.tokens.items()) as token:
            with sp.if_(token.value > 0):
                sp.verify(player.bonds.contains(token.key), message = "Platform_NotEnoughTokens")
                player.bonds[token.key] = sp.as_nat(player.bonds[token.key] - token.value, message = "Platform_NotEnoughTokens")
                txs.push(sp.record(
                    amount = token.value,
                    to_ = sp.sender,
                    token_id = token.key,
                ))

        self.ledger_transfer(txs)

        player.withdraw = sp.none
        channel.players[sp.sender] = player
        self.data.channels[channel_id] = channel

    @sp.entry_point
    def withdraw_cancel(self, channel_id):
        """Cancel a running withdraw_request after it timedout

            Params:
                channel_id (bytes): id of the channel where the withdraw request has been made
        """
        channel = self.get_opened_channel(channel_id)
        sp.verify(channel.players.contains(sp.sender), "Platform_SenderNotInChannel")
        player = sp.local('player', channel.players[sp.sender]).value
        sp.verify(player.withdraw.is_some(), "Platform_NoWithdrawOpened")
        sp.verify(sp.now >= player.withdraw.open_some().timeout, message = "Platform_ChallengeDelayNotOver")
        channel.players[sp.sender].withdraw = sp.none
        self.data.channels[channel_id] = channel

    # Admin #

    @sp.entry_point
    def admin_new_model(self, model, metadata, permissions, rewards):
        sp.verify(self.data.admins.contains(sp.sender), "Platform_NotAdmin")
        model_id = sp.compute(sp.blake2b(model))
        with sp.if_(~self.data.models.contains(model_id)):
            unpacked = sp.compute(sp.unpack(model, types.t_model_lambdas).open_some("Platform_ModelUnpackFailure"))
            self.data.model_metadata[model_id] = metadata
            self.data.model_permissions[model_id] = permissions
            self.data.models[model_id] = sp.record(
                apply_   = unpacked.apply_,
                init     = unpacked.init,
                outcomes = unpacked.outcomes,
            )
        with sp.if_(sp.len(rewards) > 0):
            self.ledger_transfer(rewards)

    @sp.entry_point
    def admin_setup(self, ledger, add_admins, remove_admins):
        sp.verify(self.data.admins.contains(sp.sender), "Platform_NotAdmin")

        with sp.if_(ledger.is_some()):
            self.data.ledger = ledger.open_some()
        with sp.for_("admin", add_admins) as admin:
            self.data.admins.add(admin)
        with sp.for_("admin", remove_admins.elements()) as remove_admin:
            sp.verify(~(remove_admin == sp.sender), "Platform_CannotRemoveSelf")
            self.data.admins.remove(admin)

    @sp.entry_point
    def admin_game_permissions(self, game_id, key, permission):
        sp.verify(self.data.admins.contains(sp.sender), "Platform_NotAdmin")
        sp.verify(self.data.games.contains(game_id), message = "Platform_GameNotFound")
        self.update_metadata(self.data.games[game_id].permissions, key, permission)

    @sp.entry_point
    def admin_model_metadata(self, model_id, key, metadata):
        sp.verify(self.data.admins.contains(sp.sender), "Platform_NotAdmin")
        sp.verify(self.data.models.contains(model_id), message = "Platform_ModelNotFound")
        self.update_metadata(self.data.model_metadata[model_id], key, metadata)

    @sp.entry_point
    def admin_model_permissions(self, model_id, key, permission):
        sp.verify(self.data.admins.contains(sp.sender), "Platform_NotAdmin")
        sp.verify(self.data.models.contains(model_id), message = "Platform_ModelNotFound")
        self.update_metadata(self.data.model_permissions[model_id], key, permission)

    @sp.entry_point
    def admin_global_metadata(self, key, metadata):
        sp.verify(self.data.admins.contains(sp.sender), "Platform_NotAdmin")
        self.update_metadata(self.data.metadata, key, metadata)

    @sp.entry_point(lazify = True)
    def admin_update_operators(self, fa2, operators):
        sp.verify(self.data.admins.contains(sp.sender), "Platform_NotAdmin")
        t_operator_param = sp.TRecord(
            owner = sp.TAddress,
            operator = sp.TAddress,
            token_id = sp.TNat
        ).layout(("owner", ("operator", "token_id")))
        t = sp.TList(
            sp.TVariant(
                add_operator = t_operator_param,
                remove_operator = t_operator_param
            )
        )
        fa2_contract = sp.contract(t, address = fa2, entry_point = "update_operators")
        sp.transfer(operators, sp.tez(0), fa2_contract.open_some("Plateform_FA2Unreacheable"))

    # @sp.entry_point
    # def admin_update_entrypoints(self, ep):
    #     sp.verify(self.data.admins.contains(sp.sender), "Platform_NotAdmin")
    #     with ep.match_cases() as arg:
    #         with arg.match("on_received_bonds") as code:
    #             sp.set_entry_point("on_received_bonds", code)
    #         with arg.match("withdraw_challenge") as code:
    #             sp.set_entry_point("withdraw_challenge", code)
    #         with arg.match("withdraw_finalize") as code:
    #             sp.set_entry_point("withdraw_finalize", code)
    #         with arg.match("admin_update_operators") as code:
    #             sp.set_entry_point("admin_update_operators", code)
    #         with arg.match("game_settle") as code:
    #             sp.set_entry_point("game_settle", code)

# Utils #

def compute_game_id(constants):
    return sp.blake2b(sp.pack(
        sp.pair(constants.channel_id, sp.pair(constants.model_id, constants.game_nonce))
    ))

def action_new_game(constants, initial_config):
    constants  = sp.set_type_expr(constants, types.t_constants)
    initial_config = sp.set_type_expr(initial_config, types.t_initial_config)
    return sp.pack(("New Game", constants, initial_config))

def action_play(game_id, new_current, new_state, move_data):
    game_id     = sp.set_type_expr(game_id, sp.TBytes)
    new_current = sp.set_type_expr(new_current, types.t_current)
    new_state   = sp.set_type_expr(new_state, sp.TBytes)
    move_data   = sp.set_type_expr(move_data, sp.TBytes)
    return sp.pack(("Play", game_id, new_current, new_state, move_data))

def action_new_outcome(game_id, new_outcome, timeout):
    game_id     = sp.set_type_expr(game_id, sp.TBytes)
    new_outcome = sp.set_type_expr(new_outcome, types.t_proposed_outcome)
    return sp.pack(("New Outcome", game_id, new_outcome, timeout))

def transfer(sender, receiver, bonds):
    return sp.record(sender = sender, receiver = receiver, bonds = bonds)

def minus_tokens(a, b):
    sp.set_type(a, sp.TMap(sp.TNat, sp.TInt))
    sp.set_type(b, types.t_token_map)
    with sp.for_('token', b.items()) as token:
        with sp.if_(a.contains(token.key)):
            amount = sp.compute(a[token.key] - sp.to_int(b[token.key]))
            with sp.if_( amount == 0):
                del a[token.key]
            with sp.else_():
                a[token.key] = amount
        with sp.else_():
            a[token.key] = 0 - sp.to_int(b[token.key])

def add_tokens(a, b):
    sp.set_type(a, sp.TMap(sp.TNat, sp.TInt))
    sp.set_type(b, types.t_token_map)
    with sp.for_('token', b.items()) as token:
        with sp.if_(a.contains(token.key)):
            a[token.key] +=  sp.to_int(b[token.key])
        with sp.else_():
            amount = sp.to_int(b[token.key])
            with sp.if_(~(amount == 0)):
                a[token.key] = amount


# Test utils #

abort = sp.set_type_expr(sp.variant("game_aborted", sp.unit), types.t_proposed_outcome)
def game_finished(outcome):
    return sp.set_type_expr(sp.variant("game_finished", outcome), types.t_proposed_outcome)

def outcome(gamePlatform, game_id):
    return gamePlatform.data.games[game_id].current.outcome.open_some().open_variant('final')

def finished_outcome(gamePlatform, game_id):
    return outcome(gamePlatform, game_id).open_variant('game_finished')

def player_bonds(gamePlatform, channel_id, player_addr):
    return gamePlatform.data.channels[channel_id].players[player_addr].bonds

ledger = sp.address("KT1_LEDGER")
admins = sp.set([sp.address("tz1_GAMEPLATFORM_ADMIN")])

if "templates" not in __name__:
    sp.add_compilation_target(
        "platform",
        GamePlatform(
            admins,
            ledger,
            storage_overrides = {
                "metadata": sp.utils.metadata_of_url("https://cloudflare-ipfs.com/ipfs/QmZ6NT3SQ4YmS9FFtZjAvMQ6hDbMhhHvTG1D6FqBnm8cXF"),
            }
        ),
    )
