import model
from model import WHITE, BLACK


def is_valid_input(square_name: str):
    return len(square_name) == 2 and square_name[0].lower() in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] and square_name[1] in ['1', '2', '3', '4', '5', '6', '7', '8']


def main():
    g = model.Game()
    running = True
    turn = WHITE
    color = "WHITE"

    while running:
        color = "WHITE" if turn == WHITE else "BLACK"
        move_success = False
        while not move_success:
            print("-" * 5, color, "-" * 5)
            g.display(turn)
            valid_input = False
            square_to_move_from = ""
            square_to_move_to = ""
            while not valid_input:
                square_to_move_from = input(f"[{color}] Enter what you want to move: ")
                square_to_move_to = input(f"[{color}] Enter where you want to move: ")
                valid_input = is_valid_input(square_to_move_from) and is_valid_input(square_to_move_to) and \
                              g.board.get(square_to_move_from) is not None and g.board.get(square_to_move_from).color == turn

                if not valid_input:
                    print("\nInvalid input! Try again!\n")
                    g.display(turn)

            move_success = g.move(square_to_move_from, square_to_move_to)

        print()
        turn *= -1


if __name__ == '__main__':
    main()
