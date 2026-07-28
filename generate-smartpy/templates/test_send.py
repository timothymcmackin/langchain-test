import smartpy as sp

dest1 = sp.address("tz1M9CMEtsXm3QxA7FmMU2Qh7xzsuGXVbcDr")
dest2 = sp.address("tz1YtuZ4vhzzn7ssCt93Put8U9UJDdvCXci4")

class C1(sp.Contract):
    @sp.entry_point
    def ep(self):
        sp.send(dest1, sp.tez(1))

class C2(sp.Contract):
    @sp.entry_point
    def ep(self, cond):
        sp.if cond == True:
             sp.send(dest2, sp.tez(2))

class C3(sp.Contract):
    @sp.entry_point
    def ep1(self):
        sp.send(dest1, sp.tez(1))

    @sp.entry_point
    def ep2(self):
        pass

class C4(sp.Contract):
    @sp.entry_point
    def ep1(self):
        sp.send(dest1, sp.tez(1))

    @sp.entry_point
    def ep2(self, cond):
        sp.if cond == True:
            sp.send(dest2, sp.tez(2))

class C5(sp.Contract):
    @sp.entry_point
    def ep(self, params):
        sp.if params == True:
            sp.send(dest1, sp.tez(1))
        sp.else:
            sp.verify(params == False)

class C6(sp.Contract):
    @sp.entry_point
    def ep(self):
        c = sp.contract(sp.TInt, dest1, entry_point = "myEntryPoint")
        sp.transfer(-42, sp.mutez(0), c.open_some())

@sp.add_test(name = "Send")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Send")
    scenario += C1()
    scenario += C2()
    scenario += C3()
    scenario += C4()
    scenario += C5()
    scenario += C6()

sp.add_compilation_target("testSend", C1())
