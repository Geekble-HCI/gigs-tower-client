from .command_handler import CommandType
from .events import EventType, InputSource, GameEvent

class GameHandler:
    """
    외부(예: MQTTManager 등)에서 들어오는 게임 명령을
    Event로 변환해서 GameActionHandler에 위임한다.
    """
    def __init__(self, gigs_instance, action_handler):
        self._gigs = gigs_instance
        self._action = action_handler

    def handle_command(self, cmd: CommandType):
        mapping = {
            CommandType.GAME_START: EventType.GAME_START,
            CommandType.GAME_STOP:  EventType.GAME_STOP,
            CommandType.GAME_RESET: EventType.GAME_RESET,
        }
        et = mapping.get(cmd)
        if not et:
            print(f"[GameCmd] Unknown cmd: {cmd}")
            return False
        ev = GameEvent(kind=et, source=InputSource.COMMAND, raw=str(cmd))
        self._action.on_command(ev)
        return True