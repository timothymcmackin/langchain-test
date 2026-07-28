import smartpy as sp

class MyContract(sp.Contract):
    def __init__(self, **kargs):
        # self.init_metadata is a helper function that generates the expected metadata representation.
        # Users can copy/paste and provision the metadata as specified at:
        # -  https://gitlab.com/tzip/tzip/-/blob/master/proposals/tzip-16/tzip-16.md#metadata-uris
        self.init_metadata("meta_0", {"toto": "truc"});
        meta_1 = {
            "truc": "toto",
            "plam" : {1, 2, 3},
            "a": sp.key("tz1..."),
            "foo" : (),
            "views" : [self.get_x, self.get_cst, self.get_storage],
            "f": lambda x : x + 2
        }
        self.init_metadata("meta_1", meta_1)
        self.init(**kargs)

    @sp.entry_point
    def incr(self):
        self.data.x += 1

    @sp.entry_point
    def change_metadata(self, params):
        self.data.metadata[""] = params

    @sp.offchain_view(pure = True)
    def get_x(self, params):
        """blah blah ' some documentation """
        sp.result(sp.record(a = self.data.x, b = 12 + params))

    @sp.offchain_view(doc = "The storage")
    def get_storage(self):
        sp.result(self.data.x)

    @sp.offchain_view(doc = "The storage times some params - this is an example")
    def multiply_storage(self, params):
        sp.result(self.data.x * params)

    @sp.offchain_view()
    def get_cst(self):
        """42"""
        sp.result(42)

    @sp.offchain_view(doc = "My bad")
    def big_fail(self):
        sp.failwith("my_bad")

    @sp.offchain_view()
    def big_fail2(self):
        with sp.set_result_type(sp.TBool):
            sp.failwith("my_bad2")

class MyContract2(MyContract):
    @sp.entry_point(lazify = True)
    def a_lazy_entry_point(self):
        pass

@sp.add_test(name = "Metadata")
def test():
    scenario = sp.test_scenario()
    c1 = MyContract(x=1, metadata = sp.utils.metadata_of_url("ipfs://Qme9L4y6ZvPwQtaisNGTUE7VjU7PRtnJFs8NjNyztE3dGT"))
    scenario += c1
    c1.incr()
    c1.change_metadata(sp.utils.bytes_of_string(""))
    c2 = MyContract2(x=1, metadata = sp.utils.metadata_of_url("ipfs://Qme9L4y6ZvPwQtaisNGTUE7VjU7PRtnJFs8NjNyztE3dGT"))
    scenario += c2
    scenario.verify(c1.get_cst() == 42)
    scenario.verify(c1.get_storage() == 2)
    scenario.verify(c1.get_storage() == c1.data.x)
    scenario.verify(c1.multiply_storage(12) == 24)

sp.add_compilation_target("metadata", MyContract(x=1, metadata = sp.utils.metadata_of_url("ipfs://Qme9L4y6ZvPwQtaisNGTUE7VjU7PRtnJFs8NjNyztE3dGT")))
