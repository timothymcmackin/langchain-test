import smartpy as sp

class TestAddressComparison(sp.Contract):
    def __init__(self, **args):
        self.init(**args)

    @sp.entry_point
    def test(self, params):
        sp.verify(
            sp.utils.same_underlying_address(sp.fst(params), sp.snd(params))
        )

    @sp.entry_point
    def ep(self, address):
        sp.verify(self.isKT1(address), "Not KT1")
        self.data.x = address < sp.address("KT1XvNYseNDJJ6Kw27qhSEDF8ys8JhDopzfG")
        self.data.y = address >= sp.address("KT18amZmM5W7qDWVt2pH6uj7sCEd3kbzLrHT")

    def isKT1(self, address):
        return (address <= sp.address("KT1XvNYseNDJJ6Kw27qhSEDF8ys8JhDopzfG")) & (address >= sp.address("KT18amZmM5W7qDWVt2pH6uj7sCEd3kbzLrHT"))


@sp.add_test(name = "TestAddressComparison")
def test():
    scenario = sp.test_scenario()
    c1 = TestAddressComparison(x = False, y = False)

    scenario.register(c1)

    alice = sp.test_account("alice")
    c1.ep(alice.address).run(valid = False)
    c1.ep(sp.address("KT1TezoooozzSmartPyzzSTATiCzzzwwBFA1"))

    c1.test((
        sp.address("KT1WD5PV1i1HQTFhNUxVGNjRda63trNyshwU"),
        sp.address("KT1WD5PV1i1HQTFhNUxVGNjRda63trNyshwU")
    ))

    c1.test((
        sp.address("KT1WD5PV1i1HQTFhNUxVGNjRda63trNyshwU"),
        sp.address("KT1WD5PV1i1HQTFhNUxVGNjRda63trNyshwU%a")
    ))

    c1.test((
        sp.address("KT1WD5PV1i1HQTFhNUxVGNjRda63trNyshwU"),
        sp.address("KT1WD5PV1i1HQTFhNUxVGNjRda63trNyshwU%")
    ))

    c1.test((
        sp.address("KT1WD5PV1i1HQTFhNUxVGNjRda63trNyshwU"),
        sp.address("tz1Z6Uk4qfdAJLJuCdGzL8aheqedW8sBQv2T")
    )).run(valid = False)

    c1.test((
        sp.address("KT1WD5PV1i1HQTFhNUxVGNjRda63trNyshwU"),
        sp.address("KT1AYAtnyeZKifkjv5ooKXsKuWWbpECMgoUC")
    )).run(valid = False)

    c1.test((
        sp.address("KT1WD5PV1i1HQTFhNUxVGNjRda63trNyshwU"),
        sp.address("KT1AYAtnyeZKifkjv5ooKXsKuWWbpECMgoUC%")
    )).run(valid = False)
