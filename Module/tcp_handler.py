import socket
import threading
import time

class TCPHandler:
    def __init__(self, message_callback):
        self.HOST = '0.0.0.0'
        self.PORT = 12345
        self.tcp_socket = None
        self.client_socket = None
        self.message_callback = message_callback

    def setup(self):
        """TCP 연결 설정"""
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.bind((self.HOST, self.PORT))
            self.tcp_socket.listen(1)
            print(f"TCP server started. Listening on port {self.PORT}...")
            
            # 클라이언트 연결 대기
            self.client_socket, addr = self.tcp_socket.accept()
            print(f"[Connected] {addr}")
            return True
            
        except Exception as e:
            print(f"TCP server setup failed: {e}")
            self.tcp_socket = None
            self.client_socket = None
            return False

    def send_message(self, message):
        """TCP 메시지 전송"""
        if self.client_socket:
            try:
                self.client_socket.sendall(str(message).encode())
                print(f"[Sent] {message}")
            except Exception as e:
                print(f"Failed to send message: {e}")

    def start_monitoring(self):
        """TCP 메시지 모니터링"""
        def tcp_monitor():
            while True:
                if self.client_socket:
                    try:
                        data = self.client_socket.recv(1024)
                        if data:
                            message = data.decode()
                            self.message_callback(message)
                    except:
                        pass
                time.sleep(0.1)

        monitor_thread = threading.Thread(target=tcp_monitor, daemon=True)
        monitor_thread.start()

    def cleanup(self):
        """리소스 정리"""
        if self.client_socket:
            self.client_socket.close()
        if self.tcp_socket:
            self.tcp_socket.close()
