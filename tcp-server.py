import socket

HOST = '0.0.0.0'
PORT = 12345

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"Server started. Listening on port {PORT}...")

client_socket, addr = server_socket.accept()
print(f"[Connected] {addr}")

try:
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        message = data.decode()
        print(f"[Received] {message}")

        client_socket.sendall(f"Message received: {message}".encode())

except KeyboardInterrupt:
    print("Server shutting down.")

client_socket.close()
server_socket.close()