import pygame
import sys
import argparse
from Module.tcp_handler import TCPHandler
from Module.serial_handler import SerialHandler
from Module.game_state import GameState, GameStateManager
from Module.screen_manager import ScreenManager
from Module.score_manager import ScoreManager

def parse_arguments():
    parser = argparse.ArgumentParser(description='Samyang Pop Game Client')
    parser.add_argument('--tcp', action='store_true', help='Enable TCP connection')
    parser.add_argument('--type', type=int, choices=[1,2,3,4,5,6], default=1,
                      help='''Game type:
    1: Healthy Burger
    2: Sleep Disturbance
    3: Rowing Machine
    4: Pool Ball
    5: Air Siso
    6: Robot Basketball''')
    parser.add_argument('--enter', action='store_true', help='Show enter screen')
    parser.add_argument('--exit', action='store_true', help='Show exit screen')
    return parser.parse_args()

class CalorieMachine:
    def __init__(self, use_tcp=False, game_type=1, show_enter=False, show_exit=False):
        pygame.init()
        
        self.screen_manager = ScreenManager()
        self.serial_handler = SerialHandler(self.handle_input)
        self.score_manager = ScoreManager()
        self.game_state = GameStateManager(
            self.screen_manager.update_screen,
            self.handle_state_change,
            game_type
        )

        # 시작 상태 결정
        if show_enter:
            self.game_state.show_enter()
        elif show_exit:
            self.game_state.show_exit()
        else:
            self.game_state.show_init()
            # ENTER/EXIT가 아닐 때만 통신 초기화
            self.setup_communications(use_tcp)

    def setup_communications(self, use_tcp):
        """통신 초기화 함수"""
        # TCP 핸들러 조건부 초기화
        self.tcp_handler = None
        self.use_tcp = use_tcp
        if use_tcp:
            self.tcp_handler = TCPHandler(self.OnReceivedTCPMessage)
            self.tcp_handler.setup()
            self.tcp_handler.start_monitoring()

        self.serial_handler.setup()
        self.serial_handler.start_monitoring()

    def wait_for_connections(self):
        """모든 연결이 준비될 때까지 대기"""
        while True:
            # 이벤트 처리
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_a:
                    self.handle_input('a')
            
            # 화면 업데이트 처리
            self.screen_manager.process_message_queue()
            
            # ENTER나 EXIT 상태일 때는 연결 상태를 체크하지 않음
            if self.game_state.current_state in [GameState.ENTER, GameState.EXIT]:
                pygame.time.wait(100)
                continue
            
            # 연결 상태 체크
            if self.serial_handler.is_ready():
                if not self.use_tcp or (self.use_tcp and self.tcp_handler.is_ready()):
                    break
            
            pygame.time.wait(100)
        
        # ENTER나 EXIT 상태가 아닐 때만 WAITING으로 전환
        if self.game_state.current_state not in [GameState.ENTER, GameState.EXIT]:
            self.game_state.show_waiting()

    def handle_input(self, input_value):
        print(f"Input received: {input_value}, Current state: {self.game_state.current_state}")  # 디버깅용 로그 추가
        if input_value == 'a':
            if self.game_state.current_state == GameState.INIT:
                self.game_state.show_waiting()  # INIT 상태에서 WAITING으로 강제 전환
            elif self.game_state.current_state == GameState.SCORE:
                if self.use_tcp:
                    self.tcp_handler.send_message('-4')
                self.game_state.show_result(self.score_manager.get_total_score())  # 점수를 전달하여 결과 화면으로
            elif self.game_state.current_state == GameState.WAITING:
                if self.use_tcp:
                    self.tcp_handler.send_message('-1')
                self.game_state.start_countdown()
            elif self.game_state.current_state == GameState.PLAYING:
                self.game_state.show_score(7176)
        else:
            if self.game_state.current_state == GameState.PLAYING:
                score = int(input_value)
                print(f"Score received: {score}")  # 디버깅용 로그 추가
                if score >0:
                    self.score_manager.add_score(score)

    def OnReceivedTCPMessage(self, message):
        try:
            score = float(message)
            if score >= 0 and self.game_state.current_state == GameState.PLAYING:
                self.score_manager.add_score(score)
        except ValueError:
            print(f"Invalid message format: {message}")

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
    args = parse_arguments()
    game = CalorieMachine(
        use_tcp=args.tcp, 
        game_type=args.type,
        show_enter=args.enter,
        show_exit=args.exit
    )
    game.run()
