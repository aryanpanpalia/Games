import pickle
import random
import socket
import threading
import time

import model
from model import WHITE, BLACK, GameRules, CHECKMATE, GAME_IN_PLAY, STALEMATE


class Room:
    def __init__(self, host, code):
        self.player1: socket.socket = host
        self.player2: socket.socket = None
        self.code: int = code

    def play(self):
        self.player1.send(bytes("LET THE GAME BEGIN", "utf-8"))
        self.player2.send(bytes("LET THE GAME BEGIN", "utf-8"))

        g = model.Game()
        running = True
        players = {"WHITE": self.player1, "BLACK": self.player2}
        colors = {self.player1: "WHITE", self.player2: "BLACK"}
        turn = WHITE
        color = "WHITE"

        while running:
            color = "WHITE" if turn == WHITE else "BLACK"

            # Before each turn (white and black), send each player the game, their color, and which color's turn it is
            # Client-side: both players will display whose turn it is as well as the board, however, the player whose turn it is will then be in an input-loop and asked
            # to give a valid move until they succeed to do so (move will be checked client-side for validity). Then the move will be sent to the server and applied

            pickled_game = pickle.dumps(g)
            self.player1.sendall(pickled_game)
            self.player1.sendall(bytes(colors[self.player1], "utf-8"))
            self.player1.sendall(bytes(color, "utf-8"))

            self.player2.sendall(pickled_game)
            self.player2.sendall(bytes(colors[self.player2], "utf-8"))
            self.player2.sendall(bytes(color, "utf-8"))

            time.sleep(5)

            if GameRules.check_if_game_ended(g) == CHECKMATE:
                print(f"Checkmate! {color} won!")
                running = False
            elif GameRules.check_if_game_ended(g) == STALEMATE:
                print("Stalemate!")
                running = False

            turn *= -1

    def __repr__(self):
        return f"{self.player1}; {self.player2}; {self.code}"


unfilled = []
filled = []
rooms = []

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('0.0.0.0', 55555))


def handle_new_connection(csock, addr):
    csock.send(bytes("Welcome to Chess!", "utf-8"))
    csock.send(bytes("Do you want to create or join a room: ", "utf-8"))

    response = csock.recv(1024).decode("utf-8")

    if response.lower() == "create":
        new_room_code = random.choice([x for x in range(1, 10000) if x not in [room.code for room in rooms]])
        new_room = Room(csock, new_room_code)
        unfilled.append(new_room)
        rooms.append(new_room)
        csock.send(bytes(f"Your room code is {new_room_code}", "utf-8"))
    elif response.lower() == "join":
        # prompt them for join code then set them as player 2
        csock.send(bytes("Enter the room code: ", "utf-8"))
        response = csock.recv(1024).decode("utf-8")

        for room in unfilled:
            if int(response) == room.code:
                room.player2 = csock

                unfilled.remove(room)
                filled.append(room)

                room.player1.send(bytes("Someone has joined the room!", "utf-8"))
                csock.send(bytes(f"Joined room!", "utf-8"))

                room_thread = threading.Thread(target=room.play)
                room_thread.start()


def handle_new_connections():
    s.listen()

    while True:
        clientsocket, address = s.accept()
        handle_new_connection_thread = threading.Thread(target=handle_new_connection, args=(clientsocket, address))
        handle_new_connection_thread.start()


handle_new_connections_thread = threading.Thread(target=handle_new_connections)
handle_new_connections_thread.start()

while True:
    time.sleep(1)
