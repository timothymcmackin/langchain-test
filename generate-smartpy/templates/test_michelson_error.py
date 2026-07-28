import smartpy as sp

class MyContract(sp.Contract):
    def __init__(self, **kargs):
        self.init(x = [])

@sp.add_test(name = "Test")
def test():
    scenario = sp.test_scenario()
    scenario.register(MyContract(), accept_unknown_types = not sp.in_browser, show = True)
