# Test empty data structures, in storage and in entry points.

import smartpy as sp

class C(sp.Contract):
    def __init__(self):
        self.init( m1 = {}, m2 = {'a': 'b'}
                 , l1 = [], l2 = ['c']
                 , o1 = sp.none
#                 , o2 = sp.some('d') # This should be uncommented. See #41.
        )

    @sp.entry_point
    def ep1(self):
        self.data.m1 = {'e': 'f'}
        self.data.l1 = ['g']
        self.data.o1 = sp.some('h')

    @sp.entry_point
    def ep2(self):
        self.data.m2 = {}
        self.data.l2 = []
#        self.data.o2 = sp.none

@sp.add_test(name = "test")
def test():
    c = C()
    scenario = sp.test_scenario()
    scenario.h1("Empty")
    scenario += c
    c.ep1()
    c.ep2()

sp.add_compilation_target("testEmpty", C())
