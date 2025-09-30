"""게임 타입별 처리 전략 (Strategy Pattern)"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
from .game_state import PlayerProgressState
from .error_type import ErrorType

class GameTypeStrategy(ABC):
    """게임 타입별 처리 전략 인터페이스"""

    @abstractmethod
    def get_progress_state(self, current_state: str) -> str:  # current_state는 향후 확장용
        """현재 상태에 따른 progress_state 반환"""
        pass

    @abstractmethod
    def validate_tag(self, validation_result: dict) -> Optional[dict]:
        """태그 검증 결과 처리 (에러 발생 시 dict 반환, 정상 시 None)"""
        pass

    @abstractmethod
    def handle_tag_success(self, action_handler, rfid: str, nickname: str):
        """태그 성공 시 처리"""
        pass

class EnterGameStrategy(GameTypeStrategy):
    """입장 게임 전략 (game_type=7)"""

    def get_progress_state(self, current_state: str) -> str:  # current_state는 향후 확장용
        return PlayerProgressState.ENTER

    def validate_tag(self, validation_result: dict) -> Optional[dict]:
        from Module.config.message_loader import message_loader

        if validation_result.get('duplicate_player'):
            return {
                'type': ErrorType.PLAYER_DUPLICATE_ENTER,
                'message': message_loader.get_error_message('PLAYER_DUPLICATE_ENTER')
            }
        return None

    def handle_tag_success(self, action_handler, rfid: str, nickname: str):
        action_handler._handle_enter_success(rfid, nickname)

class ExitGameStrategy(GameTypeStrategy):
    """퇴장 게임 전략 (game_type=8)"""

    def get_progress_state(self, current_state: str) -> str:  # current_state는 향후 확장용
        return PlayerProgressState.EXIT

    def validate_tag(self, validation_result: dict) -> Optional[dict]:
        from Module.config.message_loader import message_loader

        if validation_result.get('player_not_found'):
            return {
                'type': ErrorType.PLAYER_NOT_FOUND_EXIT,
                'message': message_loader.get_error_message('PLAYER_NOT_FOUND_EXIT')
            }
        return None

    def handle_tag_success(self, action_handler, rfid: str, nickname: str):
        action_handler._handle_exit_success(rfid, nickname)

class PlayableGameStrategy(GameTypeStrategy):
    """플레이 가능 게임 전략 (game_type=1~6)"""

    def get_progress_state(self, current_state: str) -> str:  # current_state는 향후 확장용
        return PlayerProgressState.IN_PROGRESS

    def validate_tag(self, validation_result: dict) -> Optional[dict]:
        from Module.config.message_loader import message_loader

        if validation_result.get('duplicate_game'):
            return {
                'type': ErrorType.GAME_DUPLICATE_EXECUTION,
                'message': message_loader.get_error_message('GAME_DUPLICATE_EXECUTION')
            }
        elif validation_result.get('player_not_found'):
            return {
                'type': ErrorType.PLAYER_NOT_FOUND_GAME,
                'message': message_loader.get_error_message('PLAYER_NOT_FOUND_GAME')
            }
        return None

    def handle_tag_success(self, action_handler, rfid: str, nickname: str):
        action_handler._handle_waiting_success(rfid, nickname)

class GameTypeStrategyFactory:
    """게임 타입 전략 팩토리"""

    _strategies: Dict[int, GameTypeStrategy] = {}

    @classmethod
    def get_strategy(cls, game_type: int) -> GameTypeStrategy:
        """게임 타입에 맞는 전략 반환 (캐싱)"""
        if game_type not in cls._strategies:
            cls._strategies[game_type] = cls._create_strategy(game_type)
        return cls._strategies[game_type]

    @classmethod
    def _create_strategy(cls, game_type: int) -> GameTypeStrategy:
        """게임 타입별 전략 생성"""
        from Module.config.game_config import GameType

        if GameType.is_entrance(game_type):
            return EnterGameStrategy()
        elif GameType.is_exit(game_type):
            return ExitGameStrategy()
        elif GameType.is_playable(game_type):
            return PlayableGameStrategy()
        else:
            raise ValueError(f"Unknown game_type: {game_type}")