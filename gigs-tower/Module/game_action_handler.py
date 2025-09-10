from .events import GameEvent, EventType, InputSource
from .game_state import GameState, GameStateManager

class GameActionHandler:
    """
    Serial / Keyboard / GameCommand에서 들어오는 이벤트를
    한 곳에서 처리하여 GameStateManager를 호출한다.
    """
    def __init__(self, gsm: GameStateManager, gigs_instance=None):
        self.gsm = gsm
        self._gigs = gigs_instance  # TCP/점수 등 부수효과에서 사용

    # RFID 공통 처리
    def on_rfid_detected(self, ev: GameEvent):
        current = self.gsm.current_state
        rfid = ev.raw
        print(f"[Action] RFID '{rfid}' detected from {ev.source}, state={current}")

        # 1. Publish RFID detection event immediately. This also stores the RFID.
        self.gsm.publish_rfid_detected(rfid)

        # 2. Perform original state transition logic.
        if current == GameState.INIT:
            print("[Action] INIT -> WAITING")
            self.gsm.show_waiting()

        elif current == GameState.WAITING:
            print("[Action] WAITING -> COUNTDOWN")
            if getattr(self._gigs, "use_tcp", False):
                self._gigs.tcp_handler.send_message('-1')
            self.gsm.start_countdown()

        elif current == GameState.PLAYING:
            print("[Action] PLAYING -> RESULT")
            score = getattr(self._gigs.score_manager, "get_total_score", lambda: 0)()
            if score == 0:
                score = 7176
            self.gsm.show_result(score)

        elif current == GameState.ENTER:
            self.gsm.sound_manager.play_bgm('enter_result')
            # ENTER/EXIT are one-off events, so clear the RFID immediately after use.
            self.gsm.clear_last_rfid()

        elif current == GameState.EXIT:
            self.gsm.sound_manager.play_bgm('exit_result')
            # ENTER/EXIT are one-off events, so clear the RFID immediately after use.
            self.gsm.clear_last_rfid()

        else:
            # This now includes SCORE and RESULT states, where RFID was previously ignored.
            # Now it's published, which is correct according to the new request.
            print(f"[Action] RFID event published for state {current}. No state transition.")

    # 점수 수신
    def on_score_received(self, ev: GameEvent):
        score = ev.score or 0
        if self.gsm.current_state == GameState.PLAYING:
            self._gigs.score_manager.add_score(score)
            print(f"[Action] Added {score} points!")
        else:
            print(f"[Action] Score {score} ignored in {self.gsm.current_state}")

    # START/STOP/RESET
    def on_command(self, ev: GameEvent):
        cs = self.gsm.current_state

        if ev.kind == EventType.GAME_START:
            if cs == GameState.INIT:
                print("[GameCmd] INIT -> WAITING")
                self.gsm.show_waiting()
            elif cs == GameState.WAITING:
                print("[GameCmd] WAITING -> COUNTDOWN")
                if getattr(self._gigs, "use_tcp", False):
                    self._gigs.tcp_handler.send_message('-1')
                self.gsm.start_countdown()
            elif cs == GameState.PLAYING:
                print("[GameCmd] PLAYING -> RESULT (force end)")
                score = self._gigs.score_manager.get_total_score()
                if score == 0:
                    score = 7176
                self.gsm.show_result(score)
            else:
                print(f"[GameCmd] START ignored in {cs}")

        elif ev.kind == EventType.GAME_STOP:
            if cs == GameState.PLAYING:
                print("[GameCmd] show_score(7176)")
                self.gsm.show_score(7176)  # TODO: 실행중 점수 반영
            else:
                print(f"[GameCmd] STOP ignored in {cs}")

        elif ev.kind == EventType.GAME_RESET:
            print("[GameCmd] RESET -> WAITING")
            self.gsm.show_waiting()