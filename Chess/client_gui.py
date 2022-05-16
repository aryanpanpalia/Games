import os
import pickle
import select
import socket
import sys
import threading

import pygame as pg
import pygame.time

import model
from model import *


def is_valid_input(square_name: str):
    return len(square_name) == 2 and square_name[0].lower() in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] and square_name[1] in ['1', '2', '3', '4', '5', '6', '7', '8']


def draw_board(win, game, perspective=WHITE):
    for row in range(8):
        for col in range(8):
            white = (row + col) % 2 == 0
            square = pg.Rect(col * 100, row * 100, 100, 100)
            pg.draw.rect(win, (9 * 16 + 10, 7 * 16 + 11, 4 * 16 + 15) if white else (3 * 16 + 7, 1 * 16 + 13, 1 * 16), square)

    for piece in game.board.pieces:
        if not piece.captured:
            piece_image = piece_images[str(piece)]
            col = piece.square.col
            row = piece.square.row

            if perspective == WHITE:
                win.blit(piece_image, (col * 100, row * 100))
            else:
                win.blit(piece_image, ((7 - col) * 100, (7 - row) * 100))

    if square_to_move_from is not None and not move_incomplete:
        piece = game.board.get(square_to_move_from)
        for square in game.generate_legal_squares_to_move_to_for(piece):
            col = square.col
            row = square.row

            if perspective == WHITE:
                pg.draw.circle(win, (64, 64, 64), (col * 100 + 50, row * 100 + 50), 20)
            else:
                pg.draw.circle(win, (64, 64, 64), ((7 - col) * 100 + 50, (7 - row) * 100 + 50), 20)

    pg.display.update()


def send(sock: socket.socket, data: bytes):
    data_len = str(len(data)).encode("utf-8")
    data_len += b' ' * (HEADER - len(data_len))
    sock.sendall(data_len)
    sock.sendall(data)


def recv(sock: socket.socket) -> bytes:
    header = b''
    received_length = 0

    while HEADER - received_length > 0:
        header += sock.recv(HEADER - received_length)
        received_length = len(header)

    data_len = int(header.decode("utf-8"))
    received_length = 0

    chunks = []
    while data_len - received_length > 0:
        chunk = sock.recv(data_len - received_length)
        chunks.append(chunk)
        received_length += len(chunk)

    data = b''.join(chunks)

    return data


def handle_multiplayer(sock: socket.socket):
    global game, my_color, turn_color, turn, my_color_int, square_to_move_from, square_to_move_to, promotion_val, ready_to_send, about_to_send, game_over
    sock.setblocking(False)
    while not game_over:
        readable, _, _ = select.select([sock], [], [], 1)

        if readable and not game_over:
            sock.setblocking(True)

            maybe_game = recv(sock)

            # not game. actually message asking for rematch
            if len(maybe_game) < 2000:
                return

            game = pickle.loads(maybe_game)
            my_color = recv(sock).decode("utf-8")
            turn_color = recv(sock).decode("utf-8")

            turn = -1 if turn_color == "WHITE" else 1
            my_color_int = -1 if my_color == "WHITE" else 1
            sock.setblocking(False)

        if ready_to_send:
            sock.setblocking(True)

            from_square = square_to_move_from.convert_to_name()
            to_square = square_to_move_to.convert_to_name()
            if promotion_val:
                promotion = promotion_val.to_bytes(1, "big")

            about_to_send = True

            send(sock, bytes(from_square, "utf-8"))
            send(sock, bytes(to_square, "utf-8"))

            if promotion_val:
                send(sock, promotion)

            sock.setblocking(False)

            ready_to_send = False


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER, PORT))

        # Welcome message
        msg = recv(s).decode("utf-8")
        print(msg)

        # Message prompting for create or join
        msg = recv(s)

        response = ""

        while response.lower() not in ["create", "join"]:
            response = input("Enter whether you want to join or create a room [join, create]: ")

        send(s, bytes(response, "utf-8"))

        if response.lower() == "create":
            # Message giving room code
            msg = recv(s).decode("utf-8")
            print(msg)
            print("Waiting for someone to join...")
        elif response.lower() == "join":
            valid_room_code = False
            while not valid_room_code:
                response = input("Enter your room code: ")

                # Send request for valid codes
                send(s, bytes("-1", "utf-8"))
                # Message containing all current room codes
                room_codes = pickle.loads(recv(s))

                if int(response) in room_codes:
                    valid_room_code = True
                else:
                    print("Invalid room code!")

            send(s, bytes(response, "utf-8"))

        # Message stating that someone/you joined the room
        msg = recv(s).decode("utf-8")
        print(msg)

        # Message from inside Room.play(): "LET THE GAME BEGIN"
        msg = recv(s).decode("utf-8")
        print(msg)

        in_room = True
        while in_room:
            pg.init()
            pg.display.set_caption("Chess [WHITE]")
            win = pg.display.set_mode((800, 800))

            in_game = True

            handle_multiplayer_thread = threading.Thread(target=handle_multiplayer, args=(s,))
            handle_multiplayer_thread.start()

            while in_game:
                global game, my_color, turn_color, turn, my_color_int, square_to_move_from, square_to_move_to, promotion_val, ready_to_send, about_to_send, move_incomplete, game_over

                draw_board(win, game, perspective=my_color_int)
                pg.display.set_caption(f"Chess [{turn_color}]")

                if GameRules.check_if_game_ended(game) == CHECKMATE:
                    print(f"Checkmate! You lost!")
                    in_game = False
                    break
                elif GameRules.check_if_game_ended(game) == STALEMATE:
                    print("Stalemate!")
                    in_game = False
                    break

                events = pg.event.get()
                for event in events:
                    if event.type == pg.QUIT:
                        quit(-1)
                    elif event.type == pg.MOUSEBUTTONDOWN:
                        pos = event.dict['pos']
                        row = pos[1] // 100
                        col = pos[0] // 100

                        if my_color_int == WHITE:
                            square = Square((row, col))
                        else:
                            square = Square((7 - row, 7 - col))

                        if game.board.get(square) and game.board.get(square).color == my_color_int:
                            square_to_move_from = square
                        elif square_to_move_to is None:
                            square_to_move_to = square

                    elif event.type == pg.MOUSEBUTTONUP:
                        pos = event.dict['pos']
                        row = pos[1] // 100
                        col = pos[0] // 100

                        if my_color_int == WHITE:
                            square = Square((row, col))
                        else:
                            square = Square((7 - row, 7 - col))

                        if square_to_move_from is not None and square_to_move_to is None and square_to_move_from != square:
                            square_to_move_to = square

                if square_to_move_from and square_to_move_to and my_color_int == turn:
                    # Promotion
                    piece_moved = game.board.get(square_to_move_from)
                    if piece_moved.piece_type == PAWN:
                        if piece_moved.color == WHITE:
                            if square_to_move_to.row == 0:
                                promotion_val = QUEEN
                        else:
                            if square_to_move_to.row == 7:
                                promotion_val = QUEEN

                    move_success = game.move(square_to_move_from, square_to_move_to, promotion=promotion_val)
                    move_incomplete = True

                    if move_success:
                        if GameRules.check_if_game_ended(game) == CHECKMATE:
                            print(f'Checkmate! {"WHITE" if turn == WHITE else "BLACK"} won!')
                            in_game = False
                        elif GameRules.check_if_game_ended(game) == STALEMATE:
                            print("Stalemate!")
                            in_game = False

                        draw_board(win, game, perspective=my_color_int)

                        ready_to_send = True

                        while not about_to_send:
                            pygame.time.Clock().tick(15)

                        move_incomplete = False
                        about_to_send = False

                        square_to_move_from = None
                        square_to_move_to = None
                        promotion_val = None
                        turn *= -1
                    else:
                        square_to_move_from = None
                        square_to_move_to = None
                        promotion_val = None

            draw_board(win, game, perspective=my_color_int)

            for _ in range(5 * 30):
                pygame.event.pump()
                pygame.time.Clock().tick(30)

            game_over = True
            pg.quit()

            s.setblocking(True)

            response = input("Rematch [y, N]: ")
            while response.lower() not in ["", "y", "n"]:
                response = input("Rematch [y, N]: ")

            if response.lower() == "y":
                send(s, bytes("y", "utf-8"))
            else:
                send(s, bytes("n", "utf-8"))

            # Rematch decision
            msg = recv(s).decode("utf-8")
            print(msg)
            if msg == "Rematch denied!":
                in_room = False
            else:
                game_over = False


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

    piece_images = {image[1]: pygame.transform.smoothscale(pygame.image.load(rss_path(f'assets/{image}')), (100, 100)) for image in os.listdir(rss_path("assets"))}

    game: model.Game = Game()
    my_color = None
    turn_color = None
    turn = None
    my_color_int = None

    square_to_move_from = None
    square_to_move_to = None
    promotion_val = None

    move_incomplete = False
    ready_to_send = False
    about_to_send = False

    game_over = False

    main()
