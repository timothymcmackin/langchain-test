# Simple Vote - Example for illustrative purposes only.

import smartpy as sp

class SimpleVote(sp.Contract):
    def __init__(self):
        self.init(votes = [])

    @sp.entry_point
    def vote(self, params):
        sp.set_type(params.vote, sp.TString)
        self.data.votes.push(sp.record(sender = sp.sender, vote = params.vote))

@sp.add_test(name = "Voting")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Voting")
    voter1 = sp.test_account("Voter1")
    # define a contract
    c1 = SimpleVote()
    # show its representation
    scenario.h2("Contract")
    scenario += c1
    c1.vote(vote = 'aaa').run(sender = voter1)

sp.add_compilation_target("voting", SimpleVote())
