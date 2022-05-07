import py_compile
import time
import pygame as pg
import pickle
import socket
import select

import model
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
            pg.display.set_caption("Chess")
            win = pg.display.set_mode((800, 800))

            square_to_move_from = None
            square_to_move_to = None

            g: model.Game = Game()
            my_color = None
            turn_color = None

            in_game = True

            s.setblocking(False)

            while in_game:
                readable, writable, error = select.select([s], [], [s], 0.1)

                if readable:
                    s.setblocking(True)
                    g: model.Game = pickle.loads(recv(s))
                    my_color = recv(s).decode("utf-8")
                    turn_color = recv(s).decode("utf-8")
                    turn = -1 if turn_color == "WHITE" else 1
                    my_color_int = -1 if my_color == "WHITE" else 1
                    s.setblocking(False)
                
                if error:
                    print("Error")
                    pg.quit()
                    time.sleep(2)
                    quit(-1)

                draw_board(win, g, perspective=my_color_int)

                if GameRules.check_if_game_ended(g) == CHECKMATE:
                    print(f"Checkmate! You lost!")
                    in_game = False
                    break
                elif GameRules.check_if_game_ended(g) == STALEMATE:
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

                        if square_to_move_from is None:
                            if g.board.get(square) and g.board.get(square).color == my_color_int:
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
                    piece_moved = g.board.get(square_to_move_from)
                    promotion_val = None
                    if piece_moved.piece_type == PAWN:
                        if piece_moved.color == WHITE:
                            if square_to_move_to.row == 0:
                                promotion_val = QUEEN
                        else:
                            if square_to_move_to.row == 7:
                                promotion_val = QUEEN

                    move_success = g.move(square_to_move_from, square_to_move_to, promotion=promotion_val)

                    if move_success:
                        if GameRules.check_if_game_ended(g) == CHECKMATE:
                            print(f'Checkmate! {"WHITE" if turn == WHITE else "BLACK"} won!')
                            in_game = False
                        elif GameRules.check_if_game_ended(g) == STALEMATE:
                            print("Stalemate!")
                            in_game = False

                        s.setblocking(True)
                        send(s, bytes(square_to_move_from.convert_to_name(), "utf-8"))
                        send(s, bytes(square_to_move_to.convert_to_name(), "utf-8"))
                        
                        if promotion_val:
                            send(s, promotion_val.to_bytes(1, "big"))

                        s.setblocking(False)

                        turn *= -1

                    square_to_move_from = None
                    square_to_move_to = None

            pg.quit()

            s.setblocking(True)

            # Message asking if player wants to play again
            msg = recv(s)

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


if __name__ == '__main__':
    HEADER = 64
    SERVER = socket.gethostname()
    PORT = 55555
    main()