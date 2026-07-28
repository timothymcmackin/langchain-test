# Check DFS, calling other contracts - Example for illustrative purposes only.

import smartpy as sp

class Check_dfs(sp.Contract):
    def __init__(self):
        self.init(steps = "", conclusion = "")

    @sp.entry_point
    def a(self):
        self.data.steps += ".a"
        sp.transfer(sp.unit, sp.mutez(0), sp.self_entry_point("aa"))

    @sp.entry_point
    def aa(self):
        self.data.steps += ".aa"

    @sp.entry_point
    def b(self):
        self.data.steps += ".b"
        sp.if self.data.steps == "check.a.b":
            self.data.conclusion = "BFS"
        sp.else:
            self.data.conclusion = "DFS"

    @sp.entry_point
    def check(self):
        self.data.steps = "check"
        self.data.conclusion = ""
        sp.transfer(sp.unit, sp.mutez(0), sp.self_entry_point("a"))
        sp.transfer(sp.unit, sp.mutez(0), sp.self_entry_point("b"))

@sp.add_test(name = "dfs")
def test():
    scenario = sp.test_scenario()
    scenario.h2("Depth first")
    check_dfs = Check_dfs()
    scenario += check_dfs
    check_dfs.check()
    scenario.verify(check_dfs.data.conclusion == "DFS")

sp.add_compilation_target("check_dfs_comp", Check_dfs())
