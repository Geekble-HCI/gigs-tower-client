import pygame
import sys
from .game_state import GameState


class InputHandler:
    """키보드 입력을 처리하는 클래스"""
    
    def __init__(self, gigs_instance):
        """
        InputHandler 초기화
        
        Args:
            gigs_instance: GIGS 클래스 인스턴스 (콜백 함수들에 접근하기 위함)
        """
        self._gigs = gigs_instance
        self._key_mappings = {
            pygame.K_a: self._handle_key_a,
            pygame.K_b: self._handle_key_b,
            pygame.K_ESCAPE: self._handle_escape,
        }
    
    def process_events(self):
        """
        pygame 이벤트를 처리하고 게임 실행 상태를 반환
        
        Returns:
            bool: 게임이 계속 실행되어야 하면 True, 종료해야 하면 False
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return self._quit_game()
            elif event.type == pygame.KEYDOWN:
                return self._handle_keydown(event.key)
        
        return True  # 게임 계속 실행
    
    def _handle_keydown(self, key):
        """
        키 다운 이벤트 처리
        
        Args:
            key: 눌린 키 코드
            
        Returns:
            bool: 게임이 계속 실행되어야 하면 True, 종료해야 하면 False
        """
        if key in self._key_mappings:
            return self._key_mappings[key]()
        
        return True  # 매핑되지 않은 키는 무시하고 게임 계속 실행
    
    def _handle_key_a(self):
        """A 키 처리"""
        self.handle_serial_input('a')
        return True
    
    def _handle_key_b(self):
        """B 키 처리 (PLAYING 상태에서만 동작)"""
        if self._gigs.game_state.current_state == GameState.PLAYING:
            self._gigs.game_state.show_score(7176)
        return True
    
    def _handle_escape(self):
        """ESC 키 처리 (게임 종료)"""
        return self._quit_game()
    
    def _quit_game(self):
        """게임 종료 처리"""
        pygame.quit()
        sys.exit()
        return False  # 이 라인은 실제로는 실행되지 않음 (sys.exit() 때문)
    
    def add_key_mapping(self, key, handler_func):
        """
        새로운 키 매핑 추가
        
        Args:
            key: pygame 키 상수
            handler_func: 키가 눌렸을 때 호출할 함수 (bool 반환 필요)
        """
        self._key_mappings[key] = handler_func
    
    def remove_key_mapping(self, key):
        """
        키 매핑 제거
        
        Args:
            key: pygame 키 상수
        """
        if key in self._key_mappings:
            del self._key_mappings[key]
    
    def handle_serial_input(self, input_value):
        """
        시리얼 입력 처리 (원래 handle_input 메서드)
        
        Args:
            input_value: 입력된 값 (문자열 또는 숫자)
        """
        print(f"Input received: {input_value}, Current state: {self._gigs.game_state.current_state}")
        
        if input_value == 'a':
            if self._gigs.game_state.current_state == GameState.WAITING:
                if self._gigs.use_tcp:
                    self._gigs.tcp_handler.send_message('-1')
                self._gigs.game_state.start_countdown()
            # elif self._gigs.game_state.current_state == GameState.INIT:
            #     self._gigs.game_state.show_waiting()  # INIT 상태에서 WAITING으로 강제 전환
            # elif self._gigs.game_state.current_state == GameState.SCORE:
            #     if self._gigs.use_tcp:
            #         self._gigs.tcp_handler.send_message('-4')
            #     self._gigs.game_state.show_result(self._gigs.score_manager.get_total_score())  # 점수를 전달하여 결과 화면으로
            # elif self._gigs.game_state.current_state == GameState.PLAYING:
            #     self._gigs.game_state.show_score(7176)
        else:
            if self._gigs.game_state.current_state == GameState.PLAYING:
                try:
                    score = int(input_value)
                    print(f"Score received: {score}")
                    if score > 0:
                        self._gigs.score_manager.add_score(score)
                except ValueError:
                    pass  # 숫자로 변환할 수 없는 입력은 무시
