from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Union, Callable, Optional

#  장치 제어 처리: Command Pattern 적용

# 1. CommandType Enum 
class CommandType(str, Enum):
    VOLUME = "volume"
    MUTE_ON = "mute_on"   # 음소거 켜기
    MUTE_OFF = "mute_off"   # 음소거 해제
    MUTE_TOGGLE = "mute_toggle"

    GAME_START = "game_start"
    GAME_STOP = "game_stop"
    GAME_RESET = "game_reset"
    PING = "ping"

# 2. Command Interface
class CommandInterface(ABC):
    @abstractmethod
    def execute(self, cmd: CommandType, value: Any = None, timestamp: str = "", device_id: str = "") -> bool:
        pass

# 3. Concrete Command
class VolumeCommand(CommandInterface):
    def __init__(self, sound_manager):
        self.sound_manager = sound_manager

    def execute(self, cmd: CommandType, value: Any = None, timestamp: str = "", device_id: str = "") -> bool:
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

class MuteCommand(CommandInterface):
    def __init__(self, sound_manager):
        self.sound_manager = sound_manager
    
    def execute(self, cmd: CommandType, value: Any = None, timestamp: str = "", device_id: str = "") -> bool:
        try:
            # 예상 응답 - ex) {"cmd":"mute_on", "value":""}
            if cmd == CommandType.MUTE_ON:
                self.sound_manager.mute()
                print("[Mute] Sound muted")
            elif cmd == CommandType.MUTE_OFF:
                self.sound_manager.unmute()
                print("[Mute] Sound unmuted")
            elif cmd == CommandType.MUTE_TOGGLE:
                self.sound_manager.toggle_mute()
                print("[Mute] Sound mute toggled")
            else:
                print(f"[Mute] Unknown mute command: {cmd}")
                return False
            return True
        except Exception as e:
            print(f"[Mute] Mute command error: {e}")
            return False

class PingCommand(CommandInterface):
    def __init__(self, mqtt_manager=None, health_check: Optional[Callable[[], dict]] = None):
        self.mqtt_manager = mqtt_manager
        self.health_check = health_check

    def execute(self, cmd: CommandType, value: Any = None, timestamp: str = "", device_id: str = "") -> bool:
        try:
            self.mqtt_manager.publish_device_register()      

            return True
        except Exception as e:
            print(f"[Ping] Ping handling error: {e}")
            return False
    
class GameCommand(CommandInterface):
    def __init__(self, game_handler):
       self.game_handler = game_handler
    
    def execute(self, cmd: CommandType, value: Any = None, timestamp: str = "", device_id: str = "") -> bool:
        try:
            self.game_handler.handle_command(cmd)

        except Exception as e:
            print(f"[GameCmd] Failed to change Game Status: {e}")
            return False


# 4. Dispatcher (Invoker)
class CommandDispatcher:
    def __init__(self):
        self.handlers: Dict[CommandType, CommandInterface] = {}

    def register(self, command_type: Union[CommandType, List[CommandType]], handler: CommandInterface):
        if isinstance(command_type, list):
            for c in command_type:
                print(f"[Dispatch] command handler register: {c}")
                self.handlers[c] = handler
        else:
            print(f"[Dispatch] command handler register: {command_type}")
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

        return handler.execute(command_enum, value, timestamp, device_id)
