import pygame
import sys
from .game_state import GameState


class InputHandler:
    
    def __init__(self, gigs_instance):
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
        """A 키 처리 (테스트 모드 전용)"""
        # 테스트 모드일 때만 키보드 입력 처리
        if hasattr(self._gigs, 'test_mode') and self._gigs.test_mode:
            current_state = self._gigs.game_state.current_state
            print(f"[INPUT TEST] A key pressed - current state: {current_state}")
            
            # 상태별 처리
            if current_state == GameState.INIT:
                print("[INPUT TEST] INIT -> WAITING")
                self._gigs.game_state.show_waiting()
            elif current_state == GameState.WAITING:
                print("[INPUT TEST] WAITING -> COUNTDOWN")
                if self._gigs.use_tcp:
                    self._gigs.tcp_handler.send_message('-1')
                self._gigs.game_state.start_countdown()
            elif current_state == GameState.PLAYING:
                print("[INPUT TEST] PLAYING -> RESULT (forcing game end)")
                # 테스트용 점수로 결과 화면 표시
                test_score = self._gigs.score_manager.get_total_score()
                if test_score == 0:
                    test_score = 7176  # 기본 테스트 점수
                self._gigs.game_state.show_result(test_score)
            else:
                print(f"[INPUT TEST] A key pressed in {current_state} - no action")
        
        return True
    
    def _handle_key_b(self):
        """B 키 처리 (PLAYING 상태에서만 동작)"""
        # 테스트 모드일 때만 키보드 입력 처리
        if hasattr(self._gigs, 'test_mode') and self._gigs.test_mode:
            print(f"[INPUT TEST] B key pressed - current state: {self._gigs.game_state.current_state}")
            if self._gigs.game_state.current_state == GameState.PLAYING:
                print("[INPUT TEST] Calling show_score(7176)")
                self._gigs.game_state.show_score(7176)
            else:
                print("[INPUT TEST] B key ignored (not in PLAYING state)")
        return True
    
    def _handle_escape(self):
        """ESC 키 처리 (게임 종료)"""
        if hasattr(self._gigs, 'test_mode') and self._gigs.test_mode:
            print("[INPUT TEST] ESC key pressed - exiting...")
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