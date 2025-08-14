import threading
import time
from .sound_manager import SoundManager

class GameState:
    INIT = "INIT"
    WAITING = "WAITING"
    COUNTDOWN = "COUNTDOWN"
    PLAYING = "PLAYING"
    SCORE = "SCORE"
    RESULT = "RESULT"
    ENTER = "ENTER"  # 새로운 상태 추가
    EXIT = "EXIT"    # 새로운 상태 추가

class GameStateManager:
    def __init__(self, screen_update_callback, state_change_callback=None, game_type=1, score_wait_time=15, countdown_time=10, mqtt_client=None):
        self.current_state = GameState.INIT  # 초기 상태를 INIT으로 변경
        self.countdown = 10
        self.timer_thread = None
        self.screen_update_callback = screen_update_callback
        self.sound_manager = SoundManager(game_type)  # game_type 전달
        self.result_thread = None
        self.score_thread = None  # Add score timeout thread
        self.state_change_callback = state_change_callback  # 상태 변경 콜백 추가
        self.play_thread = None
        self.score_wait_time = score_wait_time  # Store the wait time
        self.countdown_time = countdown_time  # Store the countdown time
        self.mqtt_client = mqtt_client # MQTT 클라이언트 저장
        self.device_id = mqtt_client.device_id if mqtt_client else "unknown_client"
        self.device_ip = mqtt_client.ip_address if mqtt_client else "unknown_ip"
        
    def _publish_state(self, state, score=None):
        if self.mqtt_client:
            topic = f"device/{self.device_ip}/state" # IP 주소 기반 topic
            payload = {"device_id": self.device_id, "state": state }
            if score is not None:
                payload["score"] = score
            self.mqtt_client.publish(topic, payload)

    def start_countdown(self):
        self.current_state = GameState.COUNTDOWN
        self._publish_state(self.current_state)
        self.countdown = self.countdown_time  # Use the configured countdown time
        self.sound_manager.play_bgm('countdown')  # play_sound -> play_bgm
        
        def countdown_timer():
            while self.countdown > 0 and self.current_state == GameState.COUNTDOWN:
                self.screen_update_callback(f"게임이 곧 시작됩니다.\n\n{self.countdown}")
                self.countdown -= 1
                time.sleep(1)
            if self.current_state == GameState.COUNTDOWN:
                self.start_game()

        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(0)
        self.timer_thread = threading.Thread(target=countdown_timer)
        self.timer_thread.daemon = True
        self.timer_thread.start()

    def start_game(self):
        self.current_state = GameState.PLAYING
        self._publish_state(self.current_state)
        self.sound_manager.play_bgm_loop('playing')  # play_sound_loop -> play_bgm_loop
        self.screen_update_callback("게임 진행 중...")
        if self.state_change_callback:
            self.state_change_callback(GameState.PLAYING)
            
        def play_timer():
            time.sleep(60)  # 60초 대기
            if self.current_state == GameState.PLAYING:
                if self.state_change_callback:
                    self.state_change_callback(GameState.SCORE)
        
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(0)
        self.play_thread = threading.Thread(target=play_timer)
        self.play_thread.daemon = True
        self.play_thread.start()

    def show_score(self, score):
        self.current_state = GameState.SCORE
        self._publish_state(self.current_state, score=score)
        self.sound_manager.play_bgm('score')  # play_sound -> play_bgm
        self.screen_update_callback(f"당신의 점수는?\n\n{score}\n\n태그를 하여\n점수를 획득하세요!")
        
        def score_timer():
            time.sleep(self.score_wait_time)  # Use the configured wait time
            if self.current_state == GameState.SCORE:  # 여전히 SCORE 상태라면
                self.show_waiting()  # WAITING 상태로 전환
        
        # 이전 타이머가 있다면 정리
        if self.score_thread and self.score_thread.is_alive():
            self.score_thread.join(0)
        self.score_thread = threading.Thread(target=score_timer, daemon=True)
        self.score_thread.start()

    def show_result(self, score):
        self.current_state = GameState.RESULT
        self._publish_state(self.current_state, score=score)
        self.sound_manager.play_bgm('result')  # play_sound -> play_bgm
        self.screen_update_callback(f"{int(score)}점을\n획득했습니다!")
        
        def result_timer():
            time.sleep(3)  # 3초 대기
            if self.current_state == GameState.RESULT:
                self.show_waiting()
        
        if self.result_thread and self.result_thread.is_alive():
            self.result_thread.join(0)
        self.result_thread = threading.Thread(target=result_timer)
        self.result_thread.daemon = True
        self.result_thread.start()

    def show_waiting(self):
        """게임 상태를 대기 상태로 초기화"""
        self.current_state = GameState.WAITING
        self._publish_state(self.current_state)
        self.countdown = self.countdown_time  # Use the configured countdown time
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(0)
        self.timer_thread = None
        self.sound_manager.stop_bgm()

        # 게임 타입에 따른 메시지 설정
        game_messages = {
            1: "헬시 버거\n챌린지",
            2: "꿀잠 방해꾼\nOUT!",
            3: "불태워!\n칼로링머신",
            4: "볼볼볼\n영양소",
            5: "바이오데이터\n에어시소",
            6: "슛잇!\n무빙 골대"
        }
        
        game_title = game_messages.get(self.sound_manager.game_type, "칼로링머신")
        self.screen_update_callback(f"{game_title}\n\n태그를 하면\n게임이 시작됩니다!")

    def show_init(self):
        """초기화 상태 표시"""
        self.current_state = GameState.INIT
        self._publish_state(self.current_state)
        self.sound_manager.play_bgm_loop('waiting')  # play_sound_loop -> play_bgm_loop
        self.screen_update_callback("시스템 초기화 중...")

    def show_enter(self):
        """입장 상태 표시"""
        self.current_state = GameState.ENTER
        self._publish_state(self.current_state)
        self.sound_manager.play_bgm_loop('enter')  # enter.wav 또는 enter.mp3 필요
        self.screen_update_callback("게임을 시작해주세요!")

    def show_exit(self):
        """퇴장 상태 표시"""
        self.current_state = GameState.EXIT
        self._publish_state(self.current_state)
        self.sound_manager.play_bgm_loop('exit')  # exit.wav 또는 exit.mp3 필요
        self.screen_update_callback("수고하셨습니다!")
