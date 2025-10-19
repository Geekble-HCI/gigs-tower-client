"""
리소스 모니터링 유틸리티
스레드, 메모리 사용량 추적 및 로깅 (표준 라이브러리만 사용)
"""
import threading
import time
import os
import sys
from datetime import datetime
from typing import Optional


class ResourceMonitor:
    """시스템 리소스 모니터링 (스레드, 메모리)"""

    def __init__(self, log_interval: int = 300, enable_logging: bool = True):
        """
        Args:
            log_interval: 로그 출력 간격 (초, 기본 5분)
            enable_logging: 로깅 활성화 여부
        """
        self.log_interval = log_interval
        self.enable_logging = enable_logging
        self.initial_thread_count = threading.active_count()
        self.initial_memory = self._get_memory_usage()
        self.start_time = time.time()

        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def _get_memory_usage(self) -> float:
        """메모리 사용량 조회 (MB) - 플랫폼별 처리"""
        try:
            # Windows
            if sys.platform == 'win32':
                import ctypes
                class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                    _fields_ = [
                        ('cb', ctypes.c_ulong),
                        ('PageFaultCount', ctypes.c_ulong),
                        ('PeakWorkingSetSize', ctypes.c_size_t),
                        ('WorkingSetSize', ctypes.c_size_t),
                        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
                        ('QuotaPagedPoolUsage', ctypes.c_size_t),
                        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
                        ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                        ('PagefileUsage', ctypes.c_size_t),
                        ('PeakPagefileUsage', ctypes.c_size_t),
                    ]

                counters = PROCESS_MEMORY_COUNTERS()
                counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)

                if ctypes.windll.psapi.GetProcessMemoryInfo(
                    ctypes.windll.kernel32.GetCurrentProcess(),
                    ctypes.byref(counters),
                    ctypes.sizeof(counters)
                ):
                    return counters.WorkingSetSize / 1024 / 1024  # MB

            # Linux - /proc/self/status 사용
            elif sys.platform.startswith('linux'):
                with open('/proc/self/status') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            # VmRSS is in kB
                            return int(line.split()[1]) / 1024  # MB

            # macOS - resource 모듈 사용
            elif sys.platform == 'darwin':
                import resource
                rusage = resource.getrusage(resource.RUSAGE_SELF)
                # macOS에서 ru_maxrss는 bytes 단위
                return rusage.ru_maxrss / 1024 / 1024  # MB

        except Exception:
            # 폴백: 메모리 조회 실패 시 0 반환 (상대적 변화만 추적)
            pass

        return 0.0

    def start(self):
        """백그라운드 모니터링 시작"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return

        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        if self.enable_logging:
            mem_str = f"{self.initial_memory:.1f}MB" if self.initial_memory > 0 else "N/A"
            print(f"[MONITOR] Started | Threads: {self.initial_thread_count} | Memory: {mem_str}")

    def stop(self):
        """모니터링 중지"""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)

    def _monitor_loop(self):
        """모니터링 루프"""
        while not self._stop_event.wait(timeout=self.log_interval):
            self.log_snapshot()

    def get_current_stats(self) -> dict:
        """현재 리소스 상태 조회"""
        current_threads = threading.active_count()
        current_memory = self._get_memory_usage()
        uptime = time.time() - self.start_time

        return {
            "threads": current_threads,
            "thread_delta": current_threads - self.initial_thread_count,
            "memory_mb": current_memory,
            "memory_delta_mb": current_memory - self.initial_memory,
            "uptime_hours": uptime / 3600,
            "timestamp": datetime.now().isoformat()
        }

    def log_snapshot(self):
        """현재 상태 로그 출력"""
        if not self.enable_logging:
            return

        stats = self.get_current_stats()

        # 스레드 증가량에 따른 경고 레벨
        thread_delta = stats["thread_delta"]
        memory_delta = stats["memory_delta_mb"]

        if thread_delta > 50 or memory_delta > 500:
            level = "CRITICAL"
        elif thread_delta > 20 or memory_delta > 200:
            level = "WARN"
        else:
            level = "INFO"

        # 메모리 정보가 없으면 스레드만 출력
        if stats["memory_mb"] > 0:
            print(
                f"[MONITOR][{level}] "
                f"Uptime: {stats['uptime_hours']:.1f}h | "
                f"Threads: {stats['threads']} ({thread_delta:+d}) | "
                f"Memory: {stats['memory_mb']:.1f}MB ({memory_delta:+.1f}MB)"
            )
        else:
            print(
                f"[MONITOR][{level}] "
                f"Uptime: {stats['uptime_hours']:.1f}h | "
                f"Threads: {stats['threads']} ({thread_delta:+d})"
            )

    def get_thread_details(self) -> list:
        """활성 스레드 상세 정보"""
        threads = []
        for thread in threading.enumerate():
            threads.append({
                "name": thread.name,
                "daemon": thread.daemon,
                "alive": thread.is_alive(),
                "ident": thread.ident
            })
        return threads

    def log_thread_details(self):
        """스레드 상세 정보 로그 (디버깅용)"""
        if not self.enable_logging:
            return

        threads = self.get_thread_details()
        print(f"\n[MONITOR] Thread Details (Total: {len(threads)}):")
        for t in threads:
            print(f"  - {t['name']} | daemon={t['daemon']} | alive={t['alive']}")
        print()


# 싱글톤 인스턴스
_monitor_instance: Optional[ResourceMonitor] = None


def get_monitor(log_interval: int = 300, enable_logging: bool = True) -> ResourceMonitor:
    """ResourceMonitor 싱글톤 인스턴스 반환"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = ResourceMonitor(log_interval, enable_logging)
    return _monitor_instance
