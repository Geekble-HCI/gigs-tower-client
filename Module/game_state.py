import threading
import time
from .sound_manager import SoundManager

class GameState:
    INIT = "INIT"  # 새로운 상태 추가
    WAITING = "WAITING"
    COUNTDOWN = "COUNTDOWN"
    PLAYING = "PLAYING"
    SCORE = "SCORE"
    RESULT = "RESULT"  # 새로운 상태 추가

class GameStateManager:
    def __init__(self, screen_update_callback, state_change_callback=None, game_type=1):
        self.current_state = GameState.INIT  # 초기 상태를 INIT으로 변경
        self.countdown = 10
        self.timer_thread = None
        self.screen_update_callback = screen_update_callback
        self.sound_manager = SoundManager(game_type)  # game_type 전달
        self.result_thread = None
        self.score_thread = None  # Add score timeout thread
        self.state_change_callback = state_change_callback  # 상태 변경 콜백 추가
        self.play_thread = None
        
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
        self.sound_manager.play_sound_loop('playing')
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
        self.sound_manager.play_sound('score')
        self.screen_update_callback(f"당신의 점수는?\n\n{score}\n\n태그를 하여\n점수를 획득하세요!")
        
        def score_timer():
            time.sleep(15)  # 15초 대기
            if self.current_state == GameState.SCORE:  # 여전히 SCORE 상태라면
                self.show_waiting()  # WAITING 상태로 전환
        
        # 이전 타이머가 있다면 정리
        if self.score_thread and self.score_thread.is_alive():
            self.score_thread.join(0)
        self.score_thread = threading.Thread(target=score_timer, daemon=True)
        self.score_thread.start()

    def show_result(self, score):
        self.current_state = GameState.RESULT
        self.sound_manager.play_sound('result')
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
        self.countdown = 10
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(0)
        self.timer_thread = None
        self.sound_manager.stop_sound()
        # self.sound_manager.play_sound_loop('waiting')
        self.screen_update_callback("칼로링머신\n\n태그를 하면\n게임이 시작됩니다!")

    def show_init(self):
        """초기화 상태 표시"""
        self.current_state = GameState.INIT
        self.sound_manager.play_sound_loop('init')  # 대기 사운드 재생
        self.screen_update_callback("시스템 초기화 중...")
