# https://github.com/smartcontractkit/LockDeposit/blob/master/contracts/MultiNodeLockDeposit.sol

"""
  uint8 public minimumRequiredQuorum;

  // paymentAmount is how much each oracle is paid per request
  uint256 public paymentAmount;

  // dailyCap is the maximum amount that can be either unlocked or deposited within a 24 hour period
  uint256 public dailyCap;
  // unlockedThisPeriod is the running tally of how much LINK has been unlocked within
  // this period
  uint256 public unlockedThisPeriod;
  // Depositedthisperiod is the running tally of how much LINK has been deposited within
  // this period
  uint256 public depositedThisPeriod;

  // startPeriod marks the time that the current period started
  uint256 public startPeriod;

  struct NodeResponses {
    bool unlocked;
    uint256 count;
    mapping(address => bool) responded;
  }

  mapping(bytes32 => NodeResponses) private nodeResponses;

  // Writer addresses are allowed to confirm a transaction on the foreign source
  // chain in order to release LINK on this, the destination chain.
  // There should be the same number of these as there are oracles on the foreign source chain.
  // Note that these are node external adapter public keys, NOT oracle addresses!
  mapping(address => bool) public registeredWriters;

  // Only whitelisted addresses are allowed to send or receive LINK to this contract
  mapping(address => bool) public whitelisted;

  struct Node {
    bytes32 jobId;
    address writer;
    uint256 oracleIdx;
  }
"""

import smartpy as sp

class MyContract(sp.Contract):
    def __init__(self, **kargs):
        self.init(minimumRequiredQuorum = 0,
                  dailyCap = 0,
                  unlockedThisPeriod = 0,
                  depositedThisPeriod = 0,
                  startPeriod = 0, ### timestamp ?

                  nodes = sp.big_map()
                  )

    @sp.entry_point
    def addNode(self, oracle, jobId, writer):
        ## verify owner
        sp.verify(~self.data.nodes.contains(oracle))

    @sp.entry_point
    def registerForeignChainDeposit(self,
                                    _foreignChainTxHash,
                                    _blockHash,
                                    _recipient,
                                    _amount
                                    ):
        ## verify owner
        pass

    #@sp.entry_point
    def unlockLink(self, _to, _amount):
        pass


@sp.add_test(name = "Minimal")
def test():
    return
    scenario = sp.test_scenario()
    scenario.h1("Minimal")
    c1 = MyContract(x=12)
    scenario += c1
