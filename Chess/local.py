import model
from model import *


def is_valid_input(square_name: str):
    return len(square_name) == 2 and square_name[0].lower() in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] and square_name[1] in ['1', '2', '3', '4', '5', '6', '7', '8']


def display(game):
    if game.turn == WHITE:
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


def main():
    game = model.Game()
    running = True
    turn = WHITE

    while running:
        color = "WHITE" if turn == WHITE else "BLACK"
        move_success = False
        print("-" * 5, color, "-" * 5)
        display(game)
        while not move_success:
            square_to_move_from = input(f"[{color}] Enter what you want to move: ")
            square_to_move_to = input(f"[{color}] Enter where you want to move: ")
            valid_input = is_valid_input(square_to_move_from) and is_valid_input(square_to_move_to) and \
                          game.board.get(square_to_move_from) is not None and game.board.get(square_to_move_from).color == turn

            if not valid_input:
                print("\nInvalid input! Try again!\n")
                display(game)
            else:
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
            print(f"Checkmate! {color} won!")
            running = False
        elif game.check_if_game_ended() == STALEMATE:
            print("Stalemate!")
            running = False

        turn *= -1


if __name__ == '__main__':
    main()
