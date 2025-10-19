from sched import Event
from Module.game.events import GameEvent, EventType, InputSource
from typing import Callable, Optional
import serial
import serial.tools.list_ports
import threading
import time

class SerialHandler:
    def __init__(self, gigs_instance=None, on_event: Optional[Callable[[Event], None]] = None):
        self.serial_ports = {}  # 여러 시리얼 포트를 저장
        self.excluded_ports = [
            '/dev/cu.debug-console',
            '/dev/cu.Bluetooth-Incoming-Port',
            '/dev/cu.iPhone-WirelessiAP',
            '/dev/tty.Bluetooth-Incoming-Port',
            '/dev/tty.debug-console',
            '/dev/cu.BT-RY'
        ]
        self.is_connected = False
        self._stop_threads = False  # 스레드 중단 플래그
        self.setup_thread = None
        self._gigs = gigs_instance
        self._on_event = on_event

        self.setup()

    # ---------------------------
    # 연결 설정
    # ---------------------------
    
    def setup(self):
        def setup_worker():
            while not self._stop_threads:
                try:
                    ports = list(serial.tools.list_ports.comports())
                    # 이미 열린 포트 개수로 초기화
                    connected_count = sum(1 for p in self.serial_ports.values() if p.is_open)

                    for port in ports:
                        if port.device in self.excluded_ports or port.device.startswith("/dev/tty."):
                            continue

                        if port.device not in self.serial_ports:
                            try:
                                new_port = serial.Serial(port.device, 115200, timeout=1)
                                self.serial_ports[port.device] = new_port
                                print(f"[SERIAL] Connected to {port.device}")
                                connected_count += 1
                                self.start_port_monitoring(port.device, new_port)
                            except Exception as e:
                                print(f"[SERIAL] Failed to connect to {port.device}: {e}")

                    self.is_connected = connected_count > 0

                    if not self.is_connected:
                        print("[SERIAL] No suitable ports found, retrying...")
                        time.sleep(2)
                    else:
                        time.sleep(3)
                        for device, port in list(self.serial_ports.items()):
                            if not port.is_open:
                                print(f"[SERIAL] Port {device} closed, reconnecting...")
                                self.reset_and_reconnect_port(device)

                except Exception as e:
                    print(f"[SERIAL] Setup error: {e}")
                    time.sleep(2)

        self.setup_thread = threading.Thread(target=setup_worker, daemon=True)
        self.setup_thread.start()
        print(f"[THREAD] setup_thread started (total active: {threading.active_count()})")
        return True

    # ---------------------------
    # 포트 모니터링
    # ---------------------------
    def start_port_monitoring(self, port_device, port):
        def port_monitor():
            while not self._stop_threads:
                try:
                    if not port.is_open:
                        break
                    if port.in_waiting:
                        raw = port.readline().decode(errors="ignore").strip()
                        if raw:
                            print(f"[SERIAL] Input from {port_device}: {raw}")
                            self._dispatch_serial_input(raw)
                except Exception as e:
                    print(f"[SERIAL] Error reading from {port_device}: {e}")
                    try:
                        port.close()
                    except:
                        pass
                    self.serial_ports.pop(port_device, None)
                    break
                time.sleep(0.05)

        monitor_thread = threading.Thread(target=port_monitor, daemon=True, name=f"SerialMonitor-{port_device}")
        monitor_thread.start()
        print(f"[THREAD] port_monitor started for {port_device} (total active: {threading.active_count()})")
    


    # ---------------------------
    # 입력 분기 처리
    # ---------------------------
    def _dispatch_serial_input(self, received_data: str):
        ev = self._parse_serial_data(received_data)
        if ev and self._on_event:
            self._on_event(ev)

    def _parse_serial_data(self, s: str):
        if not s:
            return None
        if len(s) == 8 and s.isalnum():
            return GameEvent(kind=EventType.RFID_DETECTED, source=InputSource.SERIAL, raw=s)
        if s == 'a':
            return GameEvent(kind=EventType.RFID_DETECTED, source=InputSource.SERIAL, raw=s)
        try:
            score_value = float(s)
            return GameEvent(kind=EventType.SCORE_RECEIVED, source=InputSource.SERIAL, raw=s, score=score_value)
        except ValueError:
            pass
        return GameEvent(kind=EventType.UNKNOWN, source=InputSource.SERIAL, raw=s)

    # ---------------------------
    # 상태 확인
    # ---------------------------
    def is_ready(self):
        """현재 연결이 유효한지"""
        return any(port.is_open for port in self.serial_ports.values())

    # ---------------------------
    # cleanup 개선
    # ---------------------------
    def cleanup(self):
        """모든 포트 및 스레드 안전 종료"""
        print("[SERIAL] Cleanup started...")
        self._stop_threads = True  # 스레드 종료 플래그 설정

        # 포트 닫기
        for device, port in list(self.serial_ports.items()):
            try:
                if port.is_open:
                    port.close()
                    print(f"[SERIAL] Closed {device}")
            except Exception as e:
                print(f"[SERIAL] Error closing {device}: {e}")

        self.serial_ports.clear()
        self.is_connected = False
        print("[SERIAL] Cleanup complete")

    # ---------------------------
    # 리셋 및 재연결
    # ---------------------------
    def reset_and_reconnect_port(self, device: str):
        port = self.serial_ports.get(device)
        if not port:
            print(f"[SERIAL] No active port found for {device}")
            return False

        try:
            if port.is_open:
                print(f"[SERIAL] Resetting {device}...")
                port.setDTR(False)
                time.sleep(0.5)
                port.setDTR(True)
                port.close()
                time.sleep(1)

                new_port = serial.Serial(device, 115200, timeout=1)
                self.serial_ports[device] = new_port
                print(f"[SERIAL] Reconnected to {device}")
                self.start_port_monitoring(device, new_port)
                self.is_connected = True
                return True
        except Exception as e:
            print(f"[SERIAL] Failed to reset {device}: {e}")
            self.is_connected = False
            return False

    def reset_and_reconnect_ports(self):
        for device in list(self.serial_ports.keys()):
            self.reset_and_reconnect_port(device)

    # ---------------------------
    # 메시지 전송
    # ---------------------------
    def send_message(self, message):
        if not self.is_ready():
            print(f"[SERIAL] Send skipped: no active ports - {message}")
            return
        
        for device, port in list(self.serial_ports.items()):
            try:
                if port.is_open:
                    port.write(f"{message}\n".encode())
                    port.flush()
                    print(f"[SERIAL] Sent '{message}' to {device}")
            except Exception as e:
                print(f"[SERIAL] Failed to send '{message}' to {device}: {e}")