import serial
import serial.tools.list_ports
import threading
import time

class SerialHandler:
    def __init__(self, input_callback):
        self.serial_port = None
        self.input_callback = input_callback
        self.excluded_ports = [
            '/dev/cu.debug-console',
            '/dev/cu.Bluetooth-Incoming-Port',
            '/dev/cu.iPhone-WirelessiAP',
            '/dev/tty.Bluetooth-Incoming-Port',
            '/dev/tty.debug-console',
            '/dev/cu.BT-RY'
        ]
        self.is_connected = False
        self.setup_thread = None

    def setup(self):
        def setup_worker():
            while not self.is_connected:
                try:
                    ports = list(serial.tools.list_ports.comports())
                    for port in ports:
                        if port.device in self.excluded_ports:
                            continue
                        try:
                            self.serial_port = serial.Serial(port.device, 115200, timeout=1)
                            print(f"Connected to {port.device}")
                            self.is_connected = True
                            return
                        except:
                            print(f"Failed to connect to {port.device}")
                    print("No suitable serial port found, retrying...")
                except Exception as e:
                    print(f"Serial port error: {e}")
                time.sleep(1)  # 1초 대기 후 재시도

        self.setup_thread = threading.Thread(target=setup_worker, daemon=True)
        self.setup_thread.start()
        return True  # 즉시 True 반환하고 백그라운드에서 연결 시도

    def is_ready(self):
        """시리얼 연결이 준비되었는지 확인"""
        return self.is_connected

    def start_monitoring(self):
        def serial_monitor():
            while True:
                if self.serial_port and self.serial_port.is_open:
                    try:
                        if self.serial_port.in_waiting:
                            received_data = self.serial_port.readline().decode().strip()
                            if received_data == 'a':
                                self.input_callback('a')
                    except:
                        pass
                time.sleep(0.1)

        monitor_thread = threading.Thread(target=serial_monitor, daemon=True)
        monitor_thread.start()

    def cleanup(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
