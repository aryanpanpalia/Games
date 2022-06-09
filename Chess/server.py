import pickle
import random
import socket
import sys
import threading
import time
from typing import Tuple

import select

from model import *


def send(sock: socket.socket, data: bytes, type_=""):
    header = {
        "type": type_,
        "length": len(data)
    }

    pickled_header = pickle.dumps(header)

    assert len(pickled_header) <= HEADER, "Length of un-padded header is greater than maximum header size"

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


class Room:
    def __init__(self, host, code):
        self.player1: socket.socket = host
        self.player2: socket.socket = None
        self.code: int = code

    def play(self):
        in_room = True
        players = {"WHITE": self.player1, "BLACK": self.player2}
        colors = {self.player1: "WHITE", self.player2: "BLACK"}
        other_player = {self.player1: self.player2, self.player2: self.player1}

        while in_room:
            game = Game()
            in_game = True
            turn = WHITE

            p1_game_state = {
                "in_game": in_game,
                "game": game,
                "player_color": colors[self.player1],
                "turn_color": "WHITE"
            }

            p2_game_state = {
                "in_game": in_game,
                "game": game,
                "player_color": colors[self.player2],
                "turn_color": "WHITE"
            }

            send(self.player1, pickle.dumps(p1_game_state), type_="gamestate")
            send(self.player2, pickle.dumps(p2_game_state), type_="gamestate")

            while in_game:
                turn_color = "WHITE" if turn == WHITE else "BLACK"

                readable, _, _ = select.select([self.player1, self.player2], [], [], 1)

                for player_sock in readable:
                    data, data_type = recv(player_sock)
                    if data_type == "move":
                        # Get and apply move
                        move_string = data.decode("utf-8").lower()
                        square_to_move_from = move_string[:2]
                        square_to_move_to = move_string[2:4]

                        promotion_value = None
                        if len(move_string) == 5:
                            promotion_value = int(move_string[4])

                        move = Move(
                            initial_loc=Square.get_square(square_to_move_from),
                            final_loc=Square.get_square(square_to_move_to),
                            piece_moved=game.board.get(square_to_move_from),
                            piece_captured=game.board.get(square_to_move_to),
                            promotion=promotion_value
                        )
                        move = game.correct_en_passant(move)
                        game.move(move)

                        turn *= -1
                        turn_color = "WHITE" if turn == WHITE else "BLACK"

                        if game.check_if_game_ended() == CHECKMATE:
                            game.moves[-1].mate = True
                        elif turn == WHITE:
                            if game.is_targeted(WHITE, game.board.black_king.square, check_if_exposes_king=False):
                                game.moves[-1].check = True
                        elif turn == BLACK:
                            if game.is_targeted(BLACK, game.board.white_king.square, check_if_exposes_king=False):
                                game.moves[-1].check = True

                        if game.check_if_game_ended() == CHECKMATE or game.check_if_game_ended() == STALEMATE:
                            in_game = False

                        p1_game_state = {
                            "in_game": in_game,
                            "game": game,
                            "player_color": colors[self.player1],
                            "turn_color": turn_color
                        }

                        p2_game_state = {
                            "in_game": in_game,
                            "game": game,
                            "player_color": colors[self.player2],
                            "turn_color": turn_color
                        }

                        send(self.player1, pickle.dumps(p1_game_state), type_="gamestate")
                        send(self.player2, pickle.dumps(p2_game_state), type_="gamestate")
                    elif data_type == "draw_offer":
                        send(other_player[player_sock], bytes("draw_offer", "utf-8"), type_="draw_offer")
                    elif data_type == "draw_accept":
                        send(other_player[player_sock], bytes("draw_accept", "utf-8"), type_="draw_accept")
                        in_game = False
                    elif data_type == "draw_reject":
                        send(other_player[player_sock], bytes("draw_reject", "utf-8"), type_="draw_reject")
                    elif data_type == "resign":
                        send(other_player[player_sock], bytes("resign", "utf-8"), type_="resign")
                        in_game = False

            p1_resp, _ = recv(self.player1)
            p2_resp, _ = recv(self.player2)
            p1_resp = p1_resp.decode("utf-8").lower()
            p2_resp = p2_resp.decode("utf-8").lower()

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
    response, _ = recv(csock)
    response = response.decode("utf-8").lower()

    if response == "create":
        new_room_code = random.choice([x for x in range(1, 10000) if x not in [room.code for room in rooms]])
        new_room = Room(csock, new_room_code)
        unfilled.append(new_room)
        rooms.append(new_room)
        send(csock, bytes(f"Your room code is {new_room_code}", "utf-8"))
    elif response == "join":
        # Receive valid room code from client
        response, _ = recv(csock)
        response = response.decode("utf-8")

        while response == "-1":
            room_codes = [room.code for room in unfilled]
            pickled_room_codes = pickle.dumps(room_codes)
            send(csock, pickled_room_codes)

            response, _ = recv(csock)
            response = response.decode("utf-8")

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
