import smartpy as sp

class C(sp.Contract):
    def __init__(self):
        self.init( x    = 0
                 , xxs  = sp.utils.matrix([[0]])
                 , xxxs = sp.utils.cube([[[0]]])
                 , rs   = [sp.record(a=5,b=6)]
                 , ms   = [{'a': 97, 'b': 98},{'a': 0, 'b': 1}]
                 )

    @sp.entry_point
    def ep1(self):
        self.data.x = 0
        r = sp.record(a=2,b=3)
        s = sp.local('s', sp.record(a=5,b=6))
        sp.for r in [r, s.value]:
            self.data.x += r.a # read record attribute
        sp.verify(self.data.x == 7)

    @sp.entry_point
    def ep2(self):
        self.data.x = 2
        sp.for i in [self.data.x, self.data.x, self.data.x]:
            self.data.x += i # write to something mentioned in the list (no effect)
        sp.verify(self.data.x == 8)

    @sp.entry_point
    def ep3(self):
        r = sp.record(a=2,b=3)
        self.data.rs = [r,r,r]
        sp.for i in self.data.rs:
            i.a = 0  # write to record attribute
        r = sp.record(a=0,b=3)
        # sp.verify(self.data.rs == [r,r,r])

    @sp.entry_point
    def ep4(self):
        xs = [2,3]
        self.data.xxs = sp.utils.matrix([xs,xs,xs])
        sp.for xs in self.data.xxs.values():
            xs[0] = 0 # write to sub-list
            sp.send(sp.address("tz1PiDHTNJXhqpkbRUYNZEzmePNd21WcB8yB"), sp.utils.nat_to_mutez(xs[1]))
        xs = [0,3]
        # sp.verify(self.data.xxs == [xs,xs,xs])

    @sp.entry_point
    def ep5(self):
        self.data.x = 0
        self.data.xxxs = sp.utils.cube([[[1]],[[2]]])
        sp.for xs in self.data.xxxs[self.data.x].values():
            self.data.x = 1
            xs[0] = 0
        # sp.verify(self.data.xxxs == [[[0]],[[2]]])

    @sp.entry_point
    def ep6(self):
        self.data.xxxs = sp.utils.cube([[[0],[10]],[[20],[30]]])
        sp.for xs in self.data.xxxs[self.data.xxxs[0][0][0]].values():
            xs[0] = 1
        # sp.verify(self.data.xxxs == [[[1],[1]],[[20],[30]]])

    @sp.entry_point
    def ep7(self):
        self.data.ms = [{'a': 97, 'b': 98},{'a': 0, 'b': 1}]
        sp.for m in self.data.ms:
            del m['a']
        # sp.verify(self.data.ms == [{'b': 98}, {'b': 1}])

@sp.add_test(name = "For")
def test():
    s = sp.test_scenario()
    c = C()
    s += c
    c.ep1()
    c.ep2()
    c.ep3()
    # c.ep4()
    # c.ep5()
    # c.ep6()
    c.ep7()
