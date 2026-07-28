import smartpy as sp

FA2_NFT_MINIMAL = sp.io.import_template("fa2_nft_minimal.py")
FA2_FUNGIBLE_MINIMAL = sp.io.import_template("fa2_fungible_minimal.py")

admin = sp.test_account("Administrator")
admin2 = sp.test_account("Administrator2")
alice = sp.test_account("Alice")
bob = sp.test_account("Bob")
charlie = sp.test_account("Charlie")


def make_metadata(symbol, name, decimals):
    """Helper function to build metadata JSON bytes values."""
    return sp.map(
        l={
            "decimals": sp.utils.bytes_of_string("%d" % decimals),
            "name": sp.utils.bytes_of_string(name),
            "symbol": sp.utils.bytes_of_string(symbol),
        }
    )


tok0_md = make_metadata(name="Token Zero", decimals=1, symbol="Tok0")
tok1_md = make_metadata(name="Token One", decimals=1, symbol="Tok1")
tok2_md = make_metadata(name="Token Two", decimals=1, symbol="Tok2")


class Fa2NftMinimalTest(FA2_NFT_MINIMAL.Fa2NftMinimal):
    def __init__(self):
        self.ledger_type = "NFT"
        FA2_NFT_MINIMAL.Fa2NftMinimal.__init__(
            self,
            administrator=admin.address,
            metadata_base=FA2_NFT_MINIMAL.metadata_base,
            metadata_url="https://example.com",
        )
        self.update_initial_storage(
            next_token_id=3,
            ledger=sp.big_map(
                {0: alice.address, 1: alice.address, 2: alice.address},
                tkey=sp.TNat,
                tvalue=sp.TAddress,
            ),
            token_metadata=sp.big_map(
                {
                    0: sp.record(token_id=0, token_info=tok0_md),
                    1: sp.record(token_id=1, token_info=tok1_md),
                    2: sp.record(token_id=2, token_info=tok2_md),
                },
                tkey=sp.TNat,
                tvalue=sp.TRecord(
                    token_id=sp.TNat,
                    token_info=sp.TMap(sp.TString, sp.TBytes),
                ),
            ),
        )


class Fa2FungibleMinimalTest(FA2_FUNGIBLE_MINIMAL.Fa2FungibleMinimal):
    def __init__(self):
        self.ledger_type = "Fungible"
        FA2_FUNGIBLE_MINIMAL.Fa2FungibleMinimal.__init__(
            self,
            administrator=admin.address,
            metadata_base=FA2_NFT_MINIMAL.metadata_base,
            metadata_url="https://example.com",
        )
        self.update_initial_storage(
            next_token_id=3,
            ledger=sp.big_map(
                {
                    (alice.address, 0): 42,
                    (alice.address, 1): 42,
                    (alice.address, 2): 42,
                },
                tkey=sp.TPair(sp.TAddress, sp.TNat),
                tvalue=sp.TNat,
            ),
            token_metadata=sp.big_map(
                {
                    0: sp.record(token_id=0, token_info=tok0_md),
                    1: sp.record(token_id=1, token_info=tok1_md),
                    2: sp.record(token_id=2, token_info=tok2_md),
                },
                tkey=sp.TNat,
                tvalue=sp.TRecord(
                    token_id=sp.TNat,
                    token_info=sp.TMap(sp.TString, sp.TBytes),
                ),
            ),
        )


class TestReceiverBalanceOf(sp.Contract):
    """Helper used to test the `balance_of` entrypoint.

    Don't use it on-chain as it can be gas locked.
    """

    def __init__(self):
        self.init(last_known_balances=sp.big_map())

    @sp.entry_point
    def receive_balances(self, params):
        sp.set_type(params, sp.TList(t_balance_of_response))
        with sp.for_("resp", params) as resp:
            owner = (resp.request.owner, resp.request.token_id)
            with sp.if_(self.data.last_known_balances.contains(sp.sender)):
                self.data.last_known_balances[sp.sender][owner] = resp.balance
            with sp.else_():
                self.data.last_known_balances[sp.sender] = sp.map({owner: resp.balance})


t_balance_of_response = sp.TRecord(
    request=sp.TRecord(owner=sp.TAddress, token_id=sp.TNat).layout(
        ("owner", "token_id")
    ),
    balance=sp.TNat,
).layout(("request", "balance"))

################################################################################

# Standard features tests


def test_core_interfaces(fa2, test_name=""):
    """Test that each core interface has the right type and layout.

    Args:
        test_name (string): Name of the test
        fa2 (sp.Contract): The FA2 contract on which the tests occur.

    The contract must contains the tokens 0: tok0_md, 1: tok1_md, 2: tok2_md.

    For NFT contracts, `alice` must own the three tokens.

    For Fungible contracts, `alice` must own 42 of each token types.

    Tests:

    - Entrypoints: `balance_of`, `transfer`, `update_operators`
    - Storage: test of `token_metadata`
    """
    test_name = "test_core_interfaces_" + fa2.ledger_type + "_" + test_name

    @sp.add_test(name=test_name)
    def test():
        sc = sp.test_scenario()
        sc.h1(test_name)
        sc.table_of_contents()
        sc.p("A call to all the standard entrypoints and off-chain views.")

        sc.h2("Accounts")
        sc.show([admin, alice, bob])

        sc.h2("FA2 contract")
        sc += fa2

        # Entrypoints

        sc.h2("Entrypoint: update_operators")
        fa2.update_operators(
            sp.set_type_expr(
                [
                    sp.variant(
                        "add_operator",
                        sp.record(
                            owner=alice.address, operator=alice.address, token_id=0
                        ),
                    )
                ],
                sp.TList(
                    sp.TVariant(
                        add_operator=sp.TRecord(
                            owner=sp.TAddress, operator=sp.TAddress, token_id=sp.TNat
                        ).layout(("owner", ("operator", "token_id"))),
                        remove_operator=sp.TRecord(
                            owner=sp.TAddress, operator=sp.TAddress, token_id=sp.TNat
                        ).layout(("owner", ("operator", "token_id"))),
                    )
                ),
            )
        ).run(sender=alice)

        sc.h2("Entrypoint: transfer")
        fa2.transfer(
            sp.set_type_expr(
                [
                    sp.record(
                        from_=alice.address,
                        txs=[sp.record(to_=alice.address, amount=1, token_id=0)],
                    )
                ],
                sp.TList(
                    sp.TRecord(
                        from_=sp.TAddress,
                        txs=sp.TList(
                            sp.TRecord(
                                to_=sp.TAddress, token_id=sp.TNat, amount=sp.TNat
                            ).layout(("to_", ("token_id", "amount")))
                        ),
                    ).layout(("from_", "txs"))
                ),
            )
        ).run(sender=alice)

        sc.h2("Entrypoint: balance_of")
        sc.h3("Receiver contract")
        c2 = TestReceiverBalanceOf()
        sc += c2

        sc.h3("Call to balance_of")
        fa2.balance_of(
            sp.set_type_expr(
                sp.record(
                    callback=sp.contract(
                        sp.TList(t_balance_of_response),
                        c2.address,
                        entry_point="receive_balances",
                    ).open_some(),
                    requests=[sp.record(owner=alice.address, token_id=0)],
                ),
                sp.TRecord(
                    requests=sp.TList(
                        sp.TRecord(owner=sp.TAddress, token_id=sp.TNat).layout(
                            ("owner", "token_id")
                        )
                    ),
                    callback=sp.TContract(
                        sp.TList(
                            sp.TRecord(
                                request=sp.TRecord(
                                    owner=sp.TAddress, token_id=sp.TNat
                                ).layout(("owner", "token_id")),
                                balance=sp.TNat,
                            ).layout(("request", "balance"))
                        )
                    ),
                ).layout(("requests", "callback")),
            )
        ).run(sender=alice)

        # Storage

        sc.h2("Storage: token_metadata")
        sc.verify_equal(
            fa2.data.token_metadata[0], sp.record(token_id=0, token_info=tok0_md)
        )


def test_transfer(fa2, test_name=""):
    """Test that transfer entrypoint works as expected.

    Do not test transfer permission policies.

    Args:
        test_name (string): Name of the test
        fa2 (sp.Contract): The FA2 contract on which the tests occur.

    SingleAsset contract: The contract must contains the token 0: tok0_md.
    Others: The contract must contains the tokens 0: tok0_md, 1: tok1_md, 2: tok2_md.

    NFT contract: `sp.test_account("Alice").address` must own all the tokens.
    Fungible contract: `sp.test_account("Alice").address` must own 42 of each token.

    Tests:
        - initial minting works as expected.
        - `get_balance` returns `balance = 0` for non owned tokens.
        - transfer of 0 tokens works when not owning tokens.
        - transfer of 0 doesn't change `ledger` storage.
        - transfer of 0 tokens works when owning tokens.
        - transfers with multiple operations and transactions works as expected.
        - fails with `FA2_INSUFFICIENT_BALANCE` when not enought balance.
        - transfer to self doesn't change anything.
        - transfer to self with more than balance gives `FA2_INSUFFICIENT_BALANCE`.
        - transfer to self of undefined token gives `FA2_TOKEN_UNDEFINED`.
        - transfer to someone else of undefined token gives `FA2_TOKEN_UNDEFINED`.
    """
    test_name = "test_transfer_" + fa2.ledger_type + "_" + test_name

    @sp.add_test(name=test_name, is_default=False)
    def test():
        sc = sp.test_scenario()
        sc.h1(test_name)
        sc.table_of_contents()

        sc.h2("Accounts")
        sc.show([admin, alice, bob])

        sc.h2("Contract")
        sc += fa2

        if fa2.ledger_type == "NFT":
            ICO = 1  # Initial coin offering.
            TX = 1  # How much we transfer at a time during the tests.
        else:
            ICO = 42  # Initial coin offering.
            TX = 12  # How much we transfer at a time during the tests.

        # Check that the contract storage is correctly initialized.
        sc.verify(fa2.get_balance(sp.record(owner=alice.address, token_id=0)) == ICO)
        if not fa2.ledger_type == "SingleAsset":
            sc.verify(
                fa2.get_balance(sp.record(owner=alice.address, token_id=1)) == ICO
            )
            sc.verify(
                fa2.get_balance(sp.record(owner=alice.address, token_id=2)) == ICO
            )

        # Check that the balance is interpreted as zero when the owner doesn't hold any.
        # TZIP-12: If the token owner does not hold any tokens of type token_id,
        #          the owner's balance is interpreted as zero.
        sc.verify(fa2.get_balance(sp.record(owner=bob.address, token_id=0)) == 0)

        sc.h2("Zero amount transfer")
        sc.p("TZIP-12: Transfers of zero amount MUST be treated as normal transfers.")

        # Check that someone with 0 token can transfer 0 token.
        fa2.transfer(
            [
                sp.record(
                    from_=bob.address,
                    txs=[sp.record(to_=alice.address, amount=0, token_id=0)],
                ),
            ]
        ).run(sender=bob)

        # Check that the contract storage is unchanged.
        sc.verify(fa2.get_balance(sp.record(owner=alice.address, token_id=0)) == ICO)
        sc.verify(fa2.get_balance(sp.record(owner=bob.address, token_id=0)) == 0)

        # Check that someone with some tokens can transfer 0 token.
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=bob.address, amount=0, token_id=0)],
                ),
            ]
        ).run(sender=alice)

        # Check that the contract storage is unchanged.
        sc.verify(fa2.get_balance(sp.record(owner=alice.address, token_id=0)) == ICO)
        sc.verify(fa2.get_balance(sp.record(owner=bob.address, token_id=0)) == 0)

        sc.h2("Transfers Alice -> Bob")
        sc.p(
            """TZIP-12: Each transfer in the batch MUST decrement token balance
                of the source (from_) address by the amount of the transfer and
                increment token balance of the destination (to_) address by the
                amount of the transfer."""
        )

        # Perform a complex transfer with 2 operations, one of which contains 2 transactions.
        if fa2.ledger_type == "SingleAsset":
            fa2.transfer(
                [
                    sp.record(
                        from_=alice.address,
                        txs=[
                            sp.record(to_=bob.address, amount=TX // 3, token_id=0),
                            sp.record(to_=bob.address, amount=TX // 3, token_id=0),
                        ],
                    ),
                    sp.record(
                        from_=alice.address,
                        txs=[sp.record(to_=bob.address, amount=TX // 3, token_id=0)],
                    ),
                ]
            ).run(sender=alice)
        else:
            fa2.transfer(
                [
                    sp.record(
                        from_=alice.address,
                        txs=[
                            sp.record(to_=bob.address, amount=TX, token_id=0),
                            sp.record(to_=bob.address, amount=TX, token_id=1),
                        ],
                    ),
                    sp.record(
                        from_=alice.address,
                        txs=[sp.record(to_=bob.address, amount=TX, token_id=2)],
                    ),
                ]
            ).run(sender=alice)

        # Check that the contract storage is correctly updated.
        sc.verify(
            fa2.get_balance(sp.record(owner=alice.address, token_id=0)) == ICO - TX
        )
        sc.verify(fa2.get_balance(sp.record(owner=bob.address, token_id=0)) == TX)

        if not fa2.ledger_type == "SingleAsset":
            sc.verify(
                fa2.get_balance(sp.record(owner=alice.address, token_id=1)) == ICO - TX
            )
            sc.verify(fa2.get_balance(sp.record(owner=bob.address, token_id=1)) == TX)

        # Check without using get_balance because the ledger interface
        # differs between NFT and fungible.
        if fa2.ledger_type == "NFT":
            sc.verify(fa2.data.ledger[0] == bob.address)
        else:
            if fa2.ledger_type == "Fungible":
                sc.verify(fa2.data.ledger[(alice.address, 0)] == ICO - TX)
                sc.verify(fa2.data.ledger[(bob.address, 0)] == TX)
            else:
                sc.verify(fa2.data.ledger[alice.address] == ICO - TX)
                sc.verify(fa2.data.ledger[bob.address] == TX)

        # Error tests

        # test of FA2_INSUFFICIENT_BALANCE.
        sc.h2("Insufficient balance")
        sc.p(
            """TIP-12: If the transfer amount exceeds current token balance of
                the source address, the whole transfer operation MUST fail with
                the error mnemonic "FA2_INSUFFICIENT_BALANCE"."""
        )

        # Compute bob_balance to transfer 1 more token.
        bob_balance = sc.compute(
            fa2.get_balance(sp.record(owner=bob.address, token_id=0))
        )

        # Test that a complex transfer with only one insufficient
        # balance fails.
        fa2.transfer(
            [
                sp.record(
                    from_=bob.address,
                    txs=[
                        sp.record(
                            to_=alice.address, amount=bob_balance + 1, token_id=0
                        ),
                        sp.record(to_=alice.address, amount=0, token_id=0),
                    ],
                ),
                sp.record(
                    from_=bob.address,
                    txs=[sp.record(to_=alice.address, amount=0, token_id=0)],
                ),
            ]
        ).run(sender=bob, valid=False, exception="FA2_INSUFFICIENT_BALANCE")

        sc.h2("Same address transfer")
        sc.p(
            """TZIP-12: Transfers with the same address (from_ equals to_) MUST
                be treated as normal transfers."""
        )

        # Test that someone can transfer all his balance to itself
        # without problem.
        fa2.transfer(
            [
                sp.record(
                    from_=bob.address,
                    txs=[sp.record(to_=bob.address, amount=bob_balance, token_id=0)],
                ),
            ]
        ).run(sender=bob)

        # Check that the contract storage is unchanged.
        sc.verify(
            fa2.get_balance(sp.record(owner=alice.address, token_id=0)) == ICO - TX
        )
        sc.verify(fa2.get_balance(sp.record(owner=bob.address, token_id=0)) == TX)
        if not fa2.ledger_type == "SingleAsset":
            sc.verify(
                fa2.get_balance(sp.record(owner=alice.address, token_id=1)) == ICO - TX
            )
            sc.verify(fa2.get_balance(sp.record(owner=bob.address, token_id=1)) == TX)

        # Test that someone cannot transfer more tokens than he holds
        # even to himself.
        fa2.transfer(
            [
                sp.record(
                    from_=bob.address,
                    txs=[
                        sp.record(to_=bob.address, amount=bob_balance + 1, token_id=0)
                    ],
                ),
            ]
        ).run(sender=bob, valid=False, exception="FA2_INSUFFICIENT_BALANCE")

        # test of FA2_TOKEN_UNDEFINED.
        sc.h2("Not defined token")
        sc.p(
            """TZIP-12: If one of the specified token_ids is not defined within
                the FA2 contract, the entrypoint MUST fail with the error
                mnemonic "FA2_TOKEN_UNDEFINED"."""
        )

        # A transfer of 0 tokens to self gives FA2_TOKEN_UNDEFINED if
        # not defined.
        fa2.transfer(
            [
                sp.record(
                    from_=bob.address,
                    txs=[sp.record(to_=bob.address, amount=0, token_id=4)],
                ),
            ]
        ).run(sender=bob, valid=False, exception="FA2_TOKEN_UNDEFINED")

        # A transfer of 1 token to someone else gives
        # FA2_TOKEN_UNDEFINED if not defined.
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=bob.address, amount=1, token_id=4)],
                ),
            ]
        ).run(sender=bob, valid=False, exception="FA2_TOKEN_UNDEFINED")


def test_balance_of(fa2, test_name=""):
    """Test that balance_of entrypoint works as expected.

    Args:
        test_name (string): Name of the test
        fa2 (sp.Contract): The FA2 contract on which the tests occur.

    SingleAsset contract: The contract must contains the token 0: tok0_md.
    Others: The contract must contains the tokens 0: tok0_md, 1: tok1_md, 2: tok2_md.

    NFT contract: `sp.test_account("Alice").address` must own all the tokens.
    Fungible contract: `sp.test_account("Alice").address` must own 42 of each token.

    Tests:

    - `balance_of` calls back with valid results.
    - `balance_of` fails with `FA2_TOKEN_UNDEFINED` when token is undefined.
    """
    test_name = "test_balance_of_" + fa2.ledger_type + "_" + test_name

    @sp.add_test(name=test_name)
    def test():
        sc = sp.test_scenario()
        sc.h1(test_name)
        sc.table_of_contents()

        sc.h2("Accounts")
        sc.show([admin, alice, bob])

        # We initialize the contract with an initial mint.
        sc.h2("Contract")
        sc += fa2

        sc.h3("Receiver contract")
        c2 = TestReceiverBalanceOf()
        sc += c2

        # Call to balance_of.
        if fa2.ledger_type == "SingleAsset":
            fa2.balance_of(
                callback=sp.contract(
                    sp.TList(t_balance_of_response),
                    c2.address,
                    entry_point="receive_balances",
                ).open_some(),
                requests=[
                    sp.record(owner=alice.address, token_id=0),
                    sp.record(owner=alice.address, token_id=0),
                ],
            ).run(sender=alice)
        else:
            fa2.balance_of(
                callback=sp.contract(
                    sp.TList(t_balance_of_response),
                    c2.address,
                    entry_point="receive_balances",
                ).open_some(),
                requests=[
                    sp.record(owner=alice.address, token_id=0),
                    sp.record(owner=alice.address, token_id=1),
                ],
            ).run(sender=alice)

        if fa2.ledger_type == "NFT":
            ICO = 1  # Initial coin offering.
        else:
            ICO = 42  # Initial coin offering.

        # Check that balance_of returns the correct balances.
        sc.verify(c2.data.last_known_balances[fa2.address][(alice.address, 0)] == ICO)
        if not fa2.ledger_type == "SingleAsset":
            sc.verify(
                c2.data.last_known_balances[fa2.address][(alice.address, 1)] == ICO
            )

        # Expected errors
        sc.h2("FA2_TOKEN_UNDEFINED error")
        fa2.balance_of(
            callback=sp.contract(
                sp.TList(t_balance_of_response),
                c2.address,
                entry_point="receive_balances",
            ).open_some(),
            requests=[
                sp.record(owner=alice.address, token_id=0),
                sp.record(owner=alice.address, token_id=5),
            ],
        ).run(sender=alice, valid=False, exception="FA2_TOKEN_UNDEFINED")


def test_no_transfer(fa2, test_name=""):
    """Test that the `no-transfer` policy works as expected.

    Args:
        test_name (string): Name of the test
        fa2 (sp.Contract): The FA2 contract on which the tests occur.

    The contract must contains the tokens 0: tok0_md, 1: tok1_md, 2: tok2_md.

    For NFT contracts, `alice` must own the three tokens.

    For Fungible contracts, `alice` must own 42 of each token types.

    Tests:

    - transfer fails with FA2_TX_DENIED.
    - transfer fails with FA2_TX_DENIED even for admin.
    - update_operators fails with FA2_OPERATORS_UNSUPPORTED.
    """
    test_name = "test_no-transfer_" + fa2.ledger_type + "_" + test_name

    @sp.add_test(name=test_name, is_default=False)
    def test():
        sc = sp.test_scenario()
        sc.h1(test_name)
        sc.table_of_contents()

        sc.h2("Accounts")
        sc.show([admin, alice, bob])

        sc.h2("FA2 with NoTransfer policy")
        sc.p("No transfer are allowed.")
        sc += fa2

        # Transfer fails as expected.
        sc.h2("Alice cannot transfer: FA2_TX_DENIED")
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=bob.address, amount=1, token_id=0)],
                )
            ]
        ).run(sender=alice, valid=False, exception="FA2_TX_DENIED")

        # Even Admin cannot transfer.
        sc.h2("Admin cannot transfer alice's token: FA2_TX_DENIED")
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=alice.address, amount=1, token_id=0)],
                )
            ]
        ).run(sender=admin, valid=False, exception="FA2_TX_DENIED")

        # update_operators is unsuported.
        sc.h2("Alice cannot add operator: FA2_OPERATORS_UNSUPPORTED")
        fa2.update_operators(
            [
                sp.variant(
                    "add_operator",
                    sp.record(owner=alice.address, operator=bob.address, token_id=0),
                )
            ]
        ).run(sender=alice, valid=False, exception="FA2_OPERATORS_UNSUPPORTED")


def test_owner_transfer(fa2, test_name=""):
    """Test that the `owner-transfer` policy works as expected.

    Args:
        test_name (string): Name of the test
        fa2 (sp.Contract): the FA2 contract on which the tests occur.

    The contract must contains the tokens 0: tok0_md, 1: tok1_md, 2: tok2_md.

    For NFT contracts, `alice` must own the three tokens.

    For Fungible contracts, `alice` must own 42 of each token types.

    Tests:

    - owner can transfer.
    - transfer fails with FA2_NOT_OWNER for non owner, even admin.
    - update_operators fails with FA2_OPERATORS_UNSUPPORTED.
    """
    test_name = "test_owner-transfer_" + fa2.ledger_type + "_" + test_name

    @sp.add_test(name=test_name, is_default=False)
    def test():
        sc = sp.test_scenario()
        sc.h1(test_name)
        sc.table_of_contents()

        sc.h2("Accounts")
        sc.show([admin, alice, bob])

        sc.h2("FA2 with OwnerTransfer policy")
        sc.p("Only owner can transfer, no operator allowed.")
        sc += fa2

        # The owner can transfer its tokens.
        sc.h2("Alice can transfer")
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=alice.address, amount=1, token_id=0)],
                )
            ]
        ).run(sender=alice)

        # Admin cannot transfer someone else tokens.
        sc.h2("Admin cannot transfer alices's token: FA2_NOT_OWNER")
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=alice.address, amount=1, token_id=0)],
                )
            ]
        ).run(sender=admin, valid=False, exception="FA2_NOT_OWNER")

        # Someone cannot transfer someone else tokens.
        sc.h2("Admin cannot transfer alices's token: FA2_NOT_OWNER")
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=alice.address, amount=1, token_id=0)],
                )
            ]
        ).run(sender=bob, valid=False, exception="FA2_NOT_OWNER")

        # Someone cannot add operator.
        sc.h2("Alice cannot add operator: FA2_OPERATORS_UNSUPPORTED")
        fa2.update_operators(
            [
                sp.variant(
                    "add_operator",
                    sp.record(owner=alice.address, operator=bob.address, token_id=0),
                )
            ]
        ).run(sender=alice, valid=False, exception="FA2_OPERATORS_UNSUPPORTED")


def test_owner_or_operator_transfer(fa2, test_name=""):
    """Test that the `owner-or-operator-transfer` policy works as expected.

    Args:
        test_name (string): Name of the test
        fa2 (sp.Contract): The FA2 contract on which the tests occur.

    SingleAsset contract: The contract must contains the token 0: tok0_md.
    Others: The contract must contains the tokens 0: tok0_md, 1: tok1_md, 2: tok2_md.

    NFT contract: `sp.test_account("Alice").address` must own all the tokens.
    Fungible contract: `sp.test_account("Alice").address` must own 42 of each token.

    Tests:

    - owner can transfer.
    - transfer fails with FA2_NOT_OPERATOR for non operator, even admin.
    - update_operators fails with FA2_OPERATORS_UNSUPPORTED.
    - owner can add operator.
    - operator can transfer.
    - operator cannot transfer for non allowed `token_id`.
    - owner can remove operator and add operator in a batch.
    - removed operator cannot transfer anymore.
    - operator added in a batch can transfer.
    - add then remove the same operator doesn't change the storage.
    - remove then add the same operator does change the storage.
    """
    test_name = "test_owner-or-operator-transfer_" + fa2.ledger_type + "_" + test_name

    @sp.add_test(name=test_name, is_default=False)
    def test():
        operator_bob = sp.record(owner=alice.address, operator=bob.address, token_id=0)
        operator_charlie = sp.record(
            owner=alice.address, operator=charlie.address, token_id=0
        )

        sc = sp.test_scenario()
        sc.h1(test_name)
        sc.table_of_contents()

        sc.h2("Accounts")
        sc.show([admin, alice, bob])

        sc.h2("FA2 with OwnerOrOperatorTransfer policy")
        sc.p("Owner or operators can transfer.")
        sc += fa2

        # Owner can transfer his tokens.
        sc.h2("Alice can transfer")
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=alice.address, amount=1, token_id=0)],
                )
            ]
        ).run(sender=alice)

        # Admin can transfer others tokens.
        sc.h2("Admin cannot transfer alices's token: FA2_NOT_OPERATOR")
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=alice.address, amount=1, token_id=0)],
                )
            ]
        ).run(sender=admin, valid=False, exception="FA2_NOT_OPERATOR")

        # Update operator works.
        sc.h2("Alice adds Bob as operator")
        fa2.update_operators([sp.variant("add_operator", operator_bob)]).run(
            sender=alice
        )

        # The contract is updated as expected.
        sc.verify(fa2.data.operators.contains(operator_bob))

        # Operator can transfer allowed tokens on behalf of owner.
        sc.h2("Bob can transfer Alice's token id 0")
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=alice.address, amount=1, token_id=0)],
                )
            ]
        ).run(sender=bob)

        if not fa2.ledger_type == "SingleAsset":
            # Operator cannot transfer not allowed tokens on behalf of owner.
            sc.h2("Bob cannot transfer Alice's token id 1")
            fa2.transfer(
                [
                    sp.record(
                        from_=alice.address,
                        txs=[sp.record(to_=alice.address, amount=1, token_id=1)],
                    )
                ]
            ).run(sender=bob, valid=False, exception="FA2_NOT_OPERATOR")

        # Batch of update_operators actions.
        sc.h2("Alice can remove Bob as operator and add Charlie")
        fa2.update_operators(
            [
                sp.variant("remove_operator", operator_bob),
                sp.variant("add_operator", operator_charlie),
            ]
        ).run(sender=alice)

        # The contract is updated as expected.
        sc.verify(~fa2.data.operators.contains(operator_bob))
        sc.verify(fa2.data.operators.contains(operator_charlie))

        # A removed operator lose its rights.
        sc.h2("Bob cannot transfer Alice's token 0 anymore")
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=alice.address, amount=1, token_id=0)],
                )
            ]
        ).run(sender=bob, valid=False, exception="FA2_NOT_OPERATOR")

        # The new added operator can now do the transfer.
        sc.h2("Charlie can transfer Alice's token")
        fa2.transfer(
            [
                sp.record(
                    from_=alice.address,
                    txs=[sp.record(to_=charlie.address, amount=1, token_id=0)],
                )
            ]
        ).run(sender=charlie)

        # The contract is updated as expected.
        sc.verify(fa2.get_balance(sp.record(owner=charlie.address, token_id=0)) == 1)

        # Remove after a Add does nothing.
        sc.h2("Add then Remove in the same batch is transparent")
        sc.p(
            """TZIP-12: If two different commands in the list add and remove an
                operator for the same token owner and token ID, the last command
                in the list MUST take effect."""
        )
        fa2.update_operators(
            [
                sp.variant("add_operator", operator_bob),
                sp.variant("remove_operator", operator_bob),
            ]
        ).run(sender=alice)
        sc.verify(~fa2.data.operators.contains(operator_bob))

        # Add after remove works
        sc.h2("Remove then Add do add the operator")
        fa2.update_operators(
            [
                sp.variant("remove_operator", operator_bob),
                sp.variant("add_operator", operator_bob),
            ]
        ).run(sender=alice)
        sc.verify(fa2.data.operators.contains(operator_bob))


################################################################################

# Optional features tests


class NS:
    """Non standard features of FA2_lib

    Mixin tested:

    - Admin,
    - WithdrawMutez
    - ChangeMetadata
    - OffchainviewTokenMetadata
    - OnchainviewBalanceOf
    - Mint*
    - Burn*
    """

    def test_admin(fa2, test_name=""):
        """Test `Admin` mixin

        - non admin cannot set admin
        - admin can set admin
        - new admin can set admin
        """
        test_name = "FA2_optional_interfaces_admin" + fa2.ledger_type + test_name

        @sp.add_test(name=test_name, is_default=False)
        def test():
            sc = sp.test_scenario()
            sc += fa2
            sc.h1(test_name)
            sc.h2("Non admin cannot set admin")
            fa2.set_administrator(alice.address).run(
                sender=alice, valid=False, exception="FA2_NOT_ADMIN"
            )
            fa2.set_administrator(admin2.address).run(sender=admin)
            sc.verify(~fa2.is_administrator(admin.address))
            sc.verify(fa2.is_administrator(admin2.address))
            fa2.set_administrator(admin.address).run(sender=admin2)

    def test_mint(fa2, test_name=""):
        """Test `Mint*` mixin.

        - `mint` fails with `FA2_NOT_ADMIN` for non-admin.
        - `mint` adds the tokens.
        - `mint` update the supply.
        - `mint` works for existing tokens in fungible contracts.
        """
        test_name = "FA2_mint_" + fa2.ledger_type + test_name

        def mint_nft(sc):
            sc.h2("Mint entrypoint")
            # Non admin cannot mint a new NFT token.
            sc.h3("NFT mint failure")
            fa2.mint([sp.record(metadata=tok0_md, to_=alice.address)]).run(
                sender=alice, valid=False, exception="FA2_NOT_ADMIN"
            )

            sc.h3("Mint")
            # Mint of a new NFT token.
            fa2.mint(
                [
                    sp.record(metadata=tok0_md, to_=alice.address),
                    sp.record(metadata=tok1_md, to_=alice.address),
                    sp.record(metadata=tok2_md, to_=bob.address),
                ]
            ).run(sender=admin)

            # Check that the balance is updated.
            sc.verify(fa2.get_balance(sp.record(owner=alice.address, token_id=0)) == 1)
            sc.verify(fa2.get_balance(sp.record(owner=bob.address, token_id=0)) == 0)
            sc.verify(fa2.get_balance(sp.record(owner=alice.address, token_id=1)) == 1)
            sc.verify(fa2.get_balance(sp.record(owner=bob.address, token_id=1)) == 0)
            sc.verify(fa2.get_balance(sp.record(owner=alice.address, token_id=2)) == 0)
            sc.verify(fa2.get_balance(sp.record(owner=bob.address, token_id=2)) == 1)

            # Check that the supply is updated.
            sc.verify(fa2.total_supply(sp.record(token_id=0)) == 1)
            sc.verify(fa2.total_supply(sp.record(token_id=1)) == 1)
            sc.verify(fa2.total_supply(sp.record(token_id=2)) == 1)

        def mint_fungible(sc):
            sc.h2("Mint entrypoint")
            # Non admin cannot mint a new fungible token.
            sc.h3("Fungible mint failure")
            fa2.mint(
                [
                    sp.record(
                        token=sp.variant("new", tok0_md), to_=alice.address, amount=1000
                    )
                ]
            ).run(sender=alice, valid=False, exception="FA2_NOT_ADMIN")

            sc.h3("Mint")
            # Mint of a new fungible token.
            fa2.mint(
                [
                    sp.record(
                        token=sp.variant("new", tok0_md), to_=alice.address, amount=1000
                    )
                ]
            ).run(sender=admin)

            # Check ledger update.
            sc.verify(
                fa2.get_balance(sp.record(owner=alice.address, token_id=0)) == 1000
            )
            sc.verify(fa2.get_balance(sp.record(owner=bob.address, token_id=0)) == 0)
            # Check supply update.
            sc.verify(fa2.total_supply(sp.record(token_id=0)) == 1000)

            # Mint a new and existing token.
            fa2.mint(
                [
                    sp.record(
                        token=sp.variant("new", tok1_md), to_=alice.address, amount=1000
                    ),
                    sp.record(
                        token=sp.variant("existing", 0), to_=alice.address, amount=1000
                    ),
                    sp.record(
                        token=sp.variant("existing", 1), to_=bob.address, amount=1000
                    ),
                ]
            ).run(sender=admin)

            # Check ledger update.
            sc.verify(
                fa2.get_balance(sp.record(owner=alice.address, token_id=0)) == 2000
            )
            sc.verify(fa2.get_balance(sp.record(owner=bob.address, token_id=0)) == 0)
            sc.verify(
                fa2.get_balance(sp.record(owner=alice.address, token_id=1)) == 1000
            )
            sc.verify(fa2.get_balance(sp.record(owner=bob.address, token_id=1)) == 1000)
            # Check supply update.
            sc.verify(fa2.total_supply(sp.record(token_id=0)) == 2000)
            sc.verify(fa2.total_supply(sp.record(token_id=1)) == 2000)

        def mint_single_asset(sc):
            sc.h2("Mint entrypoint")
            # Non admin cannot mint a new fungible token.
            sc.h3("Single asset mint failure")
            fa2.mint([sp.record(to_=alice.address, amount=1000)]).run(
                sender=alice, valid=False, exception="FA2_NOT_ADMIN"
            )

            sc.h3("Mint")
            # Mint some tokens
            fa2.mint([sp.record(to_=alice.address, amount=1000)]).run(sender=admin)

            # Check ledger update.
            sc.verify(
                fa2.get_balance(sp.record(owner=alice.address, token_id=0)) == 1000
            )
            sc.verify(fa2.get_balance(sp.record(owner=bob.address, token_id=0)) == 0)
            # Check supply update.
            sc.verify(fa2.total_supply(sp.record(token_id=0)) == 1000)

            # multiple mint
            fa2.mint(
                [
                    sp.record(to_=alice.address, amount=1000),
                    sp.record(to_=bob.address, amount=1000),
                    sp.record(to_=bob.address, amount=1000),
                ]
            ).run(sender=admin)

            # Check ledger update.
            sc.verify(
                fa2.get_balance(sp.record(owner=alice.address, token_id=0)) == 2000
            )
            sc.verify(fa2.get_balance(sp.record(owner=bob.address, token_id=0)) == 2000)
            # Check supply update.
            sc.verify(fa2.total_supply(sp.record(token_id=0)) == 4000)

        @sp.add_test(name=test_name, is_default=False)
        def test():
            sc = sp.test_scenario()
            sc += fa2
            sc.h1(test_name)
            if fa2.ledger_type == "NFT":
                mint_nft(sc)
            elif fa2.ledger_type == "Fungible":
                mint_fungible(sc)
            elif fa2.ledger_type == "SingleAsset":
                mint_single_asset(sc)
            else:
                raise Exception(
                    'fa2.ledger type must be "NFT", "Fungible" or "SingleAsset".'
                )

    def test_burn(fa2, test_name=""):
        """Test `Burn*` mixin.

        - non operator cannot burn, it fails appropriately.
        - owner can burn.
        - burn fails with `FA2_INSUFFICIENT_BALANCE` when needed.
        - operator can burn if the policy allows it.
        """
        test_name = "FA2_burn_" + fa2.ledger_type + test_name

        @sp.add_test(name=test_name, is_default=False)
        def test():
            amount = 1 if fa2.ledger_type == "NFT" else 20
            sc = sp.test_scenario()
            sc += fa2
            sc.h1(test_name)
            sc.h2("Burn entrypoint")

            # Check that non operator cannot burn others tokens.
            sc.h3("Cannot burn others tokens")
            exception = (
                "FA2_NOT_OPERATOR" if fa2.policy.supports_transfer else "FA2_TX_DENIED"
            )
            fa2.burn([sp.record(token_id=0, from_=alice.address, amount=1)]).run(
                sender=bob, valid=False, exception=exception
            )

            # Not allowed transfers
            if not fa2.policy.supports_transfer:
                fa2.burn(
                    [sp.record(token_id=0, from_=alice.address, amount=amount)]
                ).run(sender=alice, valid=False, exception="FA2_TX_DENIED")
                return

            # Owner can burn.
            sc.h3("Owner burns his nft tokens")
            fa2.burn([sp.record(token_id=0, from_=alice.address, amount=amount)]).run(
                sender=alice
            )

            if fa2.ledger_type == "NFT":
                # Check that the contract storage is updated.
                sc.verify(~fa2.data.ledger.contains(0))
                # Check that burning an nft removes token_metadata.
                sc.verify(~fa2.data.token_metadata.contains(0))
            else:
                # Check ledger update.
                sc.verify(
                    fa2.get_balance(sp.record(owner=alice.address, token_id=0)) == 22
                )
                # Check that burning doesn't remove token_metadata.
                sc.verify(fa2.data.token_metadata.contains(0))
                # Check supply update.
                sc.verify(fa2.total_supply(sp.record(token_id=0)) == 22)

            # Check burn of FA2_INSUFFICIENT_BALANCE.
            sc.h3("Burn with insufficent balance")
            token_id = 0 if fa2.ledger_type == "SingleAsset" else 1
            fa2.burn(
                [sp.record(token_id=token_id, from_=alice.address, amount=43)]
            ).run(sender=alice, valid=False, exception="FA2_INSUFFICIENT_BALANCE")

            if fa2.policy.supports_operator:
                # Add operator to test if he can burn on behalf of the owner.
                sc.h3("Operator can burn on behalf of the owner")
                operator_bob = sp.record(
                    owner=alice.address, operator=bob.address, token_id=token_id
                )
                fa2.update_operators([sp.variant("add_operator", operator_bob)]).run(
                    sender=alice
                )
                # Operator can burn nft on behalf of the owner.
                fa2.burn(
                    [sp.record(token_id=token_id, from_=alice.address, amount=0)]
                ).run(sender=bob)

    def test_withdraw_mutez(fa2, test_name=""):
        """Test of WithdrawMutez.

        - non admin cannot withdraw mutez: FA2_NOT_ADMIN.
        - admin can withdraw mutez.
        """
        test_name = "FA2_withdraw_mutez" + fa2.ledger_type + test_name

        @sp.add_test(name=test_name, is_default=False)
        def test():
            sc = sp.test_scenario()
            sc += fa2
            sc.h1(test_name)
            sc.h2("Mutez receiver contract")

            class Wallet(sp.Contract):
                @sp.entry_point
                def default(self):
                    pass

            wallet = Wallet()
            sc += wallet

            # Non admin cannot withdraw mutez.
            sc.h2("Non admin cannot withdraw_mutez")
            fa2.withdraw_mutez(destination=wallet.address, amount=sp.tez(10)).run(
                sender=alice, amount=sp.tez(42), valid=False, exception="FA2_NOT_ADMIN"
            )

            # Admin can withdraw mutez.
            sc.h3("Admin withdraw_mutez")
            fa2.withdraw_mutez(destination=wallet.address, amount=sp.tez(10)).run(
                sender=admin, amount=sp.tez(42)
            )

            # Check that the mutez has been transfered.
            sc.verify(fa2.balance == sp.tez(32))
            sc.verify(wallet.balance == sp.tez(10))

    def test_change_metadata(fa2, test_name=""):
        """Test of ChangeMetadata.

        - non admin cannot set metadata
        - `set_metadata` works as expected
        """
        test_name = "FA2_change_metadata" + fa2.ledger_type + test_name

        @sp.add_test(name=test_name, is_default=False)
        def test():
            sc = sp.test_scenario()
            sc += fa2
            sc.h1(test_name)
            sc.h2("Change metadata")
            sc.h3("Non admin cannot set metadata")
            fa2.set_metadata(sp.utils.metadata_of_url("http://example.com")).run(
                sender=alice, valid=False, exception="FA2_NOT_ADMIN"
            )

            sc.h3("Admin set metadata")
            fa2.set_metadata(sp.utils.metadata_of_url("http://example.com")).run(
                sender=admin
            )

            # Check that the metadata has been updated.
            sc.verify_equal(
                fa2.data.metadata[""],
                sp.utils.metadata_of_url("http://example.com")[""],
            )

    def test_get_balance_of(fa2, test_name=""):
        """Test of `OnchainviewBalanceOf`

        - `get_balance_of` doesn't deduplicate nor reorder on nft.
        - `get_balance_of` doesn't deduplicate nor reorder on fungible.
        - `get_balance_of` fails with `FA2_TOKEN_UNDEFINED` when needed on nft.
        - `get_balance_of` fails with `FA2_TOKEN_UNDEFINED` when needed on fungible.
        """
        test_name = "FA2_get_balance_of" + fa2.ledger_type + test_name

        @sp.add_test(name=test_name, is_default=False)
        def test():
            sc = sp.test_scenario()
            sc += fa2
            sc.h1(test_name)

            # get_balance_of on fungible
            # We deliberately give multiple identical params to check for
            # non-deduplication and non-reordering.

            balance = fa2.get_balance_of(
                [
                    sp.record(owner=alice.address, token_id=0),
                    sp.record(owner=alice.address, token_id=0),
                    sp.record(owner=bob.address, token_id=0),
                    sp.record(owner=alice.address, token_id=0),
                ]
            )
            if fa2.ledger_type == "NFT":
                sc.verify_equal(
                    balance,
                    sp.set_type_expr(
                        [
                            sp.record(
                                balance=1,
                                request=sp.record(owner=alice.address, token_id=0),
                            ),
                            sp.record(
                                balance=1,
                                request=sp.record(owner=alice.address, token_id=0),
                            ),
                            sp.record(
                                balance=0,
                                request=sp.record(owner=bob.address, token_id=0),
                            ),
                            sp.record(
                                balance=1,
                                request=sp.record(owner=alice.address, token_id=0),
                            ),
                        ],
                        sp.TList(t_balance_of_response),
                    ),
                )
            else:
                sc.verify_equal(
                    balance,
                    sp.set_type_expr(
                        [
                            sp.record(
                                balance=42,
                                request=sp.record(owner=alice.address, token_id=0),
                            ),
                            sp.record(
                                balance=42,
                                request=sp.record(owner=alice.address, token_id=0),
                            ),
                            sp.record(
                                balance=0,
                                request=sp.record(owner=bob.address, token_id=0),
                            ),
                            sp.record(
                                balance=42,
                                request=sp.record(owner=alice.address, token_id=0),
                            ),
                        ],
                        sp.TList(t_balance_of_response),
                    ),
                )

            # Check that on-chain view fails on undefined tokens.
            sc.verify(
                sp.catch_exception(
                    fa2.get_balance_of([sp.record(owner=alice.address, token_id=5)])
                )
                == sp.some("FA2_TOKEN_UNDEFINED")
            )

    def test_offchain_token_metadata(fa2, test_name=""):
        """Test `OffchainviewTokenMetadata`.

        Tests:

        - `token_metadata` works as expected on nft and fungible.
        """
        test_name = "FA2_offchain_token_metadata" + fa2.ledger_type + test_name

        @sp.add_test(name=test_name, is_default=False)
        def test():
            sc = sp.test_scenario()
            sc += fa2
            sc.h1(test_name)
            sc.verify_equal(
                fa2.token_metadata(0), sp.record(token_id=0, token_info=tok0_md)
            )

    def test_pause(fa2, test_name=""):
        """Test the `Pause` policy decorator.

        - transfer works without pause
        - transfer update_operators without pause
        - non admin cannot set_pause
        - admin can set pause
        - transfer fails with ('FA2_TX_DENIED', 'FA2_PAUSED') when paused.
        - update_operators fails with
        ('FA2_OPERATORS_UNSUPPORTED', 'FA2_PAUSED') when paused.
        """
        test_name = "FA2_pause_" + fa2.ledger_type + test_name

        @sp.add_test(name=test_name)
        def test():
            sc = sp.test_scenario()
            sc.h1(test_name)
            sc.table_of_contents()
            sc.h2("Accounts")
            sc.show([admin, alice, bob])
            sc.h2("FA2 Contract")
            sc += fa2

            sc.h2("Transfer without pause")
            fa2.transfer(
                [
                    sp.record(
                        from_=alice.address,
                        txs=[sp.record(to_=alice.address, amount=0, token_id=0)],
                    ),
                ]
            ).run(sender=alice)

            sc.h2("Update_operator without pause")
            fa2.update_operators(
                [
                    sp.variant(
                        "add_operator",
                        sp.record(
                            owner=alice.address, operator=alice.address, token_id=0
                        ),
                    ),
                    sp.variant(
                        "remove_operator",
                        sp.record(
                            owner=alice.address, operator=alice.address, token_id=0
                        ),
                    ),
                ]
            ).run(sender=alice)

            sc.h2("Pause entrypoint")
            sc.h3("Non admin cannot set pause")
            fa2.set_pause(True).run(
                sender=alice, valid=False, exception="FA2_NOT_ADMIN"
            )

            sc.h3("Admin set pause")
            fa2.set_pause(True).run(sender=admin)

            sc.h2("Transfer fails with pause")
            fa2.transfer(
                [
                    sp.record(
                        from_=alice.address,
                        txs=[sp.record(to_=alice.address, amount=0, token_id=0)],
                    ),
                ]
            ).run(sender=alice, valid=False, exception=("FA2_TX_DENIED", "FA2_PAUSED"))

            sc.h2("Update_operator fails with pause")
            fa2.update_operators(
                [
                    sp.variant(
                        "add_operator",
                        sp.record(
                            owner=alice.address, operator=alice.address, token_id=0
                        ),
                    ),
                    sp.variant(
                        "remove_operator",
                        sp.record(
                            owner=alice.address, operator=alice.address, token_id=0
                        ),
                    ),
                ]
            ).run(
                sender=alice,
                valid=False,
                exception=("FA2_OPERATORS_UNSUPPORTED", "FA2_PAUSED"),
            )


################################################################################


if "templates" not in __name__:
    ###################
    # Fa2_nft_minimal #
    ###################

    test_core_interfaces(Fa2NftMinimalTest(), "minimal")
    test_transfer(Fa2NftMinimalTest(), "minimal")
    test_owner_or_operator_transfer(Fa2NftMinimalTest(), "minimal")
    test_balance_of(Fa2NftMinimalTest(), "minimal")

    ########################
    # Fa2_fungible_minimal #
    ########################

    test_core_interfaces(Fa2FungibleMinimalTest(), "minimal")
    test_transfer(Fa2FungibleMinimalTest(), "minimal")
    test_owner_or_operator_transfer(Fa2FungibleMinimalTest(), "minimal")
    test_balance_of(Fa2FungibleMinimalTest(), "minimal")
