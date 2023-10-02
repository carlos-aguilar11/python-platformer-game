import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = "localhost"
port = 12345
client_socket.bind((host, port))

while True:
    # TODO: Gather the client's game state (like position, actions, etc.)

    # Fake data
    some_data = "My Game state"

    # Send the game state data to the server
    client_socket.send(some_data.encode("utf-8"))

    # Receive the updates game state from the server
    received_data = client_socket.recv(1024).decode("utf-8")

    # TODO Update the client's game state based on received data

    # For demonstartion, printing the received data
    print(f"Received from Server: {received_data}")

    # TODO Add a condition to break out of the loop, perhaps based on user input or game state
