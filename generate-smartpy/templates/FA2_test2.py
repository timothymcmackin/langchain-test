import smartpy as sp

FA2 = sp.io.import_template("FA2.py")

FA2.add_test(FA2.FA2_config(non_fungible = True, add_mutez_transfer = True), is_default = not sp.in_browser)
FA2.add_test(FA2.FA2_config(readable = False), is_default = not sp.in_browser)
FA2.add_test(FA2.FA2_config(force_layouts = False), is_default = not sp.in_browser)
FA2.add_test(FA2.FA2_config(debug_mode = True, support_operator = False), is_default = not sp.in_browser)
