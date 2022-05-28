import os
import sys

import pygame as pg

from model import *


def is_valid_input(square_name: str):
    return len(square_name) == 2 and square_name[0].lower() in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] and square_name[1] in ['1', '2', '3', '4', '5', '6', '7', '8']


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def draw_board(x, y, width, height, win, game, perspective):
    global square_to_move_from
    square_width = width // 8
    square_height = height // 8
    for row in range(8):
        for col in range(8):
            white = (row + col) % 2 == 0
            square = pg.Rect(col * square_width + x, row * square_height + y, square_width, square_height)
            pg.draw.rect(win, (9 * 16 + 10, 7 * 16 + 11, 4 * 16 + 15) if white else (3 * 16 + 7, 1 * 16 + 13, 1 * 16), square)

    for piece in game.board.pieces:
        if not piece.captured:
            piece_image = piece_images[str(piece)]
            col = piece.square.col
            row = piece.square.row

            if perspective == WHITE:
                win.blit(piece_image, (col * square_width + x, row * square_height + y))
            else:
                win.blit(piece_image, ((7 - col) * square_width + x, (7 - row) * square_height + y))

    if square_to_move_from:
        piece = game.board.get(square_to_move_from)
        for square in game.generate_legal_squares_to_move_to_for(piece):
            col = square.col
            row = square.row

            if perspective == WHITE:
                pg.draw.circle(win, (64, 64, 64), (col * square_width + x + 50, row * square_height + y + 50), 20)
            else:
                pg.draw.circle(win, (64, 64, 64), ((7 - col) * square_width + x + 50, (7 - row) * square_height + y + 50), 20)


def draw_move_list(x, y, width, height, win, game):
    font = pg.font.SysFont("bahnschrift", 20)
    square = pg.Rect(x, y, width, height)
    pg.draw.rect(win, (50, 50, 50), square)

    for i, group in enumerate(chunker(game.moves, 2)):
        win.blit(font.render(f"{i + 1}. ", True, (200, 200, 200)), (x + 10, y + 10 + 20 * i))
        win.blit(font.render(group[0].to_algebraic_notation(), True, (200, 200, 200)), (x + 50, y + 10 + + 20 * i))
        if len(group) == 2:
            win.blit(font.render(group[1].to_algebraic_notation(), True, (200, 200, 200)), (x + 150, y + 10 + 20 * i))


def render(win, game, perspective=WHITE):
    draw_board(BOARD_OFFSET_X, BOARD_OFFSET_Y, BOARD_WIDTH, BOARD_HEIGHT, win, game, perspective)
    draw_move_list(MOVE_LIST_OFFSET_X, MOVE_LIST_OFFSET_Y, MOVE_LIST_WIDTH, MOVE_LIST_HEIGHT, win, game)

    pg.display.update()


def main():
    pg.init()
    pg.display.set_caption("Chess")
    win = pg.display.set_mode((WIDTH, HEIGHT))

    game = Game()
    running = True

    global square_to_move_from

    square_to_move_from = None
    square_to_move_to = None
    turn = WHITE

    while running:
        render(win, game, perspective=turn)

        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN:
                pos = event.dict['pos']
                row = (pos[1] - BOARD_OFFSET_Y) // (BOARD_WIDTH // 8)
                col = (pos[0] - BOARD_OFFSET_X) // (BOARD_HEIGHT // 8)

                if turn == WHITE:
                    square = Square((row, col))
                else:
                    square = Square((7 - row, 7 - col))

                if game.board.get(square) and game.board.get(square).color == turn:
                    square_to_move_from = square
                elif not square_to_move_to:
                    square_to_move_to = square
            elif event.type == pg.MOUSEBUTTONUP:
                pos = event.dict['pos']
                row = (pos[1] - BOARD_OFFSET_Y) // (BOARD_WIDTH // 8)
                col = (pos[0] - BOARD_OFFSET_X) // (BOARD_HEIGHT // 8)

                if turn == WHITE:
                    square = Square((row, col))
                else:
                    square = Square((7 - row, 7 - col))

                if square_to_move_from and not square_to_move_to and square_to_move_from != square:
                    square_to_move_to = square

        if square_to_move_from is not None and square_to_move_to is not None:
            # Promotion
            piece_moved = game.board.get(square_to_move_from)
            promotion_value = None
            if piece_moved.piece_type == PAWN:
                if piece_moved.color == WHITE:
                    if square_to_move_to.row == 0:
                        promotion_value = QUEEN
                else:
                    if square_to_move_to.row == 7:
                        promotion_value = QUEEN

            move = Move(
                initial_loc=square_to_move_from,
                final_loc=square_to_move_to,
                piece_moved=game.board.get(square_to_move_from),
                piece_captured=game.board.get(square_to_move_to),
                promotion=promotion_value
            )
            move = game.correct_en_passant(move)
            move_success = game.is_move_legal(move)

            if move_success:
                game.move(move)

                if game.check_if_game_ended() == CHECKMATE:
                    print(f'Checkmate! {"WHITE" if turn == WHITE else "BLACK"} won!')
                    game.moves[-1].mate = True
                    running = False
                elif game.check_if_game_ended() == STALEMATE:
                    print("Stalemate!")
                    running = False
                elif turn == WHITE:
                    if game.is_targeted(WHITE, game.board.black_king.square, check_if_exposes_king=False):
                        game.moves[-1].check = True
                elif turn == BLACK:
                    if game.is_targeted(BLACK, game.board.white_king.square, check_if_exposes_king=False):
                        game.moves[-1].check = True

                turn *= -1

            square_to_move_from = None
            square_to_move_to = None

    for _ in range(2 * 30):
        pg.event.pump()
        render(win, game, perspective=turn)
        pg.time.Clock().tick(30)


def rss_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


if __name__ == '__main__':
    WIDTH = 1300
    HEIGHT = 900

    BOARD_OFFSET_X = 20
    BOARD_OFFSET_Y = 50
    BOARD_WIDTH = 800
    BOARD_HEIGHT = 800

    MOVE_LIST_OFFSET_X = BOARD_OFFSET_X + BOARD_WIDTH + 20
    MOVE_LIST_OFFSET_Y = 50
    MOVE_LIST_WIDTH = 440
    MOVE_LIST_HEIGHT = 800

    piece_images = {image[1]: pg.transform.smoothscale(pg.image.load(rss_path(f'assets/{image}')), (100, 100)) for image in os.listdir(rss_path("assets"))}

    square_to_move_from = None
    main()
