import pygame
from Module.game_handler import GameHandler
from Module.sound_manager import SoundManager
from Module.serial_handler import SerialHandler
from Module.game_state import GameState, GameStateManager
from Module.screen_manager import ScreenManager
from Module.score_manager import ScoreManager
from Module.input_handler import InputHandler
from Module.mqtt_manager import MQTTManager

# 👇 추가
from Module.game_action_handler import GameActionHandler
from Module.events import EventType

class GIGS:
    # ============================================================================
    # 초기화 관련 메서드들
    # ============================================================================
    def __init__(self, game_type=1, show_enter=False, show_exit=False,
                 score_wait_time=15, countdown_time=10, mqtt_broker=None, device_id=None,
                 test_mode=False):
        pygame.init()

        # 테스트 모드이면 countdown_time을 1초로
        self.test_mode = test_mode
        if self.test_mode:
            countdown_time = 1

        # 기본 컴포넌트
        self.sound_manager = SoundManager(game_type)
        self.screen_manager = ScreenManager()
        self.score_manager = ScoreManager()

        self.game_state = GameStateManager(
            screen_update_callback=self.screen_manager.update_screen,
            state_change_callback=self.handle_state_change,
            game_type=game_type,
            score_wait_time=score_wait_time,
            countdown_time=countdown_time,
            mqtt_client=None  # GameStateManager 먼저 생성 (mqtt_client는 아래에서 주입)
        )

        # 액션 핸들러 생성(상태 전환의 단일 진입점)
        action = GameActionHandler(gsm=self.game_state, gigs_instance=self)

        # 입력/명령 핸들러에 action 주입
        self.input_handler = InputHandler(self, action_handler=action)
        self.game_handler = GameHandler(self, action_handler=action)

        # Serial은 on_event 콜백으로 라우팅
        self.serial_handler = SerialHandler(self, on_event=lambda ev: self._route_serial_event(action, ev))

        # MQTT 매니저 생성 - GameActionHandler(action)를 전달 (RFID 검증 응답 처리용)
        self.mqtt_manager = MQTTManager(mqtt_broker, device_id, game_type, self.sound_manager, action)

        # MQTT 클라이언트를 GameStateManager에 "사후 주입"
        client = self.mqtt_manager.get_client()
        self.game_state.mqtt_client = client
        self.game_state.device_id = client.device_id if client else "unknown_client"
        self.game_state.device_ip = client.ip_address if client else "unknown_ip"

        # MQTTManager에 GameStateManager 연결 (에러 메시지 처리를 위해 필요)
        self.mqtt_manager.set_game_state_manager(self.game_state)

        # 모드 플래그
        self.test_mode = test_mode

        self.init_mode(show_enter, show_exit, test_mode)

    # 시리얼 이벤트 → 액션 핸들러 라우팅
    def _route_serial_event(self, action, ev):
        if ev.kind == EventType.RFID_DETECTED:
            action.on_rfid_detected(ev)
        elif ev.kind == EventType.SCORE_RECEIVED:
            action.on_score_received(ev)
        elif ev.kind in (EventType.GAME_START, EventType.GAME_STOP, EventType.GAME_RESET):
            action.on_command(ev)
        else:
            print(f"[Serial] Unknown/ignored: {ev.raw}")

    def init_mode(self, show_enter, show_exit, test_mode):
        if test_mode:
            print("[TEST MODE] Keyboard input enabled:")
            print("  - A: Mock RFID detected (8-char UID : QWER1234)")
            print("  - B: Mock Score +10")
            print("  - ESC: Exit")


        if show_enter:
            self.game_state.show_enter()
        elif show_exit:
            self.game_state.show_exit()
        else:
            self.game_state.show_init()
        
        # ENTER/EXIT/GAME 모드 모두 시리얼 통신 설정 필요
        self.setup_communications()

    # ============================================================================
    # 통신 관련 메서드들
    # ============================================================================
    def setup_communications(self):
        self.serial_handler.setup()
        self.serial_handler.start_monitoring()


    def wait_for_connections(self):
        waiting_shown = False

        # 시리얼 재연결 즉시 시작
        self.serial_handler.reset_and_reconnect_ports()

        while True:
            running = self.input_handler.process_events()
            if not running:
                return

            self.screen_manager.process_message_queue()

            # 에러 상태면 자동복구/수동복구가 끝날 때까지 아무 것도 덮지 않고 루프만 돌게 함
            if self.game_state.current_state == GameState.ERROR:
                pygame.time.wait(50)
                continue

            # ENTER/EXIT 상태일 때는 루프 유지
            if self.game_state.current_state in [GameState.ENTER, GameState.EXIT]:
                pygame.time.wait(100)
                continue

            # 시리얼 준비 여부 확인
            serial_ready = self.serial_handler.is_ready()  # reset/reconnect 완료 시 True

            if serial_ready:
                 # 에러가 아닐 때만 WAITING을 초기 1회 표시
                if not waiting_shown and self.game_state.current_state not in [GameState.ERROR]:
                    self.game_state.show_waiting()
                    waiting_shown = True
                break

            pygame.time.wait(100)

    

    # ============================================================================
    # 게임 상태 관리 메서드들
    # ============================================================================
    def handle_state_change(self, new_state):
        if new_state == GameState.PLAYING:
            self.serial_handler.send_message('-2')
            self.score_manager.reset_score()
        elif new_state == GameState.SCORE:
            self.serial_handler.send_message('-3')
            final_score = int(self.score_manager.get_total_score())
            self.game_state.show_score(final_score)

    def run(self):
        self.wait_for_connections()
        running = True
        while running:
            running = self.input_handler.process_events()
            self.screen_manager.process_message_queue()
            pygame.time.wait(10)