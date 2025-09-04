import serial
import serial.tools.list_ports
import threading
import time

class SerialHandler:
    def __init__(self, gigs_instance=None):
        self.serial_ports = {}  # 여러 시리얼 포트를 저장하는 딕셔너리
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
        self._gigs = gigs_instance  # GIGS 인스턴스 참조

    def setup(self):
        def setup_worker():
            while not self.is_connected:
                try:
                    ports = list(serial.tools.list_ports.comports())
                    connected_count = 0
                    
                    for port in ports:
                        if port.device in self.excluded_ports:
                            continue
                        if port.device not in self.serial_ports:
                            try:
                                new_port = serial.Serial(port.device, 115200, timeout=1)
                                self.serial_ports[port.device] = new_port
                                print(f"Connected to {port.device}")
                                connected_count += 1
                                # 각 포트마다 모니터링 시작
                                self.start_port_monitoring(port.device, new_port)
                            except:
                                print(f"Failed to connect to {port.device}")
                    
                    if connected_count > 0:
                        self.is_connected = True
                        return
                    
                    print("No suitable serial ports found, retrying...")
                except Exception as e:
                    print(f"Serial port error: {e}")
                time.sleep(1)

        self.setup_thread = threading.Thread(target=setup_worker, daemon=True)
        self.setup_thread.start()
        return True

    def start_port_monitoring(self, port_device, port):
        """각 포트별 모니터링 스레드 시작"""
        def port_monitor():
            while True:
                try:
                    if port.is_open and port.in_waiting:
                        received_data = port.readline().decode().strip()
                        print(f"[SERIAL] Input from {port_device}: {received_data}")
                        
                        # 'a' 신호를 받으면 RFID 처리
                        if received_data == 'a':
                            self._handle_rfid_detected()

                        # 이외의 serial 신호를 받으면 점수 처리
                        elif received_data.isdigit():
                            from Module.game_state import GameState
                            current_state = self._gigs.game_state.current_state

                            score_to_add = int(received_data)
                            if current_state == GameState.PLAYING:
                                self._gigs.score_manager.add_score(score_to_add)
                                print(f"[SERIAL] Added {score_to_add} points!")
                except:
                    print(f"Error reading from {port_device}")
                    break
                time.sleep(0.1)

        monitor_thread = threading.Thread(target=port_monitor, daemon=True)
        monitor_thread.start()

    def is_ready(self):
        """하나 이상의 시리얼 연결이 준비되었는지 확인"""
        return self.is_connected
        # return True # 로컬 테스트용 

    def start_monitoring(self):
        """이제 개별 포트 모니터링은 setup 과정에서 처리"""
        pass

    def _handle_rfid_detected(self):
        """RFID 카드 감지 시 호출되는 메서드"""
        if not self._gigs:
            print("[SERIAL] No GIGS instance available")
            return
            
        from Module.game_state import GameState
        current_state = self._gigs.game_state.current_state
        print(f"[SERIAL] RFID card detected! Current state: {current_state}")
        
        # 상태별 처리 (input_handler의 A키와 동일한 로직)
        if current_state == GameState.INIT:
            print("[SERIAL] INIT -> WAITING")
            self._gigs.game_state.show_waiting()
        elif current_state == GameState.WAITING:
            print("[SERIAL] WAITING -> COUNTDOWN")
            if self._gigs.use_tcp:
                self._gigs.tcp_handler.send_message('-1')
            self._gigs.game_state.start_countdown()
        elif current_state == GameState.PLAYING:
            print("[SERIAL] PLAYING -> RESULT (forcing game end)")
            # 테스트용 점수로 결과 화면 표시
            test_score = self._gigs.score_manager.get_total_score()
            if test_score == 0:
                test_score = 7176  # 기본 테스트 점수
            self._gigs.game_state.show_result(test_score)
        else:
            print(f"[SERIAL] RFID detected in {current_state} - no action")

    def cleanup(self):
        """모든 시리얼 포트 정리"""
        for port in self.serial_ports.values():
            if port and port.is_open:
                port.close()
