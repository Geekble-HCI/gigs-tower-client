class ErrorType:
    # Type 7 (ENTER) 관련 에러
    PLAYER_DUPLICATE_ENTER = "PLAYER_DUPLICATE_ENTER"    # 플레이어 중복 생성 불가

    # Type 1-6 (INPROGRESS) 관련 에러
    GAME_DUPLICATE_EXECUTION = "GAME_DUPLICATE_EXECUTION"  # 게임 중복 실행 불가
    PLAYER_NOT_FOUND_GAME = "PLAYER_NOT_FOUND_GAME"      # 플레이어 미생성 시 게임 불가

    # Type 8 (EXIT) 관련 에러
    PLAYER_NOT_FOUND_EXIT = "PLAYER_NOT_FOUND_EXIT"      # 플레이어 미생성 시 퇴장 불가

    # 기타 에러
    NETWORK_ERROR = "NETWORK_ERROR"                       # 네트워크 오류
    SYSTEM_ERROR = "SYSTEM_ERROR"                         # 시스템 오류