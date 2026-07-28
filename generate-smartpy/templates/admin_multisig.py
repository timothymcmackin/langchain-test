import smartpy as sp

"""
    A Multisig Contract used to administrate other contracts.
    THIS CONTRACT IS FOR ILLUSTRATIVE PURPOSE.
    IT HAS NOT BEEN AUDITED.
"""

class MS_TYPES:
    #############################################
    #           == Multisig Types ==            #
    #                                           #
    # The types in this file are shared with    #
    # contracts interacting with the multisig   #
    # contract.                                 #
    #############################################

    # Internal administration action type specification
    InternalAdminAction = sp.TVariant(
        changeSigners   = sp.TVariant(
                            removed = sp.TSet(sp.TAddress),
                            added   = sp.TList(
                                        sp.TRecord(
                                            address     = sp.TAddress,
                                            publicKey   = sp.TKey
                                        ).right_comb()
                                    )
                        ).right_comb(),
        changeQuorum    = sp.TNat,
        changeMetadata  = sp.TPair(sp.TString, sp.TOption(sp.TBytes)),
    ).right_comb()

    # External administration action type specification
    ExternalAdminAction = sp.TRecord(
        target  = sp.TAddress,
        actions = sp.TBytes
    ).right_comb()

    # Proposal action type specification
    ProposalAction = sp.TVariant(
        internal = sp.TList(InternalAdminAction),
        external = sp.TList(ExternalAdminAction)
    ).right_comb()

    # Proposal type specification
    Proposal = sp.TRecord(
        startedAt       = sp.TTimestamp,
        initiator       = sp.TAddress,
        endorsements    = sp.TSet(sp.TAddress),
        actions         = ProposalAction
    ).right_comb()

    AggregatedProposalParams = sp.TRecord(
        signatures      = sp.TList(
                            sp.TRecord(
                                signerAddress   = sp.TAddress,
                                signature       = sp.TSignature
                            ).right_comb()
                        ),
        proposalId      = sp.TNat,
        actions         = ProposalAction
    ).right_comb()

    AggregatedEndorsementParams = sp.TList(
        sp.TRecord(
            signatures      = sp.TList(
                                sp.TRecord(
                                    signerAddress   = sp.TAddress,
                                    signature       = sp.TSignature
                                ).right_comb()
                            ),
            proposalId      = sp.TNat
        ).right_comb()
    )

#####################################
# + Metadata                        #
#####################################
METADATA = {
    "name"          : "Generic Multisig Administrator",
    "version"       : "1",
    "description"   : "Generic Multisig Administrator",
    "source"        : {
        "tools": [ "SmartPy" ]
    },
    "interfaces"    : [ "TZIP-016" ],
}

#####################################
# + Error Messages                  #
#####################################
class ERR:
    def make(s): return ("MULTISIG_" + s)

    Badsig                 = make("Badsig")
    ProposalUnknown        = make("ProposalUnknown")
    NotInitiator           = make("NotInitiator")
    SignerUnknown          = make("SignerUnknown")
    InvalidTarget          = make("InvalidTarget")
    MoreQuorumThanSigners  = make("MoreQuorumThanSigners")
    InvalidProposalId      = make("InvalidProposalId")

#####################################
# + Helpers                         #
#####################################
class MultisigHelpers:
    def failIfNotSigner(self, address):
        sp.verify(self.data.signers.contains(address), message = ERR.SignerUnknown)

    def failIfProposalNotActive(self, proposalId):
        sp.verify(self.data.activeProposals.contains(proposalId), message = ERR.ProposalUnknown)

#####################################
# + Contract                        #
#####################################
class MultisigAdmin(sp.Contract, MultisigHelpers):
    def __init__(
            self,
            quorum,
            signers,
            metadataURL
        ):

        # Metadata helper
        self.init_metadata("metadata", METADATA)

        self.init_type(
            sp.TRecord(
                quorum          = sp.TNat,
                lastProposalId  = sp.TNat,
                signers         = sp.TMap(
                                    sp.TAddress,
                                    sp.TRecord(
                                        publicKey       = sp.TKey,
                                        lastProposalId  = sp.TOption(sp.TNat)
                                    ).right_comb()
                                ),
                proposals       = sp.TBigMap(sp.TNat, MS_TYPES.Proposal),
                activeProposals = sp.TSet(sp.TNat),
                metadata        = sp.TBigMap(sp.TString, sp.TBytes),
            ).right_comb()
        )
        self.init(
            quorum              = quorum,
            lastProposalId      = 0,
            signers             = signers,
            proposals           = sp.big_map(),
            activeProposals     = sp.set(),
            metadata            = sp.utils.metadata_of_url(metadataURL)
        )

    #####################################
    # ++ ENTRYPOINTS                    #
    #####################################

    @sp.entry_point
    def proposal(self, actions):
        """
            Each user can have at most one proposal active at a time.
            Submitting a new proposal overrides the previous one.
        """
        # Proposals can only be submitted by registered signers
        self.failIfNotSigner(sp.sender)

        # If the proposal initiator has an active proposal,
        # then replace that proposal with the new one
        signerLastProposalId = self.data.signers[sp.sender].lastProposalId
        with sp.if_(signerLastProposalId != sp.none):
            self.data.activeProposals.remove(signerLastProposalId.open_some())

        # Increment proposal counter
        self.data.lastProposalId += 1
        proposalId = self.data.lastProposalId
        # Store new proposal
        self.data.activeProposals.add(proposalId)
        self.data.proposals[proposalId] = sp.record(
            startedAt       = sp.now,
            initiator       = sp.sender,
            endorsements    = sp.set([sp.sender]),
            actions         = actions
        )
        # Update signer's last proposal
        self.data.signers[sp.sender].lastProposalId = sp.some(proposalId)

        # Approve the proposal if quorum only requires 1 vote
        with sp.if_(self.data.quorum < 2):
            self.onApproved(
                sp.record(
                    proposalId  = proposalId,
                    actions     = actions,
                )
            )

    @sp.entry_point
    def endorsement(self, endorsements):
        """
            Entrypoint used to submit endorsements to single/multiple proposals.
        """
        # Endorsements can only be submitted by registered signers
        self.failIfNotSigner(sp.sender)

        # Iterate over every endorsement
        with sp.for_("pId", endorsements) as pId:
            self.registerEndorsement(
                sp.record(
                    proposalId      = pId,
                    signerAddress   = sp.sender
                )
            )

            # Approve the proposal if quorum was reached
            proposal = self.data.proposals[pId]
            with sp.if_(sp.len(proposal.endorsements) >= self.data.quorum):
                self.onApproved(
                    sp.record(
                        proposalId  = pId,
                        actions     = proposal.actions,
                    )
                )

    @sp.entry_point
    def aggregated_proposal(self, params):
        """
            Users can send aggregated proposal, which are signed offchain and validated onchain.
        """
        sp.set_type(params, MS_TYPES.AggregatedProposalParams)
        self.failIfNotSigner(sp.sender)

        self.data.lastProposalId += 1
        sp.verify(self.data.lastProposalId == params.proposalId, message = ERR.InvalidProposalId)

        proposal        = sp.compute(
                            sp.record(
                                startedAt       = sp.now,
                                initiator       = sp.sender,
                                endorsements    = sp.set([sp.sender]),
                                actions         = params.actions
                            )
                        )

        # If the proposal initiator has an active proposal,
        # then replace that proposal with the new one
        proposerLastProposalId = self.data.signers[sp.sender].lastProposalId
        with sp.if_(proposerLastProposalId != sp.none):
            self.data.activeProposals.remove(proposerLastProposalId.open_some())
        self.data.signers[sp.sender].lastProposalId = sp.some(params.proposalId)

        self.data.activeProposals.add(params.proposalId)
        self.data.proposals[params.proposalId] = proposal

        preSignature    = sp.compute(
                            sp.pack(
                                sp.record(
                                    actions         = params.actions,
                                    # (contractAddress + proposalId) protect against replay attacks
                                    proposalId      = params.proposalId,
                                    contractAddress = sp.self_address,
                                )
                            )
                        )

        # Validate and apply endorsements
        with sp.for_("signature", params.signatures) as signature:
            self.failIfNotSigner(signature.signerAddress)

            publicKey = self.data.signers[signature.signerAddress].publicKey
            sp.verify(sp.check_signature(publicKey, signature.signature, preSignature), message = ERR.Badsig)

            proposal.endorsements.add(signature.signerAddress)

        # Check quorum
        with sp.if_(sp.len(proposal.endorsements) >= self.data.quorum):
            self.onApproved(
                sp.record(
                    proposalId  = params.proposalId,
                    actions     = proposal.actions,
                )
            )

    @sp.entry_point
    def aggregated_endorsement(self, endorsements):
        """
            Users can send aggregated votes, which are signed offchain and validated onchain.
        """
        sp.set_type(endorsements, MS_TYPES.AggregatedEndorsementParams)

        with sp.for_("endorsment", endorsements) as endorsement:
            with sp.for_("signature", endorsement.signatures) as signature:
                self.failIfNotSigner(signature.signerAddress)
                preSignature = sp.pack(
                    sp.record(
                        # (contractAddress + proposalId) protect against replay attacks
                        contractAddress = sp.self_address,
                        proposalId      = endorsement.proposalId
                    )
                )
                publicKey = self.data.signers[signature.signerAddress].publicKey
                sp.verify(
                    sp.check_signature(publicKey, signature.signature, preSignature),
                    message = ERR.Badsig
                )
                self.registerEndorsement(
                    sp.record(
                        proposalId      = endorsement.proposalId,
                        signerAddress   = signature.signerAddress
                    )
                )
            proposal = sp.compute(self.data.proposals[endorsement.proposalId])
            with sp.if_(sp.len(proposal.endorsements) >= self.data.quorum):
                self.onApproved(
                    sp.record(
                        proposalId  = endorsement.proposalId,
                        actions     = proposal.actions,
                    )
                )

    @sp.entry_point
    def cancel_proposal(self, proposalId):
        self.failIfNotSigner(sp.sender)

        # Signers can only cancel their own proposals
        sp.verify(self.data.proposals[proposalId].initiator == sp.sender, message = ERR.NotInitiator)
        self.data.activeProposals.remove(proposalId)

    #####################################
    # ++ GLOBAL LAMBDAS                 #
    #####################################

    @sp.private_lambda(with_storage="read-write", wrap_call=True)
    def registerEndorsement(self, params):
        self.failIfProposalNotActive(params.proposalId)
        # Add endorsement to proposal
        self.data.proposals[params.proposalId].endorsements.add(params.signerAddress)

    @sp.private_lambda(with_storage="read-write", with_operations=True, wrap_call=True)
    def onApproved(self, params):
        with (params.actions).match_cases() as arg:
            # Internal actions are applied to the multisig contract
            with arg.match("internal") as internalActions:
                with sp.for_("action", internalActions) as action:
                    self.selfAdmin(action)
                # Removes all active proposals after an administrative change.
                self.removeActiveProposals()
            # External actions are applied to other contracts
            with arg.match("external") as externalActions:
                with sp.for_("action", externalActions) as action:
                    target = sp.contract(sp.TBytes, action.target).open_some(ERR.InvalidTarget)
                    sp.transfer(action.actions, sp.tez(0), target)

        self.data.activeProposals.remove(params.proposalId)

    def selfAdmin(self, action):
        """
            Apply administrative actions to the multisig contract
        """
        with (action).match_cases() as arg:
            with arg.match('changeQuorum') as quorum:
                self.data.quorum = quorum
            with arg.match('changeMetadata') as metadata:
                k, v = sp.match_pair(metadata)
                with sp.if_(v.is_some()):
                    self.data.metadata[k] = v.open_some()
                with sp.else_():
                    del self.data.metadata[k]

            with arg.match('changeSigners') as changeSigners:
                with (changeSigners).match_cases() as cvAction:
                    with cvAction.match('removed') as removeSet:
                        with sp.for_("address", removeSet.elements()) as address:
                            with sp.if_(self.data.signers.contains(address)):
                                # Remove signer
                                del self.data.signers[address]
                                # We don't remove signer[address].lastProposalId
                                # because we remove all activeProposals after it.
                    with cvAction.match('added') as addList:
                        with sp.for_("signer", addList) as signer:
                            self.data.signers[signer.address]   = sp.record(
                                                                    publicKey       = signer.publicKey,
                                                                    lastProposalId  = sp.none
                                                                )
        # Ensure that the contract never requires more quorum than the total of signers.
        sp.verify(self.data.quorum <= sp.len(self.data.signers), message = ERR.MoreQuorumThanSigners)

    def removeActiveProposals(self):
        """
            This method removes all active proposals when either the quorum or the signers get updated.
        """
        self.data.activeProposals = sp.set([])


sp.add_compilation_target(
    "multisig_admin",
    MultisigAdmin(
        quorum              = 1,
        signers             = sp.map(
                                {
                                    sp.address("KT1_SIGNER1_ADDRESS") : sp.record(
                                                                            publicKey       = sp.key("KT1_SIGNER1_KEY"),
                                                                            lastProposalId  = sp.none
                                                                        )
                                },
                                tkey    = sp.TAddress,
                                tvalue  = sp.TRecord(
                                            publicKey       = sp.TKey,
                                            lastProposalId  = sp.TOption(sp.TNat)
                                        ).right_comb()
                            ),
        metadataURL         = "ipfs://"
    )
)

if "templates" not in __name__:


    #########
    # Helpers

    class InternalHelper():
        def variant(content):
            return sp.variant("internal", content)

        def changeQuorum(quorum):
            return sp.variant("changeQuorum", quorum)

        def removeSigners(l):
            return sp.variant("changeSigners",
                sp.variant("removed", sp.set(l))
            )

        def addSigners(l):
            added_list = []
            for added_info in l:
                addr, publicKey = added_info
                added_list.append(
                    sp.record(
                        address = addr,
                        publicKey = publicKey)
                    )
            return sp.variant("changeSigners",
                sp.variant("added", sp.list(added_list))
            )

    class ExternalHelper():
        def variant(content):
            return sp.variant("external", content)

        def changeActive(active):
            return sp.variant("changeActive", active)

        def changeAdmin(address):
            return sp.variant("changeAdmin", address)

    def sign(account, contract):
        message = sp.pack(
            sp.record(
                contractAddress = contract.address,
                proposalId      = contract.data.lastProposalId
            )
        )
        signature = sp.make_signature(account.secret_key, message, message_format = 'Raw')
        vote = sp.record(
            signerAddress   = account.address,
            signature       = signature
        )
        return vote

    ################
    # Test contract

    class Administrated(sp.Contract):
        """
            This contract is a sample
            It shows how a contract can be administrated
            through the multisig administration contract
        """
        def __init__(self, admin, active):
            self.init(
                admin = admin,
                active = active
            )

        AdministrationType = sp.TVariant(
            changeAdmin    = sp.TAddress,
            changeActive   = sp.TBool
        )

        @sp.entry_point
        def administrate(self, actionsBytes):
            sp.verify(sp.sender == self.data.admin, message = "NOT ADMIN")

            # actionsBytes is packed and must be unpacked
            actions = sp.unpack(actionsBytes, sp.TList(Administrated.AdministrationType)).open_some(message = "Actions are invalid")

            with sp.for_("action", actions) as action:
                with (action).match_cases() as arg:
                    with arg.match('changeActive') as active:
                        self.data.active = active
                    with arg.match('changeAdmin') as admin:
                        self.data.admin = admin

        @sp.entry_point
        def verifyActive(self):
            sp.verify(self.data.active, message = "NOT ACTIVE")

        # Helpers

        def packActions(self, actions):
            actions = sp.set_type_expr(actions, sp.TList(Administrated.AdministrationType))
            return sp.pack(actions)


    def add_test(internal_tests, is_default = True):
        name = "Internal Administration tests" if internal_tests else "External Administration tests"
        @sp.add_test(name = name, is_default = is_default)
        def test():
            sc = sp.test_scenario()
            sc.h1(name)
            sc.table_of_contents()

            admin = sp.test_account("admin")
            signer1 = sp.test_account("signer1")
            signer2 = sp.test_account("signer2")
            signer3 = sp.test_account("signer3")
            signer4 = sp.test_account("signer4")

            if internal_tests:

                sc.h3("Originate Multisig Admin")
                multisigAdmin = MultisigAdmin(
                    quorum              = 1,
                    signers             = sp.map(
                                            {
                                                signer1.address : sp.record(
                                                                    publicKey       = signer1.public_key,
                                                                    lastProposalId  = sp.none
                                                                ),
                                                signer2.address : sp.record(
                                                                    publicKey       = signer2.public_key,
                                                                    lastProposalId  = sp.none
                                                                )
                                            }
                                        ),
                    metadataURL         = "ipfs://"
                )
                sc += multisigAdmin

                ##########################
                # Auto-accepted proposal #
                ##########################
                sc.h2("Auto-accepted proposal when quorum is 1")
                sc.h3("signer1 propose to change quorum to 2")
                sc.verify(multisigAdmin.data.quorum == 1)
                changeQuorum = InternalHelper.changeQuorum(2)
                sc += multisigAdmin.proposal(InternalHelper.variant([changeQuorum])).run(sender = signer1)
                sc.verify(multisigAdmin.data.quorum == 2)

                ####################
                # Add a 3rd signer #
                ####################
                sc.h2("Adding a 3rd signer")
                sc.h3("signer2 new proposal to include signer3")
                sc.verify(sp.len(multisigAdmin.data.signers) == 2)
                sc.verify(~multisigAdmin.data.signers.contains(signer3.address))
                changeSigners = InternalHelper.addSigners([(signer3.address, signer3.public_key)])
                sc += multisigAdmin.proposal(InternalHelper.variant([changeSigners])).run(sender = signer2)
                sc.h3("signer1 votes the proposal")
                sc += multisigAdmin.endorsement([multisigAdmin.data.lastProposalId]).run(sender = signer1)
                sc.verify(multisigAdmin.data.signers.contains(signer3.address))
                sc.verify(sp.len(multisigAdmin.data.signers) == 3)

                ############################################
                # New proposal (change Quorum from 2 to 3) #
                ############################################
                sc.h2("New proposal (change Quorum from 2 to 3)")
                sc.h3("signer1 new proposal to change quorum to 3")
                changeQuorum = InternalHelper.changeQuorum(3)
                sc += multisigAdmin.proposal(InternalHelper.variant([changeQuorum])).run(sender = signer1)
                # Proposal has not been validated yet
                sc.verify(multisigAdmin.data.quorum == 2)
                sc.h3("signer2 votes the proposal (2/2)")
                sc += multisigAdmin.endorsement([multisigAdmin.data.lastProposalId]).run(sender = signer2)
                sc.verify(multisigAdmin.data.quorum == 3)

                ###########################################
                # Newly included signer starts a proposal #
                ###########################################
                sc.h2("Newly included signer starts a proposal")
                sc.h3("New proposal by signer 3 to decrease quorum to 2")
                changeQuorum = InternalHelper.changeQuorum(2)
                sc += multisigAdmin.proposal(InternalHelper.variant([changeQuorum])).run(sender = signer3)
                sc.h3("signer1 votes the proposal")
                sc += multisigAdmin.endorsement([multisigAdmin.data.lastProposalId]).run(sender = signer1)
                sc.verify(multisigAdmin.data.quorum == 3)
                sc.h3("signer2 votes the proposal")
                sc += multisigAdmin.endorsement([multisigAdmin.data.lastProposalId]).run(sender = signer2)
                sc.verify(multisigAdmin.data.quorum == 2)

                ##########
                # Cancel #
                ##########
                sc.h2("Proposal cancellation")
                sc.h3("New proposal by signer 1")
                changeTimeout = InternalHelper.changeQuorum(3)
                sc += multisigAdmin.proposal(InternalHelper.variant([changeTimeout])).run(sender = signer1)
                sc.verify(sp.len(multisigAdmin.data.activeProposals) == 1)
                sc.h3("Signer 2 tries to cancel the proposal (must fail, only the initiator can cancel)")
                sc += multisigAdmin.cancel_proposal(multisigAdmin.data.lastProposalId).run(sender = signer2, valid = False)
                sc.h3("Signer 1 cancels the proposal")
                sc += multisigAdmin.cancel_proposal(multisigAdmin.data.lastProposalId).run(sender = signer1)
                sc.verify(sp.len(multisigAdmin.data.activeProposals) == 0)
                sc.h3("Signer 2 tries to vote the canceled proposal")
                sc += multisigAdmin.endorsement([multisigAdmin.data.lastProposalId]).run(sender = signer2, valid = False)
                sc.verify(multisigAdmin.data.quorum != 3)

                ######################
                # 2 actions proposal #
                ######################
                sc.h2("2 actions proposal")
                sc.h3("Signer 1 new proposal: change quorum to 2 and add signer 4")
                sc.verify(~multisigAdmin.data.signers.contains(signer4.address))
                changeQuorum = InternalHelper.changeQuorum(3)
                changeSigners = InternalHelper.addSigners([(signer4.address, signer4.public_key)])
                sc += multisigAdmin.proposal(InternalHelper.variant([changeQuorum, changeSigners])).run(sender = signer1)
                sc.h3("Signer 2 votes the proposal")
                sc += multisigAdmin.endorsement([multisigAdmin.data.lastProposalId]).run(sender = signer2)
                sc.verify(multisigAdmin.data.quorum == 3)
                sc.verify(multisigAdmin.data.signers.contains(signer4.address))

                #########################################
                # 2 Internal proposals at the same time #
                #########################################
                sc.h3("Signer 1 new proposal: change quorum to 2 and remove signer 4")
                changeQuorum = InternalHelper.changeQuorum(2)
                sc += multisigAdmin.proposal(InternalHelper.variant([changeQuorum])).run(sender = signer1)
                changeSigners = InternalHelper.removeSigners([signer4.address])
                sc += multisigAdmin.proposal(InternalHelper.variant([changeSigners])).run(sender = signer2)
                sc.verify(sp.len(multisigAdmin.data.activeProposals) == 2)
                sc.h3("Signer 3 votes on quorum proposal")
                sc += multisigAdmin.endorsement([sp.as_nat(multisigAdmin.data.lastProposalId - 1)]).run(sender = signer3)
                sc.h3("Signer 4 votes on signers proposal")
                sc += multisigAdmin.endorsement([multisigAdmin.data.lastProposalId]).run(sender = signer4)
                sc.h3("Confirm that nothing has changed")
                sc.verify(multisigAdmin.data.quorum == 3)
                sc.verify(multisigAdmin.data.signers.contains(signer4.address))
                sc.h3("Signer 4 votes on quorum proposal")
                sc += multisigAdmin.endorsement([sp.as_nat(multisigAdmin.data.lastProposalId - 1)]).run(sender = signer4)
                sc.h3("Confirm that quorum was updated and signers proposal was canceled")
                sc.verify(sp.len(multisigAdmin.data.activeProposals) == 0)
                sc.verify(multisigAdmin.data.quorum == 2)
                sc.verify(multisigAdmin.data.signers.contains(signer4.address))

                #########################
                # Multisig endorsements #
                #########################
                sc.h2("Multi vote in one call")
                sc.h3("Signer 1 new proposal")
                changeQuorum = InternalHelper.changeQuorum(3)
                sc += multisigAdmin.proposal(InternalHelper.variant([changeQuorum])).run(sender = signer1)
                sc.h3("Signer 2 and Signer 3 votes are pushed by Signer 1")
                signer2_endorsement = sign(signer2, contract = multisigAdmin)
                signer3_endorsement = sign(signer3, contract = multisigAdmin)
                proposalEndorsements = sp.record(
                    proposalId = multisigAdmin.data.lastProposalId,
                    signatures = [signer2_endorsement, signer3_endorsement]
                )
                sc += multisigAdmin.aggregated_endorsement([proposalEndorsements]).run(sender = signer1)
                sc.verify(multisigAdmin.data.quorum == 3)

                #####################
                # Multisig proposal #
                #####################
                sc.h2("Multi vote in one call")
                sc.h3("Signer 1 new proposal")
                changeQuorum = InternalHelper.changeQuorum(3)
                sc += multisigAdmin.proposal(InternalHelper.variant([changeQuorum])).run(sender = signer1)
                sc.h3("Signer 2 and Signer 3 votes are pushed by Signer 1")
                signer2_vote = sign(signer2, contract = multisigAdmin)
                signer3_vote = sign(signer3, contract = multisigAdmin)
                proposalVotes = sp.record(
                    proposalId = multisigAdmin.data.lastProposalId,
                    signatures = [signer2_vote, signer3_vote]
                )
                sc += multisigAdmin.aggregated_endorsement([proposalVotes]).run(sender = signer1)
                sc.verify(multisigAdmin.data.quorum == 3)

            ##########################################

            else:

                sc.h3("Originate Multisig Admin")
                multisigAdmin = MultisigAdmin(
                    quorum              = 3,
                    signers             = sp.map(
                                            {
                                                signer1.address : sp.record(
                                                                    publicKey       = signer1.public_key,
                                                                    lastProposalId  = sp.none
                                                                ),
                                                signer2.address : sp.record(
                                                                    publicKey       = signer2.public_key,
                                                                    lastProposalId  = sp.none
                                                                ),
                                                signer3.address : sp.record(
                                                                    publicKey       = signer3.public_key,
                                                                    lastProposalId  = sp.none
                                                                )
                                            }
                                        ),
                    metadataURL         = "ipfs://"
                )
                sc += multisigAdmin

                sc.h3("Originate administrated contract")
                administrated = Administrated(admin.address, False)
                sc += administrated
                administrated_entrypoint = administrated.typed.administrate

                sc.h2("Set multisig as admin of administrated contract")
                sc.verify(administrated.data.active == False)
                sc.verify(administrated.data.admin == admin.address)
                actions = administrated.packActions([ExternalHelper.changeAdmin(multisigAdmin.address)])
                sc += administrated.administrate(actions).run(sender = admin)
                sc.verify(administrated.data.active == False)
                sc.verify(administrated.data.admin == multisigAdmin.address)

                sc.h2("Activate the administrated contract")
                sc.h3("Signer 1 new proposal: changeActive")
                actions = administrated.packActions([ExternalHelper.changeActive(True)])
                sc += multisigAdmin.proposal(ExternalHelper.variant(
                    [sp.record(
                        target  = sp.to_address(administrated_entrypoint),
                        actions = actions
                    )]
                )).run(sender = signer1)
                sc.verify(administrated.data.active == False)
                sc.h3("Signer 2 votes")
                sc += multisigAdmin.endorsement([multisigAdmin.data.lastProposalId]).run(sender = signer2)
                sc.verify(administrated.data.active == False)
                sc.h3("Signer 3 votes")
                sc += multisigAdmin.endorsement([multisigAdmin.data.lastProposalId]).run(sender = signer3)
                sc.verify(administrated.data.active == True)

                sc.h2("Use Multisig vote to deactivate the administrated contract")
                sc.h3("Signer 1 new proposal: changeActive")
                actions = administrated.packActions([ExternalHelper.changeActive(False)])
                sc += multisigAdmin.proposal(ExternalHelper.variant(
                    [sp.record(
                        target  = sp.to_address(administrated_entrypoint),
                        actions = actions
                    )]
                )).run(sender = signer1)
                sc.verify(administrated.data.active == True)
                sc.h3("Signer 2 and Signer 3 votes are pushed by Signer 1")
                signer2_vote = sign(signer2, contract = multisigAdmin)
                signer3_vote = sign(signer3, contract = multisigAdmin)
                proposalVotes = sp.record(
                    proposalId = multisigAdmin.data.lastProposalId,
                    signatures = [signer2_vote, signer3_vote]
                )
                sc += multisigAdmin.aggregated_endorsement([proposalVotes]).run(sender = signer1)
                sc.verify(administrated.data.active == False)

    add_test(internal_tests = True)
    add_test(internal_tests = False)
