import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init_type(sp.TRecord(claimed = sp.TBool, deck = sp.TMap(sp.TIntOrNat, sp.TInt), nextPlayer = sp.TInt, size = sp.TIntOrNat, winner = sp.TInt).layout((("claimed", "deck"), ("nextPlayer", ("size", "winner")))))
    self.init(claimed = False,
              deck = {0 : 1, 1 : 2, 2 : 3, 3 : 4, 4 : 5},
              nextPlayer = 1,
              size = 5,
              winner = 0)

  @sp.entry_point
  def claim(self, params):
    sp.verify(sp.sum(self.data.deck.values()) == 0)
    sp.verify(~ self.data.claimed)
    self.data.claimed = True
    self.data.winner = self.data.nextPlayer
    sp.verify(params.winner == self.data.winner)

  @sp.entry_point
  def remove(self, params):
    sp.verify(params.cell >= 0)
    sp.verify(params.cell < self.data.size)
    sp.verify(params.k >= 1)
    sp.verify(params.k <= 2)
    sp.verify(params.k <= self.data.deck[params.cell])
    self.data.deck[params.cell] -= params.k
    self.data.nextPlayer = 3 - self.data.nextPlayer

sp.add_compilation_target("test", Contract())