import pickle
import socket

import model

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
            g: model.Game = pickle.loads(s.recv(2277))
            my_color = s.recv(5).decode("utf-8")
            turn_color = s.recv(5).decode("utf-8")

            print(my_color, turn_color)
            g.display(my_color)



if __name__ == '__main__':
    main()
