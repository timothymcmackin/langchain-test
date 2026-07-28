import smartpy as sp

"""
    An Oracle is the on-chain incarnation of an Oracle provider.
    It maintains a queue of requests of type `TRequest` containing
    a sender, a target entry point and parameters.

    Client and Oracle exchange via an Escrow.
    Escrow locks payment between the request moment and the fulfill or cancel moment.
    It ensures that the cancel cannot be done before the timeout.
    FA2 `proxy` entry point transfers the locked tokens to Escrow and transmits the request.
    It ensures that payment and request are synchronized.

    Client and Oracle need to have reasonable trust in the Escrow.
    Client and Escrow need a moderate trust toward the Oracle. In particular:
      Escrow provides a hard cancel that permits the Client to cancel without Oracle being called.
      Escrow provides a hard fulfill for the Oracle to request its payment without Client being called.
    Oracle don't need to trust the Client (requester and receiver).
    Client requester don't need to trust the Client target (receiver).

    A Client version that don't have confidence in escrow for verifying tickets (see below)
    can be setup with `verify_answer_validity = true`.

    Client is responsible for never generating two tickets with identical `client_request_id`
    otherwise he might receive callbacks he doesn't expect.

    Requests and Results are transmitted via tickets.
    Escrow guarantees the Result ticket to be the answer to the Request ticket ---
    taking into account what was explained previously about `client_request_id`.
    Escrow guarantees the validity of the ticket's tag.
    It doesn't guarantee the Result value to be valid.

    A Request contains:
    tag (sp.TString): `REQUEST_TAG`
    oracle (sp.TAddress): address of the Oracle
    target (sp.TAddress): address (and entry point) of the target
    job_id (sp.TBytes): job_id as required by Oracle
    parameters (TParameters): Optional parameters
    cancel_timeout (sp.TTimestamp): Time after which the Client can cancel the request
    fulfill_timeout (sp.TTimestamp): Time after which the Oracle cannot fulfill anymore
    client_request_id (sp.TNat): Id of the request. Client shall never emits two requests with same id for its own safety.

    A Result contains:
    tag (sp.TString): `RESULT_TAG`
    client (sp.TAddress): address of the client requester
    client_request_id (sp.TNat): Id of the request
    result (TValue): result value computed by the Oracle

    Validity for `OracleRequest` and `OracleResult`
    <OracleRequest>.content.tag == REQUEST_TAG
    <OracleResult>.content.tag == RESULT_TAG
    <OracleResult>.ticketer == <OracleRequest>.content.oracle
    <OracleRequest>.ticketer == <OracleResult>.content.client
    <OracleRequest>.content.request.client_request_id == <OracleResult>.content.client_request_id

    Parameters of type `TParameters` can be a Int, String or Bytes
"""

REQUEST_TAG = "OracleRequest"
RESULT_TAG  = "OracleResult"

# 10 ^ 18
wLINK_decimals = 10 ** 18

# Value returned by Oracle
TValue = sp.TVariant(int = sp.TInt, string = sp.TString, bytes = sp.TBytes)

# Request parameters
TParameters = sp.TOption(TValue)

# Content of the request ticket
TRequest = sp.TTicket(sp.TRecord(tag               = sp.TString,
                                 oracle            = sp.TAddress,
                                 target            = sp.TAddress,
                                 job_id            = sp.TBytes,
                                 parameters        = TParameters,
                                 cancel_timeout    = sp.TTimestamp,
                                 fulfill_timeout   = sp.TTimestamp,
                                 client_request_id = sp.TNat))
# Result ticket
TResult = sp.TTicket(sp.TRecord(tag               = sp.TString,
                                client            = sp.TAddress,
                                client_request_id = sp.TNat,
                                result            = TValue))

# Request ticket + amount locked
TRequestAmount = sp.TRecord(request = TRequest, amount = sp.TNat)

# Request ticket + amount locked + proxy sender
TRequestAmountSender = sp.TRecord(request = TRequest, amount = sp.TNat, sender = sp.TAddress)

# Answer : request ticket + result ticket
TAnswer = sp.TRecord(request = TRequest, result = TResult)

class ERR():
    TicketInvalidRequestTag        = "TicketExpectedTag:" + REQUEST_TAG
    TicketInvalidResultTag         = "TicketExpectedTag:" + RESULT_TAG
    TicketOracleNotMatch           = "TicketOracleNotMatch"
    TicketClientNotMatch           = "TicketClientNotMatch"
    TicketClientRequestIdNotMatch  = "TicketClientRequestIdNotMatch"

    OracleSenderIsNotEscrow        = "OracleNotEscrow"
    OracleSenderIsNotEscrowOrAdmin = "OracleSenderIsNotEscrowOrAdmin"
    OracleInactive                 = "OracleInactive"
    OracleAmountBelowMin           = "OracleAmountBelowMin"
    OracleTimeoutBelowMin          = "OracleTimeoutBelowMinTimeout"
    OracleRequestKeyAlreadyKnown   = "OracleRequestKeyAlreadyKnown"
    OracleRequestUnknown           = "OracleRequestUnknown"
    OracleSenderIsNotAdmin         = "OracleNotAdmin"

    EscrowRequestIdAlreadyKnownForClient = "EscrowRequestIdAlreadyKnownForClient"
    EscrowRequestIdUnknownForClient      = "EscrowRequestIdUnknownForClient"
    EscrowCannotFulfillAfterTimeout      = "EscrowCantFulfillAfterTimeout"
    EscrowCannotCancelBeforeTimeout      = "EscrowCantCancelBeforeTimeout"
    EscrowSenderAndTicketerNotMatch      = "EscrowSenderAndTicketerNotMatch"
    EscrowRequestUnknown                 = "EscrowRequestUnknown"
    EscrowOracleNotFound                 = "EscrowOracleNotFound"
    EscrowTargetNotFound                 = "EscrowTargetNotFound"
    EscrowSenderNotToken                 = "EscrowSenderNotToken"

    RequesterNotAdmin      = "RequesterNotAdmin"
    RequesterTargetUnknown = "RequesterTargetUnknown"

    ReceiverBadRequester = "ReceiverBadRequester"
    ReceiverNotAdmin     = "ReceiverNotAdmin"
    ReceiverNotEscrow    = "ReceiverNotEscrow"
    ReceiverBadRequestId = "ReceiverBadRequestId"

    TokenWrongEscrowInterface = "TokenWrongEscrowInterface"

def read_int(x):
    return x.open_variant("int")

def read_bytes(x):
    return x.open_variant("bytes")

def read_string(x):
    return x.open_variant("string")

def request_result_validity(request, result):
    sp.verify(request.content.tag == REQUEST_TAG,         message = ERR.TicketInvalidRequestTag)
    sp.verify(result.content.tag  == RESULT_TAG,          message = ERR.TicketInvalidResultTag)
    sp.verify(request.ticketer == result.content.client,  message = ERR.TicketClientNotMatch)
    sp.verify(result.ticketer  == request.content.oracle, message = ERR.TicketOracleNotMatch)
    sp.verify(request.content.client_request_id == result.content.client_request_id, message = ERR.TicketClientRequestIdNotMatch)

# Oracle is the on-chain incarnation of an Oracle provider.
# It maintains a queue of requests of type `TRequest` containing
# a sender, a target entry point and parameters.
class Oracle(sp.Contract):
    def __init__(self,
                 admin,
                 escrow_contract,
                 escrow_address      = None,
                 min_cancel_timeout  = 5,
                 min_fulfill_timeout = 5,
                 min_amount          = 0):
        self.escrow_contract = escrow_contract
        if escrow_address is None:
            escrow_address = escrow_contract.address
        self.init(
            setup = sp.record(
                admin               = admin,
                active              = True,
                min_cancel_timeout  = min_cancel_timeout,
                min_fulfill_timeout = min_fulfill_timeout,
                min_amount          = min_amount,
                escrow              = escrow_address
                ),
            next_id = 0,
            reverse_requests = sp.big_map(tkey = sp.TRecord(client = sp.TAddress, client_request_id = sp.TNat), tvalue = sp.TNat),
            requests = sp.big_map(tkey = sp.TNat, tvalue = TRequest),
        )

    def result(self, setup, next_id, reverse_requests, requests):
        sp.result(sp.record(setup = setup, next_id = next_id, reverse_requests = reverse_requests, requests = requests))

    @sp.entry_point
    def create_request(self, params):
        sp.set_type(params, TRequestAmount)
        amount, ticket = sp.match_record(params, "amount", "request")
        # We avoid DUP of self.data.requests which contains tickets
        with sp.modify_record(self.data, "data") as data:
            sp.verify(sp.sender == data.setup.escrow, message = ERR.OracleSenderIsNotEscrow)
            sp.verify(data.setup.active, message = ERR.OracleInactive)
            request = sp.read_ticket(ticket)
            # We don't verify request.tag == REQUEST_TAG because we trust Escrow
            sp.verify(data.setup.min_amount <= amount, message = ERR.OracleAmountBelowMin)
            sp.verify(sp.now.add_minutes(data.setup.min_cancel_timeout) <= request.content.cancel_timeout, message = ERR.OracleTimeoutBelowMin)
            sp.verify(sp.now.add_minutes(data.setup.min_fulfill_timeout) <= request.content.fulfill_timeout, message = ERR.OracleTimeoutBelowMin)

            reverse_request_key = sp.compute(sp.record(client = request.ticketer, client_request_id = request.content.client_request_id))
            sp.verify(~data.reverse_requests.contains(reverse_request_key), message = ERR.OracleRequestKeyAlreadyKnown)
            data.reverse_requests[reverse_request_key] = data.next_id
            data.requests[data.next_id] = request.copy
            data.next_id += 1

    @sp.entry_point
    def setup(self, params):
        with sp.modify_record(self.data) as data:
            # We do not check active here; otherwise, the contract could be inactivated forever
            sp.verify(sp.sender == data.setup.admin, message = ERR.OracleSenderIsNotAdmin)
            data.setup = params

    @sp.entry_point
    def fulfill_request(self, request_id, result, force):
        # If target (i.e. the receiver) fails on receive
        # the param `force` can be put to True otherwise if shall be False.
        with sp.modify_record(self.data) as data:
            # We do not want to check active here since sp.sender == admin.
            sp.verify(sp.sender == data.setup.admin, message = ERR.OracleSenderIsNotAdmin)
            ticket, requests = sp.get_and_update(data.requests, request_id)
            data.requests = requests
            request = sp.read_ticket(ticket.open_some(ERR.OracleRequestUnknown))

            escrow = None
            sp.if force:
                escrow = sp.contract(TAnswer, data.setup.escrow, entry_point = "force_fulfill_request").open_some()
            sp.else:
                escrow = sp.contract(TAnswer, data.setup.escrow, entry_point = "fulfill_request").open_some()
            result_ticket = sp.ticket(sp.record(tag = RESULT_TAG,
                                                client = request.ticketer,
                                                client_request_id = request.content.client_request_id,
                                                result = result), 1)
            arg = sp.record(request = request.copy, result = result_ticket)
            sp.transfer(arg, sp.mutez(0), escrow)
            reverse_request_key = sp.record(client = request.ticketer, client_request_id = request.content.client_request_id)
            data.reverse_requests = sp.update_map(data.reverse_requests, reverse_request_key, value = sp.none)

    @sp.entry_point
    def cancel_request(self, client, client_request_id):
        with sp.modify_record(self.data, "data") as data:
            # We do not want to check active here.
            # Otherwise the Client would be bound to use a force cancellation.
            sp.verify( (sp.sender == data.setup.escrow) | (sp.sender == data.setup.admin), message = ERR.OracleSenderIsNotEscrowOrAdmin)
            reverse_request_key = sp.record(client = client, client_request_id = client_request_id)
            request_id, reverse_requests = sp.get_and_update(data.reverse_requests, reverse_request_key)
            data.reverse_requests = reverse_requests
            data.requests = sp.update_map(data.requests, request_id.open_some(ERR.OracleRequestUnknown), value = sp.none)
# Escrow receive the request and payment and transmits the request to the oracle
# The requester can cancel the request and recover his payment after a timeout
# If the Oracle answers before a cancel:
#    the Escrow sends the reward to the Oracle and the answer to Target
class Escrow(sp.Contract):
    def __init__(self, token_contract,
                       token_id = 0,
                       token_address = None,
                       token_is_proxy = True):
        self.token_contract = token_contract
        if token_address is None:
            token_address = token_contract.address
        self.init(token    = token_address,
                  token_id = token_id,
                  locked   = sp.big_map(tkey = sp.TRecord(client = sp.TAddress, client_request_id = sp.TNat),
                                        tvalue = sp.TRecord(amount = sp.TNat, cancel_timeout = sp.TTimestamp)
                                       )
                  )
        self.token_is_proxy = token_is_proxy

    def transfer_tokens(self, from_, to_, amount):
        token = sp.contract(self.token_contract.batch_transfer.get_type(), self.data.token, entry_point = "transfer").open_some()
        arg = [sp.record(from_ = from_, txs = [sp.record(to_ = to_, token_id = self.data.token_id, amount = amount)])]
        sp.transfer(arg, sp.tez(0), token)

    @sp.entry_point
    def send_request(self, params):
        params_sender = None
        if self.token_is_proxy:
            sp.set_type(params, TRequestAmountSender)
            amount, ticket, params_sender = sp.match_record(params, "amount", "request", "sender")
        else:
            sp.set_type(params, TRequestAmount)
            amount, ticket = sp.match_record(params, "amount", "request")

        # read the request
        request = sp.read_ticket(ticket)
        # Verify if sender is ticketer
        # It's important otherwise the oracle could re-send the ticket after a cancel
        # or the receiver after a fulfill
        if self.token_is_proxy:
            sp.verify(sp.sender == self.data.token, message = ERR.EscrowSenderNotToken)
            # We TRUST the proxy for passing its sp.sender inside params.sender
            sp.verify(params_sender == request.ticketer, message = ERR.EscrowSenderAndTicketerNotMatch)
            # We don't lock tokens, proxy shall have done it
        else:
            sp.verify(sp.sender == request.ticketer, message = ERR.EscrowSenderAndTicketerNotMatch)
            # Lock tokens
            self.transfer_tokens(from_ = sp.sender, to_ = sp.self_address, amount = amount)

        sp.verify(request.content.tag == REQUEST_TAG, message = ERR.TicketInvalidRequestTag)
        # register the request
        request_key = sp.compute(sp.record(client = request.ticketer, client_request_id = request.content.client_request_id))
        sp.verify(~self.data.locked.contains(request_key), message = ERR.EscrowRequestIdAlreadyKnownForClient)
        self.data.locked[request_key] = sp.record(amount = amount, cancel_timeout = request.content.cancel_timeout)

        # create_request on oracle
        oracle = sp.contract(TRequestAmount, request.content.oracle, entry_point = "create_request")
        arg = sp.record(amount = amount, request = request.copy)
        sp.transfer(arg, sp.tez(0), oracle.open_some(ERR.EscrowOracleNotFound))

    @sp.entry_point
    def cancel_request(self, params):
        # Retrieve locked info
        request_key = sp.compute(sp.record(client = sp.sender, client_request_id = params.client_request_id))
        sp.verify(self.data.locked.contains(request_key), message = ERR.EscrowRequestIdUnknownForClient)
        request_info = self.data.locked[request_key]

        # Verify and refund client
        sp.verify(sp.now >= request_info.cancel_timeout , message = ERR.EscrowCannotCancelBeforeTimeout)
        self.transfer_tokens(from_ = sp.self_address, to_ = sp.sender, amount = request_info.amount)
        del self.data.locked[request_key]

        # Notify Oracle
        # If Oracle fails, i.e., if it is uncooperative,
        # we can use `force = True` and not notify it
        sp.if ~params.force:
            t = sp.TRecord(client = sp.TAddress, client_request_id = sp.TNat)
            oracle_contract = sp.contract(t, params.oracle, entry_point = "cancel_request")
            sp.transfer(request_key, sp.tez(0), oracle_contract.open_some(ERR.EscrowOracleNotFound))

    def sub_fulfill(self, params):
        sp.set_type(params, TAnswer)
        # Read tickets
        request_ticket, result_ticket = sp.match_record(params, "request", "result")
        request = sp.read_ticket(request_ticket)
        result = sp.read_ticket(result_ticket)

        # Retrieve locked info
        locked = self.data.locked
        request_key = sp.compute(sp.record(client = request.ticketer, client_request_id = request.content.client_request_id))
        amount = self.data.locked[request_key].amount

        # Verify validity
        sp.verify(locked.contains(request_key), message = ERR.EscrowRequestUnknown)
        sp.verify(request.content.fulfill_timeout >= sp.now, message = ERR.EscrowCannotFulfillAfterTimeout)
        request_result_validity(request, result)
        sp.verify(sp.sender == result.ticketer, message = ERR.EscrowSenderAndTicketerNotMatch)

        # Unlock tokens
        self.transfer_tokens(from_= sp.self_address, to_ = request.content.oracle, amount = amount)
        del locked[request_key]
        return (request, result)

    @sp.entry_point
    def fulfill_request(self, params):
        request, result = self.sub_fulfill(params)
        # Callback Target
        target = sp.contract(TAnswer, request.content.target).open_some(ERR.EscrowTargetNotFound)
        arg = sp.record(request = request.copy, result = result.copy)
        sp.transfer(arg, sp.tez(0), target)

    # If Target fails (i.e. if it is uncooperative),
    # Oracle can use this entry_point not transmit the answer to Target
    @sp.entry_point
    def force_fulfill_request(self, params):
        self.sub_fulfill(params)

# Optional entry point used when token differs from escrow
# Add or remove escrow from contrat's operators
def add_remove_escrow_operator(self, params):
    t = sp.TList(sp.TVariant(
            add_operator = self.token_contract.operator_param.get_type(),
            remove_operator = self.token_contract.operator_param.get_type())
    )
    token_contract = sp.contract(t, params.token, entry_point = "update_operators")
    operator_param = self.token_contract.operator_param.make(
                    owner = sp.self_address,
                    operator = self.data.escrow,
                    token_id = 0
    )
    sp.if params.add_operator:
        arg = [sp.variant("add_operator", operator_param)]
        sp.transfer(arg, sp.tez(0), token_contract.open_some())
    sp.else:
        arg = [sp.variant("remove_operator", operator_param)]
        sp.transfer(arg, sp.tez(0), token_contract.open_some())

# Optional entry point used on client requester if receiver differs from requester
def set_receiver(self, receiver):
    sp.verify(sp.sender == self.data.admin, message = ERR.RequesterNotAdmin)
    self.data.receiver = sp.some(receiver)

# A Requester client is a smart contract that sends and pays request to oracles via the escrow.
# It creates a well formed ticket and send it to the escrow.

class Client_requester(sp.Contract):
    def __init__(self, escrow,
                       oracle,
                       token_contract,
                       job_id,
                       admin,
                       token_is_escrow = False,
                       token_address = None,
                       token_is_proxy = True):
        self.token_contract = token_contract
        if token_address is None:
            token_address = token_contract.address
        self.init(admin             = admin,
                  token             = token_address,
                  escrow            = escrow,
                  oracle            = oracle,
                  job_id            = job_id,
                  next_request_id   = 1,
                  receiver          = sp.none,
                  )
        self.token_is_proxy = token_is_proxy
        self.set_receiver = sp.entry_point(set_receiver)
        if not token_is_escrow and not token_is_proxy:
            self.add_remove_escrow_operator = sp.entry_point(add_remove_escrow_operator)

    def get_target(self):
        t = TAnswer
        target = sp.contract(t, self.data.receiver.open_some(ERR.RequesterTargetUnknown), entry_point = "set_value")
        return sp.to_address(target.open_some(ERR.RequesterTargetUnknown))

    @sp.entry_point
    def request_value(self, params):
        sp.verify(sp.sender == self.data.admin, message = ERR.RequesterNotAdmin)
        parameters = sp.set_type_expr(params.parameters, TParameters)
        # Create ticket
        content = sp.record(tag               = REQUEST_TAG,
                            oracle            = self.data.oracle,
                            target            = self.get_target(),
                            job_id            = self.data.job_id,
                            parameters        = params.parameters,
                            cancel_timeout    = sp.now.add_minutes(params.cancel_timeout_minutes),
                            fulfill_timeout   = sp.now.add_minutes(params.fulfill_timeout_minutes),
                            client_request_id = self.data.next_request_id
        )

        ticket = sp.ticket(content, 1)
        # Send request
        if self.token_is_proxy:
            arg = sp.record(escrow = self.data.escrow, request = ticket, amount = params.amount)
            t = sp.TRecord(escrow = sp.TAddress, request = TRequest, amount = sp.TNat)
            token  = sp.contract(t, self.data.token, entry_point = "proxy").open_some()
            sp.transfer(arg, sp.tez(0), token)
        else:
            arg = sp.record(amount = params.amount, request = ticket)
            escrow  = sp.contract(TRequestAmount, self.data.escrow, entry_point = "send_request").open_some()
            sp.transfer(arg, sp.tez(0), escrow)

        self.data.next_request_id += 1

    @sp.entry_point
    def cancel_value(self, params):
        sp.verify(sp.sender == self.data.admin, message = ERR.RequesterNotAdmin)
        request_id = sp.as_nat(self.data.next_request_id - 1)

        t = sp.TRecord(client_request_id = sp.TNat, force = sp.TBool, oracle = sp.TAddress)
        escrow = sp.contract(t, self.data.escrow, entry_point = "cancel_request").open_some()
        arg = sp.record(client_request_id = request_id, force = params.force, oracle = self.data.oracle)
        sp.transfer(arg, sp.mutez(0), escrow)

    @sp.entry_point
    def setup(self, params):
        sp.verify(sp.sender == self.data.admin, message = ERR.RequesterNotAdmin)
        self.data.admin  = params.admin
        self.data.escrow = params.escrow
        self.data.oracle = params.oracle
        self.data.job_id = params.job_id
        self.data.token  = params.token

# Optional entry point added to receiver if receiver diffres from requester
def setup(self, params):
    sp.verify(sp.sender == self.data.admin, message = ERR.ReceiverNotAdmin)
    self.data.requester = params.requester
    self.data.escrow = params.escrow

# A Receiver client is a smart contract that expects to be called by oracles.
# The simplest form of a Client contains a receive entry point (custom
# names are possible) with an arbitrary parameter type

class Client_receiver(sp.Contract):
    def __init__(self, admin, requester, escrow, verify_answer_validity = False):
        self.init(admin = admin,
                  requester = requester,
                  escrow = escrow,
                  last_request_id = 0,
                  value = sp.none)
        self.verify_answer_validity = verify_answer_validity
        self.setup = sp.entry_point(setup)

    def verify_requester(self, ticketer):
        sp.verify(ticketer == self.data.requester, message = ERR.ReceiverBadRequester)

    def verify_set_last_request_id(self, request_id):
        sp.verify(request_id > self.data.last_request_id, message = ERR.ReceiverBadRequestId)
        self.data.last_request_id = request_id

    @sp.entry_point
    def set_value(self, params):
        sp.verify(sp.sender == self.data.escrow, message = ERR.ReceiverNotEscrow)
        sp.set_type(params, TAnswer)
        request_ticket, result_ticket = sp.match_record(params, "request", "result")

        request = sp.read_ticket(request_ticket)
        result = sp.read_ticket(result_ticket)
        self.verify_requester(request.ticketer)
        self.verify_set_last_request_id(request.content.client_request_id)
        self.data.value = sp.some(read_int(result.content.result))

        # If we don't trust escrow for verifying tickets validity
        if self.verify_answer_validity:
            request_result_validity(request, result)

# Client class is both requester and receiver
# As a consequence, overall architecture is simplified

class Client(Client_requester, Client_receiver):
    def __init__(self, escrow,
                       oracle,
                       token_contract,
                       job_id,
                       admin,
                       verify_answer_validity = False,
                       token_is_escrow = False,
                       token_address = None,
                       token_is_proxy = True):
        self.verify_answer_validity = verify_answer_validity
        self.token_contract = token_contract
        if token_address is None:
            token_address = token_contract.address
        self.init(admin           = admin,
                  token           = token_address,
                  escrow          = escrow,
                  oracle          = oracle,
                  job_id          = job_id,
                  value           = sp.none,
                  next_request_id = 1,
        )
        self.token_is_proxy = token_is_proxy
        if not (token_is_escrow or token_is_proxy):
            self.add_remove_escrow_operator = sp.entry_point(add_remove_escrow_operator)

    def get_target(self):
        return sp.self_entry_point_address("set_value")

    def verify_requester(self, ticketer):
        sp.verify(ticketer == sp.self_address, message = ERR.ReceiverBadRequester)

    def verify_set_last_request_id(self, request_id):
        sp.verify(request_id == sp.as_nat(self.data.next_request_id - 1), message = ERR.ReceiverBadRequester)

# Oracle Requests are paid with tokens handled in an FA2 contract.
# The FA2 contract template can be extended by a proxy entry point to
# ensure transfers to Oracle and payments are synchronized.

FA2 = sp.io.import_template("FA2.py")

def proxy(self, params):
    sp.set_type(params, sp.TRecord(escrow = sp.TAddress, request = TRequest, amount = sp.TNat))
    escrow, request_ticket, amount = sp.match_record(params, "escrow", "request", "amount")
    self.transfer.f(self, [sp.record(from_ = sp.sender, txs = [sp.record(to_ = escrow, token_id = 0, amount = amount)])])
    t = TRequestAmountSender
    escrow_contract = sp.contract(t, escrow, entry_point = "send_request").open_some(ERR.TokenWrongEscrowInterface)
    sp.transfer(sp.record(request = request_ticket, amount = amount, sender = sp.sender), sp.mutez(0), escrow_contract)

class Link_token(FA2.FA2):
    def __init__(self, admin, config, metadata, token_is_proxy = True):
        self.token_is_proxy = token_is_proxy
        if token_is_proxy:
            self.proxy = sp.entry_point(proxy)
        FA2.FA2_core.__init__(self, config, metadata, paused = False, administrator = admin)

# This contract is both the FA2 token and Escrow

class Link_token_escrow(Link_token, Escrow):
    def __init__(self, admin, config, metadata, token_is_proxy = True):
        self.token_is_proxy = token_is_proxy
        if token_is_proxy:
            self.proxy = sp.entry_point(proxy)
        locked   = sp.big_map(tkey = sp.TRecord(client = sp.TAddress, client_request_id = sp.TNat),
                                                tvalue = sp.TRecord(amount = sp.TNat, cancel_timeout = sp.TTimestamp)
                                           )
        FA2.FA2_core.__init__(self, config, metadata, paused = False, administrator = admin, locked = locked)

    def transfer_tokens(self, from_, to_, amount):
        token = sp.self_entry_point("transfer")
        arg = [sp.record(from_ = from_, txs = [sp.record(to_ = to_, token_id = 0, amount = amount)])]
        sp.transfer(arg, sp.tez(0), token)

class TokenFaucet(sp.Contract):
    def __init__(self,
                 admin,
                 token_contract,
                 token_address  = None,
                 max_amount     = 10 * wLINK_decimals):
        self.token_contract = token_contract

        if token_address is None:
            token_address = token_contract.address

        self.init(admin               = admin,
                  active              = True,
                  max_amount          = max_amount,
                  token               = token_address)

    @sp.entry_point
    def request_tokens(self, targets):
        sp.set_type(targets, sp.TSet(sp.TAddress))
        token = sp.contract(self.token_contract.batch_transfer.get_type(),
                            self.data.token,
                            entry_point = "transfer").open_some(message = "Incompatible token interface")
        targets = targets.elements().map(lambda target: sp.record(to_ = target, token_id = 0, amount = self.data.max_amount))
        sp.transfer([sp.record(from_ = sp.to_address(sp.self), txs = targets)], sp.tez(0), token)

    @sp.entry_point
    def configure(self, params):
        sp.verify(self.data.admin == sp.sender, message = "Privileged operation")
        self.data.set(params)

# This code was used to originate test contracts and is kept as an example
if False:
    @sp.add_test(name = "Origination")
    def test():
        scenario = sp.test_scenario()

        link_admin_address = sp.address('tz1LpthyZXo7EUCQnSVmWDFtSiFwHw2drbeu')
        oracle1_admin_address = sp.address('tz1ThuUF5faeAM6ob4QiCiwiGbZBCb81UhSa')
        client1_admin_address = sp.address('tz1LWjBoQWXAX9nD7R2k36oyfNwAdPd2Y6S3')

        scenario.h2("Link_token")
        link_token = Link_token(config = FA2.FA2_config(single_asset = True, allow_self_transfer = True),
                                metadata = sp.utils.metadata_of_url("ipfs://QmWDcp3BpBjvu8uJYxVqb7JLfr1pcyXsL97Cfkt3y1758o"),
                                admin = link_admin_address,
                                token_is_proxy = True)
        scenario += link_token
        link_token_address = sp.address('KT1WNGxztdLjjLrDYaHRo2VDQ5NmWyJBkwGw')

        scenario.h2("Token_faucet")
        token_faucet = TokenFaucet(link_admin_address, link_token, link_token_address, 10 * wLINK_decimals)
        scenario += token_faucet
        token_faucet_address = sp.address('KT1PATw5GykFrPRpJ3jnZmD55v17ZuPKCixh')

        scenario.h2("Escrow")
        escrow1 = Escrow(link_token, token_address = link_token_address, token_is_proxy = True)
        scenario += escrow1
        escrow_address = sp.address('KT1HdxvcsCeZFgucu9ixKYfP5DvWX7LEEDm2')

        scenario.h2("Oracle1")
        oracle1 = Oracle(oracle1_admin_address, escrow1, escrow_address = escrow_address)
        scenario += oracle1
        oracle1_address = sp.address('KT1Emrg5Lhzr4HCEnmbWF5PgWfpxCTJ3aArY')

        scenario.h2("Client1")
        client1 = Client(escrow_address, oracle1_address, link_token, sp.bytes("0x0001"), client1_admin_address, token_is_escrow = False, link_token_address = link_token_address)
        scenario += client1
        client1_address = sp.address('KT1SCwps6S9iycMoExkTUt6Y8PNhgqi8Y4HE')

        # ###
        # # Token is escrow
        scenario.h2("Link_token_escrow")
        link_token_escrow = Link_token_escrow(config = FA2.FA2_config(single_asset = True, allow_self_transfer = True),
                                              metadata = sp.utils.metadata_of_url("ipfs://QmWDcp3BpBjvu8uJYxVqb7JLfr1pcyXsL97Cfkt3y1758o"),
                                              admin = link_admin_address,
                                              token_is_proxy = True)
        scenario += link_token_escrow
        link_token_escrow_address = sp.address('KT1WvyA1VGnPhSZpHjXg8jnKyTy9HvEpQ8Uz')

        scenario.h2("token_escrow_faucet")
        token_escrow_faucet = TokenFaucet(link_admin_address, link_token_escrow, link_token_escrow_address, 10 * wLINK_decimals)
        scenario += token_escrow_faucet
        token_escrow_faucet_address = sp.address('KT1TsC6Bw36PX2aYY4PgechxDeqVCjqAeEzp')

        scenario.h2("Oracle2")
        oracle2_admin_address = oracle1_admin_address
        oracle2 = Oracle(oracle2_admin_address, token_escrow_faucet, escrow_address = link_token_escrow_address)
        scenario += oracle2
        oracle2_address = sp.address('KT1RaBDsX18ddaBfxinATrNmEpmT2TiBPee1')

        scenario.h2("Client2")
        client2_admin_address = client1_admin_address
        client2 = Client(link_token_escrow_address, oracle2_address, link_token_escrow, sp.bytes("0x0001"), client2_admin_address, token_is_escrow = True, link_token_address = link_token_address)
        scenario += client2
        client2_address = sp.address('KT1MsEWrMbBohqSJufBwsF5ZYKtkAD22xN2H')

def value_string(s):
    return sp.variant("string", s)

def value_bytes(s):
    return sp.variant("bytes", s)

def value_int(s):
    return sp.variant("int", s)

def compute_balance(scenario, token, address):
    balance = token.data.ledger.get(address, sp.record(balance = sp.nat(0)))
    return scenario.compute(balance.balance)

# The `Oracle_Config` class holds the meta-programming configuration.

class Oracle_Config():
    def __init__(self,
                 requester_is_receiver = True,
                 token_is_escrow       = False,
                 token_is_proxy        = True,
                ):
        if token_is_escrow:
            token_is_proxy = False

        self.requester_is_receiver = requester_is_receiver
        self.token_is_escrow = token_is_escrow
        self.token_is_proxy = token_is_proxy

        name = 'Oracle'
        if requester_is_receiver:
            name += "-requester_is_receiver"
        if token_is_escrow:
            name += "-token_is_escrow"
        if token_is_proxy:
            name += "-token_is_proxy"
        self.name = name

def add_test(config, is_default = True):
    @sp.add_test(name = config.name, is_default = is_default)
    def test():
        scenario = sp.test_scenario()
        scenario.h1("Chainlink Oracles: " + config.name)

        scenario.table_of_contents()

        scenario.h2("Accounts")
        admin = sp.test_account("Administrator")
        oracle1 = sp.test_account("Oracle1")
        escrow1 = sp.test_account("Escrow1")

        requester1_admin = sp.test_account("Requester1 admin")
        requester2_admin = sp.test_account("Requester2 admin")
        receiver1_admin = sp.test_account("Receiver1 admin")
        receiver2_admin = sp.test_account("Receiver2 admin")

        scenario.show([admin, oracle1, escrow1, requester1_admin, requester2_admin, receiver1_admin, receiver2_admin])

        scenario.h2("Link Token")
        link_token, escrow = (None, None)
        if config.token_is_escrow:
            link_token = Link_token_escrow(config = FA2.FA2_config(single_asset = True, allow_self_transfer = True),
                                           metadata = sp.utils.metadata_of_url(""),
                                           admin = admin.address,
                                           token_is_proxy = config.token_is_proxy)
            escrow = link_token
        else:
            link_token = Link_token(config = FA2.FA2_config(single_asset = True, allow_self_transfer = config.token_is_proxy),
                                    metadata = sp.utils.metadata_of_url(""),
                                    admin = admin.address,
                                    token_is_proxy = config.token_is_proxy)
        scenario += link_token
        link_metadata = Link_token.make_metadata(
            name = "wrapped LINK",
            decimals = 18,
            symbol = "wLINK" )
        link_token.mint(address = admin.address,
                                    amount = 500,
                                    symbol = 'tzLINK',
                                    token_id = 0,
                                    metadata = link_metadata).run(sender = admin)

        scenario.h2("Token Faucet")
        faucet = TokenFaucet(admin.address, link_token, link_token.address, 10)
        scenario += faucet

        if not config.token_is_escrow:
            scenario.h2("Escrow")
            escrow = Escrow(link_token, token_is_proxy = config.token_is_proxy)
            scenario += escrow

        scenario.h2("Oracle")
        oracle = Oracle(oracle1.address, escrow)
        scenario += oracle

        requester1, requester2, receiver1, receiver2 = (None, None, None, None)
        if config.requester_is_receiver:
            scenario.h2("requester1: Requester and Receiver")
            requester1 = Client(escrow.address, oracle.address, link_token, sp.bytes("0x0001"), requester1_admin.address, token_is_escrow = config.token_is_escrow, token_is_proxy = config.token_is_proxy)
            scenario += requester1
            receiver1 = requester1

            scenario.h2("requester2: Requester and Receiver")
            requester2 = Client(escrow.address, oracle.address, link_token, sp.bytes("0x0001"), requester2_admin.address, token_is_escrow = config.token_is_escrow, token_is_proxy = config.token_is_proxy)
            scenario += requester2
            receiver2 = requester2
        else:
            scenario.h2("Client Requester1")
            requester1 = Client_requester(escrow.address, oracle.address, link_token, sp.bytes("0x0001"), requester1_admin.address, token_is_escrow = config.token_is_escrow, token_is_proxy = config.token_is_proxy)
            scenario += requester1

            scenario.h2("Client Requester2")
            requester2 = Client_requester(escrow.address, oracle.address, link_token, sp.bytes("0x0001"), requester2_admin.address, token_is_escrow = config.token_is_escrow, token_is_proxy = config.token_is_proxy)
            scenario += requester2

            scenario.h2("Client Receiver1")
            receiver1 = Client_receiver(receiver1_admin.address, requester1.address, escrow.address)
            scenario += receiver1

            scenario.h3("Client Receiver 1 is linked to Requester1")
            requester1.set_receiver(receiver1.address).run(sender = requester1_admin)

            scenario.h2("Client Receiver2")
            receiver2 = Client_receiver(receiver2_admin.address, requester2.address, escrow.address)
            scenario += receiver2

            scenario.h3("Client Receiver 2 is linked to Requester1")
            requester2.set_receiver(receiver2.address).run(sender = requester2_admin)

        if not config.token_is_escrow and not config.token_is_proxy:
            scenario.h2("Configure escrow as requesters operator")
            arg = sp.record(add_operator = True, token = link_token.address)
            requester1.add_remove_escrow_operator(arg).run(sender = requester1_admin)
            requester2.add_remove_escrow_operator(arg).run(sender = requester2_admin)

        scenario.h2("Tokens")
        link_token.transfer([sp.record(from_ = admin.address, txs = [sp.record(to_ = faucet.address, token_id = 0, amount = 100)])]).run(sender = admin)
        link_token.transfer([sp.record(from_ = admin.address, txs = [sp.record(to_ = oracle1.address, token_id = 0, amount = 1)])]).run(sender = admin)
        faucet.request_tokens(sp.set([requester1.address, requester2.address]))

        request_id = 0
        amount = sp.nat(2)
        request_value_params = sp.record(amount = amount, parameters = sp.none, cancel_timeout_minutes = 5, fulfill_timeout_minutes = 5)
        ##########
        # Test 1 #
        ##########
        scenario.h2("requester1 sends a request that gets fulfilled")
        requester1_balance = compute_balance(scenario, link_token, requester1.address)
        escrow_balance     = compute_balance(scenario, link_token, escrow.address)
        scenario.h3("A request")
        requester1.request_value(request_value_params).run(sender = requester1_admin)
        request_id += 1
        # Founds should be locked
        requester1_new_balance = compute_balance(scenario, link_token, requester1.address)
        escrow_new_balance     = compute_balance(scenario, link_token, escrow.address)
        scenario.verify(sp.as_nat(requester1_balance - amount) == requester1_new_balance)
        scenario.verify(escrow_balance + amount == escrow_new_balance)

        scenario.h3("Ledger")
        scenario.show(link_token.data.ledger)

        oracle_balance = compute_balance(scenario, link_token, oracle.address)
        escrow_balance = compute_balance(scenario, link_token, escrow.address)
        # Request must be registered in oracle
        request_key = sp.record(client = requester1.address, client_request_id = request_id)
        scenario.verify(oracle.data.reverse_requests.contains(request_key))

        scenario.h3("Oracle consumes the request")
        oracle.fulfill_request(request_id = request_id - 1, result = value_int(2_500_000), force = False).run(sender = oracle1)

        # Founds must be unlocked
        oracle_new_balance = compute_balance(scenario, link_token, oracle.address)
        escrow_new_balance = compute_balance(scenario, link_token, escrow.address)
        scenario.verify(oracle_balance + amount == oracle_new_balance)
        scenario.verify(sp.as_nat(escrow_balance - amount) == escrow_new_balance)
        # Request must be removed from oracle
        scenario.verify(~oracle.data.reverse_requests.contains(request_key))
        # Receiver must have registered the result
        scenario.verify_equal(receiver1.data.value.open_some(), 2_500_000)

        ##########
        # Test 2 #
        ##########
        scenario.h2("requester1 sends a request that gets cancelled")
        scenario.h3("A request")
        requester1.request_value(request_value_params).run(sender = requester1_admin, now = sp.timestamp(0))
        request_id += 1

        scenario.h3("Ledger")
        scenario.show(link_token.data.ledger)

        requester1_balance = compute_balance(scenario, link_token, requester1.address)
        escrow_balance     = compute_balance(scenario, link_token, escrow.address)
        # Request must be registered in oracle
        request_key = sp.record(client = requester1.address, client_request_id = request_id)
        scenario.verify(oracle.data.reverse_requests.contains(request_key))

        scenario.h3("requester1 cancels the request")
        requester1.cancel_value(force = False).run(sender = requester1_admin, now = sp.timestamp(400))

        # Founds must be returned back
        requester1_new_balance = compute_balance(scenario, link_token, requester1.address)
        escrow_new_balance     = compute_balance(scenario, link_token, escrow.address)
        scenario.verify(requester1_balance + amount == requester1_new_balance)
        scenario.verify(sp.as_nat(escrow_balance - amount) == escrow_new_balance)
        # Request must be removed from oracle
        scenario.verify(~oracle.data.reverse_requests.contains(request_key))

        ##########
        # Test 3 #
        ##########
        scenario.h2("requester1 sends a request that gets hard cancelled")
        scenario.h3("A request")
        requester1.request_value(request_value_params).run(sender = requester1_admin, now = sp.timestamp(0))
        request_id += 1

        scenario.h3("Ledger")
        scenario.show(link_token.data.ledger)

        # Request must be registered in oracle
        request_key = sp.record(client = requester1.address, client_request_id = request_id)
        scenario.verify(oracle.data.reverse_requests.contains(request_key))

        scenario.h3("requester1 hard cancels the request")
        requester1.cancel_value(force = True).run(sender = requester1_admin, now = sp.timestamp(400))
        # Request must be still registered in oracle
        request_key = sp.record(client = requester1.address, client_request_id = request_id)
        scenario.verify(oracle.data.reverse_requests.contains(request_key))

        ##########
        # Test 4 #
        ##########
        scenario.h2("requester2 sends a request that gets fulfilled")
        scenario.h3("A request")
        requester2.request_value(request_value_params).run(sender = requester2_admin)
        request_id += 1

        scenario.h3("Ledger")
        scenario.show(link_token.data.ledger)

        scenario.h3("Oracle consumes the request")
        oracle.fulfill_request(request_id = request_id - 1, result = value_int(2_500_000), force = False).run(sender = oracle1)
        scenario.verify_equal(receiver2.data.value.open_some(), 2_500_000)

        if config.requester_is_receiver is False and config.token_is_escrow is False:
            ##########
            # Test 5 #
            ##########
            scenario.h2("Invalid request or result ticket")
            scenario.h3("Tokens")
            faucet.request_tokens(sp.set([requester1.address, escrow.address]))
            if config.token_is_proxy:
                faucet.request_tokens(sp.set([escrow.address]))

            def generate_request(ticketer,
                                 tag    = REQUEST_TAG,
                                 oracle = oracle.address,
                                 target = sp.to_address(sp.contract(TAnswer, receiver1.address, entry_point = "set_value").open_some()),
                                 job_id = sp.bytes("0x0001"),
                                 parameters        = sp.none,
                                 cancel_timeout    = sp.timestamp(400),
                                 fulfill_timeout   = sp.timestamp(400),
                                 client_request_id = sp.nat(523)):

                content = sp.record(tag = tag, oracle = oracle, target = target, job_id = job_id, parameters = parameters, cancel_timeout = cancel_timeout, fulfill_timeout = fulfill_timeout, client_request_id = client_request_id)
                return sp.test_ticket(ticketer.address, content, 1)

            def generate_result(ticketer,
                                tag               = RESULT_TAG,
                                client            = requester1.address,
                                client_request_id = sp.nat(523),
                                result            = value_int(5_000_000)):
                content = sp.record(tag = tag, client = client, client_request_id = client_request_id, result = result)
                return sp.test_ticket(ticketer.address, content, 1)

            def valid_request():
                return generate_request(requester1)

            def escrow_and_amount(request):
                if config.token_is_proxy:
                    return sp.record(escrow = escrow.address, amount = sp.nat(5), request = request)

            def and_amount(request):
                if config.token_is_proxy:
                    return sp.record(amount = sp.nat(5), request = request, sender = requester1.address)
                else:
                    return sp.record(amount = sp.nat(5), request = request)

            def valid_result():
                return generate_result(oracle)

            scenario.h3("Escrow.fulfill_request")
            scenario.h4("Everything is valid")
            request_sender = link_token.address if config.token_is_proxy else requester1.address
            escrow.send_request(and_amount(valid_request())).run(sender = request_sender, now = sp.timestamp(0))

            escrow.fulfill_request(request = valid_request(), result = valid_result()).run(sender = oracle.address)
            oracle.cancel_request(client = requester1.address, client_request_id = sp.nat(523)).run(sender = oracle1)

            scenario.h4("Wrong request tag")
            escrow.send_request(and_amount(valid_request())).run(sender = request_sender)

            invalid_request = generate_request(requester1, tag = RESULT_TAG)
            escrow.fulfill_request(request = invalid_request, result = valid_result()).run(sender = oracle.address, valid = False)

            scenario.h4("Wrong result tag")
            invalid_result = generate_result(oracle, tag = REQUEST_TAG)
            escrow.fulfill_request(request = valid_request(), result = invalid_result).run(sender = oracle.address, valid = False)

            scenario.h4("Wrong result ticketer")
            invalid_result = generate_result(requester2)
            escrow.fulfill_request(request = valid_request(), result = invalid_result).run(sender = oracle.address, valid = False)

            scenario.h4("Wrong result client")
            invalid_result = generate_result(requester1, client = requester2.address)
            escrow.fulfill_request(request = valid_request(), result = invalid_result).run(sender = oracle.address, valid = False)

            scenario.h4("Wrong result request_id")
            invalid_result = generate_result(requester1, client_request_id = sp.nat(777))
            escrow.fulfill_request(request = valid_request(), result = invalid_result).run(sender = oracle.address, valid = False)

            scenario.h3("Escrow.send_request")
            scenario.h4("Wrong request tag")
            invalid_request = generate_request(requester1, tag = RESULT_TAG)
            escrow.send_request(and_amount(invalid_request)).run(sender = request_sender, valid = False)

            if config.token_is_proxy:
                scenario.h4("Ticketer and sender not match")
                invalid_request = generate_request(ticketer = requester2)
                escrow.send_request(and_amount(invalid_request)).run(sender = link_token.address, valid = False)

                # scenario.h3("Token.proxy")
                # scenario.h4("Ticketer and sender not match")
                # invalid_request = generate_request(ticketer = requester2)
                # link_token.proxy(escrow_and_amount(invalid_request)).run(sender = requester1.address, valid = False)

if "templates" not in __name__:
    add_test(Oracle_Config())
