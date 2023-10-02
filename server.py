import socket
import threading
import json

# Initialise the server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# bind the socket to an address and port
host = "locahost"
port = 12345
server_socket.bind((host, port))

# start listening for incomming connections
server_socket.listen()

# a dictionary for holding game state, including connected players
game_state = {}


def handle_client(client_socket, address):
    print(f"new connection from {address}")
    while True:
        # receive data from the client (expeted bytes may need to change from 1024)
        data = client_socket.recv(1024)

        # if no data is received, the client has disconnected
        if not data:
            print(f"Connection from {address} closed")
            break

        # Deserialize recieved data and update the game state
        json_data = data.decode("utf-8")
        client_state = json.loads(json_data)

        # TODO Update the game_state based on client_state

        # Serialize the game state and send it back to the client
        json_reply = json.dumps(game_state)
        client_socket.send(str.encode(json_reply))

    client_socket.close()

    # Main loop to accept incoming connections
    while True:
        client_socket, address = server_socket.accept()

        # start a new thread to handle the client
        client_thread = threading.Thread(
            target=handle_client, args=(client_socket, address)
        )
        client_thread.start()
