"""게임 메시지 로더"""
import json
from pathlib import Path
from typing import Dict, Any, Mapping

class MessageLoader:
    """게임 메시지 로더 (JSON 기반)"""

    _instance = None
    _messages: Dict[str, Any] = {}

    @staticmethod
    def to_dict(payload: Any) -> dict:
        """bytes / str(JSON) / dict / None → dict 로 정규화"""
        if payload is None:
            return {}
        if isinstance(payload, Mapping):
            return dict(payload)
        if isinstance(payload, (bytes, bytearray)):
            try:
                return json.loads(payload.decode("utf-8", errors="ignore"))
            except Exception:
                return {}
        if isinstance(payload, str):
            s = payload.strip()
            try:
                return json.loads(s)
            except Exception:
                # key=value, key2=value2 형태가 올 가능성까지 최소 방어(선택)
                try:
                    parts = [p.strip() for p in s.split(",")]
                    return dict(p.split("=", 1) for p in parts if "=" in p)
                except Exception:
                    return {}
        return {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_messages()
        return cls._instance

    def _load_messages(self):
        """메시지 파일 로드"""
        config_path = Path(__file__).parent / "game_messages.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._messages = json.load(f)
        except Exception as e:
            print(f"[MessageLoader] Failed to load messages: {e}")
            self._messages = {}

    def get_game_title(self, game_type: int, with_newline: bool = True) -> str:
        """게임 타입별 타이틀 반환"""
        game_info = self._messages.get('game_titles', {}).get(str(game_type), {})
        title = game_info.get('title', '알 수 없는 게임')
        subtitle = game_info.get('subtitle')

        if subtitle:
            separator = '\n' if with_newline else ' '
            return f"{title}{separator}{subtitle}"
        return title

    def get_state_message(self, state: str, game_type: int = None, **kwargs) -> str:
        """상태별 메시지 반환 (템플릿 변수 지원)"""
        state_msgs = self._messages.get('state_messages', {})

        # game_type이 지정된 경우 해당 타입의 메시지 우선
        if game_type and isinstance(state_msgs.get(state), dict):
            template = state_msgs[state].get(str(game_type))
            if not template:
                template = state_msgs[state].get('default', '')
        else:
            template = state_msgs.get(state, '')

        # 템플릿 변수 치환
        try:
            return template.format(**kwargs)
        except KeyError as e:
            print(f"[MessageLoader] Missing template variable: {e}")
            return template

    def get_error_message(self, error_type: str, **kwargs) -> str:
        """에러 메시지 반환"""
        error_msgs = self._messages.get('error_messages', {})
        template = error_msgs.get(error_type, '알 수 없는 오류가 발생했습니다.')

        try:
            return template.format(**kwargs)
        except KeyError as e:
            print(f"[MessageLoader] Missing error template variable: {e}")
            return template

    def get_success_message(self, action: str, **kwargs) -> str:
        """성공 메시지 반환"""
        success_msgs = self._messages.get('success_messages', {})
        template = success_msgs.get(action, '')

        try:
            return template.format(**kwargs)
        except KeyError:
            return template
    
    

# 싱글톤 인스턴스
message_loader = MessageLoader()