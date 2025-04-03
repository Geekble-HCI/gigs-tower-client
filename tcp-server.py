import socket

HOST = '0.0.0.0'  # 모든 외부 접속 허용
PORT = 12345

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"서버 시작됨. 포트 {PORT}에서 대기 중...")

client_socket, addr = server_socket.accept()
print(f"[접속됨] {addr}")

try:
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        message = data.decode()
        print(f"[받은 메시지] {message}")

        # 에코 응답
        client_socket.sendall(f"받았음: {message}".encode())

except KeyboardInterrupt:
    print("서버 종료")

client_socket.close()
server_socket.close()