# Strings and Bytes - Example for illustrative purposes only.

import smartpy as sp

# A few helper functions that have probably no place in a real world
# smart contract but show general string manipulation techniques.

def string_split(s, sep):
    prev_idx = sp.local('prev_idx', 0)
    res = sp.local('res', [])
    sp.for idx in sp.range(0, sp.len(s)):
        sp.if sp.slice(s, idx, 1).open_some() == sep:
            res.value.push(sp.slice(s, prev_idx.value, sp.as_nat(idx - prev_idx.value)).open_some())
            prev_idx.value = idx + 1
    sp.if sp.len(s) > 0:
        res.value.push(sp.slice(s, prev_idx.value, sp.as_nat(sp.len(s) - prev_idx.value)).open_some())
    return res.value.rev()

def string_of_nat(params):
    c   = sp.map({x : str(x) for x in range(0, 10)})
    x   = sp.local('x', params)
    res = sp.local('res', [])
    sp.if x.value == 0:
        res.value.push('0')
    sp.while 0 < x.value:
        res.value.push(c[x.value % 10])
        x.value //= 10
    return sp.concat(res.value)

def nat_of_string(params):
    c   = sp.map({str(x) : x for x in range(0, 10)})
    res = sp.local('res', 0)
    sp.for idx in sp.range(0, sp.len(params)):
        res.value = 10 * res.value + c[sp.slice(params, idx, 1).open_some()]
    return res.value

class MyContract(sp.Contract):
    def __init__(self):
        self.init(s0 = sp.some("hello"),
                  b0 = sp.some(sp.bytes("0xAA")),
                  l0 = 0,
                  l1 = 0,
                  split = [],
                  string_of_nat = '',
                  nat_of_string = 0)

    @sp.entry_point
    def concatenating(self, b0, b1, s, sb):
        # Concatenating a list of strings or a list of bytes
        self.data.s0 = sp.some(sp.concat(s))
        self.data.b0 = sp.some(sp.concat([b0, b1, sp.concat(sb)]))

    @sp.entry_point
    def concatenating2(self, b1, b2, s1, s2):
        # Concatenating a two strings or two bytes
        self.data.s0 = sp.some(s1 + s2)
        self.data.b0 = sp.some(b1 + b2)

    @sp.entry_point
    def slicing(self, b, s):
        # Slicing a string or a byte (this returns an option)
        self.data.s0 = sp.slice(s, 2, 5)
        self.data.b0 = sp.slice(b, 1, 2)

        # Computing length with sp.len
        self.data.l0 = sp.len(s)
        with self.data.s0.match("Some") as arg:
            self.data.l0 += sp.len(arg)
        self.data.l1 = sp.len(b)

    @sp.entry_point
    def test_split(self, params):
        self.data.split = string_split(s = params, sep = ',')

    @sp.entry_point
    def test_string_of_nat(self, params):
        self.data.string_of_nat = string_of_nat(params)

    @sp.entry_point
    def test_nat_of_string(self, params):
        self.data.nat_of_string = nat_of_string(params)

# Tests
@sp.add_test(name = "String Manipulations")
def test():
    scenario = sp.test_scenario()
    scenario.h1("String Manipulations")
    c1 = MyContract()
    scenario += c1

    c1.slicing(s = "012345678901234567890123456789", b = sp.bytes("0xAA00BBCC"))
    scenario.verify_equal(c1.data.s0, sp.some("23456"))
    scenario.verify_equal(c1.data.b0, sp.some(sp.bytes("0x00BB")))
    scenario.verify_equal(c1.data.l0, 35)
    scenario.verify_equal(c1.data.l1, 4)
    c1.slicing(s = "01", b = sp.bytes("0xCC"))
    scenario.verify_equal(c1.data.s0, sp.none)
    # This one fails on sandbox because of missing type:
    scenario.verify_equal(c1.data.b0, sp.none)

    c1.concatenating( s  = ["01", "234", "567", "89"],
                                  sb = [sp.bytes('0x1234'), sp.bytes('0x'), sp.bytes('0x4567aabbCCDD')],
                                  b0 = sp.bytes("0x11"),
                                  b1 = sp.bytes("0x223344"))
    scenario.verify_equal(c1.data.s0, sp.some("0123456789"))
    scenario.verify_equal(c1.data.b0, sp.some(sp.bytes('0x1122334412344567AABBCCDD')))

    c1.concatenating2(s1 = "abc", s2 = "def", b1 = sp.bytes("0xaaaa"), b2 = sp.bytes("0xab"))

    c1.test_split("abc,def,ghi,,j")

    c1.test_string_of_nat(0)

    scenario.verify_equal(c1.data.string_of_nat, '0')

    c1.test_string_of_nat(12345678901234)

    c1.test_nat_of_string("12312345678901234123")

    scenario.show(c1.data)
    scenario.verify_equal(c1.data, sp.record(b0 = sp.some(sp.bytes("0xaaaaab")),
                                             l0 = 2,
                                             l1 = 1,
                                             s0 = sp.some('abcdef'),
                                             split = ['abc', 'def', 'ghi', '', 'j'],
                                             string_of_nat = '12345678901234',
                                             nat_of_string = 12312345678901234123))

sp.add_compilation_target("stringManipulations", MyContract())
