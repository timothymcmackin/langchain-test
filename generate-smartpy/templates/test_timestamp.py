import smartpy as sp

class C(sp.Contract):
    def __init__(self):
        self.init(out = False, next = sp.timestamp(0))

    @sp.entry_point
    def ep(self):
        self.data.out = sp.now > sp.now.add_seconds(1)
        sp.verify(sp.now.add_seconds(12) - sp.now == 12)
        sp.verify(sp.now - sp.now.add_seconds(12) == -12)
        sp.verify(sp.now - sp.now.add_seconds(12) == -12)
        sp.verify(sp.add(sp.now, sp.int(500)) == sp.timestamp(1500))
        sp.verify(sp.add(sp.int(500), sp.now) == sp.timestamp(1500))
        self.data.next = sp.now.add_seconds(24 * 3600)

@sp.add_test(name = "Timestamp")
def test():
    scenario  = sp.test_scenario()
    scenario.h1("Timestamps")
    c = C()
    scenario += c
    c.ep().run(now = sp.timestamp(1000))

sp.add_compilation_target("testTimestamp", C())
