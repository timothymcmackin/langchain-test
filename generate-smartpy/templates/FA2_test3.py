import smartpy as sp

FA2 = sp.io.import_template("FA2.py")

FA2.add_test(FA2.FA2_config(assume_consecutive_token_ids = False), is_default = not sp.in_browser)
FA2.add_test(FA2.FA2_config(store_total_supply = True), is_default = not sp.in_browser)
FA2.add_test(FA2.FA2_config(add_mutez_transfer = True), is_default = not sp.in_browser)
FA2.add_test(FA2.FA2_config(lazy_entry_points = True), is_default = not sp.in_browser)
