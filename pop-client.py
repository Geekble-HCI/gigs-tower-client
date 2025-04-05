import pygame
import sys
from Module.serial_handler import SerialHandler
from Module.game_state import GameState, GameStateManager
from Module.screen_manager import ScreenManager

class CalorieMachine:
    def __init__(self):
        pygame.init()
        
        self.screen_manager = ScreenManager()
        self.game_state = GameStateManager(self.screen_manager.update_screen)
        self.serial_handler = SerialHandler(self.handle_input)

        # 초기화 상태 표시
        self.game_state.show_init()

        # 각 모듈 초기화 시작
        self.serial_handler.setup()
        
        # 모니터링 시작
        self.serial_handler.start_monitoring()

    def wait_for_connections(self):
        """모든 연결이 준비될 때까지 대기"""
        while not (self.serial_handler.is_ready()):
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    pygame.quit()
                    sys.exit()
            self.screen_manager.process_message_queue()
            pygame.time.wait(100)
        
        # 모든 연결이 준비되면 WAITING 상태로 전환
        self.game_state.show_waiting()

    def handle_input(self, input_value):
        if input_value == 'a':
            if self.game_state.current_state == GameState.SCORE:
                self.game_state.show_result(7176)  # 점수를 전달하여 결과 화면으로
            elif self.game_state.current_state == GameState.WAITING:
                self.game_state.start_countdown()

    def OnReceivedMessage(self, message):
        try:
            score = int(message)
            if score >= 0 and self.game_state.current_state == GameState.PLAYING:
                self.game_state.show_score(score)
        except ValueError:
            print(f"Invalid message format: {message}")

    def run(self):
        # 연결 대기
        self.wait_for_connections()
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.handle_input('a')
                    elif event.key == pygame.K_b and self.game_state.current_state == GameState.PLAYING:
                        self.game_state.show_score(7176)

            self.screen_manager.process_message_queue()
            pygame.time.wait(10)

if __name__ == "__main__":
    game = CalorieMachine()
    game.run()
