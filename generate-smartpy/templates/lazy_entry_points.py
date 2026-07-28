import smartpy as sp

class C(sp.Contract):
    def __init__(self):
        self.set_initial_balance(sp.tez(100))
        self.init(x = 1, y = True)

    @sp.entry_point(lazify = True)
    def modify_x(self, n):
        self.data.x = n

    @sp.entry_point(lazify = True)
    def modify_x2(self, n):
        self.data.x = 2 * n

    @sp.entry_point(lazify = False)
    def modify_x3(self, n):
        self.data.x = 3 * n

    @sp.entry_point(lazify = False)
    def update_modify_x(self, ep):
        sp.set_entry_point("modify_x", ep)

    @sp.entry_point(lazify = True, lazy_no_code = True)
    def bounce(self, p):
        sp.set_type(p, sp.TAddress)

    @sp.entry_point(lazify = False)
    def update_bounce(self, ep):
        sp.set_entry_point("bounce", ep)
        sp.send(sp.sender, sp.tez(1))

    @sp.entry_point(lazify = False)
    def take_ticket(self, p):
        sp.set_type(p, sp.TTicket(sp.TInt))

    @sp.entry_point
    def check_bounce(self):
        sp.verify(sp.has_entry_point("bounce"))

    @sp.onchain_view()
    def get_entrypoint(self, ep_id):
        sp.result(sp.entrypoint_map()[ep_id])

    @sp.onchain_view()
    def modify_x_id(self):
        sp.result(sp.entrypoint_id("modify_x"))

def ep_incr(self, params):
    self.data.x += params

def ep_decr(self, params):
    self.data.x -= params

def ep_decr_transfers(self, params):
    sp.send(sp.test_account("me").address, sp.tez(1))
    sp.send(sp.test_account("me").address, sp.tez(2))
    self.data.x -= params

def ep_bounce(self, params):
    sp.send(params, sp.mutez(2))

@sp.add_test(name = "Upgrade")
def test():
    s = sp.test_scenario()

    s.table_of_contents()

    s.h1("Upgradable and lazy entrypoints")

    alice = sp.test_account("Alice")
    bob = sp.test_account("Bob")

    c = C()
    s += c

    s.h2("Use initial entrypoint")
    c.modify_x(1)
    c.modify_x(2)
    c.modify_x(3)
    s.verify(c.data.x == 3)

    s.h1("Updating an entrypoint")

    s.h2("Switch it to incrementing")
    c.update_modify_x(sp.utils.wrap_entry_point("modify_x", ep_incr))
    c.modify_x(1)
    c.modify_x(2)
    c.modify_x(3)
    s.verify(c.data.x == 9)

    s.h2("Switch it to decrementing")
    c.update_modify_x(sp.utils.wrap_entry_point("modify_x", ep_decr))
    c.modify_x(1)
    c.modify_x(2)
    c.modify_x(3)
    s.verify(c.data.x == 3)

    s.h2("Switch it to decrementing with additional transfers")
    c.update_modify_x(sp.utils.wrap_entry_point("modify_x", ep_decr_transfers))
    c.modify_x(1)
    c.modify_x(2)
    c.modify_x(3)
    s.verify(c.data.x == -3)

    s.h1("Testing the presence of an entrypoint")

    s.h2("entrypoint is still absent (lazy_no_code)")
    c.check_bounce().run(valid = False)
    c.bounce(alice.address).run(valid = False)

    s.h2("Add entrypoint and call it")
    c.update_bounce(sp.utils.wrap_entry_point("bounce", ep_bounce)).run(sender = bob)
    c.bounce(alice.address)
    c.check_bounce()


    s.h1("Use entrypoint from another contract")

    c2 = C()
    s += c2

    s.p("Original entry point:")
    c.update_modify_x(c2.get_entrypoint(c2.modify_x_id()))
    c.modify_x(42)
    s.verify(c.data.x == 42)

    s.p("Modified entry point (obtained via view, using entrypoint):")
    c2.update_modify_x(sp.utils.wrap_entry_point("modify_x", ep_decr))
    c.update_modify_x(c2.get_entrypoint(c2.modify_x_id()))
    c.modify_x(5)
    s.verify(c.data.x == 37)

    s.p("Modified entry point (obtained via sp.contract_entrypoint):")
    c2.update_modify_x(sp.utils.wrap_entry_point("modify_x", ep_incr))
    c.update_modify_x(sp.contract_entrypoint(c2, "modify_x"))
    c.modify_x(5)
    s.verify(c.data.x == 42)

    s.p("Entrypoint map and ids")
    s.verify(c2.modify_x_id() == 1)
    s.verify(sp.contract_entrypoint_id(c, "modify_x") == 1)
    s.verify(sp.contract_entrypoint_map(c).contains(1))
