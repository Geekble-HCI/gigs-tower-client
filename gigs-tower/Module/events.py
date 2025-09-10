from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional

class InputSource(Enum):
    SERIAL = auto()
    KEYBOARD = auto()
    COMMAND = auto()

class EventType(Enum):
    RFID_DETECTED = auto()
    SCORE_RECEIVED = auto()
    GAME_START = auto()
    GAME_STOP = auto()
    GAME_RESET = auto()
    UNKNOWN = auto()

@dataclass(frozen=True) # 불변(immutable) 처리
class GameEvent:
    kind: EventType
    source: InputSource
    raw: Optional[str] = None
    score: Optional[int] = None