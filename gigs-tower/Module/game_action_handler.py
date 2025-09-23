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
    def on_rfid_detected(self, ev: GameEvent):
        current = self.gsm.current_state
        rfid = ev.raw
        print(f"[Action] RFID '{rfid}' detected from {ev.source}, state={current}")

        # 마스터 카드 태그 시
        MASTER_CARDS_UID = {"A736C701", "A3B60E02", "DCA30E02", "C25AC601", "8D37B001", "6265B501", "QWER1234"}  # 추가 UID 가능
        if rfid in MASTER_CARDS_UID and current in [GameState.PLAYING, GameState.COUNTDOWN]:
            # 점수는 0점으로 처리하여 종료처리
            self.gsm.show_result(0)
            print(f"[Action] MASTER CARD '{rfid}' detected during game! Forcing game end.")
            return  # 이후 로직 무시

        # TODO: 공통 로직 메서드 추상화 
        # 게임 중인 경우 태그 시 예외처리
        if current in [GameState.PLAYING, GameState.COUNTDOWN]:
            self.gsm.screen_update_callback(f"게임이 진행 중 입니다.\n(태그 불가)")
            import threading
            threading.Timer(1, self.gsm._restore_state_display).start()
            print(f"[Action] Ignored RFID '{rfid}' tag When Game is Playing")
            return

        # 중복 태그 방지
        if rfid == self.gsm.last_rfid and current not in [GameState.PLAYING, GameState.SCORE]:
            self.gsm.screen_update_callback(f"이미 처리가 되었습니다.\n(RFID: {rfid})")
            self.gsm.sound_manager.play_sfx('get') # TODO: 사운드 변경
            import threading
            threading.Timer(1.5, self.gsm._restore_state_display).start()
            print(f"[Action] Duplicate RFID '{rfid}' ignored in state {current}")
            return


        # MQTT 상태 전송 (서버가 플레이어 관리 및 last_rfid 업데이트)
        self.gsm.publish_rfid_detected(rfid)

        if current == GameState.ENTER:
            self.gsm.sound_manager.play_sfx('get') # TODO: 사운드 변경
            mock_nickname = f"Player_{rfid[-4:]}" # TODO: 서버 연동 - 닉네임 받아오기
            temp_message = f"환영합니다! {mock_nickname}님\n(RFID: {rfid})"
            self.gsm.screen_update_callback(temp_message)
            import threading
            threading.Timer(1.5, self.gsm._restore_state_display).start()
            print(f"[Action] Player Eneter:  RFID '{rfid}'")
            return

        if current == GameState.EXIT:
            self.gsm.sound_manager.play_sfx('get') # TODO: 사운드 변경
            temp_message = f"퇴장 처리 되었습니다.\n(RFID: {self.gsm.last_rfid})"
            self.gsm.screen_update_callback(temp_message)
            import threading
            threading.Timer(1.5, self.gsm._restore_state_display).start()
            print(f"[Action] Player EXIT:  RFID '{rfid}'")
            return

        elif current == GameState.INIT:
            print("[Action] INIT -> WAITING")
            self.gsm.show_waiting()

        elif current == GameState.WAITING:
            # 마스터 카드가 아닌 경우에만 게임 차단 상태 체크
            if not is_master_card and getattr(self.gsm, 'game_blocked', False):
                print("[Action] Game is blocked due to error - countdown cancelled")
                return

            print("[Action] WAITING -> COUNTDOWN")
            if getattr(self._gigs, "use_tcp", False):
                self._gigs.tcp_handler.send_message('-1')
            self.gsm.start_countdown(force=is_master_card)

        elif current == GameState.PLAYING:
            print("[Action] PLAYING -> RESULT")
            score = getattr(self._gigs.score_manager, "get_total_score", lambda: 0)()
            if score == 0:
                score = 7176
            self.gsm.show_result(score)

        else:
            print(f"[Action] RFID event sent to server for state {current}")

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

        # 마스터 카드 권한 체크 (게임 명령은 마스터 권한으로 처리)
        MASTER_CARDS_UID = {"7C9E4705", "QWER1234", "87654321"}
        is_master_command = hasattr(ev, 'rfid') and ev.rfid in MASTER_CARDS_UID

        if ev.kind == EventType.GAME_START:
            if cs == GameState.INIT:
                print("[GameCmd] INIT -> WAITING")
                self.gsm.show_waiting()
            elif cs == GameState.WAITING:
                # 마스터 명령이 아닌 경우에만 게임 차단 상태 체크
                if not is_master_command and getattr(self.gsm, 'game_blocked', False):
                    print("[GameCmd] Game is blocked due to error - countdown cancelled")
                    return

                # 마스터 명령인 경우 에러 상태 자동 클리어
                if is_master_command and getattr(self.gsm, 'game_blocked', False):
                    self.gsm.clear_error()
                    print("[GameCmd] Master command cleared error state")

                print("[GameCmd] WAITING -> COUNTDOWN")
                if getattr(self._gigs, "use_tcp", False):
                    self._gigs.tcp_handler.send_message('-1')
                self.gsm.start_countdown(force=is_master_command)
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