# Hash Functions - Example for illustrative purposes only.

import smartpy as sp

class TestHashes(sp.Contract):
    def __init__(self):
        self.init(
            v = sp.bytes('0x'),
            b2b = sp.bytes('0x'),
            s256 = sp.bytes('0x'),
            s512 = sp.bytes('0x'),
            sha3 = sp.bytes('0x'),
            keccak = sp.bytes('0x'),
            tz1 = sp.key_hash("tz1M9CMEtsXm3QxA7FmMU2Qh7xzsuGXVbcDr"))

    @sp.entry_point
    def new_value(self, some_bytes):
        self.data.v = some_bytes
        self.data.b2b = sp.blake2b(some_bytes)
        self.data.s256 = sp.sha256 (some_bytes)
        self.data.s512 = sp.sha512 (some_bytes)
        self.data.sha3 = sp.sha3 (some_bytes)
        self.data.keccak = sp.keccak (some_bytes)

    @sp.entry_point
    def new_key(self, pubkey):
        self.data.tz1 = sp.hash_key(pubkey)

@sp.add_test(name = "HashFunctions")
def test():
    bob = sp.test_account("Robert")
    c1 = TestHashes()
    scenario = sp.test_scenario()
    scenario.h1("Hash Functions")
    scenario += c1
    c1.new_value(sp.bytes('0x001234'))
    c1.new_key(bob.public_key)
    scenario.verify_equal(
        c1.data,
        sp.record(
            v = sp.bytes('0x001234'),
            b2b = sp.bytes('0xFFFDFD672FF9075528F51A30408CF768A093D8C67FB3C5C8782DFF49EAB0724D'),
            s256 = sp.bytes('0x61A706DFE2DDB1339D7B1D6F10C15A26786DCD1C99B743E0B0E351A6A168D99F'),
            s512 = sp.bytes('0x0110F7F5DC329EED3F1D0E8D1AE204CC58B2A790506ACFB793200FC60BA22525DE2C5147FFF19128807352A3A33C44D673CBDA3B9840973FDFE4AD6516A73A49'),
            sha3 = sp.bytes('0x6c487a73002ced6e865cc88e87fc0ead2dbb1d8b4b5b90aea7e3254e9060ca95'),
            keccak = sp.bytes('0xa3e1b4de203e0e5d02205d680485390711ef58bc4c3687b17277b62fde10a45d'),
            tz1 = bob.public_key_hash))

sp.add_compilation_target("testHashFunctions", TestHashes())
