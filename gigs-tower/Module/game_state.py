import json
import threading
import time
from datetime import datetime
import uuid
from .sound_manager import SoundManager

class GameState:
    INIT = "INIT"
    WAITING = "WAITING"
    COUNTDOWN = "COUNTDOWN"
    PLAYING = "PLAYING"
    SCORE = "SCORE"
    RESULT = "RESULT"
    ENTER = "ENTER"  
    EXIT = "EXIT"
    TAG = "TAG"  # 태그 인식 상태
    ERROR = "ERROR"  # 에러 상태

class PlayerProgressState:
    ENTER = "ENTER"
    IN_PROGRESS = "INPROGRESS"
    EXIT = "EXIT"

class GameStateManager:
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

    def __init__(self, screen_update_callback, state_change_callback=None, game_type=1, score_wait_time=3, countdown_time=10, mqtt_client=None):
        self.current_state = GameState.INIT  # 초기 상태를 INIT으로 변경
        self.countdown = 10
        self.timer_thread = None
        self.screen_update_callback = screen_update_callback
        self.sound_manager = SoundManager(game_type)  # game_type 전달
        self.result_thread = None
        self.score_thread = None  # Add score timeout thread
        self.state_change_callback = state_change_callback  # 상태 변경 콜백 추가
        self.play_thread = None
        self.score_wait_time = 3  # Store the wait time
        self.countdown_time = countdown_time  # 현재 카운트다운(동적으로 변경 가능)
        self.default_countdown_time = countdown_time  # 기본값 보관(복귀 시 사용)
        self.mqtt_client = mqtt_client # MQTT 클라이언트 저장
        self.device_id = mqtt_client.device_id if mqtt_client else "unknown_client"
        self.device_ip = mqtt_client.ip_address if mqtt_client else "unknown_ip"
        self.game_type = game_type  # 게임 타입 저장
        self.error_thread = None  # 에러 메시지 타이머 스레드
        self.game_blocked = False  # 게임 차단 상태
        self.session_rfid: str | None = None  # 현재 세션(1판)에서 유지할 RFID
        self.last_score: int | float | None = None

    def set_session_rfid(self, rfid: str | None):
        self.session_rfid = rfid

    def clear_session_rfid(self):
        self.session_rfid = None

    @staticmethod
    def get_game_name(game_type: int, remove_newline: bool = False) -> str:
        """
        game_type에 해당하는 게임명을 반환.
        remove_newline=True일 경우, 줄바꿈(\n)을 공백으로 치환.
        """
        raw_name = GameStateManager.GAME_MESSAGES.get(game_type, "칼로링머신")
        if remove_newline:
            return raw_name.replace("\n", " ")
        return raw_name

    def _get_progress_state(self, state: str) -> str:
        """현재 상태에 따른 progress_state 결정"""
        if state == GameState.ENTER:
            return PlayerProgressState.ENTER
        elif state == GameState.EXIT:
            return PlayerProgressState.EXIT
        elif state == GameState.TAG:
            if self.sound_manager.game_type == 7:  # 입장 화면
                return PlayerProgressState.ENTER
            elif self.sound_manager.game_type == 8:  # 퇴장 화면
                return PlayerProgressState.EXIT
            else:  # type 1~6 (일반 게임)
                return PlayerProgressState.IN_PROGRESS
        
        elif state == GameState.ERROR:
            if self.sound_manager.game_type == 7:  # 입장 화면
                return PlayerProgressState.ENTER
            elif self.sound_manager.game_type == 8:  # 퇴장 화면
                return PlayerProgressState.EXIT
            else:  # type 1~6 (일반 게임)
                return PlayerProgressState.IN_PROGRESS
        else:
            return PlayerProgressState.IN_PROGRESS

    def _build_payload(self, state: str, score: int | float | None = None, rfid: str | None = None, error_type: str | None = None) -> dict:
        """서버 전송용 페이로드 생성 (단순화)"""
        progress_state = self._get_progress_state(state)
        cid = str(uuid.uuid4())

        payload = {
            "device_id": self.device_id,
            "game_type": self.sound_manager.game_type,
            "game_name": GameStateManager.get_game_name(self.sound_manager.game_type, True),
            "state": state,
            "progress_state": progress_state,
            "rfid": rfid,
            "timestamp": datetime.now().isoformat(),
            "replyTo": f"device/{self.device_id}/state",
            "correlationId": cid,
        }

        if score is not None:
            payload["score"] = score
        if error_type is not None:
            payload["error_type"] = error_type
        return payload
        
    def _publish_state(self, state, score=None, rfid=None, error_type=None):
        if not self.mqtt_client:
            return None

        # 인자로 rfid가 주어지지 않으면, 저장된 session_rfid 사용
        rfid_to_publish = rfid if rfid is not None else self.session_rfid

        topic = f"device/{self.device_ip}/state"
        payload = self._build_payload(state, score, rfid=rfid_to_publish, error_type=error_type)
        self.mqtt_client.publish(topic, json.dumps(payload, ensure_ascii=False), qos=1, retain=False)

        # INIT, WAITING 상태에서는 서버 응답이 없으므로 None 반환 (타임아웃 방지)
        if state in [GameState.INIT, GameState.WAITING]:
            print(f"[GameState] Published {state} state without expecting response (rfid: {rfid_to_publish})")
            return None

        # 다른 상태에서는 correlationId 반환 (서버 응답 기대)
        return payload["correlationId"]

    def publish_rfid_detected(self, rfid: str):
        """RFID 감지 시 TAG 상태로 MQTT 메시지 전송 (서버 응답 기대)"""
        self.set_session_rfid(rfid)
        return self._publish_state(GameState.TAG, rfid=rfid)


    def start_countdown(self, force=False):
        if not force and self.game_blocked:
            print("[GAME] Cannot start countdown: Game is blocked due to error")
            return

        self.current_state = GameState.COUNTDOWN
        self._publish_state(self.current_state)
        self.countdown = self.countdown_time 
        self.sound_manager.play_bgm('countdown')  # play_sound -> play_bgm

        def countdown_timer():
            while self.countdown > 0 and self.current_state == GameState.COUNTDOWN and not self.game_blocked:
                self.screen_update_callback(f"게임이 곧 시작됩니다.\n\n{self.countdown}")
                self.countdown -= 1
                time.sleep(1)
            if self.current_state == GameState.COUNTDOWN and not self.game_blocked:
                self.start_game()

        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(0)
        self.timer_thread = threading.Thread(target=countdown_timer)
        self.timer_thread.daemon = True
        self.timer_thread.start()

    def start_game(self, rfid: str | None = None):
        # 게임이 차단된 상태라면 게임을 시작하지 않음
        if self.game_blocked:
            print("[GAME] Cannot start game: Game is blocked due to error")
            return

        self.current_state = GameState.PLAYING
        if rfid:
            self.set_session_rfid(rfid)
        self._publish_state(self.current_state, rfid=self.session_rfid)
        self.sound_manager.play_bgm_loop('playing')  # play_sound_loop -> play_bgm_loop
        self.screen_update_callback("게임 진행 중...")
        if self.state_change_callback:
            self.state_change_callback(GameState.PLAYING)

        def play_timer():
            remaining = 50  # 50초 제한
            while remaining > 0 and self.current_state == GameState.PLAYING and not self.game_blocked:
                self.screen_update_callback(f"게임 진행 중...\n\n{remaining}")
                time.sleep(1)
                remaining -= 1
            # 시간이 다 됐을 때 SCORE 상태로 전환
            if self.current_state == GameState.PLAYING and not self.game_blocked:
                score = 0
                if hasattr(self, "_gigs") and hasattr(self._gigs, "score_manager"):
                    score = getattr(self._gigs.score_manager, "get_total_score", lambda: 0)()
                self.show_score(score)

        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(0)
        self.play_thread = threading.Thread(target=play_timer, daemon=True)
        self.play_thread.start()

    def show_score(self, score: int | float, rfid: str | None = None):
        self.current_state = GameState.SCORE
        self.last_score = score
        if rfid:
            self.set_session_rfid(rfid)
        self._publish_state(self.current_state, score=score, rfid=self.session_rfid)
        self.sound_manager.play_bgm('score')  # play_sound -> play_bgm
        self.screen_update_callback(f"당신의 점수는?\n\n{int(score)}점을\n획득했습니다!")
        
        def score_timer():
            time.sleep(self.score_wait_time)  # Use the configured wait time
            if self.current_state == GameState.SCORE:  # 여전히 SCORE 상태라면
                self.show_waiting()  # WAITING 상태로 전환
        
        # 이전 타이머가 있다면 정리
        if self.score_thread and self.score_thread.is_alive():
            self.score_thread.join(0)
        self.score_thread = threading.Thread(target=score_timer, daemon=True)
        self.score_thread.start()

    def show_result(self, score: int | float, rfid: str | None = None):
        self.current_state = GameState.RESULT
        self.last_score = score
        if rfid:
            self.set_session_rfid(rfid)
        self._publish_state(self.current_state, score=score, rfid=self.session_rfid)
        self.sound_manager.play_bgm('result')  # play_sound -> play_bgm
        self.screen_update_callback(f"{int(score)}점을\n획득했습니다!")
        
        def result_timer():
            time.sleep(3)  # 3초 대기
            if self.current_state == GameState.RESULT:
                self.show_waiting()
        
        if self.result_thread and self.result_thread.is_alive():
            self.result_thread.join(0)
        self.result_thread = threading.Thread(target=result_timer)
        self.result_thread.daemon = True
        self.result_thread.start()

    def show_waiting(self, publish_state=True):
        """게임 상태를 대기 상태로 초기화하고, 마지막 RFID 정보를 리셋."""
        self.current_state = GameState.WAITING
        self.clear_session_rfid()
        self.countdown_time = self.default_countdown_time # 카운트다운 시간을 기본값으로 복귀

        # 에러 복구 시에는 MQTT 발행하지 않음
        if publish_state:
            self._publish_state(self.current_state)

        self.countdown = self.countdown_time  # Use the configured countdown time
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(0)
        self.timer_thread = None
        self.sound_manager.stop_bgm()

        if self.sound_manager.game_type == 7:
            # 입장
            self.screen_update_callback("환영합니다!\n태그를 해주세요!")
        elif self.sound_manager.game_type == 8:
            # 퇴장
            self.screen_update_callback("수고하셨습니다!\n태그를 해주세요!")
        else:
            # 게임
            game_title = GameStateManager.get_game_name(self.sound_manager.game_type)
            self.screen_update_callback(f"{game_title}\n\n태그를 하면\n게임이 시작됩니다!")

    def show_init(self):
        """초기화 상태 표시"""
        self.current_state = GameState.INIT
        self._publish_state(self.current_state)
        self.sound_manager.play_bgm_loop('waiting')  # play_sound_loop -> play_bgm_loop
        self.screen_update_callback("시스템 초기화 중...")

    def show_enter(self, publish_state=True):
        """입장 상태 표시"""
        self.current_state = GameState.ENTER
        self.clear_session_rfid()

        # 에러 복구 시에는 MQTT 발행하지 않음
        if publish_state:
            self._publish_state(self.current_state)

        self.sound_manager.play_bgm_loop('enter') 
        self.screen_update_callback("환영합니다!\n태그를 해주세요!")

    def show_exit(self, publish_state=True):
        """퇴장 상태 표시"""
        self.current_state = GameState.EXIT
        self.clear_session_rfid()

        # 에러 복구 시에는 MQTT 발행하지 않음
        if publish_state:
            self._publish_state(self.current_state)

        self.sound_manager.play_bgm_loop('exit')  # exit.wav 또는 exit.mp3 필요
        self.screen_update_callback("수고하셨습니다!\n태그를 해주세요!")

    def show_error(self, error_type: str, error_message: str, recovery_state: str = None):
        """에러 처리 및 이전 상태로 복구"""

        # 현재 상태를 복구 대상으로 저장 (ERROR로 변경하기 전에)
        previous_state = recovery_state or self.current_state

        print(f"[ERROR] Error in {previous_state} state: {error_type}")

        # ERROR 상태로 전환
        self.current_state = GameState.ERROR
        self.game_blocked = True  # 에러 시 게임 차단
                        
        # TODO: MQTT로 에러 상태 전송
        # self._publish_state(self.current_state, error_type=error_type)

        # 에러 메시지 표시
        self.screen_update_callback(f"{error_message}")

        # 이전 상태로 복구 
        def auto_recover():
            time.sleep(2.5) 
            if self.current_state == GameState.ERROR:
                print(f"[ERROR] Auto recovery: ERROR → {previous_state}")

                self.game_blocked = False  # 자동 복구 시 차단 해제
                if previous_state == GameState.ENTER:
                    self.show_enter(publish_state=False)  # 에러 복구시 MQTT 발행 안함
                elif previous_state == GameState.EXIT:
                    self.show_exit(publish_state=False)   # 에러 복구시 MQTT 발행 안함
                else:
                    # 기본적으로 WAITING 상태로 복구
                    self.show_waiting(publish_state=False)  # 에러 복구시 MQTT 발행 안함

        if self.error_thread and self.error_thread.is_alive():
            self.error_thread.join(0)
        self.error_thread = threading.Thread(target=auto_recover, daemon=True)
        self.error_thread.start()

    def restore_state_display(self):
        """원래 상태 표시로 복구"""
        if self.current_state == GameState.ERROR:
        # 현재 상태가 ERROR면 직전 기본 화면으로 정리
            if self.sound_manager.game_type == 7:
                self.screen_update_callback("환영합니다!\n태그를 해주세요!")
            elif self.sound_manager.game_type == 8:
                self.screen_update_callback("수고하셨습니다!\n퇴장 태그를 해주세요!")
            else:
                game_title = GameStateManager.get_game_name(self.sound_manager.game_type)
                self.screen_update_callback(f"{game_title}\n\n태그를 하면\n게임이 시작됩니다!")
            return
        # 현재 상태에 맞는 기본 메시지로 복구
        if self.current_state == GameState.WAITING:
            game_title = GameStateManager.get_game_name(self.sound_manager.game_type)
            self.screen_update_callback(f"{game_title}\n\n태그를 하면\n게임이 시작됩니다!")
        elif self.current_state == GameState.PLAYING:
            self.screen_update_callback("게임 진행 중...")
        elif self.current_state == GameState.ENTER:
            self.screen_update_callback("게임을 시작해주세요!")
        elif self.current_state == GameState.EXIT:
            self.screen_update_callback("수고하셨습니다!\n퇴장 태그를 해주세요!")
        elif self.current_state == GameState.SCORE:
            s = int(self.last_score or 0)
            self.screen_update_callback(f"당신의 점수는?\n\n{s}점을\n획득했습니다!")
        elif self.current_state == GameState.RESULT:
            s = int(self.last_score or 0)
            self.screen_update_callback(f"{s}점을\n획득했습니다!")

    def recover_from_error(self):
        """에러 상태에서 WAITING으로 수동 복구"""
        if self.current_state == GameState.ERROR:
            print("[ERROR] Manual recovery: ERROR → WAITING")
            self.show_waiting()
    
    def clear_error(self, publish_state: bool = False):
        """수동 해제(마스터 명령 등)"""
        self.game_blocked = False
        print("[GameState] Error cleared")
        self.show_waiting(publish_state=publish_state)

