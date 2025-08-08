import pygame
import sys
from Module.mqtt_client import MQTTClient
from Module.sound_manager import SoundManager
from Module.tcp_handler import TCPHandler
from Module.serial_handler import SerialHandler
from Module.game_state import GameState, GameStateManager
from Module.screen_manager import ScreenManager
from Module.score_manager import ScoreManager
from Module.command_handler import CommandDispatcher, CommandType, VolumeCommand
from Module.input_handler import InputHandler


class GIGS:
    def __init__(self, use_tcp=False, game_type=1, show_enter=False, show_exit=False, score_wait_time=15, countdown_time=10, mqtt_broker=None, mqtt_client_id=None):
        pygame.init()
        
        self.sound_manager = SoundManager(game_type)
        self.screen_manager = ScreenManager()
        self.input_handler = InputHandler(self)
        self.score_manager = ScoreManager()
        self.serial_handler = SerialHandler(self.input_handler.handle_serial_input)
        
        self.mqtt_client = None
        if mqtt_broker:
            
            # MQTT 브로커 topic 및 연결 설정
            self.mqtt_client = MQTTClient(mqtt_broker, 1883, mqtt_client_id)
            
            # IP 주소 기반 토픽 구독 설정
            self.mqtt_client.add_subscription(f"device/{self.mqtt_client.ip_address}/state")
            self.mqtt_client.add_subscription(f"device/{self.mqtt_client.ip_address}/command")
            
            # 글로벌 토픽도 유지 (관리용)
            # self.mqtt_client.add_subscription("device/+/state")
            # self.mqtt_client.add_subscription("device/+/command")
            # self.mqtt_client.add_subscription(f"device/{self.mqtt_client.client_id}/ping")
            # self.mqtt_client.add_subscription("broadcast/#")
            self.mqtt_client.connect()

        self.game_state = GameStateManager(
            self.screen_manager.update_screen,
            self.handle_state_change,
            game_type,
            score_wait_time,  # Pass the score wait time
            countdown_time,    # Pass the countdown time
            self.mqtt_client # MQTT 클라이언트 전달
        )

        # Initialize command handler for MQTT commands
        self.command_handler = None
        if self.mqtt_client:
            self.command_handler = CommandDispatcher()
            self.command_handler.register(CommandType.VOLUME, VolumeCommand(self.sound_manager))
            self.mqtt_client.set_message_callback(self._handle_mqtt_command)

        # 시작 상태 결정
        if show_enter:
            self.game_state.show_enter()
        elif show_exit:
            self.game_state.show_exit()
        else:
            self.game_state.show_init()
            # ENTER/EXIT가 아닐 때만 통신 초기화
            self.setup_communications(use_tcp)


    def setup_communications(self, use_tcp):
        """통신 초기화 함수"""
        # TCP 핸들러 조건부 초기화
        self.tcp_handler = None
        self.use_tcp = use_tcp
        if use_tcp:
            self.tcp_handler = TCPHandler(self.OnReceivedTCPMessage)
            self.tcp_handler.setup()
            self.tcp_handler.start_monitoring()

        self.serial_handler.setup()
        self.serial_handler.start_monitoring()

    def wait_for_connections(self):
        """모든 연결이 준비될 때까지 대기"""
        while True:
            # InputHandler로 이벤트 처리
            self.input_handler.process_events()
            
            # 화면 업데이트 처리
            self.screen_manager.process_message_queue()
            
            # ENTER나 EXIT 상태일 때는 연결 상태를 체크하지 않음
            if self.game_state.current_state in [GameState.ENTER, GameState.EXIT]:
                pygame.time.wait(100)
                continue
            
            # 연결 상태 체크
            if self.serial_handler.is_ready():
                if not self.use_tcp or (self.use_tcp and self.tcp_handler.is_ready()):
                    break
            
            pygame.time.wait(100)
        
        # ENTER나 EXIT 상태가 아닐 때만 WAITING으로 전환
        if self.game_state.current_state not in [GameState.ENTER, GameState.EXIT]:
            self.game_state.show_waiting()

    def _handle_mqtt_command(self, topic, payload):
        """Handle MQTT command messages"""
        try:
            if self.command_handler:
                command = payload['data']['command']
                value = payload['data']['value']
                time = payload['data']['timestamp']
                deviceId = payload['data']['deviceId']

                print(f"[MQTT] args: {command}, {value}, {time}, {deviceId}")

                success = self.command_handler.dispatch(command, value, time, deviceId)
                if not success:
                    print(f"[MQTT] Command processing failed for topic: {topic}")
                
            else:
                print("[MQTT] No command handler available")
        except Exception as e:
            print(f"[MQTT] Error in command handling: {e}")

    def OnReceivedTCPMessage(self, message):
        try:
            score = float(message)
            if score > 0 and self.game_state.current_state == GameState.PLAYING:
                self.score_manager.add_score(score)
        except ValueError:
            print(f"Invalid message format: {message}")

    def handle_state_change(self, new_state):
        """게임 상태가 변경될 때 호출되는 콜백"""
        if new_state == GameState.PLAYING:
            if self.use_tcp:
                self.tcp_handler.send_message('-2')
            self.score_manager.reset_score()
        elif new_state == GameState.SCORE:
            if self.use_tcp:
                self.tcp_handler.send_message('-3')
            final_score = self.score_manager.get_total_score()
            final_score = int(final_score)
            self.game_state.show_score(final_score)

    def run(self):
        # 연결 대기
        self.wait_for_connections()
        
        running = True
        while running:
            # InputHandler로 이벤트 처리
            running = self.input_handler.process_events()
            
            # 화면 메시지 큐 처리
            self.screen_manager.process_message_queue()
            pygame.time.wait(10)
