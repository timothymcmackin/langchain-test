import smartpy as sp


class MultisigView(sp.Contract):
    """Multiple members vote for arbitrary bytes.

    This contract can be originated with a list of addresses and a number of
    required votes. Any member can submit as many bytes as they want and vote
    for active proposals.

    Any bytes that reached the required votes can be confirmed via a view.
    """

    def __init__(self, members, required_votes):
        """Constructor

        Args:
            members (sp.TSet(sp.TAddress)): people who can submit and vote for
                lambda.
            required_votes (sp.TNat): number of votes required
        """
        assert required_votes <= len(members), "required_votes must be <= len(members)"
        self.init(
            proposals=sp.big_map(tkey=sp.TBytes, tvalue=sp.TBool),
            votes=sp.big_map(tkey=sp.TBytes, tvalue=sp.TSet(sp.TAddress)),
            members=sp.set(members, t=sp.TAddress),
            required_votes=required_votes,
        )

    @sp.entry_point
    def submit_proposal(self, bytes):
        """Submit a new proposal to the vote.

        Submitting a proposal does not imply casting a vote in favour of it.

        Args:
            bytes(sp.TBytes): bytes proposed to vote.
        Raises:
            `You are not a member`
        """
        sp.verify(self.data.members.contains(sp.sender), "You are not a member")
        self.data.proposals[bytes] = False
        self.data.votes[bytes] = sp.set()

    @sp.entry_point
    def vote_proposal(self, bytes):
        """Vote for a proposal.

        There is no vote against or pass. If one disagrees with a proposal they
        can avoid to vote. Warning: old non-voted proposals never become
        obsolete.

        Args:
            id(sp.TBytes): bytes of the proposal.
        Raises:
            `You are not a member`, `Proposal not found`
        """
        sp.verify(self.data.members.contains(sp.sender), "You are not a member")
        sp.verify(self.data.proposals.contains(bytes), "Proposal not found")
        self.data.votes[bytes].add(sp.sender)
        with sp.if_(sp.len(self.data.votes[bytes]) >= self.data.required_votes):
            self.data.proposals[bytes] = True

    @sp.onchain_view()
    def is_voted(self, id):
        """Returns a boolean indicated if the proposal has been voted.

        Args:
            id (sp.TBytes): bytes of the proposal
        Return:
            (sp.TBool): True if the proposal has been voted, False otherwise.
        """
        sp.result(self.data.proposals.get(id, message="Proposal not found"))


if "templates" not in __name__:

    @sp.add_test(name="MultisigView basic scenario", is_default=True)
    def basic_scenario():
        """A scenario with a vote on the multisigView contract.

        Tests:
        - Origination
        - Proposal submission
        - Proposal vote
        """
        sc = sp.test_scenario()
        sc.h1("Basic scenario.")

        member1 = sp.test_account("member1")
        member2 = sp.test_account("member2")
        member3 = sp.test_account("member3")
        members = [member1.address, member2.address, member3.address]

        sc.h2("Origination")
        c1 = MultisigView(members, required_votes=2)
        sc += c1

        sc.h2("submit_proposal")
        c1.submit_proposal(sp.bytes("0x42")).run(sender=member1)

        sc.h2("vote_proposal")
        c1.vote_proposal(sp.bytes("0x42")).run(member1)
        c1.vote_proposal(sp.bytes("0x42")).run(member2)

        # We can check that the proposal has been validated.
        sc.verify(c1.is_voted(sp.bytes("0x42")))
