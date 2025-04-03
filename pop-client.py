import pygame
import sys
import time
import threading
import queue

class GameState:
    WAITING = "WAITING"
    COUNTDOWN = "COUNTDOWN"
    PLAYING = "PLAYING"
    SCORE = "SCORE"

class CalorieMachine:
    def __init__(self):
        pygame.init()
        
        # 전체화면 설정
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.width = self.screen.get_width()
        self.height = self.screen.get_height()
        
        # 배경 이미지 로드 및 크기 조정
        self.bg_image = pygame.image.load("Image/bg.png")
        self.bg_image = pygame.transform.scale(self.bg_image, (self.width, self.height))
        
        # 한글 폰트 설정
        try:
            self.font = pygame.font.Font("Font/RoundSquare.ttf", 74)
        except:
            print("폰트 로드 실패, 기본 폰트 사용")
            self.font = pygame.font.Font(None, 74)
        
        # 게임 상태 변수 초기화
        self.timer_thread = None  # 먼저 timer_thread 초기화
        self.current_state = GameState.WAITING
        self.countdown = 10
        
        # 메시지 큐 추가
        self.message_queue = queue.Queue()

    def reset(self):
        """게임 상태 초기화"""
        # 스레드가 실행 중이면 정리
        if hasattr(self, 'timer_thread') and self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(0)
        
        self.timer_thread = None
        self.current_state = GameState.WAITING
        self.countdown = 10

    def draw_text(self, text):
        # 여러 줄 텍스트 처리
        lines = text.split('\n')
        y = self.height // 2 - (len(lines) * 40)
        
        for line in lines:
            text_surface = self.font.render(line, True, (0, 255, 0))  # RGB for #00FF00
            text_rect = text_surface.get_rect(center=(self.width//2, y))
            self.screen.blit(text_surface, text_rect)
            y += 80

    def update_screen(self, text):
        # 메인 스레드에서만 화면 업데이트
        if threading.current_thread() is threading.main_thread():
            self.screen.blit(self.bg_image, (0, 0))
            self.draw_text(text)
            pygame.display.flip()
        else:
            self.message_queue.put(text)

    def show_waiting_screen(self):
        self.reset()  # 모든 값 초기화
        self.update_screen("칼로링머신\n\n태그를 하면\n게임이 시작됩니다!")

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_a:
                    if self.current_state == GameState.SCORE:
                        self.show_waiting_screen()  # reset 호출됨
                    elif self.current_state == GameState.WAITING:
                        self.start_countdown()
                if event.key == pygame.K_b:
                    if self.current_state == GameState.PLAYING:
                        self.show_score()
        return True

    def start_countdown(self):
        self.current_state = GameState.COUNTDOWN
        self.countdown = 10
        
        def countdown_timer():
            while self.countdown > 0 and self.current_state == GameState.COUNTDOWN:
                self.message_queue.put(f"게임이 곧 시작됩니다.\n\n{self.countdown}")
                self.countdown -= 1
                time.sleep(1)
            if self.current_state == GameState.COUNTDOWN:
                self.start_game()

        self.timer_thread = threading.Thread(target=countdown_timer)
        self.timer_thread.daemon = True
        self.timer_thread.start()

    def start_game(self):
        self.current_state = GameState.PLAYING
        self.update_screen("게임 진행 중...")

    def show_score(self):
        self.current_state = GameState.SCORE
        self.update_screen("당신의 점수는?\n\n100\n\n태그를 하여\n점수를 획득하세요!")
        
        def auto_return():
            time.sleep(10)
            if self.current_state == GameState.SCORE:
                self.current_state = GameState.WAITING

        self.timer_thread = threading.Thread(target=auto_return)
        self.timer_thread.daemon = True
        self.timer_thread.start()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            
            # 메시지 큐 처리
            try:
                while True:
                    message = self.message_queue.get_nowait()
                    self.screen.blit(self.bg_image, (0, 0))
                    self.draw_text(message)
                    pygame.display.flip()
            except queue.Empty:
                pass
            
            if self.current_state == GameState.WAITING:
                self.update_screen("칼로링머신\n\n태그를 하면\n게임이 시작됩니다!")
            
            pygame.time.wait(10)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = CalorieMachine()
    game.run()
