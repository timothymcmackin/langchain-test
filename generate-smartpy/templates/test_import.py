import smartpy as sp

welcome = sp.io.import_script_from_url("file:python/templates/welcome.py")
fa12 = sp.io.import_script_from_url("file:python/templates/FA1.2.py")
imported = sp.io.import_script_from_url("file:python/templates/test_imported.py")

@sp.add_test(name = "ImportWelcome")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Welcome")
    c1 = welcome.MyContract(1, 1)
    scenario += c1
    c2 = fa12.FA12(sp.test_account("Administrator").address, fa12.FA12_config(), token_metadata = { "decimals" : "18" })
    scenario += c2
    scenario += imported.MyContract()
    assert __name__ == "__main__"
