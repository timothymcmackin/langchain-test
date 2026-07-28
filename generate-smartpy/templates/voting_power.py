import smartpy as sp

class Voting_Power(sp.Contract):
    def __init__(self, **params):
        self.init(**params)

    @sp.entry_point
    def validate(self, key):
        self.data.a=sp.voting_power(sp.hash_key(key));
        self.data.b=sp.total_voting_power;


@sp.add_test(name = "Voting_Power")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Voting Power")

    account = sp.test_account("tz1")

    c1 = Voting_Power(a=0, b=0)
    scenario += c1

    c1.validate(account.public_key).run(
        voting_powers = {
            account.public_key_hash: 1,
            sp.key_hash("tz2"): 4
        }
    )
