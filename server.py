import socket
import threading
import json

# Initialise the server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# bind the socket to an address and port
host = "localhost"
port = 12345
server_socket.bind((host, port))

# start listening for incomming connections
server_socket.listen()

# a dictionary for holding game state, including connected players
game_state = {"player_1": {"x": 0, "y": 0}, "player_2": {"x": 0, "y": 0}}

# counter for tracking the number of connected clients
client_counter = 0


def handle_client(client_socket, address):
    global client_counter
    client_counter += 1

    # assign a player ID based on the counter
    player_id = f"player_{client_counter}"
    print(f"new connection from {address} as {player_id}")

    initial_data = {"player_id": player_id}
    initial_json_data = json.dumps(initial_data)
    client_socket.send(initial_json_data.encode("utf-8"))

    while True:
        try:
            # receive data from the client (expeted bytes may need to change from 1024)
            data = client_socket.recv(1024)

            # if no data is received, the client has disconnected
            if not data:
                print(f"Connection from {address} closed")
                break

            # Deserialize recieved data and update the game state
            json_data = data.decode("utf-8")
            client_state = json.loads(json_data)

            # Update the game_state based on client_state
            game_state[player_id] = client_state

            # Serialize the game state and send it back to the client
            json_reply = json.dumps({"game_state": game_state, "player_id": player_id})
            client_socket.send(json_reply.encode("utf-8"))

            print(f"Received client_state: {client_state}")
            print(f"Sending game_state: {game_state}")

        except Exception as error:
            print(f"An error occurred: {error}")
            break

    client_socket.close()


# Main loop to accept incoming connections
while True:
    client_socket, address = server_socket.accept()

    # start a new thread to handle the client
    client_thread = threading.Thread(
        target=handle_client, args=(client_socket, address)
    )
    client_thread.start()
