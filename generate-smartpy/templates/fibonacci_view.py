import smartpy as sp


class FibonacciView(sp.Contract):
    """Contract with a recursing view to compute the sum of fibonacci numbers."""

    @sp.onchain_view()
    def fibonacci(self, n):
        """Return the sum of fibonacci numbers until n.

        Args:
            n (sp.TInt): number of fibonacci numbers to sum.
        Return:
            (sp.TInt): the sum of fibonacci numbers
        """
        sp.set_type(n, sp.TInt)
        with sp.if_(n < 2):
            sp.result(n)
        with sp.else_():
            n1 = sp.view("fibonacci", sp.self_address, n - 1).open_some()
            n2 = sp.view("fibonacci", sp.self_address, n - 2).open_some()
            sp.result(n1 + n2)


if "templates" not in __name__:

    @sp.add_test(name="FibonacciView basic scenario", is_default=True)
    def basic_scenario():
        sc = sp.test_scenario()
        sc.h1("Basic scenario.")

        sc.h2("Origination.")
        c1 = FibonacciView()
        sc += c1

        sc.verify(c1.fibonacci(8) == 21)
