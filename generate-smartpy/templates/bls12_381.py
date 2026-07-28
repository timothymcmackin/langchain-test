import smartpy as sp


class Bls12_381(sp.Contract):
    def __init__(self, **params):
        self.init(**params)

    @sp.entry_point
    def add(self, g1, g2, fr):
        """ADD: Add two curve points or field elements.

        :: bls12_381_g1 : bls12_381_g1 : 'S -> bls12_381_g1 : 'S
        :: bls12_381_g2 : bls12_381_g2 : 'S -> bls12_381_g2 : 'S
        :: bls12_381_fr : bls12_381_fr : 'S -> bls12_381_fr : 'S
        """
        self.data.g1 += g1
        self.data.g2 += g2
        self.data.fr += fr


    @sp.entry_point
    def negate(self):
        """NEG: Negate a curve point or field element.

        :: bls12_381_g1 : 'S -> bls12_381_g1 : 'S
        :: bls12_381_g2 : 'S -> bls12_381_g2 : 'S
        :: bls12_381_fr : 'S -> bls12_381_fr : 'S
        """
        self.data.g1 = - self.data.g1
        self.data.g2 = - self.data.g2
        self.data.fr = - self.data.fr


    @sp.entry_point
    def toInt(self):
        """Convert a field (the bls12_381_fr element) to type int.

        The returned value is always between 0 (inclusive) and the order of Fr (exclusive).

        :: bls12_381_fr : 'S -> int : 'S
        """
        self.data.toIntResult = sp.some(sp.to_int(self.data.fr))


    @sp.entry_point
    def mul(self, fr, i, n):
        """ MUL: Multiply a curve point or field element by a scalar field element.

        Fr elements can be built from naturals by multiplying by the unit of Fr
        using PUSH bls12_381_fr 1; MUL. Note that the multiplication will be
        computed using the natural modulo the order of Fr.

        :: bls12_381_g1 : bls12_381_fr : 'S -> bls12_381_g1 : 'S
        :: bls12_381_g2 : bls12_381_fr : 'S -> bls12_381_g2 : 'S
        :: bls12_381_fr : bls12_381_fr : 'S -> bls12_381_fr : 'S
        :: nat : bls12_381_fr : 'S -> bls12_381_fr : 'S
        :: int : bls12_381_fr : 'S -> bls12_381_fr : 'S
        :: bls12_381_fr : nat : 'S -> bls12_381_fr : 'S
        :: bls12_381_fr : int : 'S -> bls12_381_fr : 'S
        """
        self.data.g1 = sp.mul(self.data.g1, fr)
        self.data.g2 = sp.mul(self.data.g2, fr)
        self.data.fr = sp.mul(self.data.fr, fr)
        self.data.fr = sp.mul(self.data.fr, i)
        self.data.fr = sp.mul(self.data.fr, n)


    @sp.entry_point
    def pairing_check(self, listOfPairs):
        """PAIRING_CHECK: Verify that the product of pairings of the given list
        of points is equal to 1 in Fq12.

        Returns true if the list is empty.
        Can be used to verify if two pairings P1 and P2 are equal by verifying
        P1 * P2^(-1) = 1.

    :: list (pair bls12_381_g1 bls12_381_g2) : 'S -> bool : 'S
    """
        self.data.checkResult = sp.some(sp.pairing_check(listOfPairs))

    @sp.entry_point
    def conv(self, params):
        """Non trivial combined operations

        This tests that compiler rewriting doesn't break it.
        """
        self.data.fr = sp.mul(sp.fst(sp.ediv(params, sp.mutez(1)).open_some()), sp.bls12_381_fr("0x01"))

@sp.add_test(name = "BLS12-381")
def test():
    g1 = sp.bls12_381_g1("0x17f1d3a73197d7942695638c4fa9ac0fc3688c4f9774b905a14e3a3f171bac586c55e83ff97a1aeffb3af00adb22c6bb08b3f481e3aaa0f1a09e30ed741d8ae4fcf5e095d5d00af600db18cb2c04b3edd03cc744a2888ae40caa232946c5e7e1")
    g2 = sp.bls12_381_g2("0x13e02b6052719f607dacd3a088274f65596bd0d09920b61ab5da61bbdc7f5049334cf11213945d57e5ac7d055d042b7e024aa2b2f08f0a91260805272dc51051c6e47ad4fa403b02b4510b647ae3d1770bac0326a805bbefd48056c8c121bdb80606c4a02ea734cc32acd2b02bc28b99cb3e287e85a763af267492ab572e99ab3f370d275cec1da1aaa9075ff05f79be0ce5d527727d6e118cc9cdc6da2e351aadfd9baa8cbdd3a76d429a695160d12c923ac9cc3baca289e193548608b82801")
    fr = sp.bls12_381_fr("0x2ef123703093cbbbd124e15f2054fa5781ed0b8d092ec3c6e5d76b4ca918a221")

    c1 = Bls12_381(
        g1 = g1,
        g2 = g2,
        fr = fr,
        toIntResult = sp.none,
        checkResult = sp.none
    )

    sc = sp.test_scenario()
    sc += c1
    sc.h2("Basic maths")

    c1.add(g1=g1,g2=g2, fr=fr)

    sc.verify_equal(sp.add(g1, g1), g1 + g1)
    sc.verify_equal(sp.add(g2, g2), g2 + g2)
    sc.verify_equal(sp.add(fr, fr), fr + fr)

    c1.negate()
    c1.toInt()

    sc.verify(c1.data.toIntResult == sp.some(22010428307259596184589026230464379215728696454789911939124470486372749680037))

    c1.mul(fr=fr, i=sp.int(5), n=sp.nat(1))

    sc.verify_equal(c1.data.g1, sp.bls12_381_g1("0x07e3cf9affb773e08cda3f38f9b2b33f1aa234178c17fe4a234b80ec8622861ffb925c4b49595d7e06b7317d377bb89102b3ca77a64fe03fb281212382950e94ad03303e8cead0bfaab99ec00e4741076d7162a1e6b7e273269fc3e6a1b9f0f1"))
    sc.verify_equal(c1.data.g2, sp.bls12_381_g2("0x1097f5e2e3bffa9f555ffdc44f556f363bb1b5cee17c95c8c834740843c84bbd7d2072cb91c86e55b78749dba3b8a8400b20d78f6ec32e931d0f6202b2bc31af0f38acc3aad291b2cc15c625f26bdcd8ebd09559e723855a00ce308f3cd28c040512aa4787618c0c79bcf95abd570f3debc94ece2a77ab66f332c7440372ccd3648037ba7e814d555f85498d74b3a42e009613a78c1c6ab3c6adf8c1f9c9b51a1c3399ec736526a98c888cb147eb86e49e22d9703571a096bce1a93d152f405c"))
    sc.verify_equal(c1.data.fr, sp.bls12_381_fr("0xc1255b074cd1d8fb783ef0b09e62886a82747c03e9dd5f9f3f7b2be9e2054834"))

    sc.h2("Pairing check")

    # From https://gitlab.com/metastatedev/tezos/-/commit/f10c39e0030e6b4fdd416a62de7b80b6ffdfeacf

    # The verifying key, proof, and inputs are generated from
    # ZoKrates, modified to use BLS12-381.
    # The circuit proves knowledge of a square root of 113569.

    input_x = sp.bls12_381_fr("0xa1bb010000000000000000000000000000000000000000000000000000000000")
    input_y = sp.bls12_381_fr("0x0100000000000000000000000000000000000000000000000000000000000000")
    proof_a = sp.bls12_381_g1("0x0a2841423326ab08f5f406409775e43fa0f9a0b97631fa85d2dd9242507d25059e9cf48b8b98f99a0008671423a148ec106d70637056972ef49fb6f62de2e89ba3682b9972292b6bb4e6f53799a75d2f8001ccfde280d8ac05fc209352236cbd")
    proof_b = sp.bls12_381_g2("0x0fced939fb1ad733f99669f50a383ef632f6d41dfbde434a6715afd5c7dfbb7bc5835e058ad8b590c7b38dd137d0bd0f0e1540f1b45d8aa626c360e2ea484a116243f7c802034de915db6b18d5303946f676e423cbd6046d37a82208d500625a11c7250ccb953a7ee49d704ad14de4b727733cff7cf06875d8b6444f3c0a8cbf0bd980e539c74bd5b37bb15fe816f23407d269193105fda71adf35fae9309d9d46729fcd4685699097a86f0460a2bc8b16293940cabfdcfe0f27e4107e74e90c")
    proof_c = sp.bls12_381_g1("0x0a1fb5a144ca3bdfe4ad0f183cf71dd7fdd28cbef4fcd47b5b419f65186703f62ecaaa1255fa21a6ebdd917ab1f9bd9707de7066865e2ff3875e22088619125a0d4088a622ab42224425ef89a5a149ce2db9c8292b62c7e7aaa7e87f3535304b")

    vk_gamma_c = sp.bls12_381_g1("0x063bd6e11e2fcaac1dd8cf68c6b1925a73c3c583e298ed37c41c3715115cf96358a42dbe85a0228cbfd8a6c8a8c54cd015b5ae2860d1cc47f84698d951f14d9448d03f04df2ca0ffe609a2067d6f1a892163a5e05e541279134cae52b1f23c6b")
    vk_gamma_b = sp.bls12_381_g1("0x11f5b5db1da7f1f26217edcce2219d016003af6e5b4d1ca3ad0ff477e354717e658bf16beddc4f4fb76ce39d3327811e0601709dc7ed98c70463cfa1ba33f99851b52b51d1a042d7425bec6277287441c399973632445ce61e7fdd63a70f0f60")
    vk_gamma_a = sp.bls12_381_g1("0x03535a322edd23c55b0ca025e54d450d95df49cc9ee873dcd500e8219f4771264bf159b3b105954d85c7bea8ffe1ea0400c767fe58989366c2837fba76f1b4f46644f19be8ad01e22d894b649e427e0d7e04677ee3919d982f0f96bb0a2f0c34")
    vk_delta = sp.bls12_381_g2("0x10c6d5cdca84fc3c7f33061add256f48e0ab03a697832b338901898b650419eb6f334b28153fb73ad2ecd1cd2ac67053161e9f46cfbdaf7b1132a4654a55162850249650f9b873ac3113fa8c02ef1cd1df481480a4457f351d28f4da89d19fa405c3d77f686dc9a24d2681c9184bf2b091f62e6b24df651a3da8bd7067e14e7908fb02f8955b84af5081614cb5bc49b416d9edf914fc608c441b3f2eb8b6043736ddb9d4e4d62334a23b5625c14ef3e1a7e99258386310221b22d83a5eac035c")
    vk_gamma = sp.bls12_381_g2("0x16dcbd28bff336c2649c7dd1d8391ac7ce6f7ef0124a9db7a4a485a124199eded7ce963c1c18aee1eca9994fe06f192c00e0fb653e1fc737d8d0e2f2f91424ca01f6e6e7c5c04f1c43db03a2900cf6b942aaed6ae77daea6200e094b78c38d770028d531a9d1a118ec23d5a39be7aa6dc28f778da1988856d2235c4a35e81fa48380f050d4baf7ebd7b5e058bf294da916afc34562f097c02a8fcbcf62a00de44f8ae6cfa7acb8ad254e3aeea8b2af12f65b7ee0f54855cb9bd432f3436f238f")
    vk_b = sp.bls12_381_g2("0x0e9383f98df2c6e8b5b45f3876c3384596a0cdbc41349f83c4380bf463a050cdbd1d5057aa483a642e66486d1ed7362a1869e423c3877095e215c17282b11108601166f928043254bbce603bf86f4cec9f2e97e9660e98e4f5bce9b2b3bbacb40946b702ccfcc9a31e0bfc1543a2128edcc95807740a2310ae25eb47b935648e392c58dfae5b5e899d3b970d64e4e9e209741ea8bfedcfcc16b3fd890ff02c788ec0943feaaf01bbb354317acb85fcfd611133e4e563d53ca4e0f50e21cf2e7e")
    vk_a = sp.bls12_381_g1("0x1040577c7d349e332735fc947c868c24a665f812f5dc1e7f60e65e2df80be2267a4b7341ed2287285fccd517acd96d910abba947235c364553aa6445f2f2b3a1a728225a330286ba5197ab87f0edc560d89fc7b623812f7d0d633341726e597a")

    vk_x = sc.compute(sp.mul(vk_gamma_b, input_x) + sp.mul(vk_gamma_c, input_y) + vk_gamma_a)

    c1.pairing_check(
        sp.list([
            (proof_a, proof_b),
            (-vk_x, vk_gamma),
            (-proof_c, vk_delta),
            (-vk_a, vk_b)
        ])
    )

    sc.verify(c1.data.checkResult == sp.some(True))

    c1.pairing_check([(g1, g2), (g1, g2)])

    sc.verify(c1.data.checkResult == sp.some(False))

    c1.pairing_check([])

    sc.verify(c1.data.checkResult == sp.some(True))

    c1.conv(sp.mutez(5))

    sc.verify_equal(c1.data.fr, sp.bls12_381_fr("0x0500000000000000000000000000000000000000000000000000000000000000"))
