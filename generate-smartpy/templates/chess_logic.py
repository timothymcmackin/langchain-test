import smartpy as sp

PAWN   = 1
ROOK   = 2
KNIGHT = 3
BISHOP = 4
QUEEN  = 5
KING   = 6

class Types:
    t_move = sp.TRecord(
        f = sp.TRecord(i = sp.TInt, j = sp.TInt),
        t = sp.TRecord(i = sp.TInt, j = sp.TInt),
        promotion = sp.TOption(sp.TNat),
        claim_repeat = sp.TOption(sp.TPair(sp.TNat, sp.TNat)), # Claim repeat after the move has been done, params: 2 other identical fullMove number
    )

    t_board_state = sp.TRecord(
        castle        = sp.TMap(sp.TInt, sp.TMap(sp.TInt, sp.TBool)),
        check         = sp.TBool,
        deck          = sp.TMap(sp.TInt, sp.TMap(sp.TInt, sp.TInt)),
        enPassant     = sp.TOption(sp.TRecord(i = sp.TInt, j = sp.TInt)),
        fullMove      = sp.TNat,
        halfMoveClock = sp.TNat,
        kings         = sp.TMap(sp.TInt, sp.TRecord(i = sp.TInt, j = sp.TInt)),
        nextPlayer    = sp.TInt,
        # pastMoves is (fullMove, player): blake2b(pack(castle, deck, enPassant))
        pastMoves     = sp.TMap(sp.TPair(sp.TNat, sp.TInt), sp.TBytes),
    )

    t_get_movable_to_params = sp.TRecord(
        i = sp.TInt,
        j = sp.TInt,
        player = sp.TInt,
        deck = sp.TMap(sp.TInt, sp.TMap(sp.TInt, sp.TInt)),
        pawn_capturing = sp.TBool,
    )

class _Piece_Move:
    """
        Collection of big meta-programmation functions that compute piece moves.
        If they are called more than one time in the whole contract they must be encaspulated into lambdas
    """
    def king_move(board_state, deltaX, deltaY, nextPlayer, deck, params):
        with sp.if_(abs(deck[params.f.i][params.f.j]) == KING):
            # Castling
            with sp.if_(((abs(deltaX) == 2) & (deltaY == 0))):
                sp.verify(
                    ((nextPlayer == 1) & (params.f.i == 0) & (params.f.j == 4))
                    | ((nextPlayer == -1) & (params.f.i == 7) & (params.f.j == 4))
                )
                sp.verify(board_state.castle[nextPlayer][sp.sign(deltaX)])
                with sp.if_(deltaX > 0):
                    deck[params.t.i][7] = 0
                with sp.else_():
                    deck[params.t.i][0] = 0
                deck[params.t.i][params.t.j -
                                            sp.sign(deltaX)] = ROOK * nextPlayer

            # Standard move
            with sp.else_():
                sp.verify((abs(deltaX) <= 1) & (abs(deltaY) <= 1))

            board_state.kings[nextPlayer] = sp.record(i = params.t.i, j = params.t.j)
            board_state.castle[nextPlayer] = {-1: False, 1: False}

    def rook_move(board_state, deltaX, deltaY, nextPlayer, deck, params):
        with sp.if_(abs(deck[params.f.i][params.f.j]) == ROOK):
            sp.verify((deltaX == 0) | (deltaY == 0))
            with sp.for_('k', sp.range(1, sp.to_int(sp.max(abs(deltaX), abs(deltaY))) - 1)) as k:
                dx = sp.sign(deltaX)
                dy = sp.sign(deltaY)
                sp.verify(deck[params.f.i + k * dy][params.f.j + k * dx] == 0)

                left_side =  ( (nextPlayer ==  1) & (params.f.i == 0) & (params.f.j == 0) ) | \
                                ( (nextPlayer == -1) & (params.f.i == 7) & (params.f.j == 0) )
                right_side = ( (nextPlayer ==  1) & (params.f.i == 0) & (params.f.j == 7) ) | \
                                ( (nextPlayer == -1) & (params.f.i == 7) & (params.f.j == 7) )

            with sp.if_(left_side):
                board_state.castle[nextPlayer][-1] = False
            with sp.if_(right_side):
                board_state.castle[nextPlayer][1] = False

    def queen_move(deltaX, deltaY, deck, params):
        with sp.if_(abs(deck[params.f.i][params.f.j]) == QUEEN):
            sp.verify((deltaX == 0) | (deltaY == 0)
                        | (abs(deltaX) == abs(deltaY)))
            with sp.for_('k', sp.range(1, sp.to_int(sp.max(abs(deltaX), abs(deltaY))) - 1)) as k:
                dx = sp.sign(deltaX)
                dy = sp.sign(deltaY)
                sp.verify(deck[params.f.i +
                            k * dy][params.f.j + k * dx] == 0)

    def bishop_move(deltaX, deltaY, deck, params):
        with sp.if_(abs(deck[params.f.i][params.f.j]) == BISHOP):
            sp.verify(abs(deltaX) == abs(deltaY))
            with sp.for_('k', sp.range(1, sp.to_int(sp.max(abs(deltaX), abs(deltaY))) - 1)) as k:
                dx = sp.sign(deltaX)
                dy = sp.sign(deltaY)
                sp.verify(deck[params.f.i +
                            k * dy][params.f.j + k * dx] == 0)

    def knight_move(deltaX, deltaY, deck, params):
        with sp.if_(abs(deck[params.f.i][params.f.j]) == KNIGHT):
            sp.verify(abs(deltaX * deltaY) == 2)

    def pawn_move(board_state, deltaX, deltaY, nextPlayer, resetClock, promotion, deck, params):
        with sp.if_(abs(deck[params.f.i][params.f.j]) == PAWN):
            # sp.verify(deck[params.t.i][params.t.j] == 0)
            sp.verify(
                # En passant
                ((abs(deltaX) == 1) & (deltaY*nextPlayer == 1) &
                    (board_state.enPassant.is_some()) & \
                    (params.f.i == board_state.enPassant.open_some().i) &
                    (params.f.j == board_state.enPassant.open_some().j))
                # Jump
                | ((deltaX == 0) & (deltaY*nextPlayer == 2) & \
                    (deck[params.t.i-nextPlayer][params.t.j] == 0))
                # Move
                | ((deltaX == 0) & (deltaY*nextPlayer == 1))
                # Take
                | ((abs(deltaX) == 1) & (deltaY*nextPlayer == 1) &
                    (deck[params.t.i][params.t.j] != nextPlayer))
            )

            with sp.if_((deltaY*nextPlayer == 2)):
                board_state.enPassant = sp.some(
                    sp.record(i=params.t.i-nextPlayer, j=params.t.j))
            with sp.else_():
                board_state.enPassant = sp.none
            resetClock.value = True
            # Promotion
            with sp.if_( (params.t.i == 7) | (params.t.i == 0)):
                promotion.value = True
        with sp.else_():
            board_state.enPassant = sp.none

# Meta programmation methods #

def compute_init_deck():
    pawns = 8 * [PAWN]
    initialFirstLine = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]
    deck = [initialFirstLine] + [pawns] + 4 * [8 * [0]] + [[-x for x in pawns]] + [[-x for x in initialFirstLine]]
    return sp.utils.matrix(deck)

def verify_repeat(board_state, player, fullMoves):
    """ Verify if the same position has been observed 3 times.

        Two positions are by definition "the same" if:
            - the same types of pieces occupy the same squares
            - the same player has the move
            - the remaining castling rights are the same and the possibility to capture "en passant" is the same.
        The repeated positions not need to occur in succession.

        Fullmove start at 1 and is incremented only after both players_map played one time.
    """
    sp.set_type(fullMoves, sp.TSet(sp.TNat))
    sp.verify(sp.len(fullMoves) == 3)
    with sp.for_("fullMove", fullMoves.elements()) as fullMove:
        sp.verify(
            sp.blake2b(sp.pack((board_state.castle, board_state.deck, board_state.enPassant))) == board_state.pastMoves[(fullMove, player)],
            sp.pair("NotSameMove", sp.record(fullMove = fullMove))
        )

def initial_board_state():
    return sp.set_type_expr(sp.record(
        castle        = ({ 1: {-1: True, 1: True},
                               -1: {-1: True, 1: True}}),
        check         = False,
        deck          = compute_init_deck(),
        enPassant     = sp.none,
        fullMove      = sp.nat(1),
        halfMoveClock = sp.nat(0),
        kings         = {-1: sp.record(i=7, j=4),
                          1: sp.record(i=0, j=4)},
        nextPlayer    = 1,
        pastMoves     = sp.map({(0, -1): sp.bytes("0xbaf82e0f3ca2b90e482d6b6846873df9fee4e1baf369bc897bcef3b113a359df")}),
    ), Types.t_board_state)

def is_checkmate(board_state, get_movable_to):
    """ Return sp.bool(True) if the board_state represents a checkmate"""

    not_defending = sp.build_lambda(Lambda_ready.not_defending)
    checkmate = sp.local('checkmate', True)

    nextPlayer = board_state.nextPlayer
    king = board_state.kings[nextPlayer]
    deck = sp.local("deck", board_state.deck).value

    # Are we in check?
    attacking_squares = get_movable_to(sp.record(i = king.i, j = king.j, player = nextPlayer *-1, deck = deck, pawn_capturing = True))
    with sp.if_(sp.len(attacking_squares) == 0):
        checkmate.value = False
    with sp.else_():
        # Can the King escape
        for i, j in [(1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1)]:
            with sp.if_(checkmate.value):
                move_i = king.i + i
                move_j = king.j + j
                destination_piece = sp.local("destination_piece%d_%d" % (i, j), deck.get(move_i, {}).get(move_j, nextPlayer * PAWN)).value
                # Is this destination valid?
                with sp.if_((destination_piece == 0) | (sp.sign(destination_piece) != nextPlayer)):
                    # Would the king be in check if he moves to it?
                    with sp.if_(
                        sp.len(
                            get_movable_to(sp.record(i = move_i, j = move_j, player = nextPlayer * -1, deck = deck, pawn_capturing = True))
                        ) == 0
                    ):
                        checkmate.value = False

        with sp.if_(checkmate.value):
            # Can we capture the attacking square or move a piece to block the attack?
            with sp.if_(sp.len(attacking_squares) == 1):
                # There is no move except escape to protect against 2 attacking pieces
                with sp.for_("attacking_square", attacking_squares) as attacking_square:
                    # Can we capture the attacking square?
                    defending_squares = sp.compute(get_movable_to(sp.record(i = attacking_square.i, j = attacking_square.j, player = nextPlayer*-1, deck = deck, pawn_capturing = True)))

                    checkmate.value = not_defending(sp.record(
                        defending_squares = defending_squares, attacking_square = attacking_square, deck = deck, king = king, nextPlayer = nextPlayer, checkmate = checkmate.value, get_movable_to = get_movable_to))

                    with sp.if_(checkmate.value):
                        # Can we move a piece to block the attack?
                        # KNIGHT and PAWN cannot be blocked by moving a piece between them and the king
                        with sp.if_( (deck[attacking_square.i][attacking_square.j] != KNIGHT * nextPlayer * -1) &
                                        (deck[attacking_square.i][attacking_square.j] != PAWN * nextPlayer * -1)):
                            with sp.if_(attacking_square.i == king.i):
                                # Can we put an obstructing piece in this column?
                                with sp.for_("obstructing_j", sp.range(sp.min(king.j, attacking_square.j), sp.max(king.j, attacking_square.j))) as obstructing_j:
                                    defending_squares = sp.compute(get_movable_to(sp.record(i = king.i, j = obstructing_j, player = nextPlayer, deck = deck, pawn_capturing = False)))
                                    checkmate.value = not_defending(sp.record(
                                        defending_squares = defending_squares, attacking_square = sp.record(i = king.i, j = obstructing_j), deck = deck, king = king, nextPlayer = nextPlayer, checkmate = checkmate.value, get_movable_to = get_movable_to))

                            with sp.else_():
                                with sp.if_(attacking_square.j == king.j):
                                    # Can we put an obstructing piece in this line?
                                    with sp.for_("obstructing_i", sp.range(sp.min(king.i, attacking_square.i), sp.max(king.i, attacking_square.i))) as obstructing_i:
                                        defending_squares = sp.compute(get_movable_to(sp.record(i = obstructing_i, j = king.j, player = nextPlayer, deck = deck, pawn_capturing = False)))
                                        checkmate.value = not_defending(sp.record(
                                            defending_squares = defending_squares, attacking_square = sp.record(i = obstructing_i, j = king.j), deck = deck, king = king, nextPlayer = nextPlayer, checkmate = checkmate.value, get_movable_to = get_movable_to))

                                with sp.else_():
                                    # Can we put an obstructing piece in this diagonal?
                                    d = sp.compute(sp.to_int(abs(king.i - attacking_square.i)))
                                    vec_i = sp.compute(sp.sign(attacking_square.i - king.i))
                                    vec_j = sp.compute(sp.sign(attacking_square.j - king.j))

                                    with sp.for_("i", sp.range(1, d)) as i:
                                        obstructing_i = sp.compute(king.i + vec_i * i)
                                        obstructing_j = sp.compute(king.j + vec_j * i)
                                        defending_squares = sp.compute(get_movable_to(sp.record(i = obstructing_i, j = obstructing_j, player = nextPlayer, deck = deck, pawn_capturing = False)))
                                        checkmate.value = not_defending(
                                                sp.record(
                                                    defending_squares = defending_squares,
                                                    attacking_square = sp.record(i = obstructing_i, j = obstructing_j),
                                                    deck = deck, king = king, nextPlayer = nextPlayer, checkmate = checkmate.value, get_movable_to = get_movable_to))
    return checkmate.value

# Transformed into lambdas #

class Lambda_ready:
    def get_movable_to(params):
        """
            Return player's list of pieces that are capable to move on a square.
            ASSUME That the square doesn't contain a piece owned by `player`.
            ASSUME That the square contains a piece owned by opponent if `pawn_capturing` is True
            Don't take into account "En passant".
            Don't take into account if the move/take is illegal because player would be in check after it.

            Params:
                i, j (sp.TInt): square's coordinates
                player (sp.TInt): attacking player
                deck: current deck
                pawn_capturing (sp.TBool): if pawn_capturing is True: pawns are capturing else: moving
        """
        sp.set_type(params,
            sp.TRecord(
                i = sp.TInt,
                j = sp.TInt,
                player = sp.TInt,
                deck = sp.TMap(sp.TInt, sp.TMap(sp.TInt, sp.TInt)),
                pawn_capturing = sp.TBool,
            )
        )
        i, j, player, deck = sp.match_record(params, "i", "j", "player", "deck")
        check = sp.local('check', sp.list([], t = sp.TRecord(i = sp.TInt, j = sp.TInt))).value

        # square attacked by a pawn
        with sp.if_(params.pawn_capturing):
            for c in [(i+player, j-1), (i+player, j+1)]:
                with sp.if_(deck.get(c[0], {}).get(c[1], 0) == (PAWN * player)):
                    check.push(sp.record(i = c[0], j = c[1]))

        # Pawn can move onto it
        with sp.else_():
            # move by 1
            c = (i-player, j)
            with sp.if_(deck.get(c[0], {}).get(c[1], 0) == (PAWN * player)):
                check.push(sp.record(i = c[0], j = c[1]))

            # jump
            with sp.if_( ((player ==  1) & (i == 3)) |
                            ((player == -1) & (i == 4))):
                c = (i+player*2, j)
                with sp.if_(deck.get(c[0], {}).get(c[1], 0) == (PAWN * player)):
                    check.push(sp.record(i = c[0], j = c[1]))

        # square attacked by a knight
        for c in [(i+2, j-1), (i+2, j+1), (i+1, j-2), (i+1, j+2), (i-2, j-1), (i-2, j+1), (i-1, j-2), (i-1, j+2)]:
            with sp.if_(deck.get(c[0], {}).get(c[1], 0) == KNIGHT * player):
                check.push(sp.record(i = c[0], j = c[1]))

        # square attacked by a king
        # only verified if the i j square doesn't correspond to player's KING
        with sp.if_(deck.get(i, {}).get(j, 0) != (KING * player * -1)):
            for c in [(i+1, j+1), (i-1, j-1), (i+1, j-1), (i-1, j+1), (i+0, j+1), (i+1, j+0), (i+0, j-1), (i-1, j+0)]:
                with sp.if_(deck.get(c[0], {}).get(c[1], 0) == KING * player):
                    check.push(sp.record(i = c[0], j = c[1]))

        def check_queen_other(i, j, other):
            with sp.if_(continue_.value):
                c = sp.compute(deck.get(i, {}).get(j, 0))
                with sp.if_((c != 0) & (c != KING * player * -1)):
                    with sp.if_(
                        (c == QUEEN * player) |
                        (c == other * player)
                    ):
                        check.push(sp.record(i = i, j = j))
                    with sp.else_():
                        continue_.value = False

        continue_ = sp.local('continue_', True)

        # line/column attacked by a rook/queen
        ranges = [j, 8-j, i, 8-i]
        k = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        for n, (a, b) in enumerate(k):
            with sp.for_('l', sp.range(1, ranges[n])) as l:
                check_queen_other(i + l*a, j + l*b, ROOK)
            continue_.value = True

        # diagonals attacked by a bishop/queen
        ranges = [sp.min(i, j), sp.min(8-i, 8-j), sp.min(i, 8-j), sp.min(8-i, j)]
        k = [(-1, -1), (1, 1), (-1, 1), (1, -1)]
        for n, (a, b) in enumerate(k):
            with sp.for_('l', sp.range(1, ranges[n])) as l:
                sp.verify(j+l*b<9, message = sp.record(i = i, j = j, l = l, b = b, n = n))
                check_queen_other(i + l*a, j + l*b, BISHOP)
            continue_.value = True

        return sp.set_type_expr(
                check,
                sp.TList(sp.TRecord(i = sp.TInt, j = sp.TInt))
            )

    def move_piece(board_state, move, get_movable_to):
        """
            Move a piece from one square to another in the deck
                Change the board_state accordingly (deck, kings, check, castle, enPassant, halfMoveClock, fullMove)
                Return a TBool to True if the game is draw
                Do not detect checkmate
            Return (t_board_state, TBool): new board state and `is_draw`

        """
        get_movable_to = sp.set_type_expr(
            get_movable_to,
            sp.TLambda(
                Types.t_get_movable_to_params,
                sp.TList(sp.TRecord(i = sp.TInt, j = sp.TInt))
            )
        )
        board_state = sp.local('board_state', board_state).value
        is_draw = sp.local('is_draw', False)

        sp.set_type(move, Types.t_move)
        sp.set_type(board_state, Types.t_board_state)

        sp.verify((move.f.i >= 0) & (move.f.i < 8))  # from position
        sp.verify((move.f.j >= 0) & (move.f.j < 8))
        sp.verify((move.t.i >= 0) & (move.t.i < 8))  # to position
        sp.verify((move.t.j >= 0) & (move.t.j < 8))
        deltaY = move.t.i - move.f.i
        deltaX = move.t.j - move.f.j
        sp.verify((deltaX != 0) | (deltaY != 0))
        nextPlayer = sp.compute(board_state.nextPlayer)
        deck = sp.local("deck", board_state.deck).value
        # Moving its own piece
        sp.verify(sp.sign(deck[move.f.i][move.f.j]) == nextPlayer)
        # Not moving onto its own piece
        sp.verify(sp.sign(deck[move.t.i][move.t.j]) != nextPlayer)
        # Not moving onto a king
        sp.verify(deck[move.t.i][move.t.j] != KING * nextPlayer)

        resetClock = sp.local('resetClock', False)
        promotion = sp.local('promotion', False)

        _Piece_Move.king_move  (board_state, deltaX, deltaY, nextPlayer, deck, move)
        _Piece_Move.rook_move  (board_state, deltaX, deltaY, nextPlayer, deck, move)
        _Piece_Move.queen_move (deltaX, deltaY, deck, move)
        _Piece_Move.bishop_move(deltaX, deltaY, deck, move)
        _Piece_Move.knight_move(deltaX, deltaY, deck, move)
        # Pawn move must be after every other
        # Because of the promotion system
        _Piece_Move.pawn_move  (board_state, deltaX, deltaY, nextPlayer, resetClock, promotion, deck, move)
        king = sp.compute(board_state.kings[nextPlayer])

        with sp.if_(deck[move.t.i][move.t.j] != 0):
            resetClock.value = True

        with sp.if_(promotion.value):
            piece = sp.compute(move.promotion.open_some())
            sp.verify( (piece > 1) & (piece < 6) )
            deck[move.t.i][move.t.j] = sp.mul(nextPlayer, piece)
        with sp.else_():
            sp.verify(move.promotion.is_none())
            deck[move.t.i][move.t.j] = deck[move.f.i][move.f.j]
        deck[move.f.i][move.f.j] = 0

        # Not in check after the move
        sp.verify(sp.len(get_movable_to(sp.record(i = king.i, j = king.j, player = nextPlayer * -1, deck = deck, pawn_capturing = True))) == 0)

        # Register move
        board_state.pastMoves[(board_state.fullMove, nextPlayer)] = sp.blake2b(sp.pack((board_state.castle, deck, board_state.enPassant)))
        board_state.deck = deck

        with sp.if_(move.claim_repeat.is_some()):
            fullMove1, fullMove2 = sp.match_pair(move.claim_repeat.open_some())
            verify_repeat(board_state, nextPlayer, sp.set([fullMove1, fullMove2, board_state.fullMove]))
            is_draw.value = True

        nextPlayer *= -1
        with sp.if_(nextPlayer == 1):
            board_state.fullMove += 1
        with sp.if_(resetClock.value):
            board_state.halfMoveClock = 0
        with sp.else_():
            board_state.halfMoveClock += 1

        king = sp.compute(board_state.kings[nextPlayer])

        with sp.if_(sp.len(get_movable_to(sp.record(i = king.i, j = king.j, player = nextPlayer * -1, deck = deck, pawn_capturing = True))) > 0):
            board_state.check = True

        with sp.else_():
            board_state.check = False

        with sp.if_(board_state.halfMoveClock > 49):
            is_draw.value = True

        return(board_state, is_draw.value)

    def build_fen(board_state):
        """ Compute standard fen chess board notation

            Params:
                board_state (t_board_state)
            Return (string): fen
        """
        fen = sp.local('fen', "")
        rep = sp.local('rep', sp.map({
                1: 'P',  2: 'R',  3: 'N',  4: 'B',  5: 'Q',  6: 'K',
            -1: 'p', -2: 'r', -3: 'n', -4: 'b', -5: 'q', -6: 'k',
        }))
        column = sp.local('column', sp.map({
            0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'
        }))
        to_str = sp.local('to_str', sp.map({x: str(x) for x in range(10)}))
        empty = sp.local('empty', 0)
        nb_lines = sp.local('nb_lines', 0)

        # Pieces
        with sp.for_('row', board_state.deck.values().rev()) as row:
            with sp.for_('piece', row.values()) as piece:
                with sp.if_(piece == 0):
                    empty.value += 1
                with sp.else_():
                    with sp.if_(empty.value > 0):
                        fen.value += to_str.value[empty.value]
                        empty.value = 0

                    fen.value += rep.value[piece]

            with sp.if_(empty.value > 0):
                fen.value += to_str.value[empty.value]
                empty.value = 0

            nb_lines.value += 1
            with sp.if_(nb_lines.value < 8):
                fen.value += '/'

        # Next player
        with sp.if_(board_state.nextPlayer == 1):
            fen.value += ' w '
        with sp.else_():
            fen.value += ' b '

        # Castling
        with sp.if_(board_state.castle[1][1]):
            fen.value += 'K'
        with sp.if_(board_state.castle[1][-1]):
            fen.value += 'Q'
        with sp.if_(board_state.castle[-1][1]):
            fen.value += 'k'
        with sp.if_(board_state.castle[-1][-1]):
            fen.value += 'q'
        with sp.if_(~(
            board_state.castle[1][1] | board_state.castle[1][-1] |
            board_state.castle[-1][1] | board_state.castle[-1][-1]
        )):
            fen.value += '-'

        # En passant
        with sp.if_(board_state.enPassant.is_some()):
            enPassant = sp.compute(board_state.enPassant.open_some())
            fen.value += ' ' + column.value[enPassant.j]
            fen.value += to_str.value[sp.as_nat(enPassant.i+1)] + ' '
        with sp.else_():
            fen.value += ' - '

        # Halfmove clock
        q, r = sp.match_pair(sp.ediv(board_state.halfMoveClock, 10).open_some())
        with sp.if_(q > 0):
            fen.value += to_str.value[q]
        fen.value += to_str.value[r] + ' '

        # Fullmove number
        # TODO: 100 full moves
        q, r = sp.match_pair(sp.ediv(board_state.fullMove, 10).open_some())
        with sp.if_(q > 0):
            fen.value += to_str.value[q]
        fen.value += to_str.value[r]

        return fen.value

    def not_defending(params):
        """ Return True if none one of the defending_squares can be moved to attacking_square to remove the king's check (without verifying move rules)"""
        defending_squares, attacking_square, deck, initial_king, nextPlayer, checkmate, get_movable_to = sp.match_record(params,
            "defending_squares", "attacking_square", "deck", "king", "nextPlayer", "checkmate", "get_movable_to")
        checkmate = sp.local("checkmate", checkmate)
        with sp.for_("defending_square", defending_squares) as defending_square:
            with sp.if_(checkmate.value):
                test_deck = sp.local("test_deck", deck)
                test_deck.value[attacking_square.i][attacking_square.j] = test_deck.value[defending_square.i][defending_square.j]
                test_deck.value[defending_square.i][defending_square.j] = 0
                king = sp.local("king", initial_king)
                with sp.if_(test_deck.value[attacking_square.i][attacking_square.j] == KING * nextPlayer):
                    king.value = sp.record(i = attacking_square.i, j = attacking_square.j)
                # Is not in check?
                with sp.if_(
                    sp.len(
                        get_movable_to(sp.record(i = king.value.i, j = king.value.j, player = nextPlayer *-1, deck = test_deck.value, pawn_capturing = True))
                    ) == 0
                ):
                    checkmate.value = False
        sp.result(checkmate.value)
