# WARNING Saplings are an experimental feature of Tezos that has not undergone
# any security review. For more details see
# https://tezos.gitlab.io/kathmandu/sapling.html.
# Do not reuse the code from this file in real-world applications.

import smartpy as sp


class MyContract(sp.Contract):
    def __init__(self):
        self.init_type(sp.TRecord(ledger=sp.TSaplingState()))

    @sp.entry_point
    def handle(self, operations):
        with sp.for_("operation", operations) as operation:
            result = sp.compute(
                sp.sapling_verify_update(
                    self.data.ledger, operation.transaction
                ).open_some(),
            )
            bound_data, amount, ledger = sp.match_tuple(result, "bound_data", "amount", "ledger")
            self.data.ledger = ledger
            amount_tez = sp.local(
                "amount_tez", sp.split_tokens(sp.mutez(1), abs(amount), 1)
            )
            with sp.if_(amount > 0):
                # bound_dest = sp.unpack(bound_data, sp.TAddress).open_some()
                dest = sp.implicit_account(operation.key.open_some())
                # sp.verify(bound_dest == sp.to_address(dest))
                sp.transfer(sp.unit, amount_tez.value, dest)
            with sp.else_():
                sp.verify(~operation.key.is_some())
                sp.verify(sp.amount == amount_tez.value)


@sp.add_test(name="Sapling2")
def test():
    scenario = sp.test_scenario()
    alice = sp.test_account("alice")

    scenario.h1("Sapling2")

    c1 = MyContract()
    c1.init_storage(sp.record(ledger=sp.sapling_empty_state(8)))

    scenario += c1

    c1.handle(
        [
            sp.record(
                key=sp.none,
                transaction=sp.sapling_test_transaction(
                    "", "alice", 12_000_000, 8, "0x00"
                ),
            )
        ]
    ).run(valid=False)

    c1.handle(
        [
            sp.record(
                key=sp.none,
                transaction=sp.sapling_test_transaction(
                    "", "alice", 12000000, 8, "0x00"
                ),
            )
        ]
    ).run(amount=sp.tez(12))

    c1.handle(
        [
            sp.record(
                key=sp.none,
                transaction=sp.sapling_test_transaction(
                    "alice", "bob", 2000000, 8, "0x00"
                ),
            )
        ]
    ).run(amount=sp.tez(2), valid=False)

    c1.handle(
        [
            sp.record(
                key=sp.none,
                transaction=sp.sapling_test_transaction(
                    "alice", "bob", 2000000, 8, "0x00"
                ),
            )
        ]
    ).run()

    scenario.show(sp.pack(alice.address))
    c1.handle(
        [
            sp.record(
                key=sp.some(alice.public_key_hash),
                transaction=sp.sapling_test_transaction(
                    "alice", "", 2000000, 8, "0x00"
                ),
            )
        ]
    ).run()

    c1.handle(
        [
            sp.record(
                key=sp.some(alice.public_key_hash),
                transaction=sp.sapling_test_transaction(
                    "alice", "", 8000000, 8, "0x00"
                ),
            )
        ]
    ).run()

    c1.handle(
        [
            sp.record(
                key=sp.some(alice.public_key_hash),
                transaction=sp.sapling_test_transaction("alice", "", 1, 8, "0x00"),
            )
        ]
    ).run(valid=False)
