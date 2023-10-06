import socket
import json

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def connect_to_server(host="localhost", port=12345):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    return client_socket


def send_game_state(client_socket, x, y):
    game_state = {"x": x, "y": y}
    serialized_state = json.dumps(game_state)
    client_socket.send(serialized_state.encode("utf-8"))


# Receive the updates game state from the server
def receive_game_state(client_socket):
    received_data = client_socket.recv(1024).decode("utf-8")
    updated_state = json.loads(received_data)

    # extract player_id from the received game state
    player_id = updated_state.get("player_id", "Unknown Player ID")

    return updated_state["x"], updated_state["y"], player_id
