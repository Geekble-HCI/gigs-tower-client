"""게임 시스템 전역 설정"""

class GameConfig:
    """게임 시스템 설정 상수"""

    # 마스터 카드 UID (RFID 및 명령 모두 허용)
    MASTER_RFID_CARDS = {
        "A736C701", "A3B60E02", "DCA30E02",
        "C25AC601", "8D37B001", "6265B501",
        "7C9E4705", "QWER1234", "87654321"
    }

    # 타임아웃 설정 (초 단위)
    GAME_PLAY_TIMEOUT = 50              # 게임 플레이 시간 제한
    SCORE_DISPLAY_WAIT = 3              # 점수 화면 표시 시간
    RESULT_DISPLAY_WAIT = 3             # 결과 화면 표시 시간
    TAG_DUPLICATE_DELAY = 1.5           # 중복 태그 방지 딜레이
    ERROR_AUTO_RECOVERY_DELAY = 2.5     # 에러 자동 복구 대기 시간

    # 서버 통신 설정
    SERVER_VALIDATION_TIMEOUT = 3.0     # 서버 검증 응답 대기 시간
    SERVER_RESPONSE_CHECK_INTERVAL = 0.1  # 응답 폴링 간격

    # 마스터 카드 특수 설정
    MASTER_COUNTDOWN_TIME = 3           # 마스터 카드 카운트다운 시간

    # 응답 캐시 관리
    MAX_PENDING_RESPONSES = 5           # 최대 대기 응답 수
    CLEANUP_RESPONSE_COUNT = 3          # 정리할 응답 수

class GameType:
    """게임 타입 정의"""
    HEALTHY_BURGER = 1      # 헬시 버거
    SLEEP_DISTURB = 2       # 꿀잠 방해꾼
    ROWING_MACHINE = 3      # 칼로링머신
    POOL_BALL = 4           # 볼볼볼 영양소
    AIR_SEESAW = 5          # 에어시소
    MOVING_GOAL = 6         # 무빙 골대
    ENTER = 7               # 입장
    EXIT = 8                # 퇴장

    @staticmethod
    def is_playable(game_type: int) -> bool:
        """게임 플레이 가능 타입 판별"""
        return game_type in (1, 2, 3, 4, 5, 6)

    @staticmethod
    def is_entrance(game_type: int) -> bool:
        """입장 타입 판별"""
        return game_type == 7

    @staticmethod
    def is_exit(game_type: int) -> bool:
        """퇴장 타입 판별"""
        return game_type == 8