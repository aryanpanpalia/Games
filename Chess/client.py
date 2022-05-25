import pickle
import socket
from typing import Tuple

import model
from model import *


def is_valid_input(square_name: str):
    return len(square_name) == 2 and square_name[0].lower() in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] and square_name[1] in ['1', '2', '3', '4', '5', '6', '7', '8']


def display(game, color):
    perspective = -1 if color == "WHITE" else 1
    if perspective == WHITE:
        for row in range(8):
            print(8 - row, end=" ")
            for col in range(8):
                val = game.board.board[Square.get_square(row, col)]
                if val is not None:
                    print(val, end=" ")
                else:
                    print("-", end=" ")
            print()
        print("  a b c d e f g h")
        print()
    else:
        for row in reversed(range(8)):
            print(8 - row, end=" ")
            for col in reversed(range(8)):
                val = game.board.board[Square.get_square(row, col)]
                if val is not None:
                    print(val, end=" ")
                else:
                    print("-", end=" ")
            print()
        print("  h g f e d c b a")
        print()


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
            in_game = True
            while in_game:
                game, _ = recv(s)
                game: model.Game = pickle.loads(game)

                my_color, _ = recv(s)
                my_color = my_color.decode("utf-8")

                turn_color, _ = recv(s)
                turn_color = turn_color.decode("utf-8")
                turn = -1 if turn_color == "WHITE" else 1

                if game.check_if_game_ended() == CHECKMATE:
                    print("-" * 3, "GAME OVER", "-" * 3)
                    display(game, my_color)
                    print(f"Checkmate! You lost!")
                    in_game = False
                    continue
                elif game.check_if_game_ended() == STALEMATE:
                    print("-" * 3, "GAME OVER", "-" * 3)
                    display(game, my_color)
                    print("Stalemate!")
                    in_game = False
                    continue
                elif game.is_targeted(BLACK, game.board.white_king.square, check_if_exposes_king=False) or game.is_targeted(WHITE, game.board.black_king.square, check_if_exposes_king=False):
                    print("-" * 5, turn_color, "-" * 5)
                    display(game, my_color)
                    print("Check!")
                else:
                    print("-" * 5, turn_color, "-" * 5)
                    display(game, my_color)

                if turn_color == my_color:
                    move_success = False
                    while not move_success:
                        square_to_move_from = input(f"Enter what you want to move: ")
                        square_to_move_to = input(f"Enter where you want to move: ")
                        valid_input = is_valid_input(square_to_move_from) and is_valid_input(square_to_move_to) and \
                                      game.board.get(square_to_move_from) is not None and game.board.get(square_to_move_from).color == turn

                        if not valid_input:
                            print("\nInvalid input! Try again!\n")
                            display(game, my_color)
                        else:
                            piece_moved = game.board.get(square_to_move_from)

                            # promotion
                            promotion = False
                            promotion_val = None
                            if piece_moved.piece_type == PAWN:
                                if piece_moved.color == WHITE:
                                    if square_to_move_to[1] == "8":
                                        promotion_value_str = input("To what piece do you want to promote the pawn [Q, R, B, N]: ")

                                        if promotion_value_str == "R":
                                            promotion_val = ROOK
                                        elif promotion_value_str == "B":
                                            promotion_val = BISHOP
                                        elif promotion_value_str == "N":
                                            promotion_val = KNIGHT
                                        else:
                                            promotion_val = QUEEN

                                        promotion = True
                                else:
                                    if square_to_move_to[1] == "1":
                                        promotion_value_str = input("To what piece do you want to promote the pawn [Q, R, B, N]: ")

                                        if promotion_value_str == "R":
                                            promotion_val = ROOK
                                        elif promotion_value_str == "B":
                                            promotion_val = BISHOP
                                        elif promotion_value_str == "N":
                                            promotion_val = KNIGHT
                                        else:
                                            promotion_val = QUEEN

                                        promotion = True

                            move = Move(
                                initial_loc=square_to_move_from,
                                final_loc=square_to_move_to,
                                piece_moved=game.board.get(square_to_move_from),
                                piece_captured=game.board.get(square_to_move_to),
                            )
                            move = game.correct_en_passant(move)
                            move_success = game.is_move_legal(move)

                            if move_success:
                                game.move(move)

                    print()

                    if game.check_if_game_ended() == CHECKMATE:
                        print("-" * 3, "GAME OVER", "-" * 3)
                        display(game, my_color)
                        print(f"Checkmate! You won!")
                        in_game = False
                    elif game.check_if_game_ended() == STALEMATE:
                        print("-" * 3, "GAME OVER", "-" * 3)
                        display(game, my_color)
                        print("Stalemate!")
                        in_game = False

                    send(s, bytes(square_to_move_from + square_to_move_to + str(promotion_val), "utf-8"))

            # Message asking if player wants to play again
            msg, _ = recv(s)

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


if __name__ == '__main__':
    HEADER = 64
    SERVER = socket.gethostname()
    PORT = 55555
    main()
