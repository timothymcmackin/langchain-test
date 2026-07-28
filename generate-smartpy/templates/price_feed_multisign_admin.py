import smartpy as sp

"""
    Multisign Admin is a multisign administration contract.

    Multiple signers can propose and vote for a list of batch of actions
    on the contract itself or the target.

    The contract is configurable at origination time to adapt to target needed.

    The contract supports gathering off-chain signed votes and pushing them in one call.

    Voting system:
        When the quorum is reached on a proposal,
        If the number of yay > nay: the proposal is acceped
        Else: the proposal is rejected

        Once a proposal is accepted the batchs of actions are executed,
        the other proposals are automatically canceled.

    Vocabulary:
        Action: something to do on the MultisignAdmin or Target
        Batch of Actions: multiple actions to do on the same internal call
        List of Batchs: multiple internal calls containing batch of actions

    A complexe proposal can include for example 2 batchs of actions:
    1) Self admin: change quorum + change signers
    2) Target admin: change parameter + change active

    Antipattern:
        Instead of doing 2 batchs of 2 actions
        some could be tempted to use 4 batchs of 1 action
        In this case the params will be bigger and there will be 2 internal calls.
        Advice: Use less batchs possible and most actions per batch
"""

AGGREGATOR_METADATA = {
    "name"          : "Multi-sign Administrator",
    "version"       : "1",
    "description"   : "Multi-sign administrator for the price feed aggregator",
    "source"        : {
        "tools": [ "SmartPy" ]
    },
    "interfaces"    : [ "TZIP-016" ],
}

class TYPES:
    TSelfAdminAction = sp.TVariant(
        changeVoters = sp.TRecord(
            removed = sp.TSet(sp.TAddress),
            added = sp.TList(sp.TRecord(
                addr = sp.TAddress,
                publicKey = sp.TKey))),
        changeTarget = sp.TAddress,
        changeQuorum = sp.TNat,
        changeTimeout = sp.TInt
    )

class ERR:
    MultisignAdmin_Badsig                 = "MultisignAdmin_Badsig"
    MultisignAdmin_ProposalClosed         = "MultisignAdmin_ProposalClosed"
    MultisignAdmin_ProposalUnknown        = "MultisignAdmin_ProposalUnknown"
    MultisignAdmin_AlreadyVoted           = "MultisignAdmin_AlreadyVoted"
    MultisignAdmin_VoterUnknown           = "MultisignAdmin_VoterUnknown"
    MultisignAdmin_VoterAlreadyknown      = "MultisignAdmin_VoterAlreadyknown"
    MultisignAdmin_ProposalTimedout       = "MultisignAdmin_ProposalTimedout"
    MultisignAdmin_TargetUnkown           = "MultisignAdmin_TargetUnkown"
    MultisignAdmin_MoreQuorumThanVoters   = "MultisignAdmin_MoreQuorumThanVoters"
    MultisignAdmin_VotersLessThan1        = "MultisignAdmin_VotersLessThan1"
    MultisignAdmin_TargetNotSet           = "MultisignAdmin_TargetNotSet"
    MultisignAdmin_WrongCallbackInterface = "MultisignAdmin_WrongCallbackInterface"

class MultisignAdmin(sp.Contract):
    """
        Each user can have at most one proposal
    """
    def __init__(
            self,
            quorum,
            timeout,
            addrVoterId,
            keyVoterId,
            voters,
            lastVoterId,
            metadataURL,
            TTargetAdminAction,
            TSelfAdminAction    = TYPES.TSelfAdminAction
        ):

        self.init_metadata("metadata", {
            **AGGREGATOR_METADATA,
            "views": [self.listActiveProposals]
        })

        self.TSelfAdminAction = TSelfAdminAction
        self.TTargetAdminAction = TTargetAdminAction
        self.TProposalBatchs = sp.TVariant(
            selfAdmin = sp.TList(TSelfAdminAction),
            targetAdmin = sp.TList(TTargetAdminAction)
        )
        self.TProposal = sp.TRecord(
                startedAt = sp.TTimestamp,
                id = sp.TNat,
                yay = sp.TSet(sp.TNat),
                nay = sp.TSet(sp.TNat),
                batchs = sp.TList(self.TProposalBatchs),
                canceled = sp.TBool
        )
        self.init_type(
            sp.TRecord(
                target = sp.TOption(sp.TAddress),
                quorum = sp.TNat,
                timeout = sp.TInt,
                lastVoterId = sp.TNat,
                lastVoteTimestamp = sp.TTimestamp,
                nbVoters = sp.TNat,
                voters = sp.TBigMap(
                    sp.TNat,
                    sp.TRecord(
                        publicKey = sp.TKey,
                        addr = sp.TAddress,
                        lastProposalId = sp.TNat
                    )
                ),
                addrVoterId = sp.TBigMap(sp.TAddress, sp.TNat),
                keyVoterId = sp.TBigMap(sp.TKey, sp.TNat),
                proposals = sp.TBigMap(sp.TNat, self.TProposal),
                metadata = sp.TBigMap(sp.TString, sp.TBytes),
            )
        )
        self.init(
            target              = sp.none,
            quorum              = quorum,
            timeout             = timeout,
            lastVoterId         = lastVoterId,
            lastVoteTimestamp   = sp.timestamp(0),
            nbVoters            = len(voters),
            voters              = sp.big_map(voters),
            addrVoterId         = sp.big_map(addrVoterId),
            keyVoterId          = sp.big_map(keyVoterId),
            proposals           = sp.big_map(),
            metadata            = sp.utils.metadata_of_url(metadataURL)
        )

    # ----------------
    # Public entrypoints

    @sp.entry_point
    def newProposal(self, batchs):
        sp.verify(self.data.addrVoterId.contains(sp.sender), message = ERR.MultisignAdmin_VoterUnknown)

        voterId = self.data.addrVoterId[sp.sender]
        self.data.voters[voterId].lastProposalId += 1
        self.data.proposals[voterId] = sp.record(
            startedAt = sp.now,
            id = self.data.voters[voterId].lastProposalId,
            yay = sp.set([voterId]),
            nay = sp.set([]),
            batchs = batchs,
            canceled = False,
        )
        sp.if self.data.quorum < 2:
            self.onVoted(self.data.proposals[voterId])

    @sp.entry_point
    def vote(self, votes):
        sp.verify(self.data.addrVoterId.contains(sp.sender), message = ERR.MultisignAdmin_VoterUnknown)

        voterId = self.data.addrVoterId[sp.sender]
        sp.for vote in votes:
            self.registerVote(
                sp.record(
                    initiatorId = vote.initiatorId,
                    proposalId = vote.proposalId,
                    voterId = voterId,
                    yay = vote.yay
                )
            )
            proposal = self.data.proposals[vote.initiatorId]
            sp.if (sp.len(proposal.nay) + sp.len(proposal.yay)) >= self.data.quorum:
                sp.if sp.len(proposal.nay) >= sp.len(proposal.yay):
                    proposal.canceled = True
                sp.else:
                    self.onVoted(proposal)

    @sp.entry_point
    def multiVote(self, proposalsVotes):
        """
            Signed: Pair(ADDRESS multisignAdmin, Pair(initiatorId, proposalId))
        """
        TVotes = sp.TList(sp.TRecord(
                        voterId = sp.TNat,
                        signature = sp.TSignature,
                        yay = sp.TBool
                 ))
        sp.set_type(proposalsVotes,
            sp.TList(sp.TRecord(
                initiatorId = sp.TNat,
                proposalId = sp.TNat,
                votes = TVotes
            ))
        )
        sp.for proposalVotes in proposalsVotes:
            initiatorId = proposalVotes.initiatorId
            proposalId = proposalVotes.proposalId
            sp.for vote in proposalVotes.votes:
                signed = sp.pack(
                    sp.pair(sp.self_address, sp.pair(initiatorId, proposalId))
                )
                sp.verify(self.data.voters.contains(vote.voterId), message = ERR.MultisignAdmin_VoterUnknown)
                publicKey = self.data.voters[vote.voterId].publicKey
                sp.verify(
                    sp.check_signature(
                        publicKey, vote.signature, signed,
                    ),
                    message = ERR.MultisignAdmin_Badsig
                )
                self.registerVote(
                    sp.record(initiatorId = initiatorId,
                              proposalId = proposalId,
                              voterId = vote.voterId,
                              yay = vote.yay)
                )
            proposal = self.data.proposals[initiatorId]
            sp.if (sp.len(proposal.nay) + sp.len(proposal.yay)) >= self.data.quorum:
                sp.if sp.len(proposal.nay) >= sp.len(proposal.yay):
                    proposal.canceled = True
                sp.else:
                    self.onVoted(proposal)

    @sp.entry_point
    def cancelProposal(self, proposalId):
        sp.verify(self.data.addrVoterId.contains(sp.sender),
                  message = ERR.MultisignAdmin_VoterUnknown)
        voterId = self.data.addrVoterId[sp.sender]
        proposal = self.data.proposals[voterId]
        sp.verify(self.data.proposals.contains(voterId) &
                  (proposal.id == proposalId),
                  message = ERR.MultisignAdmin_ProposalUnknown)
        proposal.canceled = True

    # ----------------
    # Public views
    @sp.entry_point
    def getParams(self, callback):
        params = sp.record(target = self.data.target, quorum = self.data.quorum, timeout = self.data.timeout)
        sp.transfer(params, sp.tez(0), callback)

    @sp.entry_point
    def getLastProposal(self, params):
        proposal = self.data.proposals[sp.fst(params)]
        callback = sp.contract(self.TProposal, sp.snd(params))
        sp.transfer(proposal, sp.tez(0), callback.open_some(message = ERR.MultisignAdmin_WrongCallbackInterface))

    # ----------------
    # Offchain views

    @sp.offchain_view(pure = True)
    def listActiveProposals(self):
        def isActive(proposal):
            # Not canceled
            active =  ~proposal.canceled
            # Not timedout
            active &= sp.now < proposal.startedAt.add_minutes(self.data.timeout)
            # Not already voted
            active &= (sp.len(proposal.nay) + sp.len(proposal.yay)) < self.data.quorum
            # Not closed by other vote
            active &= proposal.startedAt > self.data.lastVoteTimestamp
            return active
        """List active proposals"""
        TProposal = sp.TRecord(
            startedAt           = sp.TTimestamp,
            initiatorId         = sp.TNat,
            initiatorProposalId = sp.TNat,
            yay                 = sp.TSet(sp.TNat),
            nay                 = sp.TSet(sp.TNat),
            batchs              = sp.TList(self.TProposalBatchs)
        )

        proposals = sp.compute(self.data.proposals)
        response = sp.local("response", sp.list([], t = TProposal))

        sp.for voterId in sp.range(0, self.data.nbVoters, step = 1):
            sp.if proposals.contains(voterId):
                proposal = sp.compute(self.data.proposals[voterId])
                sp.if isActive(proposal):
                    response.value.push(
                        sp.record(
                            startedAt           = proposal.startedAt,
                            initiatorId         = voterId,
                            initiatorProposalId = proposal.id,
                            yay                 = proposal.yay,
                            nay                 = proposal.nay,
                            batchs              = proposal.batchs
                        )
                    )

        sp.result(response.value)

    # ----------------
    # Private functions

    @sp.private_lambda(with_storage="read-write", wrap_call=True)
    def registerVote(self, params):
        proposal = self.data.proposals[params.initiatorId]
        sp.verify(self.data.proposals.contains(params.initiatorId) &
                  (proposal.id == params.proposalId),
                  message = ERR.MultisignAdmin_ProposalUnknown)
        sp.verify((proposal.startedAt > self.data.lastVoteTimestamp) &
                  ~ proposal.canceled,
                  message = ERR.MultisignAdmin_ProposalClosed)
        sp.verify((sp.now < proposal.startedAt.add_minutes(self.data.timeout)),
                  message = ERR.MultisignAdmin_ProposalTimedout)
        sp.verify(~proposal.yay.contains(params.voterId) &
                  ~proposal.nay.contains(params.voterId),
                  message = ERR.MultisignAdmin_AlreadyVoted)
        sp.if params.yay:
            proposal.yay.add(params.voterId)
        sp.else:
            proposal.nay.add(params.voterId)

    @sp.private_lambda(with_storage="read-write", with_operations=True, wrap_call=True)
    def onVoted(self, proposal):
        self.data.lastVoteTimestamp = sp.now
        sp.for batch in proposal.batchs:
            with (batch).match_cases() as arg:
                with arg.match("selfAdmin") as selfAdminActions:
                    sp.for selfAdminAction in selfAdminActions:
                        self.selfAdmin(selfAdminAction)
                with arg.match("targetAdmin") as targetActions:
                    target = self.data.target.open_some(message = ERR.MultisignAdmin_TargetNotSet)
                    target_contract = sp.contract(sp.TList(self.TTargetAdminAction), target).open_some(ERR.MultisignAdmin_TargetUnkown)
                    sp.transfer(targetActions, sp.tez(0), target_contract)

    def selfAdmin(self, action):
        with (action).match_cases() as arg:
            with arg.match("changeQuorum", "quorum") as quorum:
                sp.verify(quorum <= self.data.nbVoters, message = ERR.MultisignAdmin_MoreQuorumThanVoters)
                self.data.quorum = quorum
            with arg.match("changeTarget", "target") as target:
                self.data.target = sp.some(target)
            with arg.match("changeTimeout", "timeout") as timeout:
                self.data.timeout = timeout
            with arg.match("changeVoters", "changeVoters") as changeVoters:
                sp.for voterAddress in changeVoters.removed.elements():
                    sp.verify(self.data.addrVoterId.contains(voterAddress), message = ERR.MultisignAdmin_VoterUnknown)
                    voterId = sp.compute(self.data.addrVoterId[voterAddress])
                    del self.data.addrVoterId[voterAddress]
                    del self.data.keyVoterId[self.data.voters[voterId].publicKey]
                    del self.data.proposals[voterId]
                    del self.data.voters[voterId]
                self.data.nbVoters = sp.as_nat(self.data.nbVoters - sp.len(changeVoters.removed))
                sp.for voter in changeVoters.added:
                    sp.verify(~self.data.addrVoterId.contains(voter.addr) &
                              ~self.data.keyVoterId.contains(voter.publicKey),
                              message = ERR.MultisignAdmin_VoterAlreadyknown)
                    self.data.lastVoterId += 1
                    voterId = self.data.lastVoterId
                    self.data.voters[voterId] = sp.record(
                        publicKey = voter.publicKey,
                        addr = voter.addr,
                        lastProposalId = 0,
                    )
                    self.data.addrVoterId[voter.addr] = voterId
                    self.data.keyVoterId[voter.publicKey] = voterId
                self.data.nbVoters += sp.len(changeVoters.added)
                sp.verify(self.data.nbVoters > 0, message = ERR.MultisignAdmin_VotersLessThan1)
                sp.verify(self.data.quorum <= self.data.nbVoters, message = ERR.MultisignAdmin_MoreQuorumThanVoters)

#########
# Helpers

class SelfHelper():
    def variant(content):
        return sp.variant("selfAdmin", content)

    def changeQuorum(quorum):
        return SelfHelper.variant(
            [sp.variant("changeQuorum", quorum)]
        )

    def changeAdmin(admin):
        return SelfHelper.variant(
            [sp.variant("changeAdmin", admin)]
        )

    def changeTarget(target):
        return SelfHelper.variant(
            [sp.variant("changeTarget", target)]
        )

    def changeTimeout(timeout):
        return SelfHelper.variant(
            [sp.variant("changeTimeout", timeout)]
        )

    def changeVoters(removed = [], added = []):
        added_list = []
        for added_info in added:
            addr, publicKey = added_info
            added_list.append(
                sp.record(
                    addr = addr,
                    publicKey = publicKey)
                )
        return SelfHelper.variant(
            [sp.variant("changeVoters",
                sp.record(
                    removed = sp.set(removed),
                    added = sp.list(added_list)
                )
            )])

def sign(account, contract, voterId, initiatorId, proposalId, yay):
    message = sp.pack(
        sp.pair(contract.address, sp.pair(initiatorId, proposalId))
    )
    signature = sp.make_signature(account.secret_key, message, message_format = 'Raw')
    vote = sp.record(
        voterId = voterId,
        signature = signature,
        yay = yay
    )
    return vote

def vote(contract, signer, yay):
    """
        Only use for test as you can't know if the proposalId correspond to
        the one you want to vote
    """
    voterId = contract.data.addrVoterId[signer.address]
    proposal = contract.data.proposals[voterId]
    return sp.record(
        proposalId = proposal.id,
        initiatorId = voterId,
        yay = yay
    )

################
# Test contract

class Administrated(sp.Contract):
    """
        This contract is a sample
        It shouws how a contract can be administrated
        through the multisign administration contract
    """
    def __init__(self, admin, active):
        self.init_type(sp.TRecord(
            admin = sp.TAddress,
            active = sp.TBool,
            value = sp.TOption(sp.TInt),
        ))
        self.init(admin = admin,
                  active = active,
                  value = sp.none)

    AdministrationType = sp.TVariant(
        setAdmin = sp.TAddress,
        setActive = sp.TBool
    )

    @sp.entry_point
    def administrate(self, actions):
        sp.verify(sp.sender == self.data.admin, message = "NOT ADMIN")
        sp.set_type(actions, sp.TList(Administrated.AdministrationType))
        sp.for action in actions:
            with (action).match_cases() as arg:
                with arg.match('setActive') as active:
                    self.data.active = active
                with arg.match('setAdmin') as admin:
                    self.data.admin = admin

    @sp.entry_point
    def setValue(self, value):
        sp.verify(self.data.active, message = "NOT ACTIVE")
        self.data.value = value

################
# Tests

def add_test(name, is_default = True):
    @sp.add_test(name = name, is_default = is_default)
    def test():
        sc = sp.test_scenario()
        sc.add_flag("no-initial-cast")
        sc.h1(name)
        sc.table_of_contents()

        admin = sp.test_account("admin")
        signer1 = sp.test_account("signer1")
        signer2 = sp.test_account("signer2")
        signer3 = sp.test_account("signer3")
        signer4 = sp.test_account("signer4")

        sc.h2("Init contracts")

        sc.h3("Administrated")
        administrated = Administrated(admin.address, False)
        sc += administrated
        administrated_entrypoint = sp.to_address(
            sp.contract(Administrated.AdministrationType, administrated.address, entry_point = "administrate").open_some()
        )

        sc.h3("multisignAdmin")
        multisignAdmin = MultisignAdmin(
            quorum = 1,
            timeout = 5,
            addrVoterId = {signer1.address: 0, signer2.address: 1},
            keyVoterId = {signer1.public_key: 0, signer2.public_key: 1},
            voters = {
                        0: sp.record(addr = signer1.address, publicKey = signer1.public_key, lastProposalId = 0),
                        1: sp.record(addr = signer2.address, publicKey = signer2.public_key, lastProposalId = 0),
                     },
            lastVoterId = 1,
            TTargetAdminAction = Administrated.AdministrationType,
            metadataURL = "https://cloudflare-ipfs.com/ipfs/QmYnU2jwq4XU4jwX1Rmu1EGfmyhMhpDCpPpHF5j9jF9y1w",
        )
        sc += multisignAdmin
        now = sp.timestamp(1)

        if name == "Self Administration tests":
            ##########################
            # Auto-accepted proposal #
            ##########################
            sc.h2("Auto-accepted proposal when quorum is 1")
            sc.h3("signer1 propose to change quorum to 2")
            sc.verify(multisignAdmin.data.quorum == 1)
            changeQuorum = SelfHelper.changeQuorum(2)
            multisignAdmin.newProposal([changeQuorum]).run(sender = signer1, now = now)
            now = now.add_seconds(1)
            sc.verify(multisignAdmin.data.quorum == 2)

            ##################
            # Invalid quorum #
            ##################
            sc.h2("Invalid quorum proposal")
            sc.h3("signer1 new proposal to change quorum to 3")
            sc.verify(multisignAdmin.data.quorum != 3)
            changeQuorum = SelfHelper.changeQuorum(3)
            multisignAdmin.newProposal([changeQuorum]).run(sender = signer1, now = now)
            # Proposal has not been validated yet
            sc.verify(multisignAdmin.data.quorum == 2)
            sc.h3("signer2 votes the proposal")
            sc.p("proposal is rejected because nbSigners < proposed quorum")
            multisignAdmin.vote([vote(multisignAdmin, signer1, yay = True)]).run(sender = signer2, valid=False)
            sc.verify(multisignAdmin.data.quorum != 3)

            ##############
            # Add signer #
            ##############
            sc.h2("Adding new voters")
            sc.h3("signer2 new proposal to include signer3")
            sc.verify(~multisignAdmin.data.voters.contains(2))
            changeVoters = SelfHelper.changeVoters([], added = [(signer3.address, signer3.public_key)])
            multisignAdmin.newProposal([changeVoters]).run(sender = signer2, now = now)
            sc.h3("signer1 votes the proposal")
            multisignAdmin.vote([vote(multisignAdmin, signer2, yay = True)]).run(sender = signer1)
            sc.verify(multisignAdmin.data.voters.contains(2))
            now = now.add_seconds(1)

            #########################
            # Newly included signer #
            #########################
            sc.h2("Newly included signer starts a proposal")
            sc.h3("New proposal by signer 3 to increase quorum to 3")
            sc.verify(multisignAdmin.data.quorum != 3)
            changeQuorum = SelfHelper.changeQuorum(3)
            multisignAdmin.newProposal([changeQuorum]).run(sender = signer3, now = now)
            sc.h3("signer1 votes the proposal")
            multisignAdmin.vote([vote(multisignAdmin, signer3, yay = True)]).run(sender = signer1)
            sc.verify(multisignAdmin.data.quorum == 3)
            now = now.add_seconds(1)

            ##########
            # Cancel #
            ##########
            sc.h2("Proposal cancellation")
            sc.h3("New proposal")
            sc.verify(multisignAdmin.data.timeout != 10)
            changeTimeout = SelfHelper.changeTimeout(10)
            multisignAdmin.newProposal([changeTimeout]).run(sender = signer1, now = now)
            sc.h3("Signer 2 tries to cancel the proposal")
            voterId = multisignAdmin.data.addrVoterId[signer1.address]
            proposalId = multisignAdmin.data.proposals[voterId].id
            multisignAdmin.cancelProposal(proposalId).run(sender = signer2, valid = False)
            sc.h3("Signer 1 cancels the proposal")
            multisignAdmin.cancelProposal(proposalId).run(sender = signer1)
            sc.h3("Signer 2 tries to vote the canceled proposal")
            multisignAdmin.vote([vote(multisignAdmin, signer1, yay = True)]).run(sender = signer2, valid = False)
            sc.verify(multisignAdmin.data.timeout != 10)

            ############
            # Rejected #
            ############
            sc.h2("Proposal rejection")
            sc.h3("New proposal")
            sc.verify(multisignAdmin.data.timeout != 10)
            changeTimeout = SelfHelper.changeTimeout(10)
            multisignAdmin.newProposal([changeTimeout]).run(sender = signer1, now = now)
            sc.h3("Signer 2 votes against the proposal")
            multisignAdmin.vote([vote(multisignAdmin, signer1, yay = False)]).run(sender = signer2)
            sc.h3("Signer 3 votes against the proposal")
            sc.verify(multisignAdmin.data.proposals[voterId].canceled == False)
            multisignAdmin.vote([vote(multisignAdmin, signer1, yay = False)]).run(sender = signer3)
            voterId = multisignAdmin.data.addrVoterId[signer1.address]
            sc.verify(multisignAdmin.data.proposals[voterId].canceled == True)
            sc.verify(multisignAdmin.data.timeout != 10)

            ######################
            # Remove signer fail #
            ######################
            sc.h2("Invalid Removed signer proposal")
            sc.h3("Signer 1 new proposal: remove signer 3")
            changeVoters = SelfHelper.changeVoters(removed = [signer3.address])
            multisignAdmin.newProposal([changeVoters]).run(sender = signer1, now = now)
            sc.h3("Signer 2 votes the remove proposal")
            multisignAdmin.vote([vote(multisignAdmin, signer1, yay = True)]).run(sender = signer2)
            sc.h3("Signer 3 tries to vote the remove proposal")
            sc.p("Fails because quorum would be > number of signers")
            multisignAdmin.vote([vote(multisignAdmin, signer1, yay = True)]).run(sender = signer3, valid = False)
            sc.verify(multisignAdmin.data.voters.contains(2))

            ######################
            # 2 actions proposal #
            ######################
            sc.h2("2 actions proposal")
            sc.h3("Signer 1 new proposal: change quorum to 2 and remove signer 3")
            sc.verify(multisignAdmin.data.quorum == 3)
            sc.verify(multisignAdmin.data.voters.contains(2))
            changeQuorum = SelfHelper.changeQuorum(2)
            changeVoters = SelfHelper.changeVoters(removed = [signer3.address])
            multisignAdmin.newProposal([changeQuorum, changeVoters]).run(sender = signer1, now = now)
            sc.h3("Signer 2 votes the proposal")
            multisignAdmin.vote([vote(multisignAdmin, signer1, yay = True)]).run(sender = signer2)
            sc.h3("Signer 3 votes the proposal")
            multisignAdmin.vote([vote(multisignAdmin, signer1, yay = True)]).run(sender = signer3)
            now = now.add_seconds(1)
            sc.verify(multisignAdmin.data.quorum == 2)
            sc.verify(~multisignAdmin.data.voters.contains(2))

            ###########################
            # Votes for past proposal #
            ###########################
            sc.h2("Vote for past proposal")
            sc.h3("Signer 1 new proposal: change timeout to 2")
            changeTimeout = SelfHelper.changeTimeout(2)
            multisignAdmin.newProposal([changeTimeout]).run(sender = signer1, now = now)
            sc.h3("Signer 2 new proposal: add new signer")
            sc.verify(multisignAdmin.data.timeout != 3)
            changeVoters = SelfHelper.changeVoters([], added = [(signer4.address, signer4.public_key)])
            multisignAdmin.newProposal([changeVoters]).run(sender = signer2)
            now = now.add_seconds(1)
            sc.h3("Signer 2 tries to vote signer1's proposal after timedout")
            multisignAdmin.vote([vote(multisignAdmin, signer1, yay = True)]).run(sender = signer2, now = now.add_minutes(100), valid = False)
            sc.h3("Signer 1 votes for signer2's proposal")
            multisignAdmin.vote([vote(multisignAdmin, signer2, yay = True)]).run(sender = signer1, now = now)
            sc.h3("Signer 2 tries to vote signer1's proposal while a more recent one was accepted")
            multisignAdmin.vote([vote(multisignAdmin, signer1, yay = True)]).run(sender = signer2, now = now.add_seconds(1), valid = False)
            now = now.add_seconds(1)

            ##############
            # Multivotes #
            ##############
            sc.h2("Multi vote in one call")
            sc.h3("Signer 1 new proposal")
            changeTimeout = SelfHelper.changeTimeout(2)
            multisignAdmin.newProposal([changeTimeout]).run(sender = signer1, now = now)
            now = now.add_seconds(1)
            sc.h3("Signer 2 and Signer 3 votes are pushed by Signer 1")
            signer2_vote = sign(signer2, voterId = 1, contract = multisignAdmin, initiatorId = 0, proposalId = proposalId, yay = True, )
            signer4_vote = sign(signer4, voterId = 3, contract = multisignAdmin, initiatorId = 0, proposalId = proposalId, yay = True, )
            proposalVotes = sp.record(initiatorId = 0, proposalId = proposalId, votes = [signer2_vote, signer4_vote])
            multisignAdmin.multiVote([proposalVotes]).run(sender = signer1, now = now)
            sc.verify(multisignAdmin.data.timeout == 2)
            now = now.add_seconds(1)

        ##########################################

        else:
            #########################
            # Target Administration #
            #########################
            now = sp.timestamp(2)
            sc.h2("Set multisignAdmin as administrated's admin")
            administrated.administrate([sp.variant("setAdmin", multisignAdmin.address)]).run(sender = admin, now = now)

            sc.h2("Use multisignadmin to set a target")
            sc.h3("Signer 1 new proposal: changeTarget")
            now = now.add_seconds(10)
            targetAddress = sp.contract(
                sp.TList(Administrated.AdministrationType),
                administrated.address,
                entry_point = "administrate"
            ).open_some()
            sc += multisignAdmin.newProposal([
                SelfHelper.changeTarget(sp.to_address(targetAddress))
            ]).run(sender = signer1, now = now)

            sc.h2("Use multisignadmin to administrate target")
            sc.h3("Signer 1 new proposal: setActive = True on target")
            sc.verify(~administrated.data.active)
            now = now.add_seconds(12)
            changeTargetActive = sp.variant("targetAdmin", [sp.variant("setActive", True)])
            multisignAdmin.newProposal([changeTargetActive]).run(sender = signer1, now = now)
            sc.verify(administrated.data.active)

if "templates" not in __name__:
    add_test("Self Administration tests")
    add_test("Target Administration tests", is_default = False)
