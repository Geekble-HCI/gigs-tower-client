import threading
import time
from .sound_manager import SoundManager

class GameState:
    WAITING = "WAITING"
    COUNTDOWN = "COUNTDOWN"
    PLAYING = "PLAYING"
    SCORE = "SCORE"
    RESULT = "RESULT"  # 새로운 상태 추가

class GameStateManager:
    def __init__(self, screen_update_callback):
        self.current_state = GameState.WAITING
        self.countdown = 10
        self.timer_thread = None
        self.screen_update_callback = screen_update_callback
        self.sound_manager = SoundManager()
        self.result_thread = None

    def start_countdown(self):
        self.current_state = GameState.COUNTDOWN
        self.countdown = 10
        self.sound_manager.play_sound('countdown')
        
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
        self.sound_manager.play_sound('playing')
        self.screen_update_callback("게임 진행 중...")

    def show_score(self, score):
        self.current_state = GameState.SCORE
        self.sound_manager.play_sound('score')
        self.screen_update_callback(f"당신의 점수는?\n\n{score}\n\n태그를 하여\n점수를 획득하세요!")

    def show_result(self, score):
        self.current_state = GameState.RESULT
        self.screen_update_callback(f"{score}점을\n획득했습니다!")
        
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
        self.countdown = 10
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(0)
        self.timer_thread = None
        self.sound_manager.play_sound('waiting')
        self.screen_update_callback("칼로링머신\n\n태그를 하면\n게임이 시작됩니다!")
