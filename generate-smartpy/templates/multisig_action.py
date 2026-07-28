import smartpy as sp

# Internal administration action type specification
InternalAdminAction = sp.TVariant(
    addSigners=sp.TList(sp.TAddress),
    changeQuorum=sp.TNat,
    removeSigners=sp.TList(sp.TAddress),
)


class MultisigAction(sp.Contract):
    """A contract that can be used by multiple signers to administrate other
    contracts. The administrated contracts implement an interface that make it
    possible to explicit the administration process to non expert users.

    Signers vote for proposals. A proposal is a list of a target with a list of
    action. An action is a simple byte but it is intended to be a pack value of
    a variant. This simple pattern make it possible to build a UX interface
    that shows the content of a proposal or build one.
    """

    def __init__(self, quorum, signers):
        self.init(
            inactiveBefore=0,
            nextId=0,
            proposals=sp.big_map(
                tkey=sp.TNat,
                tvalue=sp.TList(
                    sp.TRecord(target=sp.TAddress, actions=sp.TList(sp.TBytes))
                ),
            ),
            quorum=quorum,
            signers=sp.set(signers),
            votes=sp.big_map(tkey=sp.TNat, tvalue=sp.TSet(sp.TAddress)),
        )

    @sp.entry_point
    def send_proposal(self, proposal):
        """Signer-only. Submit a proposal to the vote.

        Args:
            proposal (sp.TList of sp.TRecord of target address and action): List\
                of target and associated administration actions.
        """
        sp.verify(self.data.signers.contains(sp.sender), "Only signers can propose")
        self.data.proposals[self.data.nextId] = proposal
        self.data.votes[self.data.nextId] = sp.set()
        self.data.nextId += 1

    @sp.entry_point
    def vote(self, pId):
        """Vote for one or more proposals

        Args:
            pId (sp.TNat): Id of the proposal.
        """
        sp.verify(self.data.signers.contains(sp.sender), "Only signers can vote")
        sp.verify(self.data.votes.contains(pId), "Proposal unknown")
        sp.verify(pId >= self.data.inactiveBefore, "The proposal is inactive")
        self.data.votes[pId].add(sp.sender)
        votes = self.data.votes.get(pId, sp.set())
        with sp.if_(sp.len(votes) >= self.data.quorum):
            self._onApproved(pId)

    def _onApproved(self, pId):
        """Inlined function. Logic applied when a proposal has been approved."""
        proposal = self.data.proposals.get(pId, [])
        with sp.for_("p_item", proposal) as p_item:
            contract = sp.contract(sp.TList(sp.TBytes), p_item.target)
            sp.transfer(p_item.actions, sp.tez(0), contract.open_some("InvalidTarget"))
        # Inactivate all proposals that have been already submitted.
        self.data.inactiveBefore = self.data.nextId

    @sp.entry_point
    def administrate(self, actions):
        """Self-call only. Administrate this contract.

        This entrypoint must be called through the proposal system.

        Args:
            actions (sp.TList of sp.TBytes): List of packed variant of \
                `InternalAdminAction` (`addSigners`, `changeQuorum`, `removeSigners`).
        """
        sp.verify(
            sp.sender == sp.self_address,
            "This entrypoint must be called through the proposal system.",
        )
        with sp.for_("action", actions) as action:
            action = sp.unpack(action, InternalAdminAction).open_some("Bad actions format")
            with (action).match_cases() as arg:
                with arg.match("changeQuorum") as quorum:
                    self.data.quorum = quorum
                with arg.match("addSigners") as added:
                    with sp.for_("signer", added) as signer:
                        self.data.signers.add(signer)
                with arg.match("removeSigners") as removed:
                    with sp.for_("address", removed) as address:
                        self.data.signers.remove(address)
            # Ensure that the contract never requires more quorum than the total of signers.
            sp.verify(
                self.data.quorum <= sp.len(self.data.signers),
                message="More quorum than signers.",
            )


if "templates" not in __name__:

    @sp.add_test(name="Basic scenario", is_default=True)
    def test():
        signer1 = sp.test_account("signer1")
        signer2 = sp.test_account("signer2")
        signer3 = sp.test_account("signer3")

        s = sp.test_scenario()
        s.h1("Basic scenario")

        s.h2("Origination")
        c1 = MultisigAction(
            quorum=2,
            signers=[signer1.address, signer2.address],
        )
        s += c1

        s.h2("Proposal for adding a new signer")
        target = sp.to_address(
            sp.contract(sp.TList(sp.TBytes), c1.address, "administrate").open_some()
        )
        action = sp.pack(
            sp.set_type_expr(sp.variant("addSigners", [signer3.address]), InternalAdminAction)
        )
        c1.send_proposal([sp.record(target=target, actions=[action])]).run(
            sender=signer1
        )

        s.h2("Signer 1 votes for the proposal")
        c1.vote(0).run(sender=signer1)
        s.h2("Signer 2 votes for the proposal")
        c1.vote(0).run(sender=signer2)

        s.verify(c1.data.signers.contains(signer3.address))
