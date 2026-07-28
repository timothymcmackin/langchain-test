import smartpy as sp

T = sp.TRecord(
    now = sp.TTimestamp,
    level = sp.TNat,
    amount = sp.TMutez,
    balance = sp.TMutez,
    chain_id = sp.TChainId,
    sender = sp.TAddress,
    source = sp.TAddress,
    total_voting_power = sp.TNat
)

class Lib(sp.Contract):
    def __init__(self):
        self.init(x = 10, z = sp.nat(42))

    @sp.onchain_view()
    def view1(self):
        sp.result(
            sp.record(z = self.data.z, self_addr = sp.self_address)
        )

    @sp.onchain_view()
    def view2(self):
        sp.result(self.data.z)

    @sp.onchain_view()
    def view3(self, a):
        sp.result(self.data.x * a)

class Lib2(Lib):
    @sp.entry_point(lazify = True)
    def ep3(self):
        self.data.y = self.data.y * 2

class C(sp.Contract):
    def __init__(self, c):
        self.init(
            result = sp.none,
            result2 = sp.none,
            contract = c,
            self_addr = sp.none,
            self_addr_2 = sp.none,
            self_addr_3 = sp.none
        )

    @sp.onchain_view(name="a_really_good_name")
    def view(self):
        sp.result(
            sp.record(
                now = sp.now,
                level = sp.level,
                amount = sp.amount,
                balance = sp.balance,
                chain_id = sp.chain_id,
                sender = sp.sender,
                source = sp.source,
                total_voting_power = sp.total_voting_power
            )
        )

    @sp.entry_point
    def store(self):
        self.data.self_addr = sp.some(sp.self_address)
        res = sp.compute(
            sp.view(
                "view1",
                self.data.contract,
                sp.unit, t = sp.TRecord(z = sp.TNat, self_addr = sp.TAddress)
            ).open_some("Invalid view")
        )
        self.data.result2 = sp.view("a_really_good_name", sp.self_address, sp.unit, t = T)
        self.data.result = sp.some(res.z)
        self.data.self_addr_2 = sp.some(res.self_addr)
        self.data.self_addr_3 = sp.some(sp.self_address)
        sp.verify(self.data.self_addr == self.data.self_addr_3)
        sp.verify(self.data.self_addr_2 == sp.some(self.data.contract))

    @sp.entry_point
    def check_view(self):
        """ Check view, possibly missing but not failing """
        sp.compute(sp.view("abc", sp.self_address, sp.unit, sp.TUnit))

    @sp.entry_point
    def failing_entry_point(self):
        sp.failwith("This is a failure")

@sp.add_test(name = "Lib")
def test():
    s = sp.test_scenario()

    alice = sp.test_account("alice")

    lib = Lib()
    s += lib
    s.verify(lib.view2() == 42)
    s.verify(lib.view3(2) == 20)

    lib2 = Lib()
    s += lib2
    s.verify(lib2.view2() == 42)
    s.verify(lib2.view3(2) == 20)

    c = C(lib.address)
    c.set_initial_balance(sp.mutez(1234))
    s += c

    # This fails in Hangzhou
    c.store().run(
        now = sp.timestamp(1),
        level = 101,
        amount = sp.mutez(100),
        chain_id = sp.chain_id_cst("0x9caecab9"),
        source = alice,
        sender = alice,
        voting_powers = {
            sp.key_hash("KT1TezoooozzSmartPyzzSTATiCzzzwwBFA1") : 10
        }
    )

    s.show(c.data.result2.open_some())

    s.verify(c.data.result2.open_some() == sp.record(
        now = sp.timestamp(1),
        level = 101,
        amount = sp.mutez(0),
        balance = sp.mutez(1334),
        chain_id = sp.chain_id_cst("0x9caecab9"),
        total_voting_power = 10,
        sender = c.address,
        source = alice.address))

    c.store().run(
        now = sp.timestamp(2),
        level = 102,
        amount = sp.mutez(150),
        chain_id = sp.chain_id_cst("0x9caecab9"),
        source = alice,
        sender = c.address,
        voting_powers = {
            sp.key_hash("KT1TezoooozzSmartPyzzSTATiCzzzwwBFA1") : 10
        }
    )

    s.verify(c.data.result2.open_some() == sp.record(
        now = sp.timestamp(2),
        level = 102,
        amount = sp.mutez(0),
        balance = sp.mutez(1484),
        chain_id = sp.chain_id_cst("0x9caecab9"),
        total_voting_power = 10,
        sender = c.address,
        source = alice.address))

    c.failing_entry_point().run(
        valid = False,
        now = sp.timestamp(3),
        level = 103,
        amount = sp.mutez(100),
        chain_id = sp.chain_id_cst("0x9caecab9"),
        source = alice,
        sender = c.address,
        voting_powers = {
            sp.key_hash("KT1TezoooozzSmartPyzzSTATiCzzzwwBFA1") : 10
        }
    )

    c.store().run(
        amount = sp.mutez(200),
        source = alice,
        sender = alice,
    )

    s.verify(c.data.result2.open_some() == sp.record(
        now = sp.timestamp(2),
        level = 102,
        amount = sp.mutez(0),
        balance = sp.mutez(1684),
        chain_id = sp.chain_id_cst("0x9caecab9"),
        total_voting_power = 10,
        sender = c.address,
        source = alice.address))

    c.store().run(
        source = alice,
        sender = alice,
    )

    s.verify(c.data.result2.open_some() == sp.record(
        now = sp.timestamp(2),
        level = 102,
        amount = sp.mutez(0),
        balance = sp.mutez(1684),
        chain_id = sp.chain_id_cst("0x9caecab9"),
        total_voting_power = 10,
        sender = c.address,
        source = alice.address))

    view_result = s.compute(c.view(), source=alice, sender=c.address)

    s.verify(view_result == sp.record(
        now = sp.timestamp(2),
        level = 102,
        amount = sp.mutez(0),
        balance = sp.mutez(1684),
        chain_id = sp.chain_id_cst("0x9caecab9"),
        total_voting_power = 10,
        sender = c.address,
        source = alice.address))

    s.verify(s.compute(c.view(), source=alice, sender=c.address, now=sp.timestamp(42)) == sp.record(
        now = sp.timestamp(42),
        level = 102,
        amount = sp.mutez(0),
        balance = sp.mutez(1684),
        chain_id = sp.chain_id_cst("0x9caecab9"),
        total_voting_power = 10,
        sender = c.address,
        source = alice.address))

    s.verify(s.compute(lib.view1()) == sp.record(z=42, self_addr=lib.address))
