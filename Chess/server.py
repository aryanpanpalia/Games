import random
import socket


class Room:
    def __init__(self, host, code):
        self.player1 = host
        self.player2 = None
        self.code = code

    def __repr__(self):
        return f"{self.player1}; {self.player2}; {self.code}"


unfilled = []
filled = []
rooms = []


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(('0.0.0.0', 55555))
    s.listen()

    # IT TAKES A BIT FOR THE WHOLE ITERATION OF THE LOOP TO RUN
    # IF SOMEONE ELSE TRIES TO CONNECT WHILE THE ITERATION IS BEING RUN, THEY MIGHT BE VERY DELAYED OR IGNORED
    while True:
        clientsocket, address = s.accept()
        print(f"Connection from {address} established!")
        clientsocket.send(bytes("Welcome to Chess!", "utf-8"))
        clientsocket.send(bytes("Do you want to create or join a room: ", "utf-8"))

        response = clientsocket.recv(1024).decode("utf-8")

        if response.lower() == "create":
            new_room_code = random.choice([x for x in range(1, 10000) if x not in [room.code for room in rooms]])
            new_room = Room(clientsocket, new_room_code)
            unfilled.append(new_room)
            rooms.append(new_room)
            print(f"Created room {new_room}")
            clientsocket.send(bytes(f"Your room code is {new_room_code}", "utf-8"))
        elif response.lower() == "join":
            # prompt them for join code then set them as player 2
            clientsocket.send(bytes("Enter the room code: ", "utf-8"))
            response = clientsocket.recv(1024).decode("utf-8")

            for room in unfilled:
                if int(response) == room.code:
                    room.player2 = clientsocket

                    unfilled.remove(room)
                    filled.append(room)
                    print(f"Filled room {room}")

                    room.player1.send(bytes("Someone has joined the room!", "utf-8"))
                    clientsocket.send(bytes(f"Joined room!", "utf-8"))

        print(unfilled)
        print(filled)


