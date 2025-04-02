import time
import threading
import keyboard

class GameState:
    WAITING = "WAITING"
    COUNTDOWN = "COUNTDOWN"
    PLAYING = "PLAYING"
    SCORE = "SCORE"

class CalorieMachine:
    def __init__(self):
        self.current_state = GameState.WAITING
        self.countdown = 10
        self.timer_thread = None

    def show_waiting_screen(self):
        print("\n--- 칼로링머신 ---")
        print("게임을 시작하려면 A키를 누르세요.")

    def start_countdown(self):
        self.current_state = GameState.COUNTDOWN
        self.countdown = 10
        print("\n게임이 곧 시작됩니다.")
        
        def countdown_timer():
            while self.countdown > 0 and self.current_state == GameState.COUNTDOWN:
                print(f"카운트다운: {self.countdown}")
                self.countdown -= 1
                time.sleep(1)
            if self.current_state == GameState.COUNTDOWN:
                self.start_game()

        self.timer_thread = threading.Thread(target=countdown_timer)
        self.timer_thread.start()

    def start_game(self):
        self.current_state = GameState.PLAYING
        print("\n게임 진행 중...")

    def show_score(self):
        self.current_state = GameState.SCORE
        print("\n당신의 점수는? 100점")
        print("태그를 하여 점수를 획득하세요!")
        
        def auto_return():
            time.sleep(10)
            if self.current_state == GameState.SCORE:
                self.current_state = GameState.WAITING
                self.show_waiting_screen()

        self.timer_thread = threading.Thread(target=auto_return)
        self.timer_thread.start()

    def handle_key_press(self, key):
        if key == 'a':
            if self.current_state in [GameState.WAITING, GameState.SCORE]:
                self.start_countdown()
        elif key == 'b':
            if self.current_state == GameState.PLAYING:
                self.show_score()

    def run(self):
        self.show_waiting_screen()
        
        keyboard.on_press(lambda e: self.handle_key_press(e.name))
        
        try:
            keyboard.wait('esc')  # esc 키를 누르면 프로그램 종료
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    game = CalorieMachine()
    game.run()
