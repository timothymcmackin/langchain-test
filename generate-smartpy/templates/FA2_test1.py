import smartpy as sp

FA2 = sp.io.import_template("FA2.py")

FA2.add_test(FA2.FA2_config(debug_mode = True), is_default = not sp.in_browser)
FA2.add_test(FA2.FA2_config(single_asset = True), is_default = not sp.in_browser)
