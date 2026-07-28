import smartpy as sp

# Worker contract that our Main contract is going to call entry points on.
# Stores a single string ('message'), with entry points to allow the string
# to be overwritten or appended to.
class Worker(sp.Contract):
    def __init__(self):
        self.init(message = "")

    @sp.entry_point
    def set_message(self, message):
        self.data.message = message

    @sp.entry_point
    def append_message(self, message, separator):
        # Only use the separator if the message is currently empty ("")
        sp.if sp.len(self.data.message) == 0:
            self.data.message = message
        sp.else:
            self.data.message = sp.concat([self.data.message, separator, message])

# The main contract.
# Calls through to the Worker contract passed by address on init.
class Main(sp.Contract):
    def __init__(self, worker_contract_address):
        self.init(worker_contract_address = worker_contract_address)

    @sp.entry_point
    def store_single_message(self, message):
        # the expected args type for the set_message entry point
        set_message_args_type = sp.TString
        # Prepare the full entry point signature.
        # Note that we have to call `.open_some()` in order to open the sp.TOption(...),
        # as the contract may not exist.
        set_message_entry_point = sp.contract(set_message_args_type, self.data.worker_contract_address, "set_message").open_some()

        # call the `set_message` entry point on the worker contract
        sp.transfer(message, sp.tez(0), set_message_entry_point)


    @sp.entry_point
    def append_multiple_messages(self, params):
        sp.set_type(params, sp.TRecord(messages = sp.TList(sp.TString), separator = sp.TString))

        # the expected args type for the append_message entry point
        append_message_args_type = sp.TRecord(message = sp.TString, separator = sp.TString)
        # Prepare the full entry point signature.
        # Note that, as above, we have to call `.open_some()` in order to open the sp.TOption(...),
        # as the contract may not exist.
        append_message_entry_point = sp.contract(append_message_args_type, self.data.worker_contract_address, "append_message").open_some()

        # call the `append_message` entry point on the worker contract once for
        # each string in params.messages
        sp.for message in params.messages:
            append_message_args = sp.record(message = message, separator = params.separator)
            sp.transfer(append_message_args, sp.tez(0), append_message_entry_point)



@sp.add_test(name = "InterContractCallsExample")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Inter-Contract Calls - example")
    scenario.table_of_contents()

    # originate the Worker contract and directly invoke it
    scenario.h2("Worker")
    worker_contract = Worker()
    scenario += worker_contract
    scenario.h3("Call the Worker contract entry points directly")
    scenario.h4("set_message")
    worker_contract.set_message("Directly set a message")
    scenario.verify(worker_contract.data.message == "Directly set a message")
    scenario.h4("append_message")
    worker_contract.append_message(message = "and append another", separator = ", ")
    scenario.verify(worker_contract.data.message == "Directly set a message, and append another")

    # originate the Main contract
    scenario.h2("Main")
    main_contract = Main(worker_contract.address)
    scenario += main_contract
    # the main contract calls through to the Worker contract methods
    scenario.h3("Call the Main contract entry points, which in turn call through to the Worker contract entry points")
    scenario.h4("store_single_message")
    main_contract.store_single_message("Indirectly set a message")
    scenario.verify(worker_contract.data.message == "Indirectly set a message")
    scenario.h4("append_multiple_messages")
    main_contract.append_multiple_messages(messages = ["and", "append", "some", "more"], separator = ", ")
    scenario.verify(worker_contract.data.message == "Indirectly set a message, and, append, some, more")

    scenario.table_of_contents()
