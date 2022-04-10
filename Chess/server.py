import pickle
import random
import socket
import sys
import threading
import time

import model
from model import WHITE, PAWN, GameRules, CHECKMATE, STALEMATE


class Room:
    def __init__(self, host, code):
        self.player1: socket.socket = host
        self.player2: socket.socket = None
        self.code: int = code

    def play(self):
        in_room = True
        players = {"WHITE": self.player1, "BLACK": self.player2}
        colors = {self.player1: "WHITE", self.player2: "BLACK"}

        self.player1.sendall(bytes("LET THE GAME BEGIN", "utf-8"))
        self.player2.sendall(bytes("LET THE GAME BEGIN", "utf-8"))

        while in_room:
            g = model.Game()
            in_game = True
            turn = WHITE

            while in_game:
                color = "WHITE" if turn == WHITE else "BLACK"
                not_color = "BLACK" if turn == WHITE else "WHITE"

                pickled_game = pickle.dumps(g)
                pickled_game_len = str(len(pickled_game)).encode('utf-8')

                self.player1.sendall(pickled_game_len)
                self.player1.sendall(pickled_game)
                self.player1.sendall(bytes(colors[self.player1], "utf-8"))
                self.player1.sendall(bytes(color, "utf-8"))

                self.player2.sendall(pickled_game_len)
                self.player2.sendall(pickled_game)
                self.player2.sendall(bytes(colors[self.player2], "utf-8"))
                self.player2.sendall(bytes(color, "utf-8"))

                square_to_move_from = players[color].recv(2).decode("utf-8").lower()
                square_to_move_to = players[color].recv(2).decode("utf-8").lower()

                # promotion
                piece_moved = g.board.get(square_to_move_from)
                promotion_value = None
                if piece_moved.piece_type == PAWN:
                    if piece_moved.color == WHITE:
                        if square_to_move_to[1] == "8":
                            promotion_value = int.from_bytes(players[color].recv(1), "big")
                    else:
                        if square_to_move_to[1] == "1":
                            promotion_value = int.from_bytes(players[color].recv(1), "big")

                g.move(square_to_move_from, square_to_move_to, promotion=promotion_value)

                if GameRules.check_if_game_ended(g) == CHECKMATE or GameRules.check_if_game_ended(g) == STALEMATE:
                    pickled_game = pickle.dumps(g)
                    pickled_game_len = str(len(pickled_game)).encode('utf-8')

                    # Send the player who did not just play the final game state
                    players[not_color].sendall(pickled_game_len)
                    players[not_color].sendall(pickled_game)
                    players[not_color].sendall(bytes(colors[self.player1], "utf-8"))
                    players[not_color].sendall(bytes(color, "utf-8"))
                    in_game = False

                turn *= -1

            self.player1.sendall(bytes("Rematch [y, N]: ", "utf-8"))
            self.player2.sendall(bytes("Rematch [y, N]: ", "utf-8"))
            p1_resp = self.player1.recv(1).decode("utf-8").lower()
            p2_resp = self.player2.recv(1).decode("utf-8").lower()

            if p1_resp == p2_resp == "y":
                # Rematch accepted
                self.player1.sendall(bytes("Rematch accepted!", "utf-8"))
                self.player2.sendall(bytes("Rematch accepted!", "utf-8"))

                w = players["WHITE"]
                b = players["BLACK"]
                players["WHITE"] = b
                players["BLACK"] = w

                p1 = colors[self.player1]
                p2 = colors[self.player2]
                colors[self.player1] = p2
                colors[self.player2] = p1
            else:
                # Rematch denied
                self.player1.sendall(bytes("Rematch denied!", "utf-8"))
                self.player2.sendall(bytes("Rematch denied!", "utf-8"))
                in_room = False

    def __repr__(self):
        return f"{self.player1}; {self.player2}; {self.code}"


def handle_new_connection(csock, addr):
    csock.sendall(bytes("Welcome to Chess!", "utf-8"))
    csock.sendall(bytes("Do you want to create or join a room: ", "utf-8"))

    response = csock.recv(1024).decode("utf-8").lower()

    if response == "create":
        new_room_code = random.choice([x for x in range(1, 10000) if x not in [room.code for room in rooms]])
        new_room = Room(csock, new_room_code)
        unfilled.append(new_room)
        rooms.append(new_room)
        csock.sendall(bytes(f"Your room code is {new_room_code}", "utf-8"))
    elif response == "join":
        # Receive valid room code from client
        response = "-1"
        while response == "-1":
            # Send all current room codes to client
            response = csock.recv(1024).decode("utf-8")

            # Request for valid codes
            if response == "-1":
                room_codes = [room.code for room in unfilled]
                pickled_room_codes = pickle.dumps(room_codes)
                msg_len = str(len(pickled_room_codes)).encode('utf-8')
                # Send room code message length
                csock.sendall(msg_len)
                # Send all current room codes
                csock.sendall(pickled_room_codes)

        for room in unfilled:
            if int(response) == room.code:
                room.player2 = csock

                unfilled.remove(room)
                filled.append(room)

                room.player1.sendall(bytes("Someone has joined the room!", "utf-8"))
                csock.sendall(bytes(f"Joined room!", "utf-8"))

                room_thread = threading.Thread(target=room.play)
                room_thread.start()


def handle_new_connections():
    s.listen()

    while True:
        clientsocket, address = s.accept()
        handle_new_connection_thread = threading.Thread(target=handle_new_connection, args=(clientsocket, address))
        handle_new_connection_thread.start()


if __name__ == '__main__':
    unfilled = []
    filled = []
    rooms = []

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 55555))

    handle_new_connections_thread = threading.Thread(target=handle_new_connections)
    handle_new_connections_thread.start()

    while True:
        sys.stdout.write(f"\rUnfilled Rooms: {len(unfilled)} {[room.code for room in unfilled]}; Filled Rooms: {len(filled)} {[room.code for room in filled]}")
        time.sleep(1)
