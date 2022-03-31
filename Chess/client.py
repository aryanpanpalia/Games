import socket


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

        # Message from inside Room.play()
        msg = s.recv(1024)
        print(msg.decode("utf-8"))


if __name__ == '__main__':
    main()
