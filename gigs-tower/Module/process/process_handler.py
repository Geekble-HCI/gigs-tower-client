import os
import sys
import pygame
from typing import Optional, Callable
import threading


class ProcessHandler:
    """프로세스 생명주기 관리 클래스"""

    # 커스텀 이벤트 타입 (pygame.USEREVENT 기반)
    PROCESS_RESTART_EVENT = pygame.USEREVENT + 100
    PROCESS_STOP_EVENT = pygame.USEREVENT + 101

    def __init__(self, cleanup_callback: Optional[Callable] = None):
        """
        Args:
            cleanup_callback: 종료 전 실행할 cleanup 함수 (예: pygame.quit)
        """
        self._cleanup_callback = cleanup_callback or self._default_cleanup

    def _default_cleanup(self):
        """기본 cleanup: pygame 종료"""
        try:
            pygame.quit()
        except Exception as e:
            print(f"[ProcessHandler] Cleanup warning: {e}")

    def _is_main_thread(self) -> bool:
        """현재 스레드가 메인 스레드인지 확인"""
        return threading.current_thread() is threading.main_thread()

    def restart_process(self) -> None:
        """
        현재 프로세스 재시작
        - 메인 스레드: 즉시 실행
        - 다른 스레드: pygame 이벤트로 메인 스레드에 요청
        """
        if self._is_main_thread():
            print("[ProcessHandler] Restarting from main thread...")
            self._cleanup_callback()
            python = sys.executable
            os.execl(python, python, *sys.argv)
        else:
            print("[ProcessHandler] Posting restart event to main thread...")
            pygame.event.post(pygame.event.Event(self.PROCESS_RESTART_EVENT))

    def stop_process(self, exit_code: int = 0) -> None:
        """
        프로세스 종료

        Args:
            exit_code: 종료 코드 (0=정상, 1=에러)
        """
        if self._is_main_thread():
            print(f"[ProcessHandler] Stopping from main thread (code={exit_code})...")
            self._cleanup_callback()
            sys.exit(exit_code)
        else:
            print(f"[ProcessHandler] Posting stop event to main thread (code={exit_code})...")
            pygame.event.post(pygame.event.Event(self.PROCESS_STOP_EVENT, {"exit_code": exit_code}))