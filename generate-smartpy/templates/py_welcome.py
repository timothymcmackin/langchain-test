import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init_type(sp.TRecord(myParameter1 = sp.TIntOrNat, myParameter2 = sp.TIntOrNat).layout(("myParameter1", "myParameter2")))
    self.init(myParameter1 = 42,
              myParameter2 = 42)

  @sp.entry_point
  def myEntryPoint(self, params):
    sp.verify(self.data.myParameter1 <= 123)
    self.data.myParameter1 += params

sp.add_compilation_target("test", Contract())