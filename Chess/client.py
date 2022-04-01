import pickle
import socket

import model
from model import GameRules, CHECKMATE, STALEMATE, WHITE, PAWN, KNIGHT, BISHOP, ROOK, QUEEN


def is_valid_input(square_name: str):
    return len(square_name) == 2 and square_name[0].lower() in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] and square_name[1] in ['1', '2', '3', '4', '5', '6', '7', '8']


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((socket.gethostname(), 55555))

        # Welcome message
        msg = s.recv(1024)
        print(msg.decode("utf-8"))

        # Message prompting for create or join
        msg = s.recv(1024)
        response = input("Enter whether you want to join or create a room: ")
        s.send(bytes(response, "utf-8"))

        if response.lower() == "create":
            # Message giving room code
            msg = s.recv(1024)
            print(msg.decode("utf-8"))
            print("Waiting for someone to join...")
        elif response.lower() == "join":
            # Message asking for room code
            msg = s.recv(1024)
            response = input("Enter your room code: ")
            s.send(bytes(response, "utf-8"))

        # Message stating that someone/you joined the room
        msg = s.recv(1024)
        print(msg.decode("utf-8"))

        # Message from inside Room.play(): "LET THE GAME BEGIN"
        msg = s.recv(1024)
        print(msg.decode("utf-8"))

        running = True
        while running:
            g: model.Game = pickle.loads(s.recv(4096))
            my_color = s.recv(5).decode("utf-8")
            turn_color = s.recv(5).decode("utf-8")
            turn = -1 if turn_color == "WHITE" else 1

            if GameRules.check_if_game_ended(g) == CHECKMATE:
                print("-" * 3, "GAME OVER", "-" * 3)
                g.display(my_color)
                print(f"Checkmate! You lost!")
                running = False
                continue
            elif GameRules.check_if_game_ended(g) == STALEMATE:
                print("-" * 3, "GAME OVER", "-" * 3)
                g.display(my_color)
                print("Stalemate!")
                running = False
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
                    running = False
                elif GameRules.check_if_game_ended(g) == STALEMATE:
                    print("-" * 3, "GAME OVER", "-" * 3)
                    g.display(my_color)
                    print("Stalemate!")
                    running = False

                s.send(bytes(square_to_move_from, "utf-8"))
                s.send(bytes(square_to_move_to, "utf-8"))

                if promotion:
                    s.send(promotion_val.to_bytes(1, "big"))


if __name__ == '__main__':
    main()
