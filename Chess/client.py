import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((socket.gethostname(), 55555))

    # Welcome message
    msg = s.recv(1024)
    print(msg.decode("utf-8"))

    # Whether joining or creating a room
    msg = s.recv(1024)
    print(msg.decode("utf-8"))
    response = input()
    s.send(bytes(response, "utf-8"))

    if response.lower() == "create":
        msg = s.recv(1024)
        print(msg.decode("utf-8"))
    elif response.lower() == "join":
        msg = s.recv(1024)
        print(msg.decode("utf-8"))
        response = input()
        s.send(bytes(response, "utf-8"))


    msg = s.recv(1024)
    print(msg.decode("utf-8"))

    msg = s.recv(1024)