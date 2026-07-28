# Game of Life - Example for illustrative purposes only.
# In honor of John Conway

import smartpy as sp

class Game_of_life(sp.Contract):
    def __init__(self, size):
        self.size  = size
        self.zero = self.private_variable("zero", sp.utils.matrix(size * [size * [0]]))
        self.init(board = {})

    @sp.entry_point
    def reset(self):
        self.data.board = self.zero

    @sp.entry_point
    def glider(self):
        self.data.board = self.zero
        x = self.size // 3
        self.data.board[x][x]     = 1
        self.data.board[x+1][x+1] = 1
        self.data.board[x+2][x-1] = 1
        self.data.board[x+2][x]   = 1
        self.data.board[x+2][x+1] = 1

    @sp.entry_point
    def bar(self):
        self.data.board = self.zero
        x = self.size // 2
        sp.for k in range(0, self.size):
            self.data.board[x][k] = 1

    @sp.entry_point
    def run(self):
        next = sp.local('next', self.zero)
        sp.for i in range(0, self.size):
            sp.for j in range(0, self.size):
                sum = sp.local('sum', 0)
                sp.for k in sp.range(-1, 2):
                    sp.if (0 <= i + k) & (i + k < self.size):
                        sp.for l in sp.range(-1, 2):
                            sp.if (0 <= j + l) & (j + l < self.size):
                                sp.if (k != 0) | (l != 0):
                                    sum.value += self.data.board[i + k][j + l]
                sp.if (self.data.board[i][j] == 0):
                    sp.if (sum.value == 3):
                        next.value[i][j] = 1
                sp.else:
                    sp.if (2 <= sum.value) & (sum.value <= 3):
                        next.value[i][j] = 1
        self.data.board = next.value

if "templates" not in __name__:
    @sp.add_test(name = "GameOfLife")
    def test():
        c1 = Game_of_life(10)
        scenario = sp.test_scenario()
        scenario.h1("Game of life")

        scenario.table_of_contents()

        scenario += c1

        scenario.h2("Zero")
        c1.reset()

        scenario.h2("Glider")
        c1.glider()
        for i in range(0, 20):
            c1.run()

        scenario.h2("Horizontal Bar")
        c1.bar()
        for i in range(0, 18):
            c1.run()

    sp.add_compilation_target("game_of_life", Game_of_life(10))
