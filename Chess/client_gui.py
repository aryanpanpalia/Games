import os
import pickle
import socket
import sys
import threading
from typing import Tuple

import pygame as pg
import select

from model import *


def is_valid_input(square_name: str):
    return len(square_name) == 2 and square_name[0].lower() in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] and square_name[1] in ['1', '2', '3', '4', '5', '6', '7', '8']


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def draw_board(x, y, width, height, win, game, perspective):
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

    if square_to_move_from and not move_in_progress:
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
    rect = pg.Rect(x, y, width, height)
    pg.draw.rect(win, (40, 40, 40), rect)

    for i, group in enumerate(chunker(game.moves[MOVE_LIST_SCROLL * 2:], 2)):
        if round(y + MOVE_LIST_LINE_HEIGHT * i + MOVE_LIST_LINE_HEIGHT, 3) <= y + height:
            rect = pg.Rect(x, y + MOVE_LIST_LINE_HEIGHT * i, width, MOVE_LIST_LINE_HEIGHT)
            if i % 2 == 0:
                pg.draw.rect(win, (30, 30, 30), rect)
            else:
                pg.draw.rect(win, (50, 50, 50), rect)

            win.blit(font.render(f"{i + 1 + MOVE_LIST_SCROLL}. ", True, (200, 200, 200)), (x + 10, y + 3 + MOVE_LIST_LINE_HEIGHT * i))
            win.blit(font.render(group[0].to_algebraic_notation(), True, (200, 200, 200)), (x + 50, y + 3 + MOVE_LIST_LINE_HEIGHT * i))
            if len(group) == 2:
                win.blit(font.render(group[1].to_algebraic_notation(), True, (200, 200, 200)), (x + 150, y + 3 + MOVE_LIST_LINE_HEIGHT * i))


def draw_draw_button(x, y, width, height, win):
    font = pg.font.SysFont("bahnschrift", 20)

    draw_rect = pg.Rect(x, y, width, height)
    pg.draw.rect(win, (30, 30, 30), draw_rect)

    # text should start at start_x + 0.5 * box_width - 0.5 * text_width, start_y + 0.5 * box_height - 0.5 * text_height so that its centered with respect to function parameters
    # text has width of 48 and height of 24
    win.blit(font.render(f"Draw", True, (200, 200, 200)), (x + 0.5 * width - 24, y + 0.5 * height - 12))


def draw_resign_buttons(x, y, width, height, win):
    font = pg.font.SysFont("bahnschrift", 20)

    resign_rect = pg.Rect(x, y, width, height)
    pg.draw.rect(win, (30, 30, 30), resign_rect)

    # text should start at start_x + 0.5 * box_width - 0.5 * text_width, start_y + 0.5 * box_height - 0.5 * text_height so that its centered with respect to function parameters
    # text has width of 61 and height of 25 and needs to be centered in a box with (start_x, start_y, box_width, box_height) = (x + width / 2 + 5, y, width / 2 - 5, height)
    win.blit(font.render(f"Resign", True, (200, 200, 200)), (x + 0.5 * width - 30.5, y + 0.5 * height - 12.5))


def render(win, game, perspective=WHITE):
    win.fill((60, 60, 60))

    draw_board(BOARD_OFFSET_X, BOARD_OFFSET_Y, BOARD_WIDTH, BOARD_HEIGHT, win, game, perspective)
    draw_move_list(MOVE_LIST_OFFSET_X, MOVE_LIST_OFFSET_Y, MOVE_LIST_WIDTH, MOVE_LIST_HEIGHT, win, game)
    draw_draw_button(DRAW_BUTTON_OFFSET_X, DRAW_BUTTON_OFFSET_Y, DRAW_BUTTON_WIDTH, DRAW_BUTTON_HEIGHT, win)
    draw_resign_buttons(RESIGN_BUTTON_OFFSET_X, RESIGN_BUTTON_OFFSET_Y, RESIGN_BUTTON_WIDTH, RESIGN_BUTTON_HEIGHT, win)

    pg.display.update()


def send(sock: socket.socket, data: bytes, type_=""):
    header = {
        "type": type_,
        "length": len(data)
    }

    pickled_header = pickle.dumps(header)
    pickled_header += b' ' * (HEADER - len(pickled_header))

    sock.sendall(pickled_header)
    sock.sendall(data)


def recv(sock: socket.socket) -> Tuple[bytes, str]:
    pickled_header = b''
    received_length = 0

    while HEADER - received_length > 0:
        pickled_header += sock.recv(HEADER - received_length)
        received_length = len(pickled_header)

    header = pickle.loads(pickled_header)
    data_len = header["length"]
    data_type = header["type"]
    received_length = 0

    chunks = []
    while data_len - received_length > 0:
        chunk = sock.recv(data_len - received_length)
        chunks.append(chunk)
        received_length += len(chunk)

    data = b''.join(chunks)

    return data, data_type


def update_from_server(sock: socket.socket):
    global game, my_color, turn_color, turn, my_color_int
    while True:
        readable, _, _ = select.select([sock], [], [], 1)

        if readable:
            data, data_type = recv(sock)
            if data_type == "gamestate":
                game_state = pickle.loads(data)
                in_game = game_state["in_game"]
                game = game_state["game"]
                my_color = game_state["player_color"]
                turn_color = game_state["turn_color"]

                turn = -1 if turn_color == "WHITE" else 1
                my_color_int = -1 if my_color == "WHITE" else 1

                if not in_game:
                    return


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER, PORT))

        print("Welcome to Chess!")

        response = ""
        while response.lower() not in ["create", "join"]:
            response = input("Enter whether you want to join or create a room [join, create]: ")

        send(s, bytes(response, "utf-8"))

        if response.lower() == "create":
            # Message giving room code
            msg, _ = recv(s)
            msg = msg.decode("utf-8")
            print(msg)
            print("Waiting for someone to join...")
        elif response.lower() == "join":
            valid_room_code = False
            while not valid_room_code:
                response = input("Enter your room code: ")

                # Send request for valid codes
                send(s, bytes("-1", "utf-8"))

                pickled_room_codes, _ = recv(s)
                room_codes = pickle.loads(pickled_room_codes)

                if int(response) in room_codes:
                    valid_room_code = True
                else:
                    print("Invalid room code!")

            send(s, bytes(response, "utf-8"))

        # Message stating that someone/you joined the room
        msg, _ = recv(s)
        msg = msg.decode("utf-8")
        print(msg)

        in_room = True
        while in_room:
            pg.init()
            pg.display.set_caption("Chess [WHITE]")
            win = pg.display.set_mode((WIDTH, HEIGHT))

            in_game = True

            update_from_server_thread = threading.Thread(target=update_from_server, args=(s,))
            update_from_server_thread.start()

            while in_game:
                global game, my_color, turn_color, turn, my_color_int, square_to_move_from, square_to_move_to, promotion_value, move_in_progress, MOVE_LIST_SCROLL

                render(win, game, perspective=my_color_int)
                pg.display.set_caption(f"Chess [{turn_color}]")

                if game.check_if_game_ended() == CHECKMATE:
                    print(f"Checkmate! You lost!")
                    break
                elif game.check_if_game_ended() == STALEMATE:
                    print("Stalemate!")
                    break

                events = pg.event.get()
                for event in events:
                    if event.type == pg.QUIT:
                        quit(-1)
                    elif event.type == pg.MOUSEBUTTONDOWN:
                        if event.dict['button'] in [1, 2, 3]:
                            pos = event.dict['pos']

                            if BOARD_OFFSET_X < pos[0] < BOARD_OFFSET_X + BOARD_WIDTH and BOARD_OFFSET_Y < pos[1] < BOARD_OFFSET_Y + BOARD_HEIGHT:
                                row = (pos[1] - BOARD_OFFSET_Y) // (BOARD_WIDTH // 8)
                                col = (pos[0] - BOARD_OFFSET_X) // (BOARD_HEIGHT // 8)

                                if my_color_int == WHITE:
                                    square = Square((row, col))
                                else:
                                    square = Square((7 - row, 7 - col))

                                if game.board.get(square) and game.board.get(square).color == my_color_int:
                                    square_to_move_from = square
                                elif not square_to_move_to:
                                    square_to_move_to = square

                        elif event.dict['button'] == 4:
                            if MOVE_LIST_OFFSET_X < event.pos[0] < MOVE_LIST_OFFSET_X + MOVE_LIST_WIDTH and MOVE_LIST_OFFSET_Y < event.pos[1] < MOVE_LIST_OFFSET_Y + MOVE_LIST_HEIGHT:
                                if MOVE_LIST_SCROLL > 0:
                                    MOVE_LIST_SCROLL -= 1
                        elif event.dict['button'] == 5:
                            if MOVE_LIST_OFFSET_X < event.pos[0] < MOVE_LIST_OFFSET_X + MOVE_LIST_WIDTH and MOVE_LIST_OFFSET_Y < event.pos[1] < MOVE_LIST_OFFSET_Y + MOVE_LIST_HEIGHT:
                                if (len(game.moves) - 2 * MOVE_LIST_SCROLL) / 2 > NUM_TURNS_IN_MOVE_LIST:
                                    MOVE_LIST_SCROLL += 1

                    elif event.type == pg.MOUSEBUTTONUP:
                        if event.dict['button'] in [1, 2, 3]:
                            pos = event.dict['pos']
                            if BOARD_OFFSET_X < pos[0] < BOARD_OFFSET_X + BOARD_WIDTH and BOARD_OFFSET_Y < pos[1] < BOARD_OFFSET_Y + BOARD_HEIGHT:
                                row = (pos[1] - BOARD_OFFSET_Y) // (BOARD_WIDTH // 8)
                                col = (pos[0] - BOARD_OFFSET_X) // (BOARD_HEIGHT // 8)

                                if my_color_int == WHITE:
                                    square = Square((row, col))
                                else:
                                    square = Square((7 - row, 7 - col))

                                if square_to_move_from and not square_to_move_to and square_to_move_from != square:
                                    square_to_move_to = square

                if square_to_move_from and square_to_move_to and my_color_int == turn:
                    # Promotion
                    piece_moved = game.board.get(square_to_move_from)
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
                        if (len(game.moves) - 2 * MOVE_LIST_SCROLL) / 2 > NUM_TURNS_IN_MOVE_LIST:
                            MOVE_LIST_SCROLL += 1

                        move_in_progress = True

                        if game.check_if_game_ended() == CHECKMATE:
                            print(f'Checkmate! {"WHITE" if turn == WHITE else "BLACK"} won!')
                            game.moves[-1].mate = True
                            in_game = False
                        elif game.check_if_game_ended() == STALEMATE:
                            print("Stalemate!")
                            in_game = False
                        elif turn == WHITE:
                            if game.is_targeted(WHITE, game.board.black_king.square, check_if_exposes_king=False):
                                game.moves[-1].check = True
                        elif turn == BLACK:
                            if game.is_targeted(BLACK, game.board.white_king.square, check_if_exposes_king=False):
                                game.moves[-1].check = True

                        render(win, game, perspective=my_color_int)

                        send(s, bytes(square_to_move_from.convert_to_name() + square_to_move_to.convert_to_name() + str(promotion_value), "utf-8"), type_="move")

                        move_in_progress = False

                        square_to_move_from = None
                        square_to_move_to = None
                        promotion_value = None
                        turn *= -1
                    else:
                        square_to_move_from = None
                        square_to_move_to = None
                        promotion_value = None

            for _ in range(2 * 30):
                pg.event.pump()
                render(win, game, perspective=my_color_int)
                pg.time.Clock().tick(30)

            pg.quit()

            response = input("Rematch [y, N]: ")
            while response.lower() not in ["", "y", "n"]:
                response = input("Rematch [y, N]: ")

            if response.lower() == "y":
                send(s, bytes("y", "utf-8"))
            else:
                send(s, bytes("n", "utf-8"))

            # Rematch decision
            msg, _ = recv(s)
            msg = msg.decode("utf-8")
            print(msg)
            if msg == "Rematch denied!":
                in_room = False


def rss_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


if __name__ == '__main__':
    HEADER = 64
    SERVER = socket.gethostname()
    PORT = 55555

    WIDTH = 1300
    HEIGHT = 900

    BOARD_OFFSET_X = 20
    BOARD_OFFSET_Y = 50
    BOARD_WIDTH = 800
    BOARD_HEIGHT = 800

    MOVE_LIST_OFFSET_X = BOARD_OFFSET_X + BOARD_WIDTH + 20
    MOVE_LIST_OFFSET_Y = 50
    MOVE_LIST_WIDTH = 440
    MOVE_LIST_HEIGHT = 730
    NUM_TURNS_IN_MOVE_LIST = 25
    MOVE_LIST_LINE_HEIGHT = MOVE_LIST_HEIGHT / NUM_TURNS_IN_MOVE_LIST
    MOVE_LIST_SCROLL = 0

    DRAW_BUTTON_OFFSET_X = BOARD_OFFSET_X + BOARD_WIDTH + 20
    DRAW_BUTTON_OFFSET_Y = MOVE_LIST_OFFSET_Y + MOVE_LIST_HEIGHT + 20
    DRAW_BUTTON_WIDTH = 210
    DRAW_BUTTON_HEIGHT = 50

    RESIGN_BUTTON_OFFSET_X = DRAW_BUTTON_OFFSET_X + DRAW_BUTTON_WIDTH + 20
    RESIGN_BUTTON_OFFSET_Y = MOVE_LIST_OFFSET_Y + MOVE_LIST_HEIGHT + 20
    RESIGN_BUTTON_WIDTH = 210
    RESIGN_BUTTON_HEIGHT = 50

    piece_images = {image[1]: pg.transform.smoothscale(pg.image.load(rss_path(f'assets/{image}')), (100, 100)) for image in os.listdir(rss_path("assets"))}

    game: Game = Game()
    my_color = None
    turn_color = None
    turn = None
    my_color_int = None

    square_to_move_from = Square((-1, -1))
    square_to_move_to = Square((-1, -1))
    promotion_value = -1

    move_in_progress = False

    main()
