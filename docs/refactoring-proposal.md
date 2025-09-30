# 게임 시스템 리팩토링 제안서

## 📌 개요

`game_action_handler.py`와 `game_state.py`에 존재하는 하드코딩된 로직들을 개선하여 유지보수성, 확장성, 테스트 용이성을 향상시키기 위한 리팩토링 제안입니다.

---

## 🎯 주요 문제점

### 1. 마스터 카드 UID 중복 정의 및 불일치

**현재 상태:**
```python
# game_action_handler.py:27 (RFID 감지용)
MASTER_CARDS_UID = {"A736C701", "A3B60E02", "DCA30E02", "C25AC601", "8D37B001", "6265B501", "QWER1234"}

# game_action_handler.py:114 (게임 명령용 - 다른 목록!)
MASTER_CARDS_UID = {"7C9E4705", "QWER1234", "87654321"}
```

**문제:**
- 동일한 목적의 마스터 카드가 두 곳에서 다르게 정의됨
- 마스터 카드 추가/제거 시 여러 곳 수정 필요
- 휴먼 에러 발생 가능성

---

### 2. 게임 타입별 하드코딩된 분기 로직

**현재 상태:**
```python
# game_action_handler.py:85-90
if game_type == 7:      # ENTER 장치
    self._handle_enter_success(rfid, nickname)
elif game_type == 8:    # EXIT 장치
    self._handle_exit_success(rfid, nickname)
elif game_type in (1,2,3,4,5,6):  # 게임 장치
    self._handle_waiting_success(rfid, nickname)

# game_action_handler.py:202-226 (검증 로직)
if game_type == 7:  # 입장
    if validation_result.get('duplicate_player'):
        return {...}
elif game_type in [1, 2, 3, 4, 5, 6]:  # 일반 게임
    if validation_result.get('duplicate_game'):
        return {...}
    elif validation_result.get('player_not_found'):
        return {...}
elif game_type == 8:  # 퇴장
    if validation_result.get('player_not_found'):
        return {...}

# game_state.py:78-101 (상태 매핑)
if state == GameState.TAG:
    if self.sound_manager.game_type == 7:  # 입장 화면
        return PlayerProgressState.ENTER
    elif self.sound_manager.game_type == 8:  # 퇴장 화면
        return PlayerProgressState.EXIT
    else:  # type 1~6 (일반 게임)
        return PlayerProgressState.IN_PROGRESS
```

**문제:**
- 게임 타입별 로직이 여러 곳에 분산
- 새로운 게임 타입 추가 시 수정 범위가 넓음
- if-elif 체인이 길고 가독성 저하

---

### 3. 게임 메시지 하드코딩

**현재 상태:**
```python
# game_state.py:26-35
GAME_MESSAGES = {
    1: "헬시 버거\n챌린지",
    2: "꿀잠 방해꾼\nOUT!",
    3: "불태워!\n칼로링머신",
    4: "볼볼볼\n영양소",
    5: "바이오데이터\n에어시소",
    6: "슛잇!\n무빙 골대",
    7: "입장 화면",
    8: "퇴장 화면"
}
```

**문제:**
- 게임 메시지가 코드에 직접 작성됨
- 다국어 지원 불가능
- 메시지 수정 시 코드 수정 필요

---

### 4. 매직 넘버와 타임아웃 값 분산

**현재 상태:**
```python
# game_action_handler.py
self.gsm.countdown_time = 3      # 마스터 카드 카운트다운
response = self._wait_for_server_response(correlation_id, timeout=3.0)  # 서버 응답 대기

# game_state.py
remaining = 50  # 게임 플레이 시간 제한
time.sleep(self.score_wait_time)  # 점수 표시 대기
time.sleep(3)  # 결과 표시 대기
time.sleep(2.5)  # 에러 자동 복구 대기
```

**문제:**
- 숫자의 의미를 파악하기 어려움
- 시간 설정 변경 시 여러 곳 수정 필요
- 테스트 시 값 조정 어려움

---

### 5. 에러 메시지 하드코딩

**현재 상태:**
```python
# game_action_handler.py:206-226
if validation_result.get('duplicate_player'):
    return {
        'type': ErrorType.PLAYER_DUPLICATE_ENTER,
        'message': "이미 입장한 플레이어입니다.\n(중복 입장이 불가능합니다.)\n\n게임을 시작해주세요!"
    }

if validation_result.get('duplicate_game'):
    return {
        'type': ErrorType.GAME_DUPLICATE_EXECUTION,
        'message': "이미 게임을 실행 하셨습니다.\n\n관리자에게 문의 바랍니다.\n(각 게임 1번만 실행 가능)"
    }
```

**문제:**
- 에러 메시지가 로직과 섞여 있음
- 메시지 일관성 관리 어려움
- 다국어 지원 불가능

---

### 6. 상태별 화면 메시지 중복

**현재 상태:**
```python
# game_state.py:278-287 (show_waiting)
if self.sound_manager.game_type == 7:
    self.screen_update_callback("환영합니다!\n태그를 해주세요!")
elif self.sound_manager.game_type == 8:
    self.screen_update_callback("수고하셨습니다!\n태그를 해주세요!")
else:
    game_title = GameStateManager.get_game_name(self.sound_manager.game_type)
    self.screen_update_callback(f"{game_title}\n\n태그를 하면\n게임이 시작됩니다!")

# game_state.py:358-385 (restore_state_display) - 거의 동일한 로직 반복
if self.current_state == GameState.ERROR:
    if self.sound_manager.game_type == 7:
        self.screen_update_callback("환영합니다!\n태그를 해주세요!")
    elif self.sound_manager.game_type == 8:
        self.screen_update_callback("수고하셨습니다!\n태그를 해주세요!")
    # ... 동일한 패턴 반복
```

**문제:**
- 동일한 로직이 여러 메서드에 중복
- 메시지 변경 시 여러 곳 수정 필요
- DRY 원칙 위반

---

## 💡 리팩토링 제안

### 제안 1: 통합 설정 파일 생성

**파일:** `gigs-tower/config/game_config.py`

```python
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
```

---

### 제안 2: 게임 메시지 외부화

**파일:** `gigs-tower/config/game_messages.json`

```json
{
  "game_titles": {
    "1": {"title": "헬시 버거", "subtitle": "챌린지"},
    "2": {"title": "꿀잠 방해꾼", "subtitle": "OUT!"},
    "3": {"title": "불태워!", "subtitle": "칼로링머신"},
    "4": {"title": "볼볼볼", "subtitle": "영양소"},
    "5": {"title": "바이오데이터", "subtitle": "에어시소"},
    "6": {"title": "슛잇!", "subtitle": "무빙 골대"},
    "7": {"title": "입장 화면"},
    "8": {"title": "퇴장 화면"}
  },
  "state_messages": {
    "waiting": {
      "7": "환영합니다!\n태그를 해주세요!",
      "8": "수고하셨습니다!\n태그를 해주세요!",
      "default": "{game_title}\n\n태그를 하면\n게임이 시작됩니다!"
    },
    "playing": "게임 진행 중...",
    "countdown": "{nickname}님\n게임이 곧 시작됩니다.\n\n{count}",
    "score": "당신의 점수는?\n\n{score}점을\n획득했습니다!",
    "result": "{score}점을\n획득했습니다!",
    "init": "시스템 초기화 중...",
    "enter": "환영합니다!\n태그를 해주세요!",
    "exit": "수고하셨습니다!\n태그를 해주세요!"
  },
  "error_messages": {
    "PLAYER_DUPLICATE_ENTER": "이미 입장한 플레이어입니다.\n(중복 입장이 불가능합니다.)\n\n게임을 시작해주세요!",
    "GAME_DUPLICATE_EXECUTION": "이미 게임을 실행 하셨습니다.\n\n관리자에게 문의 바랍니다.\n(각 게임 1번만 실행 가능)",
    "PLAYER_NOT_FOUND_GAME": "입장 처리가 필요합니다.\n먼저 입장 타워에서\n태그해주세요.",
    "PLAYER_NOT_FOUND_EXIT": "플레이어를 찾을 수 없습니다.\n(퇴장 완료)",
    "NETWORK_ERROR": "서버 연결 실패\n{detail}\n잠시 후 다시 시도해주세요.",
    "SERVER_ERROR": "서버 오류가 발생했습니다.",
    "TAG_DUPLICATE": "이미 처리가 되었습니다.\n(RFID: {rfid})",
    "TAG_BLOCKED": "게임이 진행 중 입니다.\n(태그 불가)",
    "MASTER_MODE": "마스터 모드\n\n(RFID: {rfid})"
  },
  "success_messages": {
    "enter": "플레이어 입장\n\n안녕하세요!\n(RFID: {rfid})",
    "exit": "안녕히 가세요!\n{nickname}님\n(RFID: {rfid})"
  }
}
```

**파일:** `gigs-tower/config/message_loader.py`

```python
"""게임 메시지 로더"""
import json
from pathlib import Path
from typing import Dict, Any

class MessageLoader:
    """게임 메시지 로더 (JSON 기반)"""

    _instance = None
    _messages: Dict[str, Any] = {}

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
```

---

### 제안 3: 게임 타입별 Strategy 패턴 적용

**파일:** `gigs-tower/Module/game/game_type_strategy.py`

```python
"""게임 타입별 처리 전략 (Strategy Pattern)"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
from .game_state import PlayerProgressState, GameState
from .error_type import ErrorType

class GameTypeStrategy(ABC):
    """게임 타입별 처리 전략 인터페이스"""

    @abstractmethod
    def get_progress_state(self, current_state: str) -> str:
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

    def get_progress_state(self, current_state: str) -> str:
        return PlayerProgressState.ENTER

    def validate_tag(self, validation_result: dict) -> Optional[dict]:
        from config.message_loader import message_loader

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

    def get_progress_state(self, current_state: str) -> str:
        return PlayerProgressState.EXIT

    def validate_tag(self, validation_result: dict) -> Optional[dict]:
        from config.message_loader import message_loader

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

    def get_progress_state(self, current_state: str) -> str:
        return PlayerProgressState.IN_PROGRESS

    def validate_tag(self, validation_result: dict) -> Optional[dict]:
        from config.message_loader import message_loader

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
        from config.game_config import GameType

        if GameType.is_entrance(game_type):
            return EnterGameStrategy()
        elif GameType.is_exit(game_type):
            return ExitGameStrategy()
        elif GameType.is_playable(game_type):
            return PlayableGameStrategy()
        else:
            raise ValueError(f"Unknown game_type: {game_type}")
```

---

### 제안 4: 상태 디스플레이 매니저 분리

**파일:** `gigs-tower/Module/interface/state_display_manager.py`

```python
"""상태별 화면 표시 매니저"""
from typing import Callable, Optional
from Module.game.game_state import GameState
from config.message_loader import message_loader

class StateDisplayManager:
    """상태별 화면 메시지 관리"""

    def __init__(self, screen_callback: Callable[[str], None], game_type: int):
        self.screen_callback = screen_callback
        self.game_type = game_type

    def show_message_for_state(self, state: str, **kwargs):
        """상태에 맞는 메시지 표시"""
        message = self._get_message_for_state(state, **kwargs)
        if message:
            self.screen_callback(message)

    def _get_message_for_state(self, state: str, **kwargs) -> str:
        """상태별 메시지 생성"""
        if state == GameState.WAITING:
            return message_loader.get_state_message(
                'waiting',
                game_type=self.game_type,
                game_title=message_loader.get_game_title(self.game_type)
            )

        elif state == GameState.PLAYING:
            remaining = kwargs.get('remaining')
            if remaining:
                return message_loader.get_state_message('playing') + f"\n\n{remaining}"
            return message_loader.get_state_message('playing')

        elif state == GameState.COUNTDOWN:
            return message_loader.get_state_message(
                'countdown',
                nickname=kwargs.get('nickname', '플레이어'),
                count=kwargs.get('count', '')
            )

        elif state == GameState.SCORE:
            return message_loader.get_state_message(
                'score',
                score=int(kwargs.get('score', 0))
            )

        elif state == GameState.RESULT:
            return message_loader.get_state_message(
                'result',
                score=int(kwargs.get('score', 0))
            )

        elif state == GameState.ENTER:
            return message_loader.get_state_message('enter', game_type=self.game_type)

        elif state == GameState.EXIT:
            return message_loader.get_state_message('exit', game_type=self.game_type)

        elif state == GameState.INIT:
            return message_loader.get_state_message('init')

        elif state == GameState.ERROR:
            # 에러 상태에서는 이전 상태 기본 메시지 표시
            return self._get_default_message_by_game_type()

        return ""

    def _get_default_message_by_game_type(self) -> str:
        """게임 타입별 기본 메시지"""
        return message_loader.get_state_message('waiting', game_type=self.game_type)
```

---

## 📁 새로운 파일 구조

```
gigs-tower/
├── config/
│   ├── __init__.py
│   ├── game_config.py          # 통합 설정
│   ├── game_messages.json       # 메시지 외부화
│   └── message_loader.py        # 메시지 로더
│
├── Module/
│   ├── game/
│   │   ├── game_state.py       # 수정: 메시지 로직 제거
│   │   ├── game_action_handler.py  # 수정: Strategy 패턴 적용
│   │   ├── game_type_strategy.py   # 신규: 게임 타입 전략
│   │   └── ...
│   │
│   └── interface/
│       ├── state_display_manager.py  # 신규: 상태 디스플레이 관리
│       └── ...
```

---

## 🔄 적용 예시

### Before (기존 코드)

```python
# game_action_handler.py
MASTER_CARDS_UID = {"A736C701", "A3B60E02", "DCA30E02", "C25AC601", "8D37B001", "6265B501", "QWER1234"}
is_master_card = rfid in MASTER_CARDS_UID

if game_type == 7:
    self._handle_enter_success(rfid, nickname)
elif game_type == 8:
    self._handle_exit_success(rfid, nickname)
elif game_type in (1,2,3,4,5,6):
    self._handle_waiting_success(rfid, nickname)

response = self._wait_for_server_response(correlation_id, timeout=3.0)
```

### After (리팩토링 후)

```python
# game_action_handler.py
from config.game_config import GameConfig, GameType
from Module.game.game_type_strategy import GameTypeStrategyFactory

is_master_card = rfid in GameConfig.MASTER_RFID_CARDS

strategy = GameTypeStrategyFactory.get_strategy(game_type)
strategy.handle_tag_success(self, rfid, nickname)

response = self._wait_for_server_response(
    correlation_id,
    timeout=GameConfig.SERVER_VALIDATION_TIMEOUT
)
```

---

## ✅ 리팩토링 이점

### 1. 유지보수성 향상
- 설정 변경 시 한 곳만 수정
- 코드와 데이터(메시지) 분리
- 중복 코드 제거

### 2. 확장성 개선
- 새 게임 타입 추가 시 Strategy 클래스만 추가
- 다국어 지원 준비 (JSON 파일 추가)
- 게임 설정 변경 용이

### 3. 테스트 용이성
- 설정값 모킹 가능
- Strategy 패턴으로 단위 테스트 분리
- 타임아웃 값 조정 용이

### 4. 가독성 향상
- 매직 넘버 제거
- 명확한 변수명 사용
- 관심사 분리

---

## 📋 리팩토링 우선순위

### High Priority (즉시 적용 권장)
1. ✅ **통합 설정 파일 생성** (`game_config.py`)
   - 마스터 카드 통합
   - 매직 넘버 제거
   - 타임아웃 값 통합

2. ✅ **메시지 외부화** (`game_messages.json`, `message_loader.py`)
   - 에러 메시지 분리
   - 상태 메시지 템플릿화

### Medium Priority (단계적 적용)
3. ✅ **게임 타입 Strategy 패턴** (`game_type_strategy.py`)
   - if-elif 체인 제거
   - 게임 타입별 로직 캡슐화

### Low Priority (선택적 적용)
4. ✅ **상태 디스플레이 매니저** (`state_display_manager.py`)
   - 중복 메시지 로직 통합
   - 단일 책임 원칙 준수

---

## 🚀 마이그레이션 계획

### Phase 1: 설정 및 메시지 외부화 (1-2일)
1. `config/` 디렉토리 생성
2. `game_config.py` 작성 및 적용
3. `game_messages.json`, `message_loader.py` 작성
4. 기존 코드에서 하드코딩 제거

### Phase 2: Strategy 패턴 적용 (2-3일)
1. `game_type_strategy.py` 작성
2. `game_action_handler.py` 리팩토링
3. `game_state.py`의 `_get_progress_state` 리팩토링
4. 테스트 및 검증

### Phase 3: 디스플레이 매니저 분리 (1-2일)
1. `state_display_manager.py` 작성
2. `game_state.py`의 중복 로직 제거
3. 통합 테스트

### Phase 4: 검증 및 배포 (1일)
1. 전체 시나리오 테스트
2. 성능 확인
3. 문서화 업데이트

**총 예상 기간: 5-8일**

---

## 📝 참고 사항

- 리팩토링은 기능 변경 없이 구조만 개선
- 기존 API 호환성 유지
- 단계적 적용으로 리스크 최소화
- 각 단계마다 테스트 수행 권장

---

## 🤝 기여 가이드

리팩토링 진행 시:
1. 각 Phase별로 브랜치 생성 (`refactor/phase-1`, `refactor/phase-2`, ...)
2. Phase 완료 시 PR 생성 및 리뷰
3. 테스트 통과 후 메인 브랜치 병합
4. 다음 Phase 진행

---

**작성일:** 2025-09-30
**버전:** 1.0
**담당:** Development Team