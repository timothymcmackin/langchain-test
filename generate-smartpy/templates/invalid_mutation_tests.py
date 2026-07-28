# List of scenario that should not pass

import smartpy as sp


# class InvertVerifyCondition(sp.Contract):
#     def __init__(self):
#         self.init(0)

#     @sp.entry_point
#     def fail_if_negative(self, params):
#         sp.verify(params >= 0)
#         self.data = params


# @sp.add_test(name="InvertVerifyCondition")
# def test():
#     c1 = InvertVerifyCondition()
#     sc = sp.test_scenario()
#     sc += c1
#     c1.fail_if_negative(5)
#     sc.verify(c1.data == 5)
#     # Expected:
#     # c1.fail_if_negative(-5).run(valid=False)


# @sp.add_test(name="Mutation1")
# def test():
#     s = sp.test_scenario()
#     with s.mutation_test() as mt:
#         mt.add_scenario("InvertVerifyCondition")


################################################################################


# class ErrorMessage(sp.Contract):
#     def __init__(self):
#         self.init(0)

#     @sp.entry_point
#     def fail(self):
#         sp.failwith("FAILURE")


# @sp.add_test(name="ErrorMessage")
# def test():
#     c1 = ErrorMessage()
#     sc = sp.test_scenario()
#     sc += c1
#     c1.fail().run(valid=False)
#     # Expected:
#     # c1.fail().run(valid=False, exception="FAILURE")


# @sp.add_test(name="Mutation2")
# def test():
#     s = sp.test_scenario()
#     with s.mutation_test() as mt:
#         mt.add_scenario("ErrorMessage")


################################################################################


# class OrVerifyCondition(sp.Contract):
#     def __init__(self):
#         self.init(0)

#     @sp.entry_point
#     def set_data(self, a, b):
#         with sp.if_(a | b):
#             self.data += 1


# @sp.add_test(name="OrVerifyCondition")
# def test():
#     c1 = OrVerifyCondition()
#     sc = sp.test_scenario()
#     sc += c1
#     sc.verify(c1.data == 0)
#     c1.set_data(a=True, b=False)
#     sc.verify(c1.data == 1)
#     c1.set_data(a=False, b=True)
#     sc.verify(c1.data == 2)
#     c1.set_data(a=False, b=False)
#     # Expected
#     # sc.verify(c1.data == 2)


# @sp.add_test(name="Mutation3")
# def test():
#     s = sp.test_scenario()
#     with s.mutation_test() as mt:
#         mt.add_scenario("OrVerifyCondition")


################################################################################


# class AndVerifyCondition(sp.Contract):
#     def __init__(self):
#         self.init(0)

#     @sp.entry_point
#     def set_data(self, a, b):
#         with sp.if_(a & b):
#             self.data += 1


# @sp.add_test(name="AndVerifyCondition")
# def test():
#     c1 = AndVerifyCondition()
#     sc = sp.test_scenario()
#     sc += c1
#     sc.verify(c1.data == 0)
#     c1.set_data(a=True, b=False)
#     sc.verify(c1.data == 0)
#     c1.set_data(a=False, b=True)
#     sc.verify(c1.data == 0)
#     c1.set_data(a=True, b=True)
#     # Expected
#     # sc.verify(c1.data == 1)


# @sp.add_test(name="Mutation3Bis")
# def test():
#     s = sp.test_scenario()
#     with s.mutation_test() as mt:
#         mt.add_scenario("AndVerifyCondition")


################################################################################


# class EchoTez(sp.Contract):
#     @sp.entry_point
#     def echoTez(self):
#         sp.send(sp.sender, sp.amount)


# @sp.add_test(name="EchoTez")
# def test():
#     c1 = EchoTez()
#     sc = sp.test_scenario()
#     sc += c1
#     alice = sp.test_account("alice")
#     c1.echoTez().run(sender=alice, amount=sp.tez(5))
#     # Expected
#     # A test of the consequence of the send operation.


# @sp.add_test(name="Mutation4")
# def test():
#     s = sp.test_scenario()
#     with s.mutation_test() as mt:
#         mt.add_scenario("EchoTez")


################################################################################


# class NatIsNat(sp.Contract):
#     def __init__(self):
#         self.init(0)

#     @sp.entry_point
#     def set_data(self, params):
#         sp.set_type(params, sp.TNat)
#         # Expected: Remove the following line.
#         sp.verify(params > 0)
#         self.data = params


# @sp.add_test(name="NatIsNat")
# def test():
#     c1 = NatIsNat()
#     sc = sp.test_scenario()
#     sc += c1
#     c1.set_data(5)
#     sc.verify(c1.data == 5)


# @sp.add_test(name="Mutation5")
# def test():
#     s = sp.test_scenario()
#     with s.mutation_test() as mt:
#         mt.add_scenario("NatIsNat")


################################################################################


# class ElseDoesNothing(sp.Contract):
#     def __init__(self):
#         self.init(0)

#     @sp.entry_point
#     def set_data(self, params):
#         with sp.if_(params):
#             self.data += 1


# @sp.add_test(name="ElseDoesNothing")
# def test():
#     c1 = ElseDoesNothing()
#     sc = sp.test_scenario()
#     sc += c1
#     sc.verify(c1.data == 0)
#     c1.set_data(True)
#     sc.verify(c1.data == 1)
#     c1.set_data(False)
#     # Expected
#     # sc.verify(c1.data == 1)


# @sp.add_test(name="Mutation6")
# def test():
#     s = sp.test_scenario()
#     with s.mutation_test() as mt:
#         mt.add_scenario("ElseDoesNothing")


################################################################################


# class OnchainView(sp.Contract):
#     def __init__(self):
#         self.init(sp.nat(0))

#     @sp.onchain_view()
#     def get_data(self):
#         sp.result(self.data)


# @sp.add_test(name="OnchainView")
# def test():
#     c1 = OnchainView()
#     sc = sp.test_scenario()
#     sc += c1
#     # Expected
#     # sc.verify(c1.get_data() == 0)


# @sp.add_test(name="Mutation7")
# def test():
#     s = sp.test_scenario()
#     with s.mutation_test() as mt:
#         mt.add_scenario("OnchainView")
