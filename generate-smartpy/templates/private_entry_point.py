# Private entry points - Example for illustrative purposes only.

import smartpy as sp

class Store(sp.Contract):
    def __init__(self):
        self.init(x = 0, y = 0)

    @sp.entry_point(private = True)
    def change(self, x, y):
        self.data.x = x
        self.data.y = y

    @sp.entry_point
    def go_x(self):
        self.data.x += 1
        self.data.y -= 1

    @sp.entry_point
    def go_y(self):
        self.data.x -= 1
        self.data.y += 1

if "templates" not in __name__:
    @sp.add_test(name = "Private entry points")
    def test():
        c1 = Store()
        scenario = sp.test_scenario()
        scenario += c1
        c1.go_x()
        c1.go_y()
        c1.change(x = 10, y = 12)
        c1.go_x()
        c1.go_y()
