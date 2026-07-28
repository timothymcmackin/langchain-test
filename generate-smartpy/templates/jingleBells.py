# Jingle Bells - Example for illustrative purposes only.

import smartpy as sp

lyrics = """
Dashing through the snow
In a one-horse open sleigh
O'er the fields we go
Laughing all the way

Bells on bob tail ring
Making spirits bright
What fun it is to ride and sing
A sleighing song tonight!

Jingle bells, jingle bells,
Jingle all the way.
Oh! what fun it is to ride
In a one-horse open sleigh.

Jingle bells, jingle bells,
Jingle all the way;
Oh! what fun it is to ride
In a one-horse open sleigh.
"""

lyrics = [x for x in lyrics.split('\n') if x]

class JingleBells(sp.Contract):
    def __init__(self):
        self.lyrics = sp.utils.vector(lyrics)
        self.init(rules   = ['Please sing as much as you wish!',
                             'Happy Holidays from the SmartPy team!'],
                  played  = 0,
                  verse   = 0,
                  current = "")

    @sp.entry_point
    def sing(self, params):
        sp.for i in sp.range(0, params.verses):
            sp.if self.data.verse == len(lyrics):
                self.data.played += 1
                self.data.current = ""
                self.data.verse = 0
            sp.if self.data.current != "":
                self.data.current += "\n"
            lyrics_ = sp.local('lyrics', self.lyrics)
            self.data.current += lyrics_.value[self.data.verse]
            self.data.verse += 1

if "templates" not in __name__:
    @sp.add_test(name = "JingleBells")
    def test():
        c1 = JingleBells()
        scenario = sp.test_scenario()
        scenario.h1("Jingle Bells")
        scenario += c1
        for i in range(0, 10):
            c1.sing(verses = 1)
        c1.sing(verses = 6)
        c1.sing(verses = 100)

    sp.add_compilation_target("Jingle Bells", JingleBells())
