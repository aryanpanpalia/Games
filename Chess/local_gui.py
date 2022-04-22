import pygame as pg

from model import *


def is_valid_input(square_name: str):
    return len(square_name) == 2 and square_name[0].lower() in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] and square_name[1] in ['1', '2', '3', '4', '5', '6', '7', '8']


def draw_board(win, game, perspective=WHITE):
    font = pg.font.SysFont("Comic Sans MS", 50)
    for row in range(8):
        for col in range(8):
            white = (row + col) % 2 == 0
            square = pg.Rect(col * 100, row * 100, 100, 100)
            pg.draw.rect(win, (9 * 16 + 10, 7 * 16 + 11, 4 * 16 + 15) if white else (3 * 16 + 7, 1 * 16 + 13, 1 * 16), square)

    for piece in game.board.pieces:
        if not piece.captured:
            piece_text = font.render(str(piece), True, (0, 0, 0))
            col = piece.square.col
            row = piece.square.row

            if perspective == WHITE:
                win.blit(piece_text, (col * 100 + 35, row * 100 + 15))
            else:
                win.blit(piece_text, ((7 - col) * 100 + 35, (7 - row) * 100 + 15))

    pg.display.update()


def main():
    pg.init()
    pg.display.set_caption("Chess")
    win = pg.display.set_mode((800, 800))

    game = Game()
    running = True

    square_to_move_from = None
    square_to_move_to = None
    turn = WHITE

    while running:
        draw_board(win, game, perspective=turn)

        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN:
                pos = event.dict['pos']
                row = pos[1] // 100
                col = pos[0] // 100

                if turn == WHITE:
                    square = Square((row, col))
                else:
                    square = Square((7 - row, 7 - col))

                if square_to_move_from is None:
                    if game.board.get(square) and game.board.get(square).color == turn:
                        square_to_move_from = square
                elif square_to_move_to is None:
                    square_to_move_to = square
            elif event.type == pg.MOUSEBUTTONUP:
                pos = event.dict['pos']
                row = pos[1] // 100
                col = pos[0] // 100

                if turn == WHITE:
                    square = Square((row, col))
                else:
                    square = Square((7 - row, 7 - col))

                if square_to_move_from is not None and square_to_move_to is None and square_to_move_from != square:
                    square_to_move_to = square

        if square_to_move_from is not None and square_to_move_to is not None:
            # Promotion
            piece_moved = game.board.get(square_to_move_from)
            promotion_val = None
            if piece_moved.piece_type == PAWN:
                if piece_moved.color == WHITE:
                    if square_to_move_to.row == 0:
                        promotion_val = QUEEN
                else:
                    if square_to_move_to.row == 7:
                        promotion_val = QUEEN

            move_success = game.move(square_to_move_from, square_to_move_to, promotion=promotion_val)
            square_to_move_from = None
            square_to_move_to = None

            if move_success:
                if GameRules.check_if_game_ended(game) == CHECKMATE:
                    print(f'Checkmate! {"WHITE" if turn == WHITE else "BLACK"} won!')
                    running = False
                elif GameRules.check_if_game_ended(game) == STALEMATE:
                    print("Stalemate!")
                    running = False

                turn *= -1


if __name__ == '__main__':
    main()
