import copy
from typing import List

import numpy as np

PAWN = 0
KNIGHT = 1
BISHOP = 2
ROOK = 3
QUEEN = 4
KING = 5

piece_types = [PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING]

WHITE = -1
BLACK = 1

piece_colors = [WHITE, BLACK]


class Piece:
    def __init__(self, piece_type, color, square):
        self.piece_type = piece_type
        self.color = color

        if type(square) == Square:
            self.square = square
        elif type(square) == str:
            self.square = Square.from_name(square)
        else:
            raise Exception("Square value passed to piece in __init__() is invalid.")

        self.captured = False

    def move(self, square):
        if type(square) == Square:
            self.square = square
        elif type(square) == str:
            self.square = Square.from_name(square)
        else:
            raise Exception("Square value passed to piece in move() is invalid.")

    def promote(self, piece):
        if self.piece_type == PAWN:
            self.piece_type = piece

    def __str__(self, short=True):
        # short: R
        # long: eg. R (7, 7)/(h1)
        letters = ['p', 'n', 'b', 'r', 'q', 'k']
        letter = letters[self.piece_type]

        if self.color == WHITE:
            letter = letter.upper()

        if short:
            return letter
        else:
            raise NotImplementedError("long version of __str__ for piece not yet implemented")

    def __repr__(self):
        letters = ['p', 'n', 'b', 'r', 'q', 'k']
        letter = letters[self.piece_type]

        if self.color == WHITE:
            letter = letter.upper()

        if self.captured:
            captured = "CAPTURED"
        else:
            captured = "IN PLAY"

        return f"{letter}({self.square})[{captured}]"


class Square(tuple):
    def __init__(self, tup: tuple):
        self.row = tup[0]
        self.col = tup[1]
        self.coords = tup

    @classmethod
    def from_tuple(cls, tup: tuple):
        return cls(tup)

    @classmethod
    def from_name(cls, name):
        return cls(cls.convert_to_coords(name))

    def convert_to_name(self):
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        ranks = ['8', '7', '6', '5', '4', '3', '2', '1']

        file = files[self.col]
        rank = ranks[self.row]

        return file + rank

    @staticmethod
    def convert_to_coords(name):
        file = name[0].lower()
        rank = name[1]

        files = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
        ranks = {'8': 0, '7': 1, '6': 2, '5': 3, '4': 4, '3': 5, '2': 6, '1': 7}

        row = ranks[rank]
        col = files[file]

        return row, col

    def __str__(self):
        return self.convert_to_name()

    def __repr__(self):
        return self.convert_to_name()

    def __eq__(self, other):
        return self.coords == other.coords


class Move:
    def __init__(self, initial_loc: Square, final_loc: Square, piece_moved: Piece, piece_captured=None, promotion=None):
        self.initial_loc = initial_loc
        self.final_loc = final_loc
        self.piece_moved = piece_moved
        self.piece_captured = piece_captured
        self.promotion = promotion


class Board:
    def __init__(self):
        self.board, self.pieces = self.initialize()
        self.castling = [True] * 4  # white kingside, white queenside, black kingside, black queenside
        self.en_passent: List[bool, Square, Piece] = [False, None, None]

    @property
    def white_king(self) -> Piece:
        return self.pieces[20]

    @property
    def black_king(self):
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

    def print_board(self):
        for row in range(8):
            print(8 - row, end=" ")
            for col in range(8):
                val = self.board[row, col]
                if val is not None:
                    print(val, end=" ")
                else:
                    print("-", end=" ")
            print()
        print("  a b c d e f g h")
        print()

    def apply_move(self, move: Move):
        initial_loc = move.initial_loc
        final_loc = move.final_loc
        piece_moved = move.piece_moved
        piece_captured: Piece = move.piece_captured
        promotion = move.promotion

        self.board[initial_loc] = None
        self.board[piece_moved.square] = None

        if piece_captured is not None:
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

        if piece_captured is not None:
            piece_captured.captured = True

        if promotion is not None:
            piece_moved.promote(promotion)

        self.en_passent: List[bool, Square, Piece] = [False, None, None]
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
        elif piece_moved.piece_type == KING:
            if piece_moved.color == WHITE:
                self.castling[:2] = [False] * 2
            else:
                self.castling[2:] = [False] * 2
        elif piece_moved.piece_type == PAWN:
            if abs(final_loc.coords[0] - initial_loc.coords[0]) == 2:
                if piece_moved.color == WHITE:
                    self.en_passent = [True, Square.from_tuple((initial_loc.row - 1, initial_loc.col)), piece_moved]
                else:
                    self.en_passent = [True, Square.from_tuple((initial_loc.row + 1, initial_loc.col)), piece_moved]

        self.verify()

    def verify(self):
        for row in range(8):
            for col in range(8):
                piece: Piece = self.board[row, col]
                if piece is not None:
                    if piece.square != Square.from_tuple((row, col)):
                        raise Exception("The board positions and the pieces' internal positions do not match")

    def get(self, square):
        if type(square) == Square:
            return self.board[square.row, square.col]
        elif type(square) == str:
            square = Square.from_name(square)
            return self.board[square]

    def __repr__(self):
        return f"{self.board}\n{self.pieces}\n{self.castling}\n{self.en_passent}"


class GameRules:
    @staticmethod
    def is_move_legal(board: Board, move: Move, check_if_exposes_king=True):
        initial_loc = move.initial_loc
        final_loc = move.final_loc
        piece_moved = move.piece_moved
        piece_captured: Piece = move.piece_captured
        promotion = move.promotion

        legal = False

        hdist = final_loc.col - initial_loc.col
        vdist = final_loc.row - initial_loc.row

        if piece_moved.piece_type == PAWN:
            if hdist == 0 and vdist == 0 and promotion is not None:
                legal = True
            elif hdist == 0 and piece_captured is None:
                if vdist == -1 and piece_moved.color == WHITE:
                    legal = True
                elif vdist == -2 and piece_moved.color == WHITE and initial_loc.row == 6 and board.get(
                        Square.from_tuple((initial_loc.row - 1, initial_loc.col))) is None:
                    legal = True
                elif vdist == 1 and piece_moved.color == BLACK:
                    legal = True
                elif vdist == 2 and piece_moved.color == BLACK and initial_loc.row == 1 and board.get(
                        Square.from_tuple((initial_loc.row + 1, initial_loc.col))) is None:
                    legal = True
            elif abs(hdist) == 1 and piece_captured is not None:
                if vdist == -1 and piece_moved.color == WHITE and piece_captured.color == BLACK:
                    legal = True
                elif vdist == 1 and piece_moved.color == BLACK and piece_captured.color == WHITE:
                    legal = True
            elif abs(hdist) == 1 and board.en_passent[0] is True:
                if vdist == -1 and piece_moved.color == WHITE and final_loc == board.en_passent[1] and board.en_passent[2].color == BLACK:
                    legal = True
                elif vdist == 1 and piece_moved.color == BLACK and final_loc == board.en_passent[1] and board.en_passent[2].color == WHITE:
                    legal = True
        elif piece_moved.piece_type == KNIGHT:
            if (abs(hdist) == 2 and abs(vdist) == 1) or (abs(hdist) == 1 and abs(vdist) == 2):
                if piece_captured is None:
                    legal = True
                elif piece_moved.color != piece_captured.color:
                    legal = True
        elif piece_moved.piece_type == BISHOP:
            if abs(hdist) == abs(vdist):
                # check if path is clear
                rows = range(initial_loc.row, final_loc.row, -1 if final_loc.row < initial_loc.row else 1)
                cols = range(initial_loc.col, final_loc.col, -1 if final_loc.col < initial_loc.col else 1)

                blocked = False
                for row, col in zip(rows, cols):
                    if board.get(Square.from_tuple((row, col))) not in [None, piece_moved, piece_captured]:
                        blocked = True

                if not blocked:
                    if piece_captured is None:
                        legal = True
                    elif piece_moved.color != piece_captured.color:
                        legal = True
        elif piece_moved.piece_type == ROOK:
            if hdist == 0 and vdist != 0:
                # check if path is clear
                rows = range(min(initial_loc.row, final_loc.row), max(initial_loc.row, final_loc.row))[1:]
                col = initial_loc.col

                blocked = False
                for row in rows:
                    if board.get(Square.from_tuple((row, col))) is not None:
                        blocked = True

                if not blocked:
                    if piece_captured is None:
                        legal = True
                    elif piece_moved.color != piece_captured.color:
                        legal = True
            elif hdist != 0 and vdist == 0:
                # check if path is clear
                row = initial_loc.row
                cols = range(min(initial_loc.col, final_loc.col), max(initial_loc.col, final_loc.col))[1:]

                blocked = False
                for col in cols:
                    if board.get(Square.from_tuple((row, col))) is not None:
                        blocked = True

                if not blocked:
                    if piece_captured is None:
                        legal = True
                    elif piece_moved.color != piece_captured.color:
                        legal = True
        elif piece_moved.piece_type == QUEEN:
            if abs(hdist) == abs(vdist):
                # check if path is clear
                rows = range(initial_loc.row, final_loc.row, -1 if final_loc.row < initial_loc.row else 1)
                cols = range(initial_loc.col, final_loc.col, -1 if final_loc.col < initial_loc.col else 1)

                blocked = False
                for row, col in zip(rows, cols):
                    if board.get(Square.from_tuple((row, col))) not in [None, piece_moved, piece_captured]:
                        blocked = True

                if not blocked:
                    if piece_captured is None:
                        legal = True
                    elif piece_moved.color != piece_captured.color:
                        legal = True
            elif hdist == 0 and vdist != 0:
                # check if path is clear
                rows = range(min(initial_loc.row, final_loc.row), max(initial_loc.row, final_loc.row))[1:]
                col = initial_loc.col

                blocked = False
                for row in rows:
                    if board.get(Square.from_tuple((row, col))) is not None:
                        blocked = True

                if not blocked:
                    if piece_captured is None:
                        legal = True
                    elif piece_moved.color != piece_captured.color:
                        legal = True
            elif hdist != 0 and vdist == 0:
                # check if path is clear
                row = initial_loc.row
                cols = range(min(initial_loc.col, final_loc.col), max(initial_loc.col, final_loc.col))[1:]

                blocked = False
                for col in cols:
                    if board.get(Square.from_tuple((row, col))) is not None:
                        blocked = True

                if not blocked:
                    if piece_captured is None:
                        legal = True
                    elif piece_moved.color != piece_captured.color:
                        legal = True
        elif piece_moved.piece_type == KING:
            if -1 <= hdist <= 1 and -1 <= vdist <= 1:
                if piece_moved.color == WHITE and not GameRules.is_targeted(board=board, targeting_color=BLACK, targeted_square=final_loc):
                    if piece_captured is None:
                        legal = True
                    elif piece_moved.color != piece_captured.color:
                        legal = True
                elif not GameRules.is_targeted(board=board, targeting_color=WHITE, targeted_square=final_loc):
                    if piece_captured is None:
                        legal = True
                    elif piece_moved.color != piece_captured.color:
                        legal = True
            elif board.castling[0] and piece_moved.color == WHITE and final_loc == Square.from_name("g1"):
                if board.get("f1") is None and board.get("g1") is None and \
                        not GameRules.is_targeted(board=board, targeting_color=BLACK, targeted_square=Square.from_name("f1")) and \
                        not GameRules.is_targeted(board=board, targeting_color=BLACK, targeted_square=Square.from_name("g1")):
                    legal = True
            elif board.castling[1] and piece_moved.color == WHITE and final_loc == Square.from_name("c1"):
                if board.get("d1") is None and board.get("c1") is None and board.get("b1") is None and \
                        not GameRules.is_targeted(board=board, targeting_color=BLACK, targeted_square=Square.from_name("d1")) and \
                        not GameRules.is_targeted(board=board, targeting_color=BLACK, targeted_square=Square.from_name("c1")) and \
                        not GameRules.is_targeted(board=board, targeting_color=BLACK, targeted_square=Square.from_name("b1")):
                    legal = True
            elif board.castling[2] and piece_moved.color == BLACK and final_loc == Square.from_name("g8"):
                if board.get("f8") is None and board.get("g8") is None and \
                        not GameRules.is_targeted(board=board, targeting_color=WHITE, targeted_square=Square.from_name("f8")) and \
                        not GameRules.is_targeted(board=board, targeting_color=WHITE, targeted_square=Square.from_name("g8")):
                    legal = True
            elif board.castling[3] and piece_moved.color == BLACK and final_loc == Square.from_name("c8"):
                if board.get("d8") is None and board.get("c8") is None and board.get("b8") is None and \
                        not GameRules.is_targeted(board=board, targeting_color=WHITE, targeted_square=Square.from_name("d8")) and \
                        not GameRules.is_targeted(board=board, targeting_color=WHITE, targeted_square=Square.from_name("c8")) and \
                        not GameRules.is_targeted(board=board, targeting_color=WHITE, targeted_square=Square.from_name("b8")):
                    legal = True

        if legal and check_if_exposes_king:
            test_board = copy.deepcopy(board)
            test_move = copy.deepcopy(move)

            test_move.piece_moved = test_board.pieces[board.pieces.index(piece_moved)]
            if piece_captured is not None:
                test_move.piece_captured = test_board.pieces[board.pieces.index(piece_captured)]

            test_board.apply_move(test_move)

            if piece_moved.color == WHITE:
                if GameRules.white_king_checked(test_board):
                    legal = False
            else:
                if GameRules.black_king_checked(test_board):
                    legal = False

        return legal

    @staticmethod
    def is_targeted(board, targeting_color, targeted_square: Square):
        targeting_pieces = [piece for piece in board.pieces if piece.color == targeting_color and piece.captured is False]

        # targeted_piece_placeholder = Piece(PAWN, BLACK, targeted_square)
        # if targeting_color == BLACK:
        #     targeted_piece_placeholder.color = WHITE

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
                if GameRules.is_move_legal(board, Move(piece.square, targeted_square, piece)):
                    return True
            elif piece.piece_type == KING:
                if -1 <= hdist <= 1 and -1 <= vdist <= 1:
                    return True

        return False

    @staticmethod
    def white_king_checked(board):
        targeting_pieces = [piece for piece in board.pieces if piece.color == BLACK and piece.captured is False]

        white_king: Piece = board.white_king

        for piece in targeting_pieces:
            hdist = white_king.square.col - piece.square.col
            vdist = white_king.square.row - piece.square.row

            if piece.piece_type == PAWN:
                if abs(hdist) == 1 and vdist == 1:
                    return True
            elif piece.piece_type in [KNIGHT, BISHOP, ROOK, QUEEN]:
                if GameRules.is_move_legal(board, Move(piece.square, white_king.square, piece, white_king), check_if_exposes_king=False):
                    return True
            elif piece.piece_type == KING:
                if -1 <= hdist <= 1 and -1 <= vdist <= 1:
                    return True

        return False

    @staticmethod
    def black_king_checked(board):
        targeting_pieces = [piece for piece in board.pieces if piece.color == WHITE and piece.captured is False]

        black_king: Piece = board.black_king

        for piece in targeting_pieces:
            hdist = black_king.square.col - piece.square.col
            vdist = black_king.square.row - piece.square.row

            if piece.piece_type == PAWN:
                if abs(hdist) == 1 and vdist == -1:
                    return True
            elif piece.piece_type in [KNIGHT, BISHOP, ROOK, QUEEN]:
                if GameRules.is_move_legal(board, Move(piece.square, black_king.square, piece, black_king), check_if_exposes_king=False):
                    return True
            elif piece.piece_type == KING:
                if -1 <= hdist <= 1 and -1 <= vdist <= 1:
                    return True

        return False


class Game:
    def __init__(self):
        self.board = Board()
        self.move_list = []
        self.turn = WHITE

    def move(self, from_square, to_square, promotion=None):
        iMove = Move(
            Square.from_name(from_square),
            Square.from_name(to_square),
            self.board.get(Square.from_name(from_square)),
            self.board.get(Square.from_name(to_square)),
            promotion=promotion
        )
        move = self._correct_move(self.board, iMove)

        if move.piece_moved.color != self.turn:
            print(f"It is not your turn!\n")
            return

        is_move_legal = GameRules.is_move_legal(self.board, move)

        if not is_move_legal:
            print(f"{from_square} to {to_square} is an illegal move!\nTry Again!\n")
            return

        self.board.apply_move(move)
        self.move_list.append(move)
        self.turn *= -1

    @staticmethod
    def _correct_move(board: Board, move: Move) -> Move:
        initial_loc = move.initial_loc
        final_loc = move.final_loc
        piece_moved = move.piece_moved
        piece_captured: Piece = move.piece_captured
        promotion = move.promotion

        if piece_moved is None:
            raise Exception("No piece selected to be moved")
        elif initial_loc == final_loc:
            raise Exception("The piece to be moved is not moving")

        hdist = final_loc.col - initial_loc.col
        vdist = final_loc.row - initial_loc.row

        if piece_moved.piece_type == PAWN:
            if board.en_passent[0] is True:
                if abs(hdist) == 1:
                    if vdist == -1 and piece_moved.color == WHITE and final_loc == board.en_passent[1] and board.en_passent[2].color == BLACK:
                        move = Move(initial_loc, final_loc, piece_moved, piece_captured=board.en_passent[2], promotion=promotion)
                    elif vdist == 1 and piece_moved.color == BLACK and final_loc == board.en_passent[1] and board.en_passent[2].color == WHITE:
                        move = Move(initial_loc, final_loc, piece_moved, piece_captured=board.en_passent[2], promotion=promotion)

        return move

    def force_move(self, from_square, to_square, promotion=None):
        m = Move(
            Square.from_name(from_square),
            Square.from_name(to_square),
            self.board.get(Square.from_name(from_square)),
            self.board.get(Square.from_name(to_square)),
            promotion=promotion
        )
        self.board.apply_move(m)

    def display(self):
        self.board.print_board()


# b = Board()
#
#
# def correct_move(board: Board, move: Move) -> Move:
#     initial_loc = move.initial_loc
#     final_loc = move.final_loc
#     piece_moved = move.piece_moved
#     piece_captured: Piece = move.piece_captured
#     promotion = move.promotion
#
#     if piece_moved is None:
#         raise Exception("No piece selected to be moved")
#     elif initial_loc == final_loc:
#         raise Exception("The piece to be moved is not moving")
#
#     hdist = final_loc.col - initial_loc.col
#     vdist = final_loc.row - initial_loc.row
#
#     if piece_moved.piece_type == PAWN:
#         if board.en_passent[0] is True:
#             if abs(hdist) == 1:
#                 if vdist == -1 and piece_moved.color == WHITE and final_loc == board.en_passent[1] and board.en_passent[2].color == BLACK:
#                     move = Move(initial_loc, final_loc, piece_moved, piece_captured=board.en_passent[2], promotion=promotion)
#                 elif vdist == 1 and piece_moved.color == BLACK and final_loc == board.en_passent[1] and board.en_passent[2].color == WHITE:
#                     move = Move(initial_loc, final_loc, piece_moved, piece_captured=board.en_passent[2], promotion=promotion)
#
#     return move
#
#
# def move(f, t, p=None):
#     m = Move(Square.from_name(f), Square.from_name(t), b.get(Square.from_name(f)), b.get(Square.from_name(t)), promotion=p)
#     m = correct_move(b, m)
#     legal = GameRules.is_move_legal(b, m)
#
#     if not legal:
#         print(f"{f} to {t} is an illegal move!\nTry Again!\n")
#         return
#
#     b.apply_move(m)
#     b.print_board()
#
#
# def force_move(f, t, p=None):
#     m = Move(Square.from_name(f), Square.from_name(t), b.get(Square.from_name(f)), b.get(Square.from_name(t)), promotion=p)
#     b.apply_move(m)
#     b.verify()
#     b.print_board()
#
#
# move("e2", "e4")
# move("e7", "e5")
# move("g1", "f3")
# move("b8", "c6")
# move("f1", "b5")
# move("a7", "a6")
# move("e1", "g1")
# move("d7", "d5")
# move("c8", "d7")
# move("d8", "e7")
# move("e8", "c8")


g = Game()
g.move("e2", "e4")
g.display()
g.move("e7", "e5")
g.display()
g.move("g1", "f3")
g.display()
g.move("b8", "c6")
g.display()
g.move("f1", "b5")
g.display()
g.move("b5", "c6")
g.display()