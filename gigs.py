import pygame
from Module.sound_manager import SoundManager
from Module.tcp_handler import TCPHandler
from Module.serial_handler import SerialHandler
from Module.game_state import GameState, GameStateManager
from Module.screen_manager import ScreenManager
from Module.score_manager import ScoreManager
from Module.input_handler import InputHandler
from Module.mqtt_manager import MQTTManager


class GIGS:
    # ============================================================================
    # 초기화 관련 메서드들
    # ============================================================================
    
    def __init__(self, use_tcp=False, game_type=1, show_enter=False, show_exit=False, score_wait_time=15, countdown_time=10, mqtt_broker=None, mqtt_client_id=None):
        pygame.init()
        
        self.sound_manager = SoundManager(game_type)
        self.screen_manager = ScreenManager()
        self.input_handler = InputHandler(self)
        self.score_manager = ScoreManager()
        self.serial_handler = SerialHandler(self.input_handler.handle_serial_input)
        self.mqtt_manager = MQTTManager(mqtt_broker, mqtt_client_id, self.sound_manager)

        self.game_state = GameStateManager(
            self.screen_manager.update_screen,
            self.handle_state_change,
            game_type,
            score_wait_time,
            countdown_time,
            self.mqtt_manager.get_client()
        )

        self.init_mode(show_enter, show_exit, use_tcp)

    def init_mode(self, show_enter, show_exit, use_tcp):
        if show_enter:
            # 입장 모드: 입장 화면만 표시
            self.game_state.show_enter()
        elif show_exit:
            # 퇴장 모드: 퇴장 화면만 표시
            self.game_state.show_exit()
        else:
            # 일반 게임 모드: 초기화 화면 표시 후 통신 설정
            self.game_state.show_init()
            self.setup_communications(use_tcp)

    # ============================================================================
    # 통신 관련 메서드들
    # ============================================================================
    
    def setup_communications(self, use_tcp):
        # TCP 핸들러 조건부 초기화
        self.tcp_handler = None
        self.use_tcp = use_tcp
        if use_tcp:
            self.tcp_handler = TCPHandler(self.OnReceivedTCPMessage)
            self.tcp_handler.setup()
            self.tcp_handler.start_monitoring()

        # Serial 핸들러 초기화
        self.serial_handler.setup()
        self.serial_handler.start_monitoring()

    def wait_for_connections(self):
        while True:
            self.input_handler.process_events()
            self.screen_manager.process_message_queue()
            
            if self.game_state.current_state in [GameState.ENTER, GameState.EXIT]:
                pygame.time.wait(100)
                continue
            
            if self.serial_handler.is_ready():
                if not self.use_tcp or (self.use_tcp and self.tcp_handler.is_ready()):
                    break
            
            pygame.time.wait(100)
        
        if self.game_state.current_state not in [GameState.ENTER, GameState.EXIT]:
            self.game_state.show_waiting()

    def OnReceivedTCPMessage(self, message):
        try:
            score = float(message)
            if score > 0 and self.game_state.current_state == GameState.PLAYING:
                self.score_manager.add_score(score)
        except ValueError:
            print(f"Invalid message format: {message}")

    # ============================================================================
    # 게임 상태 관리 메서드들
    # ============================================================================
    
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
        self.wait_for_connections()
        
        running = True
        while running:
            running = self.input_handler.process_events()
            
            self.screen_manager.process_message_queue()
            pygame.time.wait(10)
