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

        self.serial_handler.setup()
        self.serial_handler.start_monitoring()

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
        running = True
        self.game_state.show_waiting()  # 초기 대기 화면 표시
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
