from Module.command_handler import CommandType
from Module.game_state import GameState


class GameHandler:

    def __init__(self, gigs_instance):
        self._gigs = gigs_instance

    def handle_command(self, cmd: CommandType):
        if cmd is CommandType.GAME_START: self._on_start(cmd)
        elif cmd is CommandType.GAME_STOP: self._on_stop(cmd)
        elif cmd is CommandType.GAME_RESET: self._on_reset(cmd)

    def _on_start(self, cmd: CommandType):
        """게임 시작"""
        if cmd is CommandType.GAME_START:
            current_state = self._gigs.game_state.current_state
            # 상태별 처리
            if current_state == GameState.INIT:
                print("[GameCmd] INIT -> WAITING")
                self._gigs.game_state.show_waiting()
            elif current_state == GameState.WAITING:
                print("[GameCmd] WAITING -> COUNTDOWN")
                if self._gigs.use_tcp:
                    self._gigs.tcp_handler.send_message('-1')
                self._gigs.game_state.start_countdown()
            elif current_state == GameState.PLAYING:
                print("[GameCmd] PLAYING -> RESULT (forcing game end)")
                # 테스트용 점수로 결과 화면 표시
                test_score = self._gigs.score_manager.get_total_score()
                if test_score == 0:
                    test_score = 7176  # 기본 테스트 점수
                self._gigs.game_state.show_result(test_score)
            else:
                print(f"[GameCmd] Command({cmd}) is {current_state} - no action")
        return True
    
    def _on_stop(self, cmd: CommandType):
        """게임 중지 ( 플레이 상태인 게임 중지 )"""
        if cmd is CommandType.GAME_STOP:
            if self._gigs.game_state.current_state == GameState.PLAYING:
                print("[GameCmd] Calling show_score(7176)")
                self._gigs.game_state.show_score(7176) # TODO: 실행 중인 스코어 값으로 설정
                return True
            else:
                print("[GameCmd] {cmd} ignored (not in PlAYING state)")
                return False
        else:
            print("[GameCmd] Error: invalided {cmd}")
            return False
    
    def _on_reset(self, cmd: CommandType):
        if cmd is CommandType.GAME_RESET:
            self._gigs.game_state.show_waiting()
            print("[GameCmd] Game force init")