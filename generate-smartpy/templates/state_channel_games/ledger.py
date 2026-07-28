"""
    FA2 Contract that can easily wrap tokens from other FA2

    Each token can have specific permissions
    Token can be minted, burned and exchanged
    according these permissions

    Token Permissions (every types are packed):
        - type (String): Type of token.
            Current types:
                - "Native"
                - "FA2"
        - mint_cost (Mutez):
            Mutez cost for each mint / amount transferred after withdraw
        - mint_permissions (sp.TVariant("allow_everyone": Unit, "allow_only: Set(Address))):
            Type of permission applied to mint (if not present no mint allowed)
            "allow_only": only addresses in this set are allowed to mint
        - burn_permissions (sp.TVariant("onlyOwner": Unit, "allow_only: Set(Address)):
            Type of permission applied to burn (if not present no burn allowed)
            "allow_only": only addresses in this set are allowed to burn
        - transfer_only_to (Set(Address)):
            If this permission exists, only addresses listed can receive this token.
            Otherwise, anybody can accept it.
        - transfer_only_from (Set(Address)):
            If this permission exists, only addresses listed can send this token.
            Otherwise, anybody can send it.
        - fa_token (sp.pair(Address, Nat)):
            Address and id of the undelying FA1.2 or FA2 contract of this token
            Must be provided if type is FA2 or FA1.2

    ------------
    GamePlatform
    ------------

    This ledger has been originated to be used with the SmartPy state channels gamePlatform
    Documentation can be found at https://smartpy.io/docs/guides/state_channels/overview

    To Push bonds on the gamePlatform, you can use the `transfer_and_call` entrypoint with the following arguments:

    - from_ (Address): <your_address>
    - txs (List($TXS))

    TXS:
        to: <gamePlatform_address>
        callback: <gamePlatform_address>%on_received_bonds
        data: pack(sp.record(channel_id = <channel_id>, player_addr = <player_address>))
        token_id: <token_id> the token you want to bond
        amount: <amount> the amount you want to bond
"""

import smartpy as sp
FA2 = sp.io.import_template("FA2.py")
types = sp.io.import_template("state_channel_games/types.py").Types()

t_txs = sp.TRecord(
    to_      = sp.TAddress,
    callback = sp.TAddress,
    data     = sp.TBytes,
    token_id = sp.TNat,
    amount   = sp.TNat
).right_comb()

t_transfer_and_call = sp.TList(
    sp.TRecord(
        from_ = sp.TAddress,
        txs   = sp.TList(t_txs)
    )
)

t_sender_restrictions = sp.TVariant(
    allow_everyone = sp.TUnit,
    allow_only     = sp.TSet(sp.TAddress)
)

t_burn_restrictions = sp.TVariant(
    allow_only = sp.TSet(sp.TAddress),
    only_owner = sp.TUnit,
    only_owner_and_admin = sp.TUnit
)

class Ledger(FA2.FA2_change_metadata, FA2.FA2_token_metadata, FA2.FA2_administrator, FA2.FA2_pause, FA2.FA2_core):
    def __init__(self, config, metadata, admin, storage_overrides = {}):
        extra_storage = {
            "token_permissions": sp.big_map(
                tkey = sp.TNat,
                tvalue = sp.TMap(sp.TString, sp.TBytes)
            ),
            "token_ids": sp.big_map(
                tkey = sp.TAddress,
                tvalue = sp.TMap(sp.TNat, sp.TNat)
            ) # FA_contract address: {token_id: internal_token_id}
        }
        config.assume_consecutive_token_ids = False

        metadata_base = {
            "version": config.name # will be changed if using fatoo.
            , "description" : (
                "This is a modified implementation of FA2,"
                + " a.k.a. TZIP-012, using SmartPy.\n\n"
                + "This particular contract uses the configuration named: "
                + config.name + ".\n"
                + "This contract also wrap FA1.2/FA2 tokens with permissions"
            )
            , "interfaces": ["TZIP-012", "TZIP-016"]
            , "authors": [
                "SmartPy <https://smartpy.io>"
            ]
            , "homepage": "https://smartpy.io/docs/guides/state_channels/overview"
            , "source": {
                "tools": ["SmartPy"]
                , "location": "https://gitlab.com/SmartPy/smartpy.git"
            }
            , "permissions": {
                "operator":
                "owner-or-operator-transfer" if config.support_operator else "owner-transfer"
                , "receiver": "owner-no-hook"
                , "sender": "owner-no-hook"
            }
            , "fa2-smartpy": {
                "configuration" :
                dict([(k, getattr(config, k)) for k in dir(config) if "__" not in k and k != 'my_map'])
            }
        }
        self.init_metadata("metadata_base", metadata_base)

        FA2.FA2_core.__init__(self, config, metadata, paused = False, administrator = admin, **extra_storage)
        self.update_initial_storage(**storage_overrides)

    # Methods

    def increase_token_supply(self, token_permissions, token, amount):
        supply = sp.local('supply', amount)
        with sp.if_(token_permissions.contains("supply")):
            supply.value += sp.unpack(token_permissions["supply"], sp.TNat).open_some()
        self.data.token_permissions[token]["supply"] = sp.pack(supply.value)

    def decrease_token_supply(self, token_permissions, token, amount):
        supply = sp.local('supply', sp.unpack(token_permissions["supply"], sp.TNat).open_some())
        with sp.if_(token_permissions.contains("supply")):
            supply.value = sp.as_nat(supply.value - amount)
        self.data.token_permissions[token]["supply"] = sp.pack(supply.value)

    def verify_mint_permissions(self, token_id, amount):
        sp.verify(self.data.token_permissions.contains(token_id), message = sp.pair("Ledger_token_unpermitted", token_id))
        token_permissions = sp.compute(self.data.token_permissions.get(token_id))

        # Existence verification
        sp.verify(self.data.token_metadata.contains(token_id), message = self.error_message.token_undefined())

        # mint_permissions
        sp.verify(token_permissions.contains("mint_permissions"), message = sp.pair("Ledger_No_mint_permissions", token_id))

        mint_permissions = sp.compute(sp.unpack(token_permissions["mint_permissions"], t = t_sender_restrictions).open_some("Ledger_unpack_err"))
        with mint_permissions.match_cases() as arg:
            with arg.match("allow_only") as allow_only:
                sp.verify(allow_only.contains(sp.sender), sp.pair("Ledger_not_allowed", token_id))
            with arg.match("allow_everyone"):
                pass

        # Cost
        with sp.if_(token_permissions.contains("mint_cost")):
            mint_cost = sp.compute(sp.unpack(token_permissions["mint_cost"], sp.TMutez).open_some("Ledger_unpack_err"))
            expected_amount = sp.compute(sp.mul(amount, mint_cost))
            sp.verify(
                sp.amount == expected_amount,
                message = sp.pair("FA2_WRONG_AMOUNT_expected", expected_amount)
            )
        # Type
        sp.verify(token_permissions.contains("type"), message = sp.pair("Ledger_No_Type", token_id))
        token_type = sp.compute(sp.unpack(token_permissions["type"], sp.TString).open_some())
        sp.verify(token_type == "NATIVE", message = "Ledger_Can_Only_Mint_NATIVE")

        return token_permissions

    def verify_burn_permissions(self, token_id, address):
        sp.verify(self.data.token_permissions.contains(token_id), message = sp.pair("Ledger_token_unpermitted", token_id))
        token_permissions = sp.compute(self.data.token_permissions.get(token_id))

        # Existence verification
        sp.verify(self.data.token_metadata.contains(token_id), message = self.error_message.token_undefined())

        # burn_permissions
        sp.verify(token_permissions.contains("burn_permissions"), message = sp.pair("Ledger_No_burn_permissions", token_id))

        burn_permissions = sp.compute(sp.unpack(token_permissions["burn_permissions"], t = t_burn_restrictions).open_some("Ledger_unpack_err"))
        with burn_permissions.match_cases() as arg:
            with arg.match("allow_only") as allow_only:
                sp.verify(allow_only.contains(sp.sender), sp.pair("Ledger_not_allowed", token_id))
            with arg.match("only_owner"):
                sp.verify(sp.sender == address, "Ledger_onlyOwner")
            with arg.match("only_owner_and_admin"):
                sp.verify((sp.sender == address) | (self.data.administrator == sp.sender), "Ledger_onlyOwner")

        # Type
        sp.verify(token_permissions.contains("type"), message = sp.pair("Ledger_No_Type", token_id))
        token_type = sp.compute(sp.unpack(token_permissions["type"], sp.TString).open_some())
        sp.verify(token_type == "NATIVE", message = "Ledger_Can_Only_Burn_Native")

        return token_permissions

    def verify_transfer_permissions(self, tx, current_from):
        sp.set_type(self.data.token_permissions, sp.TBigMap(sp.TNat, sp.TMap(sp.TString, sp.TBytes) ))
        sp.verify(self.data.token_permissions.contains(tx.token_id), message = sp.pair("Ledger_token_unpermitted", tx.token_id))
        token_permissions = sp.compute(self.data.token_permissions.get(tx.token_id))

        with sp.if_(token_permissions.contains("transfer_only_to")):
            restricted_to = sp.compute(sp.unpack(token_permissions["transfer_only_to"], sp.TSet(sp.TAddress)).open_some("Ledger_unpack_err"))
            sp.verify(restricted_to.contains(tx.to_), sp.pair("transfer_only_to", restricted_to))
        with sp.if_(token_permissions.contains("transfer_only_from")):
            restricted_from = sp.compute(sp.unpack(token_permissions["transfer_only_from"], sp.TSet(sp.TAddress)).open_some("Ledger_unpack_err"))
            sp.verify(restricted_from.contains(current_from), sp.pair("transfer_only_from", restricted_from))

        # Type
        sp.verify(token_permissions.contains("type"), message = sp.pair("Ledger_No_Type", tx.token_id))

        return token_permissions

    def _transfer_fa2(self, tx, current_from, token_permissions):
        sp.verify(current_from == sp.sender, message = "Ledger_Current_From_And_Sender_Differs")
        fa2_address, fa2_token_id = sp.match_pair(sp.unpack(token_permissions["fa_token"], sp.TPair(sp.TAddress, sp.TNat)).open_some())
        fa2_contract = sp.contract(types.t_fa2_transfer, fa2_address, entry_point = "transfer")
        arg = [sp.record(
            from_ = sp.sender,
            txs   = sp.list([sp.record(
                to_      = tx.to_,
                token_id = fa2_token_id,
                amount   = tx.amount
            )])
        )]
        sp.transfer(arg, sp.tez(0), fa2_contract.open_some("Ledger_FA2_Unreacheable"))

    def _transfer_native(self, tx, current_from):
        sender_verify = ((self.is_administrator(sp.sender)) |
                         (current_from == sp.sender))
        message = self.error_message.not_owner()
        if self.config.support_operator:
            message = self.error_message.not_operator()
            sender_verify |= (self.operator_set.is_member(self.data.operators,
                                                            current_from,
                                                            sp.sender,
                                                            tx.token_id))
        if self.config.allow_self_transfer:
            sender_verify |= (sp.sender == sp.self_address)
        sp.verify(sender_verify, message = message)
        sp.verify(
            self.data.token_metadata.contains(tx.token_id),
            message = self.error_message.token_undefined()
        )
        # If amount is 0 we do nothing now:
        with sp.if_(tx.amount > 0):
            from_user = self.ledger_key.make(current_from, tx.token_id)
            from_ledger = sp.compute(self.data.ledger.get(from_user, default_value = sp.record(balance = 0)))
            sp.verify(from_ledger.balance >= tx.amount, message = self.error_message.insufficient_balance())
            to_user = self.ledger_key.make(tx.to_, tx.token_id)
            self.data.ledger[from_user].balance = sp.as_nat(from_ledger.balance - tx.amount)
            with sp.if_(self.data.ledger.contains(to_user)):
                self.data.ledger[to_user].balance += tx.amount
            with sp.else_():
                self.data.ledger[to_user] = FA2.Ledger_value.make(tx.amount)

    # Sub entry points

    def _transfer(self, params):
        sp.set_type(params, self.batch_transfer.get_type())
        sp.verify( ~self.is_paused(), message = self.error_message.paused() )

        with sp.for_("transfer", params) as transfer:
           current_from = transfer.from_
           with sp.for_("tx", transfer.txs) as tx:
                token_permissions = self.verify_transfer_permissions(tx, current_from)
                token_type = sp.compute(sp.unpack(token_permissions["type"], sp.TString).open_some())
                with sp.if_(token_type == "FA2"):
                    self._transfer_fa2(tx, current_from, token_permissions)
                with sp.else_():
                    sp.verify(token_type == "NATIVE", message = sp.pair("Ledger_Type_Unknown", token_type))
                    self._transfer_native(tx, current_from)

    # Entrypoints

    @sp.entry_point
    def transfer(self, params):
        self._transfer(params)

    def _transfer_and_call(self, batchs):
        sp.set_type(batchs, t_transfer_and_call)

        # Transfer
        with sp.for_('batchs', batchs) as batch:
            with sp.for_('transaction', batch.txs) as tx:
                self._transfer([
                    sp.record(
                        from_ = batch.from_,
                        txs   = [
                            sp.record(
                                to_      = tx.to_,
                                token_id = tx.token_id,
                                amount   = tx.amount
                            )
                        ]
                    )
                ])

                # Callback
                callback = sp.contract(types.t_callback, tx.callback).open_some(
                    "FA2_WRONG_CALLBACK_INTERFACE")
                args = sp.record(
                    sender   = batch.from_,
                    receiver = tx.to_,
                    data     = tx.data,
                    token_id = tx.token_id,
                    amount   = tx.amount
                )
                sp.transfer(args, sp.tez(0), callback)

    @sp.entry_point
    def transfer_and_call(self, batchs):
        self._transfer_and_call(batchs)

    def _mint(self, token_id, amount, address):
        token_permissions = self.verify_mint_permissions(token_id, amount)

        self.increase_token_supply(token_permissions, token_id, amount)
        to_user = self.ledger_key.make(address, token_id)
        with sp.if_(self.data.ledger.contains(to_user)):
            self.data.ledger[to_user].balance += amount
        with sp.else_():
            self.data.ledger[to_user] = FA2.Ledger_value.make(amount)

    @sp.entry_point
    def mint(self, token_id, amount, address):
        self._mint(token_id, amount, address)

    @sp.entry_point
    def burn(self, token_id, amount, address):
        token_permissions = self.verify_burn_permissions(token_id, address)

        self.decrease_token_supply(token_permissions, token_id, amount)
        from_user = self.ledger_key.make(sp.sender, token_id)
        self.data.ledger[from_user].balance = sp.as_nat(self.data.ledger[from_user].balance - amount)

    @sp.entry_point
    def push_bonds(self, platform, channel_id, player_addr, bonds):
        """ Perform a transfer_and_call with data and callback to trigger `on_received_bonds` on `platform`
        """
        sp.set_type(channel_id, sp.TBytes)
        sp.set_type(player_addr, sp.TAddress)
        with sp.for_("token", bonds.items()) as token:
            callback = sp.to_address(sp.contract(types.t_callback, platform, entry_point = "on_received_bonds").open_some())
            self._transfer_and_call([sp.record(
                from_ = sp.sender,
                txs = [
                    sp.record(
                        amount   = token.value,
                        callback = callback,
                        data     = sp.pack(sp.record(channel_id = channel_id, player_addr = player_addr)),
                        to_      = platform,
                        token_id = token.key,
                    )
            ])])

    @sp.entry_point
    def on_received_bonds(self, params):
        """ Transmit the `on_received_bonds` info to the corresponding receiver after having translating the token_id to its internal representation"""
        # We don't verify params.receiver as it is the platform address
        sp.set_type(params, types.t_callback)
        internal_token_id = self.data.token_ids[sp.sender][params.token_id]
        call_params = sp.record(
            amount   = params.amount,
            data     = params.data,
            sender   = params.sender,
            receiver = params.receiver,
            token_id = internal_token_id,
        )
        platform_contract = sp.contract(types.t_callback, params.receiver, entry_point = "on_received_bonds")
        sp.transfer(call_params, sp.tez(0), platform_contract.open_some("Ledger_Platform_Unreacheable"))

    # Admin entrypoints

    @sp.entry_point
    def set_token_info(self, token_id, token_info):
        sp.verify(self.is_administrator(sp.sender), self.error_message.not_admin())
        self.data.token_metadata[token_id] = sp.record(token_id = token_id, token_info = token_info)

    @sp.entry_point()
    def update_token_permissions(self, token_id, token_permissions):
        sp.verify(self.is_administrator(sp.sender), self.error_message.not_admin())
        new_permissions = sp.local('new_permissions', self.data.token_permissions.get(token_id, {})).value
        with sp.for_("permission", token_permissions.items()) as permission:
            with sp.if_(permission.value.is_some()):
                new_permissions[permission.key] = permission.value.open_some()
                self.add_id_if_needed(permission, token_id)
            with sp.else_():
                self.remove_id_if_needed(permission)
                del new_permissions[permission.key]
        with sp.if_(sp.len(new_permissions) == 0):
            del self.data.token_permissions[token_id]
        with sp.else_():
            self.data.token_permissions[token_id] = new_permissions

    def remove_id_if_needed(self, permission):
        with sp.if_(permission.key == "fa_token"):
            fa_address, fa_token_id = sp.match_pair(sp.unpack(permission.value.open_some(), sp.TPair(sp.TAddress, sp.TNat)).open_some())
            del self.data.token_ids[fa_address][fa_token_id]

    def add_id_if_needed(self, permission, token_id):
        with sp.if_(permission.key == "fa_token"):
            fa_address, fa_token_id = sp.match_pair(sp.unpack(permission.value.open_some(), sp.TPair(sp.TAddress, sp.TNat)).open_some())
            with sp.if_(~self.data.token_ids.contains(fa_address)):
                self.data.token_ids[fa_address] = {fa_token_id: token_id}
            with sp.else_():
                self.data.token_ids[fa_address][fa_token_id] = token_id

def build_token_permissions(added, removed_keys = [], option = True):
    changed_permissions = {}
    for key, value in added.items():
        if key == "mint_permissions":
            value = sp.set_type_expr(value, t_sender_restrictions)
        if key == "burn_permissions":
            value = sp.set_type_expr(value, t_burn_restrictions)
        if key == "fa_token_id":
            value = sp.set_type_expr(value, sp.TNat)
        if option:
            changed_permissions[key] = sp.some(sp.pack(value))
        else:
            changed_permissions[key] = sp.pack(value)
    for key in removed_keys:
        changed_permissions[key] = sp.none
    return changed_permissions

def fa2_balance(address, FA2, token_id = 0):
    return FA2.data.ledger.get((address, token_id), default_value = sp.record(balance = 0)).balance

ledger_admin = sp.address("tz1_ADMIN_LEDGER")
fa2_config = FA2.FA2_config(single_asset = False)
metadata = sp.utils.metadata_of_url("https://example.com")

wXTZ_metadata = sp.map(l = {
            # Remember that michelson wants map already in ordered
            "decimals" : sp.utils.bytes_of_string("%d" % 6),
            "name" : sp.utils.bytes_of_string("Wrapped XTZ"),
            "symbol" : sp.utils.bytes_of_string("WXTZ"),
            "thumbnailUri" : sp.utils.bytes_of_string("https://upload.wikimedia.org/wikipedia/commons/3/33/Tezos_logo.svg"),
})

wXTZ_permissions = build_token_permissions({
    "type"            : "NATIVE",
    "mint_cost"       : sp.mutez(1),
    "mint_permissions": sp.variant("allow_everyone", sp.unit)
}, option = False)

if "templates" not in __name__:
    sp.add_compilation_target(
        "Ledger",
        Ledger(
            fa2_config,
            admin = ledger_admin,
            metadata = metadata,
            storage_overrides = {
                "token_metadata": sp.big_map({0: sp.record(token_id = 0, token_info = wXTZ_metadata)}),
                "token_permissions": sp.big_map({0: wXTZ_permissions})
            },
        ),
    )
