import smartpy as sp

class Contract(sp.Contract):
  def __init__(self):
    self.init_type(sp.TRecord(value = sp.TNat).layout("value"))
    self.init(value = 0)

  @sp.entry_point
  def add(self, params):
    self.data.value = params.x + params.y

  @sp.entry_point
  def factorial(self, params):
    self.data.value = 1
    sp.for y in sp.range(1, params + 1):
      self.data.value *= y

  @sp.entry_point
  def log2(self, params):
    self.data.value = 0
    y = sp.local("y", params)
    sp.while y.value > 1:
      self.data.value += 1
      y.value //= 2

  @sp.entry_point
  def multiply(self, params):
    self.data.value = params.x * params.y

  @sp.entry_point
  def square(self, params):
    self.data.value = params * params

  @sp.entry_point
  def squareRoot(self, params):
    sp.verify(params >= 0)
    y = sp.local("y", params)
    sp.while (y.value * y.value) > params:
      y.value = ((params // y.value) + y.value) // 2
    sp.verify(((y.value * y.value) <= params) & (params < ((y.value + 1) * (y.value + 1))))
    self.data.value = y.value

sp.add_compilation_target("test", Contract())