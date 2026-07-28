# Lazy strings - Example for illustrative purposes only.

# sp.Lazy_strings is an experimental feature allowing to automatically
# populate a big map of strings and retrieve its values lazily.

import smartpy as sp

class MyContract(sp.Contract):
    def __init__(self):
        self.lazy_strings = sp.Lazy_strings(self, lambda x : x.msg)
        sp.wrap_verify_messages = self.lazy_strings
        self.init(x = 0,
                  s = "",
                  msg = self.lazy_strings,
                  bb = sp.big_map(tkey = sp.TBool, tvalue = sp.TInt)
        )

    @sp.entry_point
    def myEntryPoint(self, x, y, z):
        sp.verify(x <= 123, message = "Bad compare")
        sp.verify(y <= 123, message = "Bad compare2")
        sp.verify(z <= 123, message = "Bad compare3")
        self.data.x += x + y + z

    @sp.entry_point
    def myEntryPoint2(self):
        self.data.s = self.lazy_strings("Bad compare") + self.lazy_strings("abcdefg")

@sp.add_test(name = "Lazy")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Lazy")
    c1 = MyContract()
    scenario += c1
    c1.myEntryPoint(x = 12, y = 15, z = 20)
    c1.myEntryPoint2()

sp.add_compilation_target("lazy", MyContract())
