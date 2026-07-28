import smartpy as sp

class C(sp.Contract):
    def __init__(self):
        self.init(r = 0)

#    @sp.entry_point
#    def ep1(self, params):
#        self.data.r = 1000 * sp.ematch(params,
#                                       [ ("A", lambda x: x*2) ,
#                                         ("B", lambda x: x*3) ])

#    @sp.entry_point
#    def ep2(self, params):
#        sp.set_type(params, sp.TOption(sp.TString))
#        self.data.r = 1000 * sp.eif_some(params, lambda x: x*2, 0)

#    @sp.entry_point
#    def ep3(self, params):
#        self.data.r = 1000 * sp.eif(params, 2, 3)

#    @sp.entry_point
#    def ep4(self, params):
#        self.data.r = 1000 * sp.eif_somef(params, self.factorial, lambda _: 0)

#    @sp.entry_point
#    def ep5(self):
#        self.data.r = 1000 * sp.eiff(params, self.factorial_five, lambda _: 0)

@sp.add_test(name = "Match")
def test():
    s = sp.test_scenario()
    s += C()
