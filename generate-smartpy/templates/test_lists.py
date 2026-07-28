# Lists - Example for illustrative purposes only.

import smartpy as sp

class TestLists(sp.Contract):
    def __init__(self):
        self.init(a = sp.none,
                  b = 0,
                  c = "",
                  d = 0,
                  e = "",
                  f = [],
                  g = [],
                  head = "no head",
                  tail = ["no tail"],
        )

    @sp.entry_point
    def test(self, params):
        result = sp.record(l   = params.l,
                           lr  = params.l.rev(),
                           # from maps
                           mi  = params.m.items(),
                           mir = params.m.rev_items(),
                           mk  = params.m.keys(),
                           mkr = params.m.rev_keys(),
                           mv  = params.m.values(),
                           mvr = params.m.rev_values(),
                           # from sets
                           s   = params.s.elements(),
                           sr  = params.s.rev_elements(),
                           )
        self.data.a = sp.some(result)
        self.data.b = sp.sum(result.l)
        self.data.c = sp.concat(result.mk) # string list concatenation
        self.data.d = sp.sum(result.sr)    # int    list sum
        self.data.e = ""

        # iterations
        sp.for x in result.mv:
            sp.if sp.snd(x):
                self.data.e += sp.fst(x)

        # ranges
        sp.for i in sp.range(0, 5):
            self.data.f.push(i * i)

        self.data.g = sp.range(1, 12)

    @sp.entry_point
    def test_match(self, params):
        with sp.match_cons(params) as x1:
            self.data.head = x1.head
            self.data.tail = x1.tail
        sp.else:
            self.data.head = "abc"

    @sp.entry_point
    def test_match2(self, params):
        with sp.match_cons(params) as x1:
            with sp.match_cons(x1.tail) as x2:
                self.data.head = x1.head + x2.head
                self.data.tail = x2.tail
        sp.else:
            self.data.head = "abc"

@sp.add_test(name = "Lists")
def test():
    c1 = TestLists()
    scenario = sp.test_scenario()
    scenario.h1("Lists")
    scenario += c1

    c1.test(l = [1, 2, 3],
                        m = {'a' : ('aa', True),
                             'b' : ('bb', False),
                             'c' : ('cc', True)},
                        s = sp.set([1, 12, 100]))

    c1.test_match(['1', '2', '3'])

    target = sp.record(a = sp.some(
        sp.record(l   = sp.list([1, 2, 3]),
                  lr  = sp.list([3, 2, 1]),
                  mi  =  sp.list([sp.record(key = 'a', value = ('aa', True)),
                                  sp.record(key = 'b', value = ('bb', False)),
                                  sp.record(key = 'c', value = ('cc', True))]),
                  mir = sp.list([sp.record(key = 'c', value = ('cc', True)),
                                 sp.record(key = 'b', value = ('bb', False)),
                                 sp.record(key = 'a', value = ('aa', True))]),
                  mk  = sp.list(['a', 'b', 'c']),
                  mkr = sp.list(['c', 'b', 'a']),
                  mv  = sp.list([('aa', True), ('bb', False), ('cc', True)]),
                  mvr = sp.list([('cc', True), ('bb', False), ('aa', True)]),
                  s   = sp.list([1, 12, 100]),
                  sr  = sp.list([100, 12, 1]))),
                       b = 6,
                       c = 'abc',
                       d = 113,
                       e = 'aacc',
                       f = [16, 9, 4, 1, 0],
                       g = range(1, 12),
                       head = "1",
                       tail = ["2", "3"],
                       )
    scenario.verify_equal(c1.data, target)

    c1.test_match2(['1', '2', '3'])

    scenario.verify_equal(c1.data.tail, ['3'])
    scenario.verify_equal(c1.data.head, '12')

sp.add_compilation_target("testLists", TestLists())
