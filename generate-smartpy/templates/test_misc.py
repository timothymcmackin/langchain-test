import smartpy as sp

class C(sp.Contract):
    def __init__(self):
        self.init(xy = (0,0))

    @sp.entry_point
    def ep1(self):
        self.data.xy = (sp.snd(self.data.xy), sp.fst(self.data.xy))

    @sp.entry_point
    def ep2(self):
        self.data.xy = (sp.snd(sp.fst((self.data,())).xy), sp.fst(sp.fst((self.data,())).xy))

    @sp.entry_point
    def ep3(self):
        self.data.xy = (sp.fst(self.data.xy), sp.fst(self.data.xy))

    @sp.entry_point
    def ep4(self):
        self.data.xy = (sp.snd(self.data.xy), sp.snd(self.data.xy))

    @sp.entry_point
    def ep5(self, params):
        sp.set_type(params, sp.TNat)
        with (sp.ediv(params,2)).match_cases() as arg:
          with arg.match('None') as _:
            self.data.xy = (0,0)
          with arg.match('Some') as s65:
            self.data.xy = (1,1)

    @sp.entry_point
    def ep6(self, params):
        sp.set_type(params, sp.TNat)
        with (sp.ediv(params,2)).match_cases() as arg:
          with arg.match('Some') as s65:
            self.data.xy = (1,1)
          with arg.match('None') as _:
            self.data.xy = (0,0)

@sp.add_test(name = "Misc")
def test():
    scenario = sp.test_scenario()
    scenario += C()

sp.add_compilation_target("test_misc", C())
