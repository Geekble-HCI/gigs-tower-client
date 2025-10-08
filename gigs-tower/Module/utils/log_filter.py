"""
로그 필터링 유틸리티 - print() 래퍼
기존 코드 수정 없이 로그 레벨 필터링 적용
"""
import sys
import builtins
from .logger import Logger, LogLevel

# 원본 print 함수 저장
_original_print = builtins.print

# 필터링할 로그 태그 (레벨별)
TRACE_TAGS = ['[TRACE]', '[Action][TRACE]', '[Validation][TRACE]']
DEBUG_TAGS = ['[DEBUG]', '[MQTT][ACK-DEBUG]']
INFO_TAGS = ['[INFO]', '[Action]', '[SERIAL]', '[Validation]', '[Performance]', '[Validation Log]']
WARN_TAGS = ['[WARN]', '[GameCmd]']
ERROR_TAGS = ['[ERROR]', '[MQTT][ERROR]']
CRITICAL_TAGS = ['[CRITICAL]', '[FATAL]']


def _get_log_level_from_message(message: str) -> LogLevel:
    """메시지 내용으로 로그 레벨 추정"""
    msg_lower = message.lower()

    # TRACE 레벨 (가장 상세한 디버깅)
    for tag in TRACE_TAGS:
        if tag in message:
            return LogLevel.TRACE

    # DEBUG 레벨
    for tag in DEBUG_TAGS:
        if tag in message:
            return LogLevel.DEBUG

    # INFO 레벨
    for tag in INFO_TAGS:
        if tag in message:
            return LogLevel.INFO

    # WARN 레벨
    for tag in WARN_TAGS:
        if tag in message or 'warn' in msg_lower:
            return LogLevel.WARN

    # ERROR 레벨
    for tag in ERROR_TAGS:
        if tag in message or 'error' in msg_lower or 'fail' in msg_lower:
            return LogLevel.ERROR

    # CRITICAL 레벨
    for tag in CRITICAL_TAGS:
        if tag in message or 'critical' in msg_lower or 'fatal' in msg_lower:
            return LogLevel.CRITICAL

    # MQTT 관련은 기본 DEBUG
    if '[MQTT]' in message:
        return LogLevel.DEBUG

    # 기본값: INFO
    return LogLevel.INFO


def filtered_print(*args, **kwargs):
    """로그 레벨 필터링이 적용된 print 함수"""
    # 메시지 조합
    message = ' '.join(str(arg) for arg in args)

    # 로그 레벨 판단
    msg_level = _get_log_level_from_message(message)

    # 현재 설정된 레벨과 비교
    if msg_level >= Logger._global_level:
        _original_print(*args, **kwargs)


def enable_log_filtering():
    """전역 print() 함수를 필터링 버전으로 교체"""
    builtins.print = filtered_print


def disable_log_filtering():
    """원본 print() 함수로 복원"""
    builtins.print = _original_print
