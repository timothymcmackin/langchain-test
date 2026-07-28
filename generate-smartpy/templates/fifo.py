# Fifo - Example for illustrative purposes only.

import smartpy as sp

# The Fifo class defines a simple contract that handles push and pop instructions
# on a first-in first-out basis.
# The type of the data pushed in the data structure is not specified
# or constrained so the contract is considered 'partial', i.e., not
# fully typed.
# It can be set by interacting with the data or by calling sp.set_type(element, int).

# In this example, we define a few classes
# - SimpleFifo: a direct implementation of fifos as a smart contract
# - FifoDataType: an implementation of the data type that can be reused
# - Fifo: a smart contract using the FifoDataType
# - Fifos: another smart more complex smart contract using the FifoDataType

class SimpleFifo(sp.Contract):
    def __init__(self):
        self.init(first =  0,
                  last  = -1,
                  saved = {})

    @sp.entry_point
    def pop(self):
        sp.verify(self.data.first < self.data.last)
        del self.data.saved[self.data.first]
        self.data.first += 1

    @sp.entry_point
    def push(self, element):
        self.data.last += 1
        self.data.saved[self.data.last] = element

    def head(self):
        return self.data.saved[self.data.first]

# We define a regular python class that handles fifos but don't store its data.
class FifoDataType:
    def __call__(self):
        return sp.record(first = 0, last = -1, saved = {})

    # This will typically be used in entry points
    def pop(self, data):
        sp.verify(data.first < data.last)
        del data.saved[data.first]
        data.first += 1

    # This will typically be used in entry points
    def push(self, data, element):
        data.last += 1
        data.saved[data.last] = element

    # This may be used in some entry points but also in the contract to access its state
    def head(self, data):
        return data.saved[data.first]

# We need only one instance of FifoDataType
fifoDT = FifoDataType()

# A contract that uses the FifoDataType similar to SimpleFifo
class Fifo(sp.Contract):
    def __init__(self, element_type = None):
        self.element_type = element_type
        self.init(fif = fifoDT())

    @sp.entry_point
    def pop(self):
        fifoDT.pop(self.data.fif)

    @sp.entry_point
    def push(self, element):
        sp.set_type(element, self.element_type)
        fifoDT.push(self.data.fif, element)

    def head(self):
        return fifoDT.head(self.data.fif)

# A smart contract using two Fifos
class Fifos(sp.Contract):
    def __init__(self):
        self.init(fif = fifoDT(), queue = fifoDT())

    @sp.entry_point
    def pop(self):
        fifoDT.pop(self.data.fif)

    @sp.entry_point
    def popQ(self):
        fifoDT.pop(self.data.queue)

    @sp.entry_point
    def push(self, element):
        fifoDT.push(self.data.fif, element)
        fifoDT.push(self.data.queue, element)

    def headFif(self):
        return fifoDT.head(self.data.fif)

    def headQueue(self):
        return fifoDT.head(self.data.queue)

if "templates" not in __name__:
    @sp.add_test(name = "Fifo")
    def test():
        scenario = sp.test_scenario()
        scenario.h1("Simple Fifo Contract")
        c1 = SimpleFifo()
        scenario += c1
        c1.push(4)
        c1.push(5)
        c1.push(6)
        c1.push(7)
        c1.pop()

        scenario.h1("Using the Fifo Data Type")
        c2 = Fifo()
        scenario += c2
        c2.push(4)
        c2.push(5)
        c2.push(6)
        c2.push(7)
        c2.pop()

        scenario.h1("A more complex example using the Fifo Data Type")
        c3 = Fifos()
        scenario += c3
        c3.push(4)
        c3.push(5)
        c3.push(6)
        c3.push(7)
        c3.pop()
        c3.popQ()
        c3.popQ()

        scenario.verify(c1.head() == 5)
        scenario.verify(c2.head() == 5)
        scenario.verify(c3.headFif() == 5)
        scenario.verify(c3.headQueue() == 6)

    sp.add_compilation_target("fifo", Fifo(sp.TInt))
