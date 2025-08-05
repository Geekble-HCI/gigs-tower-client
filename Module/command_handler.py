from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any

#  장치 제어 처리: Command Pattern 적용

# 1. CommandType Enum 
class CommandType(str, Enum):
    VOLUME = "volume"
    # POWER = "power"
    GAME_START = "game_start"
    GAME_STOP = "game_stop"
    STATE_RESET = "state_reset"
    PING = "ping"

# 2. Command Interface
class CommandInterface(ABC):
    @abstractmethod
    def execute(self, value: Any, timestamp: str, device_id: str) -> bool:
        pass

# 3. Concrete Command
class VolumeCommand(CommandInterface):
    def __init__(self, sound_manager):
        self.sound_manager = sound_manager

    def execute(self, value, timestamp, device_id) -> bool:
        try:
            volume = int(value)
            if not (0 <= volume <= 100):
                print(f"[Volume] Invalid volume: {volume}")
                return False
            pygame_volume = volume / 100.0
            self.sound_manager.set_volume(pygame_volume)
            print(f"[Volume] Volume set to {volume}%")
            return True
        except Exception as e:
            print(f"[Volume] Volume error: {e}")
            return False

class PingCommand(CommandInterface):
    def execute(self, value, timestamp, device_id) -> bool:
        # TODO: Health Check
        print(f"[Ping] Ping received from {device_id} at {timestamp}")
        return True

# 4. Dispatcher (Invoker)
class CommandDispatcher:
    def __init__(self):
        self.handlers: Dict[CommandType, CommandInterface] = {}

    def register(self, command_type: CommandType, handler: CommandInterface):
        self.handlers[command_type] = handler

    def dispatch(self, cmd_str: str, value: Any, timestamp: str, device_id: str) -> bool:
        try:
            command_enum = CommandType(cmd_str)
        except ValueError:
            print(f"[Dispatch] Unknown command: {cmd_str}")
            return False

        handler = self.handlers.get(command_enum)
        if not handler:
            print(f"[Dispatch] No handler registered for: {command_enum}")
            return False

        return handler.execute(value, timestamp, device_id)