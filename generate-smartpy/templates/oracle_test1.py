import smartpy as sp

oracle = sp.io.import_template("oracle.py")

oracle.add_test(oracle.Oracle_Config(requester_is_receiver = False), is_default = not sp.in_browser)
oracle.add_test(oracle.Oracle_Config(token_is_escrow = True), is_default = not sp.in_browser)
oracle.add_test(oracle.Oracle_Config(token_is_escrow = True, requester_is_receiver = False), is_default = not sp.in_browser)
