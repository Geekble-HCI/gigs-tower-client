import pygame
import sys
from Module.tcp_handler import TCPHandler
from Module.serial_handler import SerialHandler
from Module.game_state import GameState, GameStateManager
from Module.screen_manager import ScreenManager

class CalorieMachine:
    def __init__(self):
        pygame.init()
        
        self.screen_manager = ScreenManager()
        self.game_state = GameStateManager(self.screen_manager.update_screen)
        self.tcp_handler = TCPHandler(self.OnReceivedMessage)
        self.serial_handler = SerialHandler(self.handle_input)

        # 각 모듈 초기화
        self.tcp_handler.setup()
        self.tcp_handler.start_monitoring()
        self.tcp_handler.send_message("init")
        
        self.serial_handler.setup()
        self.serial_handler.start_monitoring()

    def handle_input(self, input_value):
        self.tcp_handler.send_message('-1')
        if input_value == 'a':
            if self.game_state.current_state == GameState.SCORE:
                self.game_state.show_waiting()
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
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.handle_input('a')
                    elif event.key == pygame.K_b and self.game_state.current_state == GameState.PLAYING:
                        self.game_state.show_score(7176)

            self.screen_manager.process_message_queue()
            pygame.time.wait(10)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = CalorieMachine()
    game.run()
