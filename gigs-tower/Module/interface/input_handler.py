import os
import pygame
import sys
import threading
from Module.game.events import GameEvent, EventType, InputSource
from Module.process.process_handler import ProcessHandler


class InputHandler:
    def __init__(self, gigs_instance, action_handler, process_handler):
        self._gigs = gigs_instance
        self._action = action_handler
        self._process = process_handler
        self._key_mappings = {
            pygame.K_a: self._handle_key_a,     # A키 → master RFID
            pygame.K_u: self._handle_key_u,     # U키 → test RFID 1
            pygame.K_i: self._handle_key_i,     # I키 → test RFID 2
            pygame.K_o: self._handle_key_o,     # O키 → test RFID 3
            pygame.K_b: self._handle_key_b,     # B키 → 점수 10 Mock
            pygame.K_t: self._handle_key_t,     # T키 → Thread 상태 확인
            pygame.K_r: self._handle_key_r,     # R키 → 재시작
            pygame.K_ESCAPE: self._handle_escape, # ESC 키 -> 종료
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
            # ProcessHandler에서 post한 커스텀 이벤트 처리
            elif event.type == ProcessHandler.PROCESS_RESTART_EVENT:
                print("[InputHandler] Received RESTART event from MQTT")
                self._handle_key_r()  # 재시작 로직 재사용
                return False
            elif event.type == ProcessHandler.PROCESS_STOP_EVENT:
                print("[InputHandler] Received STOP event from MQTT")
                return self._quit_game()  # 종료 로직 재사용
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
        """A 키 처리 → 마스터 RFID 이벤트"""
        self._emit_mock_rfid("QWER1234")  # 기존 master RFID 예시
        return True

    def _handle_key_u(self):
        """U 키 처리 → 테스트 RFID #1"""
        self._emit_mock_rfid("TESTU123")
        return True

    def _handle_key_i(self):
        """I 키 처리 → 테스트 RFID #2"""
        self._emit_mock_rfid("TESTU456")
        return True

    def _handle_key_o(self):
        """O 키 처리 → 테스트 RFID #3"""
        self._emit_mock_rfid("TESTU789")
        return True
            

    def _handle_key_b(self):
        """B 키 처리 → 점수 이벤트 (10점)"""
        if getattr(self._gigs, 'test_mode', False):
            score_val = 10
            print(f"[INPUT TEST] B key pressed -> mock Score: {score_val}")
            ev = GameEvent(
                kind=EventType.SCORE_RECEIVED,
                source=InputSource.KEYBOARD,
                raw=str(score_val),
                score=score_val
            )
            self._action.on_score_received(ev)
        return True

    def _handle_key_t(self):
        """T 키 처리 → 쓰레드 상태 확인"""
        if getattr(self._gigs, 'test_mode', False):
            threads = threading.enumerate()
            print(f"\n{'='*60}")
            print(f"[THREAD CHECK] Active threads: {len(threads)}")
            print(f"[THREAD CHECK] Current game state: {self._gigs.game_state.current_state}")
            print(f"{'='*60}")

            # 쓰레드별 상세 정보
            for idx, t in enumerate(threads, 1):
                daemon_str = "daemon" if t.daemon else "normal"
                alive_str = "alive" if t.is_alive() else "dead"
                print(f"  [{idx:2d}] {t.name:30s} | {daemon_str:6s} | {alive_str}")

            print(f"{'='*60}\n")

            # ResourceMonitor가 활성화된 경우 상세 정보도 출력
            if hasattr(self._gigs, 'monitor') and self._gigs.monitor:
                stats = self._gigs.monitor.get_current_stats()
                print(f"[RESOURCE] Threads: {stats['threads']} ({stats['thread_delta']:+d} from start)")
                if stats['memory_mb'] > 0:
                    print(f"[RESOURCE] Memory: {stats['memory_mb']:.1f}MB ({stats['memory_delta_mb']:+.1f}MB from start)")
                print(f"[RESOURCE] Uptime: {stats['uptime_hours']:.2f}h")
                print(f"{'='*60}\n")
        return True
    
    def _handle_key_r(self):
        "R 키 처리 -> 파이썬 종료 후 재시작"
        self._process.restart_process() 
        # pygame.quit()
        # python = sys.executable  # 현재 파이썬 실행 파일 경로
        # os.execl(python, python, *sys.argv)  # 현재 스크립트 다시 실행

    def _handle_escape(self):
        """ESC 키 처리 (게임 종료)"""
        if hasattr(self._gigs, 'test_mode') and self._gigs.test_mode:
            print("[INPUT TEST] ESC key pressed - exiting...")
        return self._quit_game()
    
    def _quit_game(self):
        """게임 종료 처리"""
        self._process.stop_process()
        # return False  # 이 라인은 실제로는 실행되지 않음 (sys.exit() 때문)
    
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

    def _emit_mock_rfid(self, rfid: str) -> None:
        """
        공통 로직: mock rfid로 RFID_DETECTED 이벤트 생성하여 action에 전달.
        Args:
            rfid: 테스트용 RFID 문자열
        """

        if getattr(self._gigs, 'test_mode', False):
            print(f"[INPUT TEST] Emitting mock RFID -> {rfid}")
            ev = GameEvent(
                kind=EventType.RFID_DETECTED,
                source=InputSource.KEYBOARD,
                raw=rfid,
            )
            self._action.on_rfid_detected(ev)