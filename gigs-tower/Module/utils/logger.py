"""
경량화된 로깅 시스템
프로덕션 환경에서 로그 오버헤드 최소화
"""
from enum import IntEnum
from typing import Optional
import time


class LogLevel(IntEnum):
    """로그 레벨 정의"""
    CRITICAL = 50  # 시스템 장애
    ERROR = 40     # 에러 상황
    WARN = 30      # 경고
    INFO = 20      # 일반 정보
    DEBUG = 10     # 디버깅 정보
    TRACE = 0      # 상세 추적


class Logger:
    """경량화된 로거"""

    # 전역 로그 레벨 (기본: INFO)
    _global_level: LogLevel = LogLevel.INFO
    _enable_timestamp: bool = False  # 타임스탬프 비활성화로 성능 향상

    @classmethod
    def set_level(cls, level: LogLevel):
        """전역 로그 레벨 설정"""
        cls._global_level = level

    @classmethod
    def enable_timestamp(cls, enable: bool = True):
        """타임스탬프 활성화/비활성화"""
        cls._enable_timestamp = enable

    @classmethod
    def _should_log(cls, level: LogLevel) -> bool:
        """로그 출력 여부 판단"""
        return level >= cls._global_level

    @classmethod
    def _format_message(cls, level: str, tag: str, message: str) -> str:
        """로그 메시지 포맷팅"""
        if cls._enable_timestamp:
            timestamp = time.strftime("%H:%M:%S")
            return f"[{timestamp}][{level}][{tag}] {message}"
        return f"[{level}][{tag}] {message}"

    @classmethod
    def critical(cls, tag: str, message: str):
        """크리티컬 로그 (항상 출력)"""
        if cls._should_log(LogLevel.CRITICAL):
            print(cls._format_message("CRIT", tag, message))

    @classmethod
    def error(cls, tag: str, message: str):
        """에러 로그"""
        if cls._should_log(LogLevel.ERROR):
            print(cls._format_message("ERR", tag, message))

    @classmethod
    def warn(cls, tag: str, message: str):
        """경고 로그"""
        if cls._should_log(LogLevel.WARN):
            print(cls._format_message("WARN", tag, message))

    @classmethod
    def info(cls, tag: str, message: str):
        """정보 로그"""
        if cls._should_log(LogLevel.INFO):
            print(cls._format_message("INFO", tag, message))

    @classmethod
    def debug(cls, tag: str, message: str):
        """디버그 로그 (개발 환경 전용)"""
        if cls._should_log(LogLevel.DEBUG):
            print(cls._format_message("DBG", tag, message))

    @classmethod
    def trace(cls, tag: str, message: str):
        """트레이스 로그 (상세 디버깅)"""
        if cls._should_log(LogLevel.TRACE):
            print(cls._format_message("TRACE", tag, message))


# 편의 함수 (하위 호환성)
def log_critical(tag: str, message: str):
    Logger.critical(tag, message)


def log_error(tag: str, message: str):
    Logger.error(tag, message)


def log_warn(tag: str, message: str):
    Logger.warn(tag, message)


def log_info(tag: str, message: str):
    Logger.info(tag, message)


def log_debug(tag: str, message: str):
    Logger.debug(tag, message)
