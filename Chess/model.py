import copy

import numpy as np

PAWN = 0
KNIGHT = 1
BISHOP = 2
ROOK = 3
QUEEN = 4
KING = 5

WHITE = -1
BLACK = 1

STALEMATE = -1
GAME_IN_PLAY = 0
CHECKMATE = 1


class Piece:
    def __init__(self, piece_type, color, square):
        self.piece_type = piece_type
        self.color = color
        self.square = Square.get_square(square)
        self.captured = False

    def move(self, square):
        self.square = Square.get_square(square)

    def promote(self, piece):
        if self.piece_type == PAWN:
            self.piece_type = piece

    def __str__(self):
        letters = ['p', 'n', 'b', 'r', 'q', 'k']
        letter = letters[self.piece_type]

        if self.color == WHITE:
            letter = letter.upper()

        return letter

    def __repr__(self):
        return str(self)


class Square(tuple):
    def __init__(self, tup):
        self.row = tup[0]
        self.col = tup[1]
        self.coords = tup

    @classmethod
    def get_square(cls, *args):
        if len(args) == 1:
            arg = args[0]
            if type(arg) == tuple:
                return cls(arg)
            elif type(arg) == str:
                return cls.from_name(arg)
            elif type(arg) == Square:
                return arg
        elif len(args) == 2:
            a, b = args
            if type(a) == type(b) == int:
                return cls(args)

    def get_diff(self, diff):
        row = self.row + diff[0]
        col = self.col + diff[1]
        return Square((row, col))

    @staticmethod
    def is_valid(square):
        return 0 <= square.row < 8 and 0 <= square.col < 8

    def convert_to_name(self):
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        ranks = ['8', '7', '6', '5', '4', '3', '2', '1']

        file = files[self.col]
        rank = ranks[self.row]

        return file + rank

    @classmethod
    def convert_to_coords(cls, name):
        file = name[0].lower()
        rank = name[1]

        files = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
        ranks = {'8': 0, '7': 1, '6': 2, '5': 3, '4': 4, '3': 5, '2': 6, '1': 7}

        row = ranks[rank]
        col = files[file]

        return row, col

    @classmethod
    def from_name(cls, name):
        return cls(cls.convert_to_coords(name))

    def __str__(self):
        return self.convert_to_name()

    def __repr__(self):
        return self.convert_to_name()

    def __eq__(self, other):
        return self.coords == other.coords


class Move:
    def __init__(self, initial_loc, final_loc, piece_moved, piece_captured=None, promotion=None, check=None, mate=None):
        self.initial_loc: Square = Square.get_square(initial_loc)
        self.final_loc: Square = Square.get_square(final_loc)
        self.piece_moved: Piece = piece_moved
        self.piece_captured: Piece = piece_captured
        self.promotion = promotion
        self.check = check
        self.mate = mate

    def to_algebraic_notation(self):
        notation = ""
        if self.piece_moved.piece_type == PAWN:
            if self.piece_captured:
                notation += f"{self.initial_loc.convert_to_name()[0]}x"
            notation += self.final_loc.convert_to_name()
        elif self.piece_moved.piece_type != KING:
            notation += str(self.piece_moved).upper()
            if self.piece_captured:
                notation += "x"
            notation += self.final_loc.convert_to_name()
        elif self.piece_moved.piece_type == KING:
            if abs(self.final_loc.col - self.initial_loc.col) == 2:
                notation = "O-O"
            elif abs(self.final_loc.col - self.initial_loc.col) == 3:
                notation = "O-O-O"
            else:
                notation += str(self.piece_moved).upper()
                if self.piece_captured:
                    notation += "x"
                notation += self.final_loc.convert_to_name()

        if self.mate:
            notation += "#"
        elif self.check:
            notation += "+"

        return notation


class Board:
    def __init__(self):
        self.board, self.pieces = self.initialize()
        self.castling = [True] * 4  # white king-side, white queen-side, black king-side, black queen-side
        self.en_passant = [False, None, None]  # is there en passant, where it is, what pawn moved 2

    @property
    def white_king(self) -> Piece:
        return self.pieces[20]

    @property
    def black_king(self) -> Piece:
        return self.pieces[4]

    @staticmethod
    def initialize():
        r1 = Piece(ROOK, BLACK, "a8")
        k1 = Piece(KNIGHT, BLACK, "b8")
        b1 = Piece(BISHOP, BLACK, "c8")
        q = Piece(QUEEN, BLACK, "d8")
        k = Piece(KING, BLACK, "e8")
        b2 = Piece(BISHOP, BLACK, "f8")
        k2 = Piece(KNIGHT, BLACK, "g8")
        r2 = Piece(ROOK, BLACK, "h8")
        p1 = Piece(PAWN, BLACK, "a7")
        p2 = Piece(PAWN, BLACK, "b7")
        p3 = Piece(PAWN, BLACK, "c7")
        p4 = Piece(PAWN, BLACK, "d7")
        p5 = Piece(PAWN, BLACK, "e7")
        p6 = Piece(PAWN, BLACK, "f7")
        p7 = Piece(PAWN, BLACK, "g7")
        p8 = Piece(PAWN, BLACK, "h7")

        R1 = Piece(ROOK, WHITE, "a1")
        K1 = Piece(KNIGHT, WHITE, "b1")
        B1 = Piece(BISHOP, WHITE, "c1")
        Q = Piece(QUEEN, WHITE, "d1")
        K = Piece(KING, WHITE, "e1")
        B2 = Piece(BISHOP, WHITE, "f1")
        K2 = Piece(KNIGHT, WHITE, "g1")
        R2 = Piece(ROOK, WHITE, "h1")
        P1 = Piece(PAWN, WHITE, "a2")
        P2 = Piece(PAWN, WHITE, "b2")
        P3 = Piece(PAWN, WHITE, "c2")
        P4 = Piece(PAWN, WHITE, "d2")
        P5 = Piece(PAWN, WHITE, "e2")
        P6 = Piece(PAWN, WHITE, "f2")
        P7 = Piece(PAWN, WHITE, "g2")
        P8 = Piece(PAWN, WHITE, "h2")

        pieces = list(locals().values())
        board = np.array([
            [r1, k1, b1, q, k, b2, k2, r2],
            [p1, p2, p3, p4, p5, p6, p7, p8],
            [None] * 8,
            [None] * 8,
            [None] * 8,
            [None] * 8,
            [P1, P2, P3, P4, P5, P6, P7, P8],
            [R1, K1, B1, Q, K, B2, K2, R2]
        ])

        return board, pieces

    def apply_move(self, move: Move):
        initial_loc = move.initial_loc
        final_loc = move.final_loc
        piece_moved = move.piece_moved
        piece_captured: Piece = move.piece_captured
        promotion = move.promotion

        self.board[initial_loc] = None
        self.board[piece_moved.square] = None

        if piece_captured:
            piece_captured.captured = True
            self.board[piece_captured.square] = None

        self.board[final_loc] = piece_moved
        piece_moved.move(final_loc)

        # if castling, move rook
        if piece_moved.piece_type == KING and abs(final_loc.col - initial_loc.col) > 1:
            if final_loc == Square.from_name("g1"):
                rook = self.get("h1")
                self.board[Square.from_name("h1")] = None
                self.board[Square.from_name("f1")] = rook
                rook.move(Square.from_name("f1"))
            elif final_loc == Square.from_name("c1"):
                rook = self.get("a1")
                self.board[Square.from_name("a1")] = None
                self.board[Square.from_name("d1")] = rook
                rook.move(Square.from_name("d1"))
            elif final_loc == Square.from_name("g8"):
                rook = self.get("h8")
                self.board[Square.from_name("h8")] = None
                self.board[Square.from_name("f8")] = rook
                rook.move(Square.from_name("f8"))
            elif final_loc == Square.from_name("c8"):
                rook = self.get("a8")
                self.board[Square.from_name("a8")] = None
                self.board[Square.from_name("d8")] = rook
                rook.move(Square.from_name("d8"))

        if promotion is not None:
            piece_moved.promote(promotion)

        if piece_moved.piece_type == ROOK:
            if piece_moved.color == WHITE:
                if initial_loc.convert_to_name() == "a1":
                    self.castling[1] = False
                else:
                    self.castling[0] = False
            else:
                if initial_loc.convert_to_name() == "a8":
                    self.castling[3] = False
                else:
                    self.castling[2] = False

        if piece_moved.piece_type == KING:
            if piece_moved.color == WHITE:
                self.castling[:2] = [False] * 2
            else:
                self.castling[2:] = [False] * 2

        self.en_passant = [False, None, None]
        if piece_moved.piece_type == PAWN:
            if abs(final_loc.coords[0] - initial_loc.coords[0]) == 2:
                if piece_moved.color == WHITE:
                    self.en_passant = [True, Square((initial_loc.row - 1, initial_loc.col)), piece_moved]
                else:
                    self.en_passant = [True, Square((initial_loc.row + 1, initial_loc.col)), piece_moved]

    def get(self, square) -> Piece:
        return self.board[Square.get_square(square)]


class Game:
    def __init__(self):
        self.board = Board()
        self.turn = WHITE
        self.moves = []

    def is_move_legal(self, move: Move, check_if_exposes_king=True) -> bool:
        initial_loc: Square = move.initial_loc
        final_loc: Square = move.final_loc
        piece_moved: Piece = move.piece_moved
        piece_captured: Piece = move.piece_captured

        legal = False

        hdist = final_loc.col - initial_loc.col
        vdist = final_loc.row - initial_loc.row

        if hdist == vdist == 0:
            return False

        if piece_captured and piece_captured.color == piece_moved.color:
            return False

        if check_if_exposes_king:
            test_game = copy.deepcopy(self)
            test_move = Move(
                initial_loc=initial_loc,
                final_loc=final_loc,
                piece_moved=test_game.board.get(initial_loc),
                piece_captured=test_game.board.get(final_loc),
            )
            test_move = test_game.correct_en_passant(test_move)
            test_game.move(test_move)

            if piece_moved.color == WHITE:
                if test_game.is_targeted(BLACK, test_game.board.white_king.square, check_if_exposes_king=False):
                    return False
            else:
                if self.is_targeted(WHITE, test_game.board.black_king.square, check_if_exposes_king=False):
                    return False

        if piece_moved.piece_type == PAWN:
            if hdist == 0 and not piece_captured:
                if vdist == -1 and piece_moved.color == WHITE:
                    return True
                elif vdist == -2 and piece_moved.color == WHITE and initial_loc.row == 6 and not self.board.get(initial_loc.get_diff([-1, 0])):
                    return True
                elif vdist == 1 and piece_moved.color == BLACK:
                    return True
                elif vdist == 2 and piece_moved.color == BLACK and initial_loc.row == 1 and not self.board.get(initial_loc.get_diff([1, 0])):
                    return True
            elif abs(hdist) == 1 and piece_captured:
                if vdist == -1 and piece_moved.color == WHITE and piece_captured.color == BLACK:
                    return True
                elif vdist == 1 and piece_moved.color == BLACK and piece_captured.color == WHITE:
                    return True
            elif abs(hdist) == 1 and self.board.en_passant[0] is True:
                if vdist == -1 and piece_moved.color == WHITE and final_loc == self.board.en_passant[1] and self.board.en_passant[2].color == BLACK:
                    return True
                elif vdist == 1 and piece_moved.color == BLACK and final_loc == self.board.en_passant[1] and self.board.en_passant[2].color == WHITE:
                    return True
        elif piece_moved.piece_type == KNIGHT:
            if (abs(hdist) == 2 and abs(vdist) == 1) or (abs(hdist) == 1 and abs(vdist) == 2):
                return True
        elif piece_moved.piece_type == BISHOP:
            if abs(hdist) == abs(vdist):
                # check if path is clear
                rows = range(initial_loc.row, final_loc.row, -1 if final_loc.row < initial_loc.row else 1)
                cols = range(initial_loc.col, final_loc.col, -1 if final_loc.col < initial_loc.col else 1)

                blocked = False
                for row, col in zip(rows, cols):
                    if self.board.get(Square((row, col))) not in [None, piece_moved, piece_captured]:
                        blocked = True

                if not blocked:
                    return True
        elif piece_moved.piece_type == ROOK:
            if hdist == 0 and vdist != 0:
                # check if path is clear
                rows = range(min(initial_loc.row, final_loc.row), max(initial_loc.row, final_loc.row))[1:]
                col = initial_loc.col

                blocked = False
                for row in rows:
                    if self.board.get(Square((row, col))) is not None:
                        blocked = True

                if not blocked:
                    return True
            elif hdist != 0 and vdist == 0:
                # check if path is clear
                row = initial_loc.row
                cols = range(min(initial_loc.col, final_loc.col), max(initial_loc.col, final_loc.col))[1:]

                blocked = False
                for col in cols:
                    if self.board.get(Square((row, col))) is not None:
                        blocked = True

                if not blocked:
                    return True
        elif piece_moved.piece_type == QUEEN:
            if abs(hdist) == abs(vdist):
                # check if path is clear
                rows = range(initial_loc.row, final_loc.row, -1 if final_loc.row < initial_loc.row else 1)
                cols = range(initial_loc.col, final_loc.col, -1 if final_loc.col < initial_loc.col else 1)

                blocked = False
                for row, col in zip(rows, cols):
                    if self.board.get(Square((row, col))) not in [None, piece_moved, piece_captured]:
                        blocked = True

                if not blocked:
                    return True
            elif hdist == 0 and vdist != 0:
                # check if path is clear
                rows = range(min(initial_loc.row, final_loc.row), max(initial_loc.row, final_loc.row))[1:]
                col = initial_loc.col

                blocked = False
                for row in rows:
                    if self.board.get(Square((row, col))) is not None:
                        blocked = True

                if not blocked:
                    return True
            elif hdist != 0 and vdist == 0:
                # check if path is clear
                row = initial_loc.row
                cols = range(min(initial_loc.col, final_loc.col), max(initial_loc.col, final_loc.col))[1:]

                blocked = False
                for col in cols:
                    if self.board.get(Square((row, col))) is not None:
                        blocked = True

                if not blocked:
                    return True
        elif piece_moved.piece_type == KING:
            if -1 <= hdist <= 1 and -1 <= vdist <= 1:
                if piece_moved.color == WHITE and not self.is_targeted(targeting_color=BLACK, targeted_square=final_loc):
                    return True
                elif not self.is_targeted(targeting_color=WHITE, targeted_square=final_loc):
                    return True
            elif self.board.castling[0] and piece_moved.color == WHITE and final_loc == Square.from_name("g1"):
                if not self.board.get("f1") and not self.board.get("g1") and \
                        not self.is_targeted(targeting_color=BLACK, targeted_square=Square.from_name("f1")) and \
                        not self.is_targeted(targeting_color=BLACK, targeted_square=Square.from_name("g1")):
                    return True
            elif self.board.castling[1] and piece_moved.color == WHITE and final_loc == Square.from_name("c1"):
                if not self.board.get("d1") and not self.board.get("c1") and not self.board.get("b1") and \
                        not self.is_targeted(targeting_color=BLACK, targeted_square=Square.from_name("d1")) and \
                        not self.is_targeted(targeting_color=BLACK, targeted_square=Square.from_name("c1")) and \
                        not self.is_targeted(targeting_color=BLACK, targeted_square=Square.from_name("b1")):
                    return True
            elif self.board.castling[2] and piece_moved.color == BLACK and final_loc == Square.from_name("g8"):
                if not self.board.get("f8") and not self.board.get("g8") and \
                        not self.is_targeted(targeting_color=WHITE, targeted_square=Square.from_name("f8")) and \
                        not self.is_targeted(targeting_color=WHITE, targeted_square=Square.from_name("g8")):
                    return True
            elif self.board.castling[3] and piece_moved.color == BLACK and final_loc == Square.from_name("c8"):
                if not self.board.get("d8") and not self.board.get("c8") and not self.board.get("b8") and \
                        not self.is_targeted(targeting_color=WHITE, targeted_square=Square.from_name("d8")) and \
                        not self.is_targeted(targeting_color=WHITE, targeted_square=Square.from_name("c8")) and \
                        not self.is_targeted(targeting_color=WHITE, targeted_square=Square.from_name("b8")):
                    return True

        return legal

    def is_targeted(self, targeting_color, targeted_square: Square, check_if_exposes_king=True) -> bool:
        targeting_pieces = [piece for piece in self.board.pieces if piece.color == targeting_color and piece.captured is False]

        for piece in targeting_pieces:
            hdist = targeted_square.col - piece.square.col
            vdist = targeted_square.row - piece.square.row

            if piece.piece_type == PAWN:
                if targeting_color == WHITE:
                    if abs(hdist) == 1 and vdist == -1:
                        return True
                elif targeting_color == BLACK:
                    if abs(hdist) == 1 and vdist == 1:
                        return True
            elif piece.piece_type in [KNIGHT, BISHOP, ROOK, QUEEN]:
                if self.is_move_legal(Move(piece.square, targeted_square, piece), check_if_exposes_king=check_if_exposes_king):
                    return True
            elif piece.piece_type == KING:
                if -1 <= hdist <= 1 and -1 <= vdist <= 1:
                    return True

        return False

    def check_if_game_ended(self):
        moves = self.generate_legal_moves_for(self.turn)

        if len(moves) == 0:
            if self.turn == WHITE:
                if self.is_targeted(BLACK, self.board.white_king.square, check_if_exposes_king=False):
                    return CHECKMATE
                else:
                    return STALEMATE
            else:
                if self.is_targeted(WHITE, self.board.black_king.square, check_if_exposes_king=False):
                    return CHECKMATE
                else:
                    return STALEMATE

    def correct_en_passant(self, move: Move) -> Move:
        initial_loc = move.initial_loc
        final_loc = move.final_loc
        piece_moved = move.piece_moved
        promotion = move.promotion

        hdist = final_loc.col - initial_loc.col
        vdist = final_loc.row - initial_loc.row

        if piece_moved.piece_type == PAWN:
            if self.board.en_passant[0]:
                if abs(hdist) == 1:
                    if vdist == -1 and piece_moved.color == WHITE and final_loc == self.board.en_passant[1] and self.board.en_passant[2].color == BLACK:
                        move = Move(initial_loc, final_loc, piece_moved, piece_captured=self.board.en_passant[2], promotion=promotion)
                    elif vdist == 1 and piece_moved.color == BLACK and final_loc == self.board.en_passant[1] and self.board.en_passant[2].color == WHITE:
                        move = Move(initial_loc, final_loc, piece_moved, piece_captured=self.board.en_passant[2], promotion=promotion)

        return move

    def move(self, move):
        move = self.correct_en_passant(move)
        self.board.apply_move(move)
        self.moves.append(move)
        self.turn *= -1

    def generate_legal_squares_to_move_to_for(self, piece: Piece):
        all_squares = []
        squares = []
        if piece.piece_type == PAWN:
            if piece.color == WHITE:
                diffs = [[-1, 0], [-2, 0], [-1, -1], [-1, 1]]
                all_squares = [piece.square.get_diff(diff) for diff in diffs if Square.is_valid(piece.square.get_diff(diff))]
            else:
                diffs = [[1, 0], [2, 0], [1, -1], [1, 1]]
                all_squares = [piece.square.get_diff(diff) for diff in diffs if Square.is_valid(piece.square.get_diff(diff))]
        elif piece.piece_type == KNIGHT:
            diffs = [[-2, -1], [-2, 1], [-1, -2], [-1, 2], [1, -2], [1, 2], [2, -1], [2, 1]]
            all_squares = [piece.square.get_diff(diff) for diff in diffs if Square.is_valid(piece.square.get_diff(diff))]
        elif piece.piece_type == BISHOP:
            diffs = [[a, a] for a in range(-7, 8) if a != 0]
            diffs.extend([[a, -a] for a in range(-7, 8) if a != 0])
            all_squares = [piece.square.get_diff(diff) for diff in diffs if Square.is_valid(piece.square.get_diff(diff))]
        elif piece.piece_type == ROOK:
            diffs = [[a, 0] for a in range(-7, 8) if a != 0]
            diffs.extend([[0, a] for a in range(-7, 8) if a != 0])
            all_squares = [piece.square.get_diff(diff) for diff in diffs if Square.is_valid(piece.square.get_diff(diff))]
        elif piece.piece_type == QUEEN:
            diffs = [[a, a] for a in range(-7, 8) if a != 0]
            diffs.extend([[a, -a] for a in range(-7, 8) if a != 0])
            diffs.extend([[a, 0] for a in range(-7, 8) if a != 0])
            diffs.extend([[0, a] for a in range(-7, 8) if a != 0])
            all_squares = [piece.square.get_diff(diff) for diff in diffs if Square.is_valid(piece.square.get_diff(diff))]
        elif piece.piece_type == KING:
            diffs = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1], [0, 2], [0, -3]]
            all_squares = [piece.square.get_diff(diff) for diff in diffs if Square.is_valid(piece.square.get_diff(diff))]

        for square in all_squares:
            move = self.correct_en_passant(Move(piece.square, square, piece, self.board.get(square)))
            if self.is_move_legal(move):
                squares.append(square)

        return squares

    def generate_legal_moves_for(self, color):
        pieces = [piece for piece in self.board.pieces if piece.color == color and piece.captured is False]
        moves = []
        for piece in pieces:
            final_locs = []
            if piece.piece_type == PAWN:
                if color == WHITE:
                    diffs = [[-1, 0], [-2, 0], [-1, -1], [-1, 1]]
                    final_locs = [piece.square.get_diff(diff) for diff in diffs if Square.is_valid(piece.square.get_diff(diff))]
                else:
                    diffs = [[1, 0], [2, 0], [1, -1], [1, 1]]
                    final_locs = [piece.square.get_diff(diff) for diff in diffs if Square.is_valid(piece.square.get_diff(diff))]
            elif piece.piece_type == KNIGHT:
                diffs = [[-2, -1], [-2, 1], [-1, -2], [-1, 2], [1, -2], [1, 2], [2, -1], [2, 1]]
                final_locs = [piece.square.get_diff(diff) for diff in diffs if Square.is_valid(piece.square.get_diff(diff))]
            elif piece.piece_type == BISHOP:
                diffs = [[a, a] for a in range(-7, 8) if a != 0]
                diffs.extend([[a, -a] for a in range(-7, 8) if a != 0])
                final_locs = [piece.square.get_diff(diff) for diff in diffs if Square.is_valid(piece.square.get_diff(diff))]
            elif piece.piece_type == ROOK:
                diffs = [[a, 0] for a in range(-7, 8) if a != 0]
                diffs.extend([[0, a] for a in range(-7, 8) if a != 0])
                final_locs = [piece.square.get_diff(diff) for diff in diffs if Square.is_valid(piece.square.get_diff(diff))]
            elif piece.piece_type == QUEEN:
                diffs = [[a, a] for a in range(-7, 8) if a != 0]
                diffs.extend([[a, -a] for a in range(-7, 8) if a != 0])
                diffs.extend([[a, 0] for a in range(-7, 8) if a != 0])
                diffs.extend([[0, a] for a in range(-7, 8) if a != 0])
                final_locs = [piece.square.get_diff(diff) for diff in diffs if Square.is_valid(piece.square.get_diff(diff))]
            elif piece.piece_type == KING:
                diffs = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1], [0, 2], [0, -3]]
                final_locs = [piece.square.get_diff(diff) for diff in diffs if Square.is_valid(piece.square.get_diff(diff))]

            for final_loc in final_locs:
                move = self.correct_en_passant(Move(piece.square, final_loc, piece, self.board.get(final_loc)))
                if self.is_move_legal(move):
                    moves.append(move)

        return moves
