import pickle
import random
import socket
import sys
import threading
import time

from model import *


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


class Room:
    def __init__(self, host, code):
        self.player1: socket.socket = host
        self.player2: socket.socket = None
        self.code: int = code

    def play(self):
        in_room = True
        players = {"WHITE": self.player1, "BLACK": self.player2}
        colors = {self.player1: "WHITE", self.player2: "BLACK"}

        send(self.player1, bytes("LET THE GAME BEGIN", "utf-8"))
        send(self.player2, bytes("LET THE GAME BEGIN", "utf-8"))

        while in_room:
            g = Game()
            in_game = True
            turn = WHITE

            while in_game:
                color = "WHITE" if turn == WHITE else "BLACK"
                not_color = "BLACK" if turn == WHITE else "WHITE"

                pickled_game = pickle.dumps(g)

                send(self.player1, pickled_game)
                send(self.player1, bytes(colors[self.player1], "utf-8"))
                send(self.player1, bytes(color, "utf-8"))

                send(self.player2, pickled_game)
                send(self.player2, bytes(colors[self.player2], "utf-8"))
                send(self.player2, bytes(color, "utf-8"))

                square_to_move_from = recv(players[color]).decode("utf-8").lower()
                square_to_move_to = recv(players[color]).decode("utf-8").lower()

                # promotion
                piece_moved = g.board.get(square_to_move_from)
                promotion_value = None
                if piece_moved.piece_type == PAWN:
                    if piece_moved.color == WHITE:
                        if square_to_move_to[1] == "8":
                            promotion_value = int.from_bytes(recv(players[color]), "big")
                    else:
                        if square_to_move_to[1] == "1":
                            promotion_value = int.from_bytes(recv(players[color]), "big")

                move = Move(
                    initial_loc=Square.get_square(square_to_move_from),
                    final_loc=Square.get_square(square_to_move_to),
                    piece_moved=g.board.get(square_to_move_from),
                    piece_captured=g.board.get(square_to_move_to),
                    promotion=promotion_value
                )

                g.move(move)

                if g.check_if_game_ended() == CHECKMATE or g.check_if_game_ended() == STALEMATE:
                    pickled_game = pickle.dumps(g)

                    # Send the player who did not just play the final game state
                    send(players[not_color], pickled_game)
                    send(players[not_color], bytes(colors[self.player1], "utf-8"))
                    send(players[not_color], bytes(color, "utf-8"))
                    in_game = False

                turn *= -1

            send(self.player1, bytes("Rematch [y, N]: ", "utf-8"))
            send(self.player2, bytes("Rematch [y, N]: ", "utf-8"))
            p1_resp = recv(self.player1).decode("utf-8").lower()
            p2_resp = recv(self.player2).decode("utf-8").lower()

            if p1_resp == p2_resp == "y":
                # Rematch accepted
                send(self.player1, bytes("Rematch accepted!", "utf-8"))
                send(self.player2, bytes("Rematch accepted!", "utf-8"))

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
                send(self.player1, bytes("Rematch denied!", "utf-8"))
                send(self.player2, bytes("Rematch denied!", "utf-8"))
                in_room = False

    def __repr__(self):
        return f"{self.player1}; {self.player2}; {self.code}"


def handle_new_connection(csock, addr):
    send(csock, bytes("Welcome to Chess!", "utf-8"))
    send(csock, bytes("Do you want to create or join a room: ", "utf-8"))

    response = recv(csock).decode("utf-8").lower()

    if response == "create":
        new_room_code = random.choice([x for x in range(1, 10000) if x not in [room.code for room in rooms]])
        new_room = Room(csock, new_room_code)
        unfilled.append(new_room)
        rooms.append(new_room)
        send(csock, bytes(f"Your room code is {new_room_code}", "utf-8"))
    elif response == "join":
        # Receive valid room code from client
        response = "-1"
        while response == "-1":
            # Send all current room codes to client
            response = recv(csock).decode("utf-8")

            # Request for valid codes
            if response == "-1":
                room_codes = [room.code for room in unfilled]
                pickled_room_codes = pickle.dumps(room_codes)

                # Send all current room codes
                send(csock, pickled_room_codes)

        for room in unfilled:
            if int(response) == room.code:
                room.player2 = csock

                unfilled.remove(room)
                filled.append(room)

                send(room.player1, bytes("Someone has joined the room!", "utf-8"))
                send(csock, bytes(f"Joined room!", "utf-8"))

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

    HEADER = 64

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 55555))

    handle_new_connections_thread = threading.Thread(target=handle_new_connections)
    handle_new_connections_thread.start()

    while True:
        sys.stdout.write(f"\rUnfilled Rooms: {len(unfilled)} {[room.code for room in unfilled]}; Filled Rooms: {len(filled)} {[room.code for room in filled]}")
        time.sleep(1)
