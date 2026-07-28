import smartpy as sp

class Sub(sp.Contract):
    @sp.onchain_view()
    def my_view(self):
        sp.result(42)


class Main(sp.Contract):
    def __init__(self, sub):
        self.exception_optimization_level = "line"
        self.init(x = "", sub = sub)

    @sp.private_lambda(with_storage="read-write")
    def f_unit(self,x):
        self.data.x = x
        sp.result(())

    @sp.private_lambda(with_storage="read-write")
    def f_int(self,x):
        self.data.x = sp.fst(x)
        sp.result(sp.set_type_expr(sp.snd(x), sp.TInt))

    @sp.private_lambda(with_storage="read-write")
    def f_nat(self,x):
        self.data.x = sp.fst(x)
        sp.result(sp.set_type_expr(sp.snd(x), sp.TNat))

    @sp.private_lambda(with_storage="read-write")
    def f_string(self,x):
        self.data.x = sp.fst(x)
        sp.result(sp.set_type_expr(sp.snd(x), sp.TString))

    @sp.private_lambda(with_storage="read-write")
    def f_bytes(self,x):
        self.data.x = sp.fst(x)
        sp.result(sp.set_type_expr(sp.snd(x), sp.TBytes))

    @sp.private_lambda(with_storage="read-write")
    def f_mutez(self,x):
        self.data.x = sp.fst(x)
        sp.result(sp.set_type_expr(sp.snd(x), sp.TMutez))

    @sp.private_lambda(with_storage="read-write")
    def f_timestamp(self,x):
        self.data.x = sp.fst(x)
        sp.result(sp.set_type_expr(sp.snd(x), sp.TTimestamp))

    @sp.private_lambda(with_storage="read-write")
    def f_bool(self,x):
        self.data.x = sp.fst(x)
        sp.result(sp.set_type_expr(sp.snd(x), sp.TBool))

    @sp.private_lambda(with_storage="read-write")
    def f_map(self,x):
        self.data.x = sp.fst(x)
        sp.result(sp.set_type_expr(sp.snd(x), sp.TMap(sp.TInt,sp.TInt)))

    @sp.private_lambda(with_storage="read-write")
    def f_list(self,x):
        self.data.x = sp.fst(x)
        sp.result(sp.set_type_expr(sp.snd(x), sp.TList(sp.TInt)))

    @sp.private_lambda(with_storage="read-write")
    def f_pair(self,x):
        self.data.x = sp.fst(x)
        sp.result(sp.set_type_expr(sp.snd(x), sp.TPair(sp.TNat,sp.TNat)))

    @sp.private_lambda(with_storage="read-write")
    def f_option(self,x):
        self.data.x = sp.fst(x)
        sp.result(sp.set_type_expr(sp.snd(x), sp.TOption(sp.TInt)))

    @sp.private_lambda(with_storage="read-write")
    def f_option_key_hash(self,x):
        self.data.x = sp.fst(x)
        sp.result(sp.set_type_expr(sp.snd(x), sp.TOption(sp.TKeyHash)))

    @sp.private_lambda(with_storage="read-write")
    def f_lambda(self,x):
        self.data.x = sp.fst(x)
        sp.result(sp.set_type_expr(sp.snd(x), sp.TLambda(sp.TInt,sp.TInt)))

    # @sp.private_lambda(with_storage="read-write")
    # def f_chest(self,x):
    #     self.data.x = sp.fst(x)
    #     sp.result(sp.set_type_expr(sp.snd(x), sp.TChest))

    @sp.private_lambda(with_storage="read-write")
    def f_contract(self,x):
        self.data.x = sp.fst(x)
        sp.result(sp.set_type_expr(sp.snd(x), sp.TContract(sp.TInt)))

    # @sp.private_lambda(with_storage="read-write")
    # def f_chest_key(self,x):
    #     self.data.x = sp.fst(x)
    #     sp.result(sp.set_type_expr(sp.snd(x), sp.TChest_key))

    @sp.private_lambda(with_storage="read-write")
    def f_lambda2(self,x):
        self.data.x = sp.fst(x)
        sp.result(sp.set_type_expr(sp.snd(x), sp.TLambda(sp.TPair(sp.TInt,sp.TInt), sp.TInt)))

    @sp.private_lambda(with_storage="read-write")
    def f_address(self,x):
        self.data.x = sp.fst(x)
        sp.result(sp.set_type_expr(sp.snd(x), sp.TAddress))

    @sp.private_lambda(with_storage="read-write")
    def f_ticket(self,x):
        x1, x2 = sp.match_tuple(x, "x1", "x2")
        self.data.x = x1
        sp.result(sp.set_type_expr(x2, sp.TTicket(sp.TInt)))

    @sp.private_lambda(with_storage="read-write")
    def f_key(self,x):
        x1, x2 = sp.match_tuple(x, "x1", "x2")
        self.data.x = x1
        sp.result(sp.set_type_expr(x2, sp.TKey))

    @sp.private_lambda(with_storage="read-write")
    def f_signature(self,x):
        x1, x2 = sp.match_tuple(x, "x1", "x2")
        self.data.x = x1
        sp.result(sp.set_type_expr(x2, sp.TSignature))

    @sp.entry_point
    def test_prim2(self):
        a_int       = self.f_int(("A", 1))
        a_nat       = self.f_nat(("A", 1))
        a_list      = self.f_list(("A", []))
        a_timestamp = self.f_timestamp(("A", sp.timestamp(1)))
        a_address   = self.f_address(("A", self.data.sub))
        a_lambda    = self.f_lambda(("A", lambda x: x))
        a_lambda2   = self.f_lambda2(("A", lambda _: 0))
        a_ticket    = self.f_ticket(("A", sp.ticket(1,1)))
        a_map       = self.f_map(("A", {}))
        b_unit      = self.f_unit(("B"))
        b_int       = self.f_int(("B", 1))
        b_nat       = self.f_nat(("B", 1))
        b_list      = self.f_list(("B", []))
        b_pair      = self.f_pair(("B", (1,1)))

        sp.compute( a_map.get_opt(b_int) )
        sp.verify(self.data.x == "B")
        sp.compute( a_map.contains(b_int) )
        sp.verify(self.data.x == "B")
        sp.compute( a_lambda(b_int) )
        sp.verify(self.data.x == "B")
        sp.compute( a_lambda2.apply(b_int) )
        sp.verify(self.data.x == "B")
        sp.compute( sp.cons(a_int, b_list) )
        sp.verify(self.data.x == "A")
        sp.compute( a_timestamp.add_seconds(b_int) )
        sp.verify(self.data.x == "A")
        sp.compute( sp.ticket(a_int, b_nat) )
        sp.verify(self.data.x == "A")
        # sp.compute( sp.view("my_view", a_address, b_unit) )
        # sp.verify(self.data.x == "A")

        sp.compute( a_int + b_int )
        sp.verify(self.data.x == "A")
        sp.compute( a_int * b_int )
        sp.verify(self.data.x == "A")
        sp.compute( a_int - b_int )
        sp.verify(self.data.x == "A")
        sp.compute( a_int + b_int )
        sp.verify(self.data.x == "A")
        sp.compute( a_nat / b_nat )
        sp.verify(self.data.x == "A")
        sp.compute( a_int == b_int )
        sp.verify(self.data.x == "A")
        sp.compute( a_int != b_int )
        sp.verify(self.data.x == "A")
        sp.compute( a_int < b_int )
        sp.verify(self.data.x == "A")
        sp.compute( a_int <= b_int )
        sp.verify(self.data.x == "A")
        sp.compute( a_int > b_int )
        sp.verify(self.data.x == "A")
        sp.compute( a_int >= b_int )
        sp.verify(self.data.x == "A")
        sp.compute( a_int % b_int )
        sp.verify(self.data.x == "A")
        sp.compute( a_nat ^ b_nat )
        sp.verify(self.data.x == "A")
        sp.compute( sp.min(a_int, b_int) )
        sp.verify(self.data.x == "A")
        sp.compute( sp.max(a_int, b_int) )
        sp.verify(self.data.x == "A")
        sp.compute( sp.ediv(a_int, b_int) )
        sp.verify(self.data.x == "A")

        sp.compute( self.f_bool(("A",False)) | self.f_bool(("B",False)) )
        sp.verify(self.data.x == "B")
        sp.compute( self.f_bool(("A",False)) | self.f_bool(("B",True)) )
        sp.verify(self.data.x == "B")
        sp.compute( self.f_bool(("A",True)) | self.f_bool(("B",False)) )
        sp.verify(self.data.x == "A")
        sp.compute( self.f_bool(("A",True)) | self.f_bool(("B",True)) )
        sp.verify(self.data.x == "A")

        sp.compute( self.f_bool(("A",False)) & self.f_bool(("B",False)) )
        sp.verify(self.data.x == "A")
        sp.compute( self.f_bool(("A",False)) & self.f_bool(("B",True)) )
        sp.verify(self.data.x == "A")
        sp.compute( self.f_bool(("A",True)) & self.f_bool(("B",False)) )
        sp.verify(self.data.x == "B")
        sp.compute( self.f_bool(("A",True)) & self.f_bool(("B",True)) )
        sp.verify(self.data.x == "B")

    @sp.entry_point
    def test_prim3(self):
        a_nat       = self.f_nat(("A", 1))
        a_mutez     = self.f_mutez(("A", sp.mutez(1)))
        a_map       = self.f_map(("A", {}))
        b_nat       = self.f_nat(("B", 1))
        b_int       = self.f_int(("B", 1))
        c_nat       = self.f_nat(("C", 1))
        c_option    = self.f_option(("C", sp.some(1)))
        c_int       = self.f_int(("C", 1))

        sp.compute( sp.split_tokens(a_mutez, b_nat, c_nat) )
        sp.verify(self.data.x == "A")
        sp.compute( sp.split_tokens(sp.mutez(0), b_nat, c_nat) )
        sp.verify(self.data.x == "B")

        sp.compute( sp.range(a_nat, b_nat, c_nat) )
        sp.verify(self.data.x == "A") # TODO Interpreter-compiler inconsistency!

        # Irregular evaluation order!
        sp.compute( sp.update_map(a_map, b_int, c_option) )
        sp.verify(self.data.x == "B")
        sp.compute( sp.update_map(a_map, 0, c_option) )
        sp.verify(self.data.x == "C")

        # Irregular evaluation order!
        sp.compute( sp.get_and_update(a_map, b_int, c_option) )
        sp.verify(self.data.x == "B")
        sp.compute( sp.get_and_update(a_map, 0, c_option) )
        sp.verify(self.data.x == "C")

        sp.compute( sp.eif( self.f_bool(("A",True)), b_int, c_int))
        sp.verify(self.data.x == "B")
        sp.compute( sp.eif( self.f_bool(("A",True)), 0, c_int))
        sp.verify(self.data.x == "A")

        sp.compute( sp.eif( self.f_bool(("A",False)), b_int, c_int))
        sp.verify(self.data.x == "C")
        sp.compute( sp.eif( self.f_bool(("A",False)), b_int, 0))
        sp.verify(self.data.x == "A")

    @sp.entry_point
    def test_mprim2(self):
        a_nat       = self.f_nat(("A", 1))
        b_nat       = self.f_nat(("B", 1))

        sp.compute( a_nat << b_nat)
        sp.verify(self.data.x == "A")

        sp.compute( a_nat >> b_nat)
        sp.verify(self.data.x == "A")

    @sp.entry_point
    def test_mprim3(self, p):
        # sp.set_type(p.chest_key, sp.TChest_key)

        # chest     = sp.chest("0xbcf89e8a80d99cd49690dda59accc4d381c1a3facbacc1a3f9aab5e7ecdc8db6b0928eed84a7e5d9958e96b5b1f3c8ddd9b98dd394f9bafaafad85a2d7cbffeec1e280d5c6ccbab3caddb5ced3c1d39c82cea0cc99b7f788bbca85eeb1badd91fdc8e1e1e9a6cddca7bdef8faaf6acf2aeef8ccbd3d987f6d0ecf9c8c9818c92eb8a81e385fff9e8c4ad96d6e7bad6a480ec83f3cb84bedeac82baafa1b88bfd90968b9ee7b2d8aabef9d8e0d9a9c8a5a8859a8db5e6d496de95cfd2cfc4dcfae3edf9f1d5faee998694ed8aada2a7d4b88aecc8acda98d6f69cfb8df3a5ca80b48d91aa9bbbf68f918998ddc5d3cc82d3f0ce81869fd9edb8b0989dcfa5e9b59db18dd099c7b8bb848586afc7c8888f86d2c6988eeee5e5fbfc9de8a7f19e84ebc2b687049390ebd5cecb86eecfe2bef994f9a7c3eabeabdda0b4b7b59381a8a4c3d7c1b382bcf6e1adb2e3c6ce9ca5e0c0a0beb999f4eacc89cf858fb282b294d99ec2daccd9cdcc98a98b8cb5b0bbf9ed80b0f6ccd2a994f3a1faafbbacf7eebbec9399bfdfd1f0da9ee4aa9dcb8b9c85fcab87bd86b98fd7cc9a8cb2e3cc93ef86df83e5ce9bbda8c7d4cad0e4b893fde8e18b9cf283f9829f9ab8f48da8b0f1b5c8f3a1d2a1a6e5c1fec0abb09eb9b0c2c3ae9f9df6c6a7bad396f7b3b1fc90e490a4f2a5f599fedbc8b3b297a99db3b285a3f0acefe0c8d4cec08195af8098d0f4b8d488bdacd7e8effea5cdaf8dd1ccdbe4fee59eb7e1cebff2eb839b8f81d598abc798d5bdcea59bfcbaf89fbdbbcb8182a3eea1f4f5dccafcb4ddd4ff83d3879edef5d3ca06d2f1146cf4c25faf0e432bf540b4de74fae3cc68e0bc57c700000021cf744e778f4d5e220d4be7310077e6735795b6c90bbe2bdcdd9b686e3c71f833f2")

        # a_chest_key  = self.f_chest_key(("A", p.chest_key))
        a_key        = self.f_key(("A", p.key))
        # b_chest      = self.f_chest(("B", chest))
        b_signature  = self.f_signature(("B", p.signature))
        c_nat        = self.f_nat(("C", 1))
        c_bytes      = self.f_bytes(("C", sp.bytes("0x00")))

        # Time-lock is deprecated.
        # sp.compute( sp.open_chest(a_chest_key, b_chest, c_nat) )
        # sp.verify(self.data.x == "A")
        # sp.compute( sp.open_chest(p.chest_key, b_chest, c_nat) )
        # sp.verify(self.data.x == "B")

        sp.verify(sp.check_signature(a_key, b_signature, c_bytes))
        sp.verify(self.data.x == "A")
        sp.verify(sp.check_signature(p.key, b_signature, c_bytes))
        sp.verify(self.data.x == "B")

    @sp.entry_point
    def test_expr_other(self):
        a_int          = self.f_int(("A", 1))
        a_int1         = self.f_int(("A", 1))
        a_int2         = self.f_int(("A", 2))
        c_int1         = self.f_int(("C", 1))
        c_int2         = self.f_int(("C", 2))
        a_list         = self.f_list(("A", []))
        a_map          = self.f_map(("A", {1: 2}))
        a_nat          = self.f_nat(("A", 1))
        a_option       = self.f_option(("A", sp.some(1)))
        a_option_kh    = self.f_option_key_hash(("A", sp.none))
        a_string       = self.f_string(("A","abc"))
        b_int          = self.f_int(("B", 1))
        b_lambda       = self.f_lambda(("B", lambda x: x))
        b_mutez        = self.f_mutez(("B", sp.mutez(1)))
        b_nat          = self.f_nat(("B", 1))
        b_pair         = self.f_pair(("B", (1,1)))
        c_int          = self.f_int(("C", 1))
        c_nat          = self.f_nat(("C", 1))
        c_unit         = self.f_unit(("C"))
        d_int          = self.f_int(("D", 1))
        a_unit         = self.f_unit(("A"))
        c_contract     = self.f_contract(("C",sp.self_entry_point(entry_point = 'put_int')))

        sp.compute( a_option.open_some(message = b_int) )
        sp.verify(self.data.x == "A")
        sp.compute( sp.some(1).open_some(message = b_int) )
        sp.verify(self.data.x == "A")

        sp.compute(a_map[b_int])
        sp.verify(self.data.x == "B")
        sp.compute(sp.pair(a_int, b_int))
        sp.verify(self.data.x == "A")
        sp.compute(sp.record(a = a_int, b = b_int))
        # sp.verify(self.data.x == "A") # TODO Interpreter-compiler inconsistency!
        sp.compute([a_int, b_int])
        # sp.verify(self.data.x == "A") # TODO order?
        sp.compute(sp.set([a_int, b_int]))
        # sp.verify(self.data.x == "A") # TODO order?
        sp.compute({a_int: b_int, c_int: d_int})
        # sp.verify(self.data.x == "A") # TODO order?
        sp.compute({1    : b_int, c_int: d_int})
        # sp.verify(self.data.x == "B") # TODO order?
        # TODO ESaplingVerifyUpdate
        sp.compute(a_list.map(b_lambda))
        sp.verify(self.data.x == "A")

        # Irregular evaluation order!
        sp.compute(sp.create_contract_operation(Sub(), storage = c_unit, amount = b_mutez, baker = a_option_kh))
        sp.verify(self.data.x == "A")
        sp.compute(sp.create_contract_operation(Sub(), storage = c_unit, amount = b_mutez, baker = sp.none))
        sp.verify(self.data.x == "B")

        # Irregular evaluation order!
        sp.compute(sp.slice(a_string, b_nat, c_nat))
        sp.verify(self.data.x == "B")
        sp.compute(sp.slice(a_string, 0, c_nat))
        sp.verify(self.data.x == "C")

        sp.compute(sp.transfer_operation(a_int, b_mutez, c_contract))
        sp.verify(self.data.x == "A")
        sp.compute(sp.transfer_operation(0, b_mutez, c_contract))
        sp.verify(self.data.x == "B")

        # TODO ematch

    @sp.entry_point
    def put_int(self, x):
        sp.set_type(x, sp.TInt)

@sp.add_test(name = "Test_eval_order")
def test():
    s = sp.test_scenario()

    sub = Sub()
    s += sub

    main = Main(sub.address)
    s += main

    main.test_prim2()
    main.test_prim3()
    main.test_mprim2()

    # chest_key = sp.chest_key("0xf5d3cec5da988edfbee8be85b4919bc7c5a3f7ecebe7a19ac8e0c3f9c3aac5948de9b9dddab88b93c4fee4d094a3a5e48494c0ae80b4ffbcd9a8b7a2c9f3dfc0e2e18082f3d3ceabf9f1a7c8fcd4dec7b7e091a89e83f8a6ab90dea1bdbd95bff9ed8ac89c88ebeecfe5faaeb8f184e5df9298e5aff3bad5bbc1fcefdbb5b2929df9c6ced9aebefbc49decb4d9e085b1a8c39099818d97e0b3dbf287efb99c87c8eeb38f86d9e9c2bdeccec4abb5ce89bce988aba5a0adf59180898697a7e5d1dfa8d5a6aac8f0f5bd87ecb7aeaedec6a4f7f5bfead9e1cbd3a8a88fddcb939198f0ae94cecdc3e9d3d9c2b28ece8ff487a0e983868ef995b3ee90f082adf8aeddbab2efc2b5fcd5aff1a19bb3acff83b08986d0ffa3eec4afabbec280f4d498b1f2e6de01c192a381d3b8c19dd8edb4d6e689cbccb1b5c396c7abda9bc4ed9edf9ecff7c78bab8fadbbd4f4e7d1d289eace839becdfa5e7d1ddc2b0e9e1e88d87a3e3aae8c6dd889cd980e69af8b992d4b5e28cb691de94c0afe0f3fbde8b85e4eced9ec8dcd986d189e4a8bcd3fda2efbce5cde9d68499eef7bda5a782c3adf0cc84abd0c0ec91988b9a81ad819af19e97eefacea9a9b1ffe2d1bcc1e5d8dc87e89d8a92afd3fcf4d4d2e1d9e4f583c5a583ebb6f19dd7abd3f8f5d6a8ee9bf78faa8aedf0d8b0e6a1a6bf95849192b5f8bfef9581deaebef3e6f390ac99ade490e7feb5d0d589cce2e3d4b9ced493e3fac1da83f697e6c0e68f8295ec97f2c0aae7dcaffaedb5fef283d4a5b4f3fdd8e7a0b0f9c4accce9c2f9e9ba8b8391fad3d0db84cbe9f3d003")
    alice = sp.test_account("Alice")
    signature = sp.make_signature(secret_key = alice.secret_key, message = sp.bytes("0x00"), message_format = "Raw")
    #main.test_mprim3(sp.record(chest_key=chest_key, key=alice.public_key, signature=signature))
    main.test_mprim3(sp.record(key=alice.public_key, signature=signature))

    main.test_expr_other()
