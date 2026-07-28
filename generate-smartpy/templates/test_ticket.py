import smartpy as sp

class C1(sp.Contract):
    def __init__(self):
        self.init(x = sp.none, y = sp.none)

    @sp.entry_point
    def auto_call(self):
        sp.transfer(sp.ticket(1, 43), sp.tez(0), sp.self_entry_point("run"))

    @sp.entry_point
    def run(self, params):
        sp.set_type(params, sp.TTicket(sp.TInt))
        read_ticket = sp.read_ticket(params)
        self.data.y = sp.some(sp.ticket("abc", 42))
        t1, t2 = sp.split_ticket(read_ticket.copy, read_ticket.amount / 3, sp.as_nat(read_ticket.amount - read_ticket.amount // 3))
        self.data.x = sp.some(sp.join_tickets(t2, t1))

    @sp.entry_point
    def run2(self, params):
        sp.set_type(params, sp.TRecord(t = sp.TTicket(sp.TInt), x = sp.TInt))
        (x,t) = sp.match_record(params, 'x', 't')
        sp.verify(x == 42)
        read_ticket = sp.read_ticket(t)
        self.data.y = sp.some(sp.ticket("abc", 42))
        t1, t2 = sp.split_ticket(read_ticket.copy, read_ticket.amount / 3, sp.as_nat(read_ticket.amount - read_ticket.amount // 3))
        self.data.x = sp.some(sp.join_tickets(t2, t1))

class C2(sp.Contract):
    def __init__(self):
        self.init_type(sp.TTicket(sp.TString))

    @sp.entry_point
    def run(self):
        with sp.modify(self.data, 't') as t:
            read_ticket = sp.read_ticket(t)
            sp.verify(read_ticket.content == "abc")
            t1, t2 = sp.split_ticket(read_ticket.copy, read_ticket.amount/2, read_ticket.amount/2)
            t = sp.join_tickets(t2, t1)
            sp.result(t)

class C3(sp.Contract):
    def __init__(self):
        self.init_type(sp.TRecord(t = sp.TTicket(sp.TNat), x = sp.TInt))

    @sp.entry_point
    def run(self):
        with sp.modify_record(self.data, "data") as data:
            read_ticket = sp.read_ticket(data.t)
            sp.verify(read_ticket.content == 42)
            t1, t2 = sp.split_ticket(read_ticket.copy, read_ticket.amount/2, read_ticket.amount/2)
            data.t = sp.join_tickets(t2, t1)

class C4(sp.Contract):
    def __init__(self):
        self.init_type(sp.TRecord(m = sp.TMap(sp.TInt, sp.TTicket(sp.TInt))))

    @sp.entry_point
    def ep1(self):
        with sp.modify_record(self.data, "data") as data:
            (t, m) = sp.get_and_update(data.m, 42)
            data.m = m

class C5(sp.Contract):
    def __init__(self):
        self.init_type(sp.TRecord(m = sp.TMap(sp.TInt, sp.TTicket(sp.TInt)), x = sp.TInt))

    @sp.entry_point
    def ep1(self):
        with sp.modify_record(self.data, "data") as data:
            (t, m) = sp.get_and_update(data.m, 42)
            data.m = m
            data.x = 0

    @sp.entry_point
    def ep2(self, cb):
        with sp.modify_record(self.data, "data") as data:
            t1 = sp.ticket("a", 1)
            t2 = sp.ticket("b", 2)
            sp.transfer((t1,t2), sp.mutez(0), cb)

@sp.add_test(name = "Ticket")
def test():
    s = sp.test_scenario()
    c = C1()
    s += c
    c.auto_call()
    # t = sp.test_ticket(c, 5, 6)
    # c.run(t)

    s += C2()
    s += C3()
    s += C4()
    s += C5()
