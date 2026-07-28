import smartpy as sp
import sys

FA2 = sp.io.import_template("FA2.py")
MSA = sp.io.import_template("price_feed_multisign_admin.py")

# CONSTANTS (Useful when originating the contracts)
GENERATE_DEPLOYMENT_CONTRACTS = False

ADMIN_ADDRESS = sp.address("tz1evBmfWZoPDN38avoRGbjJaLBJUP8AZz6a")
AGGREGATOR_ADDRESS = sp.address("KT1CfuSjCcunNQ5qCCro2Kc74uivnor9d8ba")
PROXY_ADDRESS = sp.address("KT1PG6uK91ymZYVtjnRXv2mEdFYSH6P6uJhC")
TOKEN_ADDRESS = sp.address("KT1LcrXERzpDeUXWxLEWnLipHrhWEhzSRTt7")

ORACLE_1_ADDRESS = sp.address("KT1LhTzYhdhxTqKu7ByJz8KaShF6qPTdx5os")
ORACLE_2_ADDRESS = sp.address("KT1P7oeoKWHx5SXt73qpEanzkr8yeEKABqko")
ORACLE_3_ADDRESS = sp.address("KT1SCkxmTqTkmc7zoAP5uMYT9rp9iqVVRgdt")
ORACLE_4_ADDRESS = sp.address("KT1LLTzYhdhxTqKu7ByJz8KaShF6qPTdx5os")
ORACLE_5_ADDRESS = sp.address("KT1P6oeoKWHx5SXt73qpEanzkr8yeEKABqko")
ORACLE_6_ADDRESS = sp.address("KT1SskxmTqTkmc7zoAP5uMYT9rp9iqVVRgdt")

# Admins/Signers of multisign admin contract
ACCOUNT_1_ADDRESS = sp.address("tz1evBmfWZoPDN38avoRGbjJaLBJUP8AZz6a")
ACCOUNT_1_PUBLIC_KEY = sp.key("edpkuZ7ERiU5B8knLqQsVMH86j9RLMUyHyL665oCXDkPQxF7HGqSeJ")
ACCOUNT_1_SECRET = "edskRowES25ZTKFDV5GJamCUfLB1gjE9YP25kfXtxNg8WTMiFuoD5gtUa3Evk3gViFADogBeDhWBjHNDJoQ44sWzQzaoTH4qcj"
ACCOUNT_2_ADDRESS = sp.address("tz1NDUP7uyQNFsSzamkPMfbxirMrg3D6TR2w")
ACCOUNT_2_PUBLIC_KEY = sp.key("edpktwD9RYpBiqhFCsaN3t7BbF7uT3zqRfkSWCwuDdfMUDMwDnk9Tz")
ACCOUNT_2_SECRET = "edskS4dHu2VNf8eyLhqoMRUtzWdcTMd4y8qJVe19ea5P2N2D1M4Puizfbh9zoRpHAASPYtMcSRbrVFC127EY11nDJPEH62cYKR"

class CONSTANTS:
    NAME                = "Price Feed Aggregator"
    DESCRIPTION         = "XTZ/EUR"
    VERSION             = "1"
    RESERVE_ROUNDS      = 2
    LINK_TOKEN_ID       = 0
    DECIMALS            = 8
    TIMEOUT             = 10 # In minutes
    ORACLE_PAYMENT      = 1
    MAX_ROUND           = 2**32-1
    USE_BIGMAP_ORACLES  = False

AGGREGATOR_METADATA = {
    "name"          : CONSTANTS.NAME,
    "version"       : CONSTANTS.VERSION,
    "description"   : CONSTANTS.DESCRIPTION,
    "source"        : {
        "tools": [ "SmartPy" ]
    },
    "interfaces"    : [ "TZIP-016" ],
}

class TYPES:
    # Round specification type
    TRoundData              = sp.TRecord(
                                roundId         = sp.TNat,
                                answer          = sp.TNat,
                                startedAt       = sp.TTimestamp,
                                updatedAt       = sp.TTimestamp,
                                answeredInRound = sp.TNat
                            )
    # Round details specification type
    TRoundDetails           = sp.TRecord(
                                submissions     = sp.TMap(sp.TAddress, sp.TNat),
                                minSubmissions  = sp.TNat,
                                maxSubmissions  = sp.TNat,
                                timeout         = sp.TNat,
                                activeOracles   = sp.TSet(sp.TAddress)
                            )
    # Oracle details specification type
    TOracleDetails          = sp.TRecord(
                                startingRound       = sp.TNat,
                                endingRound         = sp.TNat,
                                lastStartedRound    = sp.TNat,
                                withdrawable        = sp.TNat,
                                adminAddress        = sp.TAddress
                            )
    # Link token recorded funds specification type
    TRecordedFunds          = sp.TRecord(
                                available   = sp.TNat,
                                allocated   = sp.TNat
                            )
    # Proxy Admin Action specification type
    TProxyAdminAction       = sp.TVariant(
                                changeActive = sp.TBool,
                                changeAdmin = sp.TAddress,
                                changeAggregator = sp.TAddress
                            )
    # Aggregator Admin Action specification type
    TAggregatorAdminAction = sp.TVariant(
                                changeOracles = sp.TRecord(
                                    removed = sp.TList(sp.TAddress),
                                    added = sp.TList(
                                        sp.TPair(
                                            sp.TAddress,
                                            sp.TRecord(
                                                startingRound       = sp.TNat,
                                                endingRound         = sp.TOption(sp.TNat),
                                                adminAddress        = sp.TAddress,
                                            )
                                        )
                                    )
                                ),
                                changeActive = sp.TBool,
                                changeAdmin = sp.TAddress,
                                updateFutureRounds = sp.TRecord(
                                    minSubmissions  = sp.TNat,
                                    maxSubmissions  = sp.TNat,
                                    restartDelay    = sp.TNat,
                                    timeout         = sp.TNat,
                                    oraclePayment   = sp.TNat,
                                )
                            )
    TBaseStorage            = {
                                "active"                : sp.TBool,
                                "decimals"              : sp.TNat,
                                "admin"                 : sp.TAddress,
                                "metadata"              : sp.TBigMap(sp.TString, sp.TBytes),

                                "minSubmissions"        : sp.TNat,
                                "maxSubmissions"        : sp.TNat,
                                "restartDelay"          : sp.TNat,
                                "timeout"               : sp.TNat, # In minutes
                                "oraclePayment"         : sp.TNat,

                                "latestRoundId"         : sp.TNat,
                                "reportingRoundId"      : sp.TNat,
                                "rounds"                : sp.TBigMap(sp.TNat, TRoundData),
                                "previousRoundDetails"  : TRoundDetails,
                                "reportingRoundDetails" : TRoundDetails,

                                "linkToken"             : sp.TAddress,
                                "recordedFunds"         : TRecordedFunds,
                                "oracles"               : sp.TMap(sp.TAddress, TOracleDetails)
                            }

class ERR:
    Aggregator_NotAdmin                             = "Aggregator_NotAdmin"
    Aggregator_NotOracle                            = "Aggregator_NotOracle"
    Aggregator_NotYetEnabledOracle                  = "Aggregator_NotYetEnabledOracle"
    Aggregator_NotLongerAllowedOracle               = "Aggregator_NotLongerAllowedOracle"
    Aggregator_InvalidRound                         = "Aggregator_InvalidRound"
    Aggregator_FutureRound                          = "Aggregator_FutureRound"
    Aggregator_RoundNotOver                         = "Aggregator_RoundNotOver"
    Aggregator_PreviousRoundNotOver                 = "Aggregator_PreviousRoundNotOver"
    Aggregator_WaitBeforeInit                       = "Aggregator_WaitBeforeInit"
    Aggregator_AlreadySubmitted                     = "Aggregator_AlreadySubmittedForThisRound"
    Aggregator_SubmittedInCurrent                   = "Aggregator_SubmittedInCurrent"
    Aggregator_CurrentHasValue                      = "Aggregator_CurrentHasValue"
    Aggregator_CallbackNotFound                     = "Aggregator_CallbackNotFound"
    Aggregator_DelayExceedTotal                     = "Aggregator_DelayExceedTotal"
    Aggregator_MaxSubmissions                       = "Aggregator_RoundMaxSubmissionExceed"
    Aggregator_MaxInferiorToMin                     = "Aggregator_MaxInferiorToMin"
    Aggregator_MaxExceedActive                      = "Aggregator_MaxExceedActive"
    Aggregator_OraclePaymentUnderflow               = "Aggregator_OraclePaymentUnderflow"
    Aggregator_NotOracleAdmin                       = "Aggregator_NotOracleAdmin"
    Aggregator_InsufficientWithdrawableFunds        = "Aggregator_InsufficientWithdrawableFunds"
    Aggregator_NotLinkToken                         = "Aggregator_NotLinkToken"
    Aggregator_InvalidTokenInterface                = "Aggregator_InvalidTokenkInterface"
    Aggregator_MinSubmissionsTooLow                 = "Aggregator_MinSubmissionsTooLow"
    Aggregator_InsufficientFundsForPayment          = "Aggregator_InsufficientFundsForPayment"

    Proxy_InvalidParametersInLatestRoundDataView    = "Proxy_InvalidParametersInLatestRoundDataView"
    Proxy_InvalidParametersInDecimalsView           = "Proxy_InvalidParametersInDecimalsView"
    Proxy_InvalidParametersInDescriptionView        = "Proxy_InvalidParametersInDescriptionView"
    Proxy_InvalidParametersInVersionView            = "Proxy_InvalidParametersInVersionView"
    Proxy_AggregatorNotConfigured                   = "Proxy_AggregatorNotConfigured"
    Proxy_NotAdmin                                  = "Proxy_NotAdmin"


################
# + Link Token
################

class LinkToken(FA2.FA2):
    def __init__(self, admin, config, metadata):
        FA2.FA2_core.__init__(self, config, metadata, paused = False, administrator = admin)

################
# - Link Token
################

class Aggregator_Views:
    # Returns the number of decimals in the answer
    # (e.g. 8)
    @sp.entry_point
    def decimals(self, callback):
        sp.transfer(self.data.decimals, sp.tez(0), callback)

    # Get data from the latest round
    @sp.entry_point
    def latestRoundData(self, callback):
        """
            Callback with data about the latest round. Consumers are encouraged
            to check that they're receiving fresh data by inspecting the
            updatedAt and answeredInRound return values.

            Args:
                callback : sp.TAddress

            Returns:
                roundId (sp.TNat): round ID for which data was retrieved
                answer (sp.TNat):  the answer for the given round
                startedAt (sp.TTimestamp): timestamp when the round was started.
                updatedAt (sp.TTimestamp): timestamp when the answer was updated.
                    (i.e. answer was last computed)
                answeredInRound (sp.TNat): the round ID of the round in which
                    the answer was computed. answeredInRound may be smaller than
                    roundId when the round timed out.
                    answeredInRound is equal to roundId when the round didn't
                    time out and was computed regularly.

                Note that for in-progress rounds (i.e. rounds that haven't yet
                received maxSubmissions) answer and updatedAt may change
                between queries.
        """
        sp.transfer(self.data.rounds[self.data.latestRoundId], sp.tez(0), callback)

class Aggregator_OffchainViews:
    @sp.offchain_view(pure = True, doc = "Gets the available amount that an oracle can withdraw")
    def getWithdrawablePayment(self, oracleAddress):
        """
            Gets the available amount that an oracle can withdraw

            Args:
                oracleAddress : sp.TAddress

            Returns:
                sp.TNat : Withdrawable payment amount
        """
        sp.result(self.data.oracles[oracleAddress].withdrawable)

    @sp.offchain_view(pure = True, doc = "Gets the number of decimals in the answer (e.g. 8)")
    def getDecimals(self):
        """
            Gets the number of decimals in the answer (e.g. 8)

            Returns:
                sp.TNat : the number of decimals
        """
        sp.result(self.data.decimals)

    # Get data from a specific round
    @sp.offchain_view(pure = True, doc = "Gets the information of a specific round")
    def getRoundData(self, roundId):
        """
            Gets the information of a specific round

            Args:
                roundId : sp.TNat

            Returns:
                roundId         (sp.TNat)       : round ID for which data was retrieved.
                answer          (sp.TNat)       : the answer for the given round.
                startedAt       (sp.TTimestamp) : timestamp when the round was started.
                updatedAt       (sp.TTimestamp) : timestamp when the answer was updated.
                answeredInRound (sp.TNat)       : the round ID of the round in which
                    the answer was computed. answeredInRound may be smaller than
                    roundId when the round timed out.
                    answeredInRound is equal to roundId when the round didn't
                    time out and was computed regularly.

                Note that for in-progress rounds (i.e. rounds that haven't yet
                received maxSubmissions) answer and updatedAt may change
                between queries.
        """
        sp.if self.data.rounds.contains(roundId):
            sp.result(sp.some(self.data.rounds[roundId]))
        sp.else:
            sp.result(sp.none)

class Aggregator_OraclePaymentMethods:
    def payOracle(self, oracle, roundId):
        """
            Update the withdrawable amount of a specific oracle after a sucessul submission
        """
        payment = self.data.oraclePayment
        funds = self.data.recordedFunds
        funds.available = sp.as_nat(funds.available - payment, message = ERR.Aggregator_OraclePaymentUnderflow)
        funds.allocated += payment
        self.data.oracles[oracle].withdrawable += payment

    def requestBalanceUpdate(self):
        """
            Call Link token and request a balance update
        """
        contract = sp.contract(
           FA2.Balance_of.entry_point_type(),
           self.data.linkToken,
           entry_point = "balance_of"
        ).open_some(message = ERR.Aggregator_InvalidTokenInterface)
        args = sp.record(
            callback    = sp.self_entry_point("updateAvailableFunds"),
            requests    = [
                sp.record(
                    owner       = sp.self_address,
                    token_id    = CONSTANTS.LINK_TOKEN_ID,
                )
            ]
        )
        sp.transfer(args, sp.tez(0), contract)

    @sp.entry_point
    def forceBalanceUpdate(self):
        """
            Call Link token and request a balance update (Forced, this should be called after an origination)
        """
        self.requestBalanceUpdate()

    @sp.entry_point
    def updateAvailableFunds(self, params):
        """
            Receive balance update from link token
        """
        sp.set_type(params, FA2.Balance_of.response_type())

        # Ensure that this entrypoint is only called by the configured token
        sp.verify(sp.sender == self.data.linkToken, message = ERR.Aggregator_NotLinkToken)

        balance = sp.local("balance", 0)
        sp.for resp in params:
            sp.verify(resp.request.owner == sp.self_address)
            balance.value = resp.balance

        sp.if (balance.value != self.data.recordedFunds.available):
            self.data.recordedFunds.available = balance.value

    def requiredReserve(self, oraclePayment, oraclesCount):
        """
            Get the amount reserved for oracle payments
        """
        return oraclePayment * oraclesCount * CONSTANTS.RESERVE_ROUNDS

    @sp.entry_point
    def withdrawPayment(self, params):
        """
            Transfers the oracle's LINK to another address. Can only be called by the oracle's admin.

            Args:
                oracleAddress       : sp.TAddress   is the oracle whose LINK is transferred
                recipientAddress    : sp.TAddress   is the address to send the LINK to
                amount              : sp.TNat       is the amount of LINK to send
        """
        sp.verify(
            self.data.oracles[params.oracleAddress].adminAddress == sp.sender,
            message = ERR.Aggregator_NotOracleAdmin
        );

        withdrawable = self.data.oracles[params.oracleAddress].withdrawable

        sp.verify(withdrawable >= params.amount, message = ERR.Aggregator_InsufficientWithdrawableFunds)

        self.data.oracles[params.oracleAddress].withdrawable = sp.as_nat(withdrawable - params.amount);
        self.data.recordedFunds.allocated = sp.as_nat(self.data.recordedFunds.allocated - params.amount);

        token = sp.contract(
            self.linkToken.batch_transfer.get_type(),
            self.data.linkToken,
            entry_point = "transfer"
        ).open_some(message = ERR.Aggregator_InvalidTokenInterface)
        arg = [
            sp.record(
                from_ = sp.self_address,
                txs = [
                    sp.record(
                        to_         = params.recipientAddress,
                        token_id    = CONSTANTS.LINK_TOKEN_ID,
                        amount      = params.amount
                    )
                ]
            )
        ]
        # Send payment
        sp.transfer(arg, sp.tez(0), token)
        # Resync available funds
        self.requestBalanceUpdate()

class Aggregator_Math:
    # Returns the sorted middle, or the average of the two middle indexed items if the
    # array has an even number of elements.
    @sp.private_lambda()
    def median(self, submissions):
        xs = submissions
        result = sp.local('result', sp.nat(0))
        half = sp.local('half', sp.len(xs) / 2)
        hist = sp.local('hist', {})
        average = sp.local('average', ~(half.value * 2 != sp.len(xs)))
        sp.for x in xs:
            sp.if hist.value.contains(x):
                hist.value[x] += 1
            sp.else:
                hist.value[x] = 1
        i = sp.local('i', 0)
        sp.for x in hist.value.items():
            sp.if average.value:
                sp.if i.value < half.value:
                    result.value = x.key
                sp.else:
                    result.value += x.key
                    result.value /= 2
                    average.value = False
                i.value += x.value
            sp.else:
                sp.if i.value <= half.value:
                    result.value = x.key
                    i.value += x.value
        sp.result(result.value)

"""
    This contract aggregates off-chain data pushed by oracles.

    The submissions are gathered in rounds, with each round aggregating the submissions
    for each oracle into a single answer.

    The latest aggregated answer is exposed as well as historical answers and their updated at timestamp.
"""
class PriceAggregator(
    sp.Contract,
    Aggregator_OffchainViews,
    Aggregator_OraclePaymentMethods,
    Aggregator_Views,
    Aggregator_Math
):
    def __init__(
        self,
        useBigmapOracles,
        initialRoundDetails,
        tokenContract,
        tokenAddress,
        active,
        decimals,
        admin,
        oracles,
        timeout,
        oraclePayment,
        minSubmissions,
        maxSubmissions,
        restartDelay,
        metadataURL
    ):
        """
            Args:
                useBigmapOracles           : Use a big map to store the oracles
                initialRoundDetails        : Initial round details
                tokenContract (sp.Contract): Token Contract used for payment
                tokenAddress (sp.TAddress) : Address of the token used for payments
                active (sp.TBool)          : Aggregator state
                decimals (sp.TNat)         : The number of decimals in the answer.
                admin (sp.TAddress)        : Admin address, supposely the PriceAggregatorAdmin multisign contract
                oracleDetails (TYPES.TOracleDetails) : Parameters of the Oracle
                timeout (sp.TNat)          : Number of minutes after which a new round can be initiate
                oraclePayment (sp.TNat)    : Amount of Token payed to Oracle at each Submission
                minSubmissions (sp.TNat)   : Min submissions' number to be able to update a value
                maxSubmissions (sp.TNat)   : Max submissions' number to be able to seal a value
                restartDelay (sp.TNat)     : Number of rounds an Oracle has to wait between 2 round initiate
                metadataURL(str)           : url of metadata file
        """

        self.linkToken          = tokenContract
        self.useBigmapOracles   = useBigmapOracles

        # Generate the metadata representation
        # The generated metadata should be copied and destributed with IPFS
        self.init_metadata("metadata", {
            **AGGREGATOR_METADATA,
            "views" : [
                self.getDecimals,
                self.getWithdrawablePayment,
                self.getRoundData
            ],
        })

        init_type   = TYPES.TBaseStorage;
        init        = {
            "active"                : active,
            "decimals"              : decimals,
            "admin"                 : admin,
            "metadata"              : sp.utils.metadata_of_url(metadataURL),
            "oracles"               : sp.map(oracles),

            "minSubmissions"        : minSubmissions,
            "maxSubmissions"        : maxSubmissions,
            "restartDelay"          : restartDelay,
            "timeout"               : timeout,
            "oraclePayment"         : oraclePayment,

            "latestRoundId"         : 0,
            "reportingRoundId"      : 0,

            "rounds"                : sp.big_map(),
            "previousRoundDetails"  : initialRoundDetails,
            "reportingRoundDetails" : initialRoundDetails,

            "linkToken"             : tokenAddress,
            "recordedFunds"         : sp.record(
                                        available   = 0,
                                        allocated   = 0
                                    ),
        }

        if useBigmapOracles:
            init_type.oraclesAddresses  = sp.TSet(sp.TAddress)
            init_type.oracles           = sp.TBigMap(sp.TAddress, TYPES.TOracleDetails)
            init.oracles                = sp.big_map(oracles)
            init.oraclesAddresses       = oracles.keys()

        self.init_type(sp.TRecord(**init_type))
        self.init(**init)

    def updatePrevious(self, submission):
        currentRoundId          = self.data.reportingRoundId
        previousRoundId         = sp.as_nat(currentRoundId - 1)
        previousRoundDetails    = self.data.previousRoundDetails

        sp.verify(
            ~previousRoundDetails.submissions.contains(sp.sender),
            message = ERR.Aggregator_SubmittedInCurrent
        )
        sp.verify(
            sp.len(previousRoundDetails.submissions) < previousRoundDetails.maxSubmissions,
            message = ERR.Aggregator_MaxSubmissions
        )

        previousRoundDetails.submissions[sp.sender] = submission
        sp.if sp.len(previousRoundDetails.submissions) >= previousRoundDetails.minSubmissions:
            self.data.rounds[previousRoundId].answer = self.median(previousRoundDetails.submissions.values())
            self.data.rounds[previousRoundId].updatedAt = sp.now
            self.data.rounds[previousRoundId].answeredInRound = currentRoundId

    def updateCurrent(self, submission):
        currentRoundId = self.data.reportingRoundId
        currentRoundDetails = self.data.reportingRoundDetails

        sp.verify(~currentRoundDetails.submissions.contains(sp.sender), message = ERR.Aggregator_AlreadySubmitted)
        sp.verify(
            sp.len(currentRoundDetails.submissions) < currentRoundDetails.maxSubmissions,
            message = ERR.Aggregator_MaxSubmissions
        )

        currentRoundDetails.submissions[sp.sender] = submission
        sp.if sp.len(currentRoundDetails.submissions) >= currentRoundDetails.minSubmissions:
            self.data.rounds[currentRoundId].answer = self.median(currentRoundDetails.submissions.values())
            self.data.rounds[currentRoundId].updatedAt = sp.now
            self.data.rounds[currentRoundId].answeredInRound = currentRoundId
            self.data.latestRoundId = currentRoundId

    def updateNext(self, submission):
        currentRoundId = self.data.reportingRoundId
        nextRoundId = currentRoundId + 1

        sp.if currentRoundId > 0:
            currentRound = self.data.rounds[currentRoundId]
            currentRoundDetails = self.data.reportingRoundDetails

            timeout = currentRound.startedAt.add_minutes(sp.to_int(self.data.timeout))
            roundInit_delay = self.data.oracles[sp.sender].lastStartedRound + self.data.restartDelay

            sp.verify(
                (self.data.oracles[sp.sender].lastStartedRound == 0) | (nextRoundId > roundInit_delay),
                message = ERR.Aggregator_WaitBeforeInit
            )
            sp.verify(
                (sp.now > timeout) | (currentRound.answeredInRound == currentRoundId),
                message = ERR.Aggregator_PreviousRoundNotOver
            )

        # If minimum submissions is 1, then include the answer in the round initialization
        answer = sp.local("answer", 0)
        answeredInRound = sp.local("answeredInRound", 0)
        sp.if self.data.minSubmissions == 1:
            answer.value = submission
            answeredInRound.value = nextRoundId

        self.data.rounds[nextRoundId] = sp.record(
            roundId         = nextRoundId,
            answer          = answer.value,
            startedAt       = sp.now,
            updatedAt       = sp.now,
            answeredInRound = answeredInRound.value
        )

        self.data.previousRoundDetails = self.data.reportingRoundDetails

        self.data.reportingRoundDetails = sp.record(
            submissions = {sp.sender: submission},
            minSubmissions = self.data.minSubmissions,
            maxSubmissions = self.data.maxSubmissions,
            timeout = self.data.timeout,
            activeOracles = self.getActiveOracles(nextRoundId),
        )

        self.data.oracles[sp.sender].lastStartedRound = nextRoundId
        self.data.reportingRoundId = nextRoundId

    @sp.private_lambda(with_storage="read-write", wrap_call=True)
    def getActiveOracles(self, roundId):
        oracles = sp.local("oracles", sp.list([], t = sp.TAddress))
        if self.useBigmapOracles:
            oracles.value = self.data.oraclesAddresses
        else:
            oracles.value = self.data.oracles.keys()

        activeOracles = sp.local("activeOracles", sp.set(l = [], t = sp.TAddress))

        sp.for oracle in oracles.value:
            oracleDetails = self.data.oracles[oracle]
            sp.if (oracleDetails.endingRound >= roundId) & (oracleDetails.startingRound <= roundId):
                activeOracles.value.add(oracle)

        sp.result(activeOracles.value)

    @sp.entry_point
    def submit(self, params):
        """
        Called by oracles when they have witnessed a need to update

        Args:
            roundId (sp.Nat)     : ID of the round this submission pertains to
            submission (sp.TNat) : updated data that the oracle is submitting
        """
        latestRoundId = self.data.latestRoundId
        currentRoundId = self.data.reportingRoundId
        roundId, submission = sp.match_pair(params)

        sp.verify(self.data.active)
        sp.verify(self.data.oracles.contains(sp.sender), message = ERR.Aggregator_NotOracle)
        sp.verify(
            self.data.oracles[sp.sender].startingRound <= roundId,
            message = ERR.Aggregator_NotYetEnabledOracle
        )
        sp.verify(
            self.data.oracles[sp.sender].endingRound > roundId,
            message = ERR.Aggregator_NotLongerAllowedOracle
        )

        # Only allow new submissions in [currentRoundId -1; currentRoundId +1] round interval
        sp.verify(
            (roundId + 1 == currentRoundId) | (roundId == currentRoundId) | (roundId == currentRoundId + 1),
            message = ERR.Aggregator_InvalidRound
        )

        sp.if (roundId + 1) == currentRoundId:
            self.updatePrevious(submission)
        sp.else:
            sp.if roundId == currentRoundId:
                self.updateCurrent(submission)
            sp.else:
                self.updateNext(submission)

        # Update the oracle withdrawable amount
        self.payOracle(sp.sender, roundId)

    @sp.entry_point
    def administrate(self, actions):
        sp.verify(sp.sender == self.data.admin, message = ERR.Aggregator_NotAdmin)
        sp.set_type(actions, sp.TList(TYPES.TAggregatorAdminAction))
        sp.for action in actions:
            with (action).match_cases() as arg:
                with arg.match('changeActive') as active:
                    self.data.active = active
                with arg.match('changeAdmin') as admin:
                    self.data.admin = admin
                with arg.match('updateFutureRounds') as futureRounds:
                    self.updateFutureRounds(futureRounds)
                with arg.match('changeOracles') as params:
                    self.changeOracles(params)

    def updateFutureRounds(self, params):
        sp.verify(sp.sender == self.data.admin, message = ERR.Aggregator_NotAdmin)

        currentRoundId = self.data.reportingRoundId

        oraclesCount = sp.compute(sp.len(self.data.oracles))
        sp.verify(params.maxSubmissions >= params.minSubmissions, message = ERR.Aggregator_MaxInferiorToMin)
        sp.verify(oraclesCount >= params.maxSubmissions, message = ERR.Aggregator_MaxExceedActive)
        sp.verify((oraclesCount == 0) | (oraclesCount > params.restartDelay), message = ERR.Aggregator_DelayExceedTotal)
        sp.verify((oraclesCount == 0) | (params.minSubmissions > 0), message = ERR.Aggregator_MinSubmissionsTooLow)

        sp.verify(self.data.recordedFunds.available >= self.requiredReserve(params.oraclePayment, oraclesCount),
            message = ERR.Aggregator_InsufficientFundsForPayment
        );

        self.data.restartDelay                  = params.restartDelay
        self.data.minSubmissions                = params.minSubmissions
        self.data.maxSubmissions                = params.maxSubmissions
        self.data.timeout                       = params.timeout
        self.data.oraclePayment                 = params.oraclePayment

    def changeOracles(self, params):
        sp.verify(sp.sender == self.data.admin, message = ERR.Aggregator_NotAdmin)
        sp.for oracleAddress in params.removed:
            del self.data.oracles[oracleAddress]
            if self.useBigmapOracles:
                self.data.oraclesAddress.remove(oracleAddress)

        sp.for oracle in params.added:
            oracleAddress, oracleData = sp.match_pair(oracle)
            self.addOracle(oracleAddress, oracleData)

    def addOracle(self, oracleAddress, params):
        sp.set_type(params.endingRound, sp.TOption(sp.TNat))

        endingRound = sp.local("endingRound", CONSTANTS.MAX_ROUND);

        sp.if params.endingRound.is_some():
            endingRound.value.set(params.endingRound.open_some())

        self.data.oracles[oracleAddress] = sp.record(
            startingRound       = params.startingRound,
            endingRound         = endingRound.value,
            adminAddress        = params.adminAddress,
            lastStartedRound    = 0,
            withdrawable        = sp.nat(0),
        );

        if self.useBigmapOracles:
            self.data.oraclesAddress.add(oracleAddress)

        reportingRoundId = self.data.reportingRoundId
        sp.if (reportingRoundId != 0) & (params.startingRound <= reportingRoundId):
            self.data.reportingRoundDetails.activeOracles.add(oracleAddress)

class Proxy(sp.Contract):
    def __init__(self, active, admin, aggregator):
        self.init_type(
            sp.TRecord(
                active          = sp.TBool,
                admin           = sp.TAddress,
                aggregator      = sp.TOption(sp.TAddress)
            )
        )
        self.init(
            active          = active,
            admin           = admin,
            aggregator      = aggregator
        )

    @sp.entry_point
    def decimals(self, params):
        aggregator = self.data.aggregator.open_some(message = ERR.Proxy_AggregatorNotConfigured)
        view = sp.contract(
            sp.TPair(sp.TUnit, sp.TAddress),
            aggregator,
            entry_point = "decimals"
        ).open_some(message = ERR.Proxy_InvalidParametersInDecimalsView);

        sp.transfer(params, sp.tez(0), view)

    @sp.entry_point
    def version(self, params):
        aggregator = self.data.aggregator.open_some(message = ERR.Proxy_AggregatorNotConfigured)
        view = sp.contract(
            sp.TPair(sp.TUnit, sp.TAddress),
            aggregator,
            entry_point = "version"
        ).open_some(message = ERR.Proxy_InvalidParametersInVersionView);

        sp.transfer(params, sp.tez(0), view)

    @sp.entry_point
    def description(self, params):
        aggregator = self.data.aggregator.open_some(message = ERR.Proxy_AggregatorNotConfigured)
        view = sp.contract(
            sp.TPair(sp.TUnit, sp.TAddress),
            aggregator,
            entry_point = "description"
        ).open_some(message = ERR.Proxy_InvalidParametersInDescriptionView);
        sp.transfer(params, sp.tez(0), view)

    @sp.entry_point
    def latestRoundData(self, params):
        aggregator = self.data.aggregator.open_some(message = ERR.Proxy_AggregatorNotConfigured)
        view = sp.contract(
            sp.TPair(sp.TUnit, sp.TAddress),
            aggregator,
            entry_point = "latestRoundData"
        ).open_some(message = ERR.Proxy_InvalidParametersInLatestRoundDataView);
        sp.transfer(params, sp.tez(0), view)

    @sp.entry_point
    def administrate(self, actions):
        sp.verify(sp.sender == self.data.admin, message = ERR.Proxy_NotAdmin)
        sp.set_type(actions, sp.TList(TYPES.TProxyAdminAction))
        sp.for action in actions:
            with (action).match_cases() as arg:
                with arg.match('changeActive') as active:
                    self.data.active = active
                with arg.match('changeAdmin') as admin:
                    self.data.admin = admin
                with arg.match('changeAggregator') as aggregator:
                    self.data.aggregator = sp.some(aggregator)

class Viewer(sp.Contract):
    def __init__(self, admin, proxy):
        self.init(
            admin = admin,
            proxy = proxy,
            latestRoundData = sp.none,
        )

    @sp.entry_point
    def getLatestRoundData(self):
        proxy = sp.contract(
            sp.TAddress,
            self.data.proxy,
            entry_point = "latestRoundData"
        ).open_some(message = "Wrong Interface: Could not resolve proxy latestRoundData entry-point.")

        sp.transfer(sp.self_entry_point_address("setLatestRoundData"), sp.tez(0), proxy)

    @sp.entry_point
    def setLatestRoundData(self, latestRoundData):
        sp.set_type(latestRoundData, TYPES.TRoundData)
        sp.verify(sp.sender == self.data.proxy)
        self.data.latestRoundData = sp.some(latestRoundData)

    @sp.entry_point
    def setup(self, admin, proxy):
        sp.verify(sp.sender == self.data.admin)
        self.data.admin = admin
        self.data.proxy = proxy

################
# + Test Helpers
################

def compute_latest_data(sc, aggregator):
    data = aggregator.data.rounds[aggregator.data.latestRoundId]
    return sc.compute(data)

def add_oracle(oracle, startingRound, endingRound, lastStartedRound):
    return sp.pair(
        oracle,
        sp.record(
            startingRound = startingRound,
            endingRound = sp.some(endingRound),
            lastStartedRound = lastStartedRound
        )
    )

################
# - Test Helpers
################

###################################
# Multisign Administrator Helpers #
###################################

class MSAggregatorHelper():
    def variant(content):
        return sp.variant("targetAdmin", content)

    def changeAdmin(admin):
        return sp.variant("changeAdmin", admin)

    def changeActive(active):
        return sp.variant("changeActive", active)

    def changeOracles(removed = [], added = []):
        return sp.variant("changeOracles",
            sp.record(
                removed = sp.list(removed),
                added = sp.list(added)
            )
        )

    def oracle(address, admin, startingRound, endingRound = sp.none):
        oracle_pair = sp.pair(
            address,
            sp.record(
                startingRound = startingRound,
                endingRound = endingRound,
                adminAddress = admin
            )
        )
        sp.set_type_expr(oracle_pair,
            sp.TPair(
                sp.TAddress,
                sp.TRecord(
                    startingRound       = sp.TNat,
                    endingRound         = sp.TOption(sp.TNat),
                    adminAddress        = sp.TAddress,
                )
            )
        )
        return oracle_pair

    def updateFutureRounds(minSubmissions, maxSubmissions, restartDelay, timeout, oraclePayment):
        return sp.variant("updateFutureRounds",
            sp.record(
                minSubmissions  = minSubmissions,
                maxSubmissions  = maxSubmissions,
                restartDelay    = restartDelay,
                timeout         = timeout,
                oraclePayment   = oraclePayment
            )
        )
MSAH = MSAggregatorHelper

class MSProxyHelper():
    def variant(content):
        return sp.variant("targetAdmin", content)

    def changeAggregator(aggregator):
        return sp.variant("changeAggregator", aggregator)

    def changeAdmin(admin):
        return sp.variant("changeAdmin", admin)

    def changeActive(active):
        return sp.variant("changeActive", active)

#########
# + Tests
#########
@sp.add_test(name = "ChainlinkPriceFeed")
def test():
    sc = sp.test_scenario()
    sc.h1("ChainLink PriceFeed")
    sc.table_of_contents()

    FALSE_ADMIN_ADDRESS = sp.test_account("FALSE ADMIN").address

    sc.show([
        ADMIN_ADDRESS,
        AGGREGATOR_ADDRESS,
        PROXY_ADDRESS,
        TOKEN_ADDRESS,
        ORACLE_1_ADDRESS,
        ORACLE_2_ADDRESS,
        ORACLE_3_ADDRESS,
        ORACLE_4_ADDRESS,
        ORACLE_5_ADDRESS,
        ORACLE_6_ADDRESS
    ])

    sc.h2("Link Token")
    linkToken = FA2.FA2(
        config = FA2.FA2_config(
            single_asset        = True,
            allow_self_transfer = True
        ),
        metadata = FA2.FA2.make_metadata(
            name = "wrapped LINK",
            decimals = 18,
            symbol = "wLINK"
        ),
        admin = ADMIN_ADDRESS,
    )
    sc += linkToken
    link_metadata = FA2.FA2.make_metadata(
        name        = "wrapped LINK",
        decimals    = 18,
        symbol      = "tzLINK"
    )
    sc += linkToken.mint(
        address     = ADMIN_ADDRESS,
        amount      = 50000000,
        symbol      = 'tzLINK',
        token_id    = CONSTANTS.LINK_TOKEN_ID,
        metadata    = link_metadata
    ).run(sender = ADMIN_ADDRESS)

    sc.h2("Aggregator")
    restartDelay = sp.nat(2)
    now = sp.timestamp(500)
    oracles = {
        ORACLE_1_ADDRESS: sp.record(
            startingRound       = 0,
            endingRound         = CONSTANTS.MAX_ROUND,
            lastStartedRound    = 0,
            withdrawable        = 0,
            adminAddress        = ADMIN_ADDRESS,
        ),
        ORACLE_2_ADDRESS: sp.record(
            startingRound       = 0,
            endingRound         = CONSTANTS.MAX_ROUND,
            lastStartedRound    = 0,
            withdrawable        = 0,
            adminAddress        = ADMIN_ADDRESS,
        ),
        ORACLE_3_ADDRESS: sp.record(
            startingRound       = 0,
            endingRound         = CONSTANTS.MAX_ROUND,
            lastStartedRound    = 0,
            withdrawable        = 0,
            adminAddress        = ADMIN_ADDRESS,
        ),
        ORACLE_4_ADDRESS: sp.record(
            startingRound       = 0,
            endingRound         = CONSTANTS.MAX_ROUND,
            lastStartedRound    = 0,
            withdrawable        = 0,
            adminAddress        = ADMIN_ADDRESS,
        ),
    }
    aggregator = PriceAggregator(
        useBigmapOracles    = CONSTANTS.USE_BIGMAP_ORACLES,
        initialRoundDetails = sp.record(
            submissions     = {},
            minSubmissions  = 0,
            maxSubmissions  = 0,
            timeout         = 0,
            activeOracles   = sp.set()
        ),
        tokenContract       = linkToken,
        tokenAddress        = linkToken.address,
        active              = True,
        decimals            = CONSTANTS.DECIMALS,
        admin               = ADMIN_ADDRESS,
        oracles             = oracles,
        timeout             = CONSTANTS.TIMEOUT,
        oraclePayment       = CONSTANTS.ORACLE_PAYMENT,
        minSubmissions      = 3,
        maxSubmissions      = 6,
        restartDelay        = restartDelay,
        metadataURL         = "<URL>"
    )
    sc += aggregator

    # Update aggregator available funds
    sc += linkToken.transfer(
            [
                linkToken.batch_transfer.item(
                    from_ = ADMIN_ADDRESS,
                    txs = [
                        sp.record(to_ = aggregator.address, amount = 50000, token_id = CONSTANTS.LINK_TOKEN_ID),
                    ]
                )
            ]
    ).run(sender = ADMIN_ADDRESS)
    sc += aggregator.forceBalanceUpdate()
    sc.show(aggregator.data.recordedFunds)

    sc.h2("Proxy")
    latestRoundDataView = sp.contract(
        sp.TAddress,
        AGGREGATOR_ADDRESS,
        entry_point = 'latestRoundData'
    ).open_some(message = "Invalid Interface")
    proxy = Proxy(
        active      = True,
        admin       = ADMIN_ADDRESS,
        aggregator  = sp.some(sp.to_address(latestRoundDataView)),
    )
    sc += proxy

    sc.h2("Viewer")
    viewer = Viewer(ADMIN_ADDRESS, PROXY_ADDRESS)
    sc += viewer

    ###################################
    # A scenario with multiple rounds #
    ###################################

    # Round 1
    sc.h2("A complete round")
    roundId = 1
    price = 500
    sc.h3(f"Oracle 1 submits value in round {roundId}")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price + 0)).run(sender = ORACLE_1_ADDRESS, now = now)
    sc.h3(f"Oracle 2 submits value in round {roundId}")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price + 5)).run(sender = ORACLE_2_ADDRESS, now = now)
    sc.h3(f"Oracle 3 submits value in round {roundId}")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price + 2)).run(sender = ORACLE_3_ADDRESS, now = now)
    sc.h3(f"Quorum is reached in round {roundId}")
    # Verify answer value
    sc.verify(compute_latest_data(sc, aggregator).answer == price + 2)
    sc.verify(compute_latest_data(sc, aggregator).roundId == roundId)
    sc.verify(compute_latest_data(sc, aggregator).answeredInRound == roundId)
    sc.show(aggregator.data.rounds[aggregator.data.latestRoundId])
    sc.h3(f"Oracle 4 submits value in round {roundId}")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price - 5)).run(sender = ORACLE_4_ADDRESS, now = now)
    sc.h3(f"Answer is updated in round {roundId}")
    # Verify answer value
    sc.verify(compute_latest_data(sc, aggregator).answer == (price + price + 2) // 2)
    sc.verify(compute_latest_data(sc, aggregator).roundId == roundId)
    sc.verify(compute_latest_data(sc, aggregator).answeredInRound == roundId)
    sc.show(aggregator.data.rounds[aggregator.data.latestRoundId])
    sc.h3(f"Oracle 5 is not assigned")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price - 5)).run(sender = ORACLE_5_ADDRESS, valid = False)

    # Round 2
    sc.h2("A timed out round")
    roundId += 1
    price = 502
    sc.h3(f"Oracle 1 fails to start a new round {roundId}")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price + 0)).run(sender = ORACLE_1_ADDRESS, now = now, valid = False)
    sc.h3(f"Oracle 2 starts a new round {roundId + 1}")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price + 1)).run(sender = ORACLE_2_ADDRESS, now = now)

    # Round 3
    roundId += 1
    now = now.add_minutes(11)
    sc.h3(f"Round {roundId} timed out")
    sc.h2("A new round")
    sc.h3(f"Oracle 3 starts a new round in round {roundId}")
    aggregator.submit((roundId, price + 1)).run(sender = ORACLE_3_ADDRESS, now = now)
    sc.h3(f"Oracle 1 fails to submit value in previous round {roundId - 1}, timed out")
    now = now.add_minutes(1)
    aggregator.submit((roundId - 1, price - 1)).run(sender = ORACLE_1_ADDRESS, now = now)
    sc.h3(f"Quorum is reached in previous round {roundId - 1}")
    sc.verify(compute_latest_data(sc, aggregator).answer == price - 1)
    sc.verify(compute_latest_data(sc, aggregator).roundId == roundId - 2)
    sc.verify(compute_latest_data(sc, aggregator).answeredInRound == roundId - 2)

    sc.show(aggregator.data.rounds[aggregator.data.latestRoundId])
    sc.h3(f"Oracle 1 submits value in current round {roundId}")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price + 2)).run(sender = ORACLE_1_ADDRESS, now = now)
    sc.h3(f"Oracle 4 submits value in previous round {roundId - 1}")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price + 3)).run(sender = ORACLE_4_ADDRESS, now = now)
    sc.h3(f"Quorum was reached in round {roundId - 1}")
    sc.verify(compute_latest_data(sc, aggregator).answer == price + 2)
    sc.verify(compute_latest_data(sc, aggregator).roundId == roundId)
    sc.verify(compute_latest_data(sc, aggregator).answeredInRound == roundId)
    sc.show(aggregator.data.rounds[aggregator.data.latestRoundId])

    # Round 4
    sc.h2("A new round")
    roundId += 1
    price = 515
    sc.h3(f"Oracle 4 starts a new round {roundId}")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price)).run(sender = ORACLE_4_ADDRESS, now = now)
    sc.h3(f"Oracle 3 fails to start a new round because {roundId} isn't over")
    now = now.add_minutes(1)
    aggregator.submit((roundId + 1, price)).run(sender = ORACLE_3_ADDRESS, now = now, valid = False)
    sc.h3(f"Oracle 1 submits value in current round {roundId}")
    now = now.add_minutes(1)
    aggregator.submit((roundId, price + 2)).run(sender = ORACLE_1_ADDRESS, now = now)
    sc.show(aggregator.data.rounds[sp.as_nat(aggregator.data.latestRoundId - 1)])
    sc.h3(f"Oracle 2 submits value in previous round {roundId - 1}")
    now = now.add_minutes(1)
    aggregator.submit((roundId - 1, price - 10)).run(sender = ORACLE_2_ADDRESS, now = now)
    sc.h3(f"Answer is updated in round {roundId - 1}")
    sc.verify(compute_latest_data(sc, aggregator).answer == 504)
    sc.verify(compute_latest_data(sc, aggregator).roundId == roundId - 1)
    sc.verify(compute_latest_data(sc, aggregator).answeredInRound == roundId)
    sc.show(aggregator.data.rounds[aggregator.data.latestRoundId])

    ##########
    # Withdraw oracle payment
    sc += aggregator.withdrawPayment(
        oracleAddress       = ORACLE_2_ADDRESS,
        recipientAddress    = ORACLE_2_ADDRESS,
        amount              = 2
    ).run(sender = ADMIN_ADDRESS)

    ##########
    # A viewer
    sc.h2("Viewer get latestRoundData")
    sc += viewer.getLatestRoundData()

    #############################
    # Aggregator's administration

    sc.h2("Administration")
    sc.h3("False Admin tries to administrate")
    updateFutureRounds = MSAH.updateFutureRounds(
        restartDelay    = 2,
        minSubmissions  = 4,
        maxSubmissions  = 6,
        timeout         = CONSTANTS.TIMEOUT,
        oraclePayment   = CONSTANTS.ORACLE_PAYMENT,
    )
    aggregator.administrate([updateFutureRounds]).run(sender = FALSE_ADMIN_ADDRESS, valid = False)

    sc.h3("Admin sets Admin 2 as Admin")
    changeAdmin = MSAH.changeAdmin(FALSE_ADMIN_ADDRESS)
    aggregator.administrate([changeAdmin]).run(sender = ADMIN_ADDRESS)

    sc.h3("Admin 2 administrates futureRounds and removes Oracle2")
    updateFutureRounds = MSAH.updateFutureRounds(
        restartDelay    = 0,
        minSubmissions  = 2,
        maxSubmissions  = 4,
        timeout         = CONSTANTS.TIMEOUT,
        oraclePayment   = CONSTANTS.ORACLE_PAYMENT,
    )
    updateOracles = MSAH.changeOracles(removed = [ORACLE_2_ADDRESS])
    aggregator.administrate([updateFutureRounds, updateOracles]).run(sender = FALSE_ADMIN_ADDRESS)


    ######################################
    # Administration via multisign admin #
    ######################################
    sc.h2("Multisign administration contract")
    now = now.add_minutes(1)
    multisignAdmin = MSA.MultisignAdmin(
        quorum                  = 1,
        timeout                 = 5,
        addrVoterId = {ACCOUNT_1_ADDRESS: 0},
        keyVoterId = {ACCOUNT_1_PUBLIC_KEY: 0},
        voters = {
            0: sp.record(
                addr            = ACCOUNT_1_ADDRESS,
                publicKey       = ACCOUNT_1_PUBLIC_KEY,
                lastProposalId  = 0
            )
        },
        lastVoterId             = 0,
        metadataURL             = "https://cloudflare-ipfs.com/ipfs/QmWGLWx4pGZBrVF9Bz12pAT3A5Dunw3o9NMAKVvWK51Cfy",
        TTargetAdminAction      = TYPES.TAggregatorAdminAction
    )
    sc += multisignAdmin

    sc.h2("Signers")
    sc.show([
        ACCOUNT_1_ADDRESS,
        ACCOUNT_2_ADDRESS
    ])

    class signer1:
        address = ACCOUNT_1_ADDRESS
    class signer2:
        address = ACCOUNT_2_ADDRESS

    sc.h2("ACCOUNT_1 adds ACCOUNT_2, change quorum and set aggregator as target")
    changeVoters = MSA.SelfHelper.changeVoters(added = [(ACCOUNT_2_ADDRESS, ACCOUNT_2_PUBLIC_KEY)])
    changeQuorum = MSA.SelfHelper.changeQuorum(2)
    targetAddress = sp.contract(
                sp.TList(TYPES.TAggregatorAdminAction),
                aggregator.address,
                entry_point = "administrate"
    ).open_some()
    changeTarget = MSA.SelfHelper.changeTarget(sp.to_address(targetAddress))
    multisignAdmin.newProposal([changeVoters, changeQuorum, changeTarget]).run(sender = ACCOUNT_1_ADDRESS, now = now)

    sc.h2("Aggregator admin sets multisign as administrator")
    changeAdmin = MSAH.changeAdmin(multisignAdmin.address)
    aggregator.administrate([changeAdmin]).run(sender = FALSE_ADMIN_ADDRESS)

    sc.h2("Adding back Oracle2 via multisign")
    sc.h3("New Proposal by ACCOUNT_1")
    now = now.add_minutes(1)
    oracle2 = MSAH.oracle(ORACLE_2_ADDRESS, ADMIN_ADDRESS, roundId+1)
    changeOracles = MSAH.changeOracles(added = [oracle2])
    multisignAdmin.newProposal([MSAH.variant([changeOracles])]).run(sender = ACCOUNT_1_ADDRESS, now = now)
    now = now.add_minutes(1)
    sc.h3("ACCOUNT_2 votes the proposal")
    sc.verify(~aggregator.data.oracles.contains(ORACLE_2_ADDRESS))
    multisignAdmin.vote([MSA.vote(multisignAdmin, signer1, yay = True)]).run(sender = ACCOUNT_2_ADDRESS)
    sc.verify(aggregator.data.oracles.contains(ORACLE_2_ADDRESS))

    sc.h2("An administration proposal that fails on Aggregator")
    sc.h3("New Proposal by ACCOUNT_1")
    updateFutureRounds = MSAH.updateFutureRounds(10, 10, 10, 10, 10)
    multisignAdmin.newProposal([MSAH.variant([updateFutureRounds])]).run(sender = ACCOUNT_1_ADDRESS, now = now)
    now = now.add_minutes(1)
    sc.h3("ACCOUNT_2 votes the proposal")
    multisignAdmin.vote([MSA.vote(multisignAdmin, signer1, yay = True)]).run(sender = ACCOUNT_2_ADDRESS, valid = False)

    ######################
    # Compilation Target #
    ######################

    sp.add_compilation_target(
        "link_token_compiled",
        FA2.FA2(
            config = FA2.FA2_config(
                single_asset        = True,
                allow_self_transfer = True
            ),
            metadata = FA2.FA2.make_metadata(
                name = "Wrapped LINK",
                decimals = 18,
                symbol = "wLINK"
            ),
            admin = ADMIN_ADDRESS,
        )
    )

    sp.add_compilation_target(
        "aggregator_compiled",
        PriceAggregator(
            useBigmapOracles    = CONSTANTS.USE_BIGMAP_ORACLES,
            initialRoundDetails = sp.record(
                submissions     = {},
                minSubmissions  = 0,
                maxSubmissions  = 0,
                timeout         = 0,
                activeOracles   = sp.set()
            ),
            tokenContract       = linkToken,
            tokenAddress        = sp.address("KT1_LINK_TOKEN_ADDRESS"),
            active              = False,
            decimals            = CONSTANTS.DECIMALS,
            admin               = sp.address("KT1_ADMIN_ADDRESS"),
            oracles             = {},
            timeout             = CONSTANTS.TIMEOUT,
            oraclePayment       = CONSTANTS.ORACLE_PAYMENT,
            minSubmissions      = 3,
            maxSubmissions      = 6,
            restartDelay        = 2,
            metadataURL         = "https://cloudflare-ipfs.com/ipfs/QmP3YHQG5BgKMmWkCnY2jLSowac3WTj7cUX7Td4cGsG3by"
        )
    )

    sp.add_compilation_target(
        "aggregator_admin_compiled",
        MSA.MultisignAdmin(
            quorum                  = 1,
            timeout                 = 5,
            addrVoterId = {
                sp.address("KT1_SIGNER1_ADDRESS"): 0
            },
            keyVoterId = {
                sp.key("KT1_SIGNER1_KEY"): 0
            },
            voters = {
                0: sp.record(
                    addr            = sp.address("KT1_SIGNER1_ADDRESS"),
                    publicKey       = sp.key("KT1_SIGNER1_KEY"),
                    lastProposalId  = 0
                )
            },
            lastVoterId             = 0,
            metadataURL             = "https://cloudflare-ipfs.com/ipfs/QmWGLWx4pGZBrVF9Bz12pAT3A5Dunw3o9NMAKVvWK51Cfy",
            TTargetAdminAction      = TYPES.TAggregatorAdminAction
        )
    )
