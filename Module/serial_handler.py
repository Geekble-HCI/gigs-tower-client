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

    def setup(self):
        print("Setting up serial port...")
        try:
            ports = list(serial.tools.list_ports.comports())
            for port in ports:
                if port.device in self.excluded_ports:
                    print(f"Skipping excluded port: {port.device}")
                    continue
                try:
                    self.serial_port = serial.Serial(port.device, 115200, timeout=1)
                    print(f"Connected to {port.device}")
                    return True
                except:
                    print(f"Failed to connect to {port.device}")
            print("No suitable serial port found")
            return False
        except Exception as e:
            print(f"Serial port error: {e}")
            return False

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
