import smartpy as sp

fa2 = sp.io.import_template("fa2_lib.py")
testing = sp.io.import_template("fa2_lib_testing.py")

if "templates" not in __name__:
    testing = sp.io.import_template("fa2_lib_testing.py")

    admin = sp.test_account("Administrator")
    alice = sp.test_account("Alice")
    tok0_md = fa2.make_metadata(name="Token Zero", decimals=1, symbol="Tok0")
    tok1_md = fa2.make_metadata(name="Token One", decimals=1, symbol="Tok1")
    tok2_md = fa2.make_metadata(name="Token Two", decimals=1, symbol="Tok2")
    TOKEN_METADATA = [tok0_md, tok1_md, tok2_md]
    METADATA = sp.utils.metadata_of_url("ipfs://example")

    class SingleAssetTest(
        fa2.Admin,
        fa2.ChangeMetadata,
        fa2.WithdrawMutez,
        fa2.MintSingleAsset,
        fa2.BurnSingleAsset,
        fa2.OnchainviewBalanceOf,
        fa2.OffchainviewTokenMetadata,
        fa2.Fa2SingleAsset,
    ):
        def __init__(self, **kwargs):
            fa2.Fa2SingleAsset.__init__(self, **kwargs)
            fa2.Admin.__init__(self, admin.address)

    def _pre_minter(base_class, policy=None):
        token_metadata = tok0_md
        ledger = {alice.address: 42}
        return base_class(
            metadata=METADATA,
            token_metadata=token_metadata,
            ledger=ledger,
            policy=policy,
        )

    # Standard features
    for _Fa2 in [fa2.Fa2SingleAsset]:
        testing.test_core_interfaces(_pre_minter(_Fa2))
        testing.test_transfer(_pre_minter(_Fa2))
        testing.test_balance_of(_pre_minter(_Fa2))
        testing.test_no_transfer(_pre_minter(_Fa2, policy=fa2.NoTransfer()))
        testing.test_owner_transfer(_pre_minter(_Fa2, policy=fa2.OwnerTransfer()))
        testing.test_owner_or_operator_transfer(_pre_minter(_Fa2))

    # Non standard features
    for _Fa2 in [SingleAssetTest]:
        token_metadata = tok0_md if _Fa2.ledger_type == "SingleAsset" else []
        testing.NS.test_admin(_Fa2(metadata=METADATA))
        testing.NS.test_mint(_Fa2(metadata=METADATA, token_metadata=token_metadata))
        testing.NS.test_burn(_pre_minter(_Fa2))
        testing.NS.test_withdraw_mutez(_Fa2(metadata=METADATA))
        testing.NS.test_change_metadata(_Fa2(metadata=METADATA))
        testing.NS.test_offchain_token_metadata(_pre_minter(_Fa2))
        testing.NS.test_get_balance_of(_pre_minter(_Fa2))
        testing.NS.test_pause(_pre_minter(_Fa2, policy=fa2.PauseTransfer()))
