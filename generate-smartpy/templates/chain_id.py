import smartpy as sp

class ChainId(sp.Contract):
    def __init__(self):
        self.init(chainId = sp.none)

    @sp.entry_point
    def test(self):
        self.data.chainId = sp.some(sp.chain_id)

@sp.add_test(name = "ChainId")
def chainIdTest():
    scenario = sp.test_scenario()

    scenario.table_of_contents()

    c = ChainId()
    scenario += c

    c.test().run(chain_id = sp.chain_id_cst("0x9caecab8"))
