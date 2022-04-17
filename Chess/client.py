import pickle
import socket

import model
from model import GameRules, CHECKMATE, STALEMATE, WHITE, PAWN, KNIGHT, BISHOP, ROOK, QUEEN


def is_valid_input(square_name: str):
    return len(square_name) == 2 and square_name[0].lower() in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] and square_name[1] in ['1', '2', '3', '4', '5', '6', '7', '8']


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
            in_game = True
            while in_game:
                g: model.Game = pickle.loads(recv(s))
                my_color = recv(s).decode("utf-8")
                turn_color = recv(s).decode("utf-8")
                turn = -1 if turn_color == "WHITE" else 1

                if GameRules.check_if_game_ended(g) == CHECKMATE:
                    print("-" * 3, "GAME OVER", "-" * 3)
                    g.display(my_color)
                    print(f"Checkmate! You lost!")
                    in_game = False
                    continue
                elif GameRules.check_if_game_ended(g) == STALEMATE:
                    print("-" * 3, "GAME OVER", "-" * 3)
                    g.display(my_color)
                    print("Stalemate!")
                    in_game = False
                    continue
                elif GameRules.white_king_checked(g.board) or GameRules.black_king_checked(g.board):
                    print("-" * 5, turn_color, "-" * 5)
                    g.display(my_color)
                    print("Check!")
                else:
                    print("-" * 5, turn_color, "-" * 5)
                    g.display(my_color)

                if turn_color == my_color:
                    move_success = False
                    while not move_success:
                        valid_input = False
                        square_to_move_from = ""
                        square_to_move_to = ""
                        while not valid_input:
                            square_to_move_from = input(f"Enter what you want to move: ")
                            square_to_move_to = input(f"Enter where you want to move: ")
                            valid_input = is_valid_input(square_to_move_from) and is_valid_input(square_to_move_to) and \
                                          g.board.get(square_to_move_from) is not None and g.board.get(square_to_move_from).color == turn

                            if not valid_input:
                                print("\nInvalid input! Try again!\n")
                                g.display(turn)

                        piece_moved = g.board.get(square_to_move_from)

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

                        move_success = g.move(square_to_move_from, square_to_move_to, promotion=promotion_val)

                    print()

                    if GameRules.check_if_game_ended(g) == CHECKMATE:
                        print("-" * 3, "GAME OVER", "-" * 3)
                        g.display(my_color)
                        print(f"Checkmate! You won!")
                        in_game = False
                    elif GameRules.check_if_game_ended(g) == STALEMATE:
                        print("-" * 3, "GAME OVER", "-" * 3)
                        g.display(my_color)
                        print("Stalemate!")
                        in_game = False

                    send(s, bytes(square_to_move_from, "utf-8"))
                    send(s, bytes(square_to_move_to, "utf-8"))

                    if promotion:
                        send(s, promotion_val.to_bytes(1, "big"))

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
