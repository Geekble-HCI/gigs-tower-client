import json
import threading
import time
from datetime import datetime
from .sound_manager import SoundManager

class GameState:
    INIT = "INIT"
    WAITING = "WAITING"
    COUNTDOWN = "COUNTDOWN"
    PLAYING = "PLAYING"
    SCORE = "SCORE"
    RESULT = "RESULT"
    ENTER = "ENTER"  # 새로운 상태 추가
    EXIT = "EXIT"    # 새로운 상태 추가

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

    def __init__(self, screen_update_callback, state_change_callback=None, game_type=1, score_wait_time=15, countdown_time=10, mqtt_client=None):
        self.current_state = GameState.INIT  # 초기 상태를 INIT으로 변경
        self.last_rfid = None  # 마지막으로 스캔된 RFID 저장
        self.countdown = 10
        self.timer_thread = None
        self.screen_update_callback = screen_update_callback
        self.sound_manager = SoundManager(game_type)  # game_type 전달
        self.result_thread = None
        self.score_thread = None  # Add score timeout thread
        self.state_change_callback = state_change_callback  # 상태 변경 콜백 추가
        self.play_thread = None
        self.score_wait_time = score_wait_time  # Store the wait time
        self.countdown_time = countdown_time  # Store the countdown time
        self.mqtt_client = mqtt_client # MQTT 클라이언트 저장
        self.device_id = mqtt_client.device_id if mqtt_client else "unknown_client"
        self.device_ip = mqtt_client.ip_address if mqtt_client else "unknown_ip"
        self.current_player_info = None  # 서버로부터 받은 플레이어 정보

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
            return 'enter'
        elif state == GameState.EXIT:
            return 'exit'
        else:
            return 'inprogress'

    def _build_payload(self, state: str, score: int | float | None = None, rfid: str | None = None) -> dict:
        """서버 전송용 페이로드 생성 (단순화)"""
        progress_state = self._get_progress_state(state)

        payload = {
            "device_id": self.device_id,
            "game_type": self.sound_manager.game_type,
            "game_name": GameStateManager.get_game_name(self.sound_manager.game_type, True),
            "state": state,
            "progress_state": progress_state,
            "rfid": rfid,
            "timestamp": datetime.now().isoformat()
        }

        if score is not None:
            payload["score"] = score
        return payload
        
    def _publish_state(self, state, score=None, rfid=None):
        if not self.mqtt_client:
            return
        # 인자로 rfid가 주어지지 않으면, 저장된 last_rfid 사용
        rfid_to_publish = rfid if rfid is not None else self.last_rfid
        topic = f"device/{self.device_ip}/state"
        payload = self._build_payload(state, score, rfid=rfid_to_publish)
        self.mqtt_client.publish(topic, json.dumps(payload, ensure_ascii=False), qos=1, retain=False)

    def publish_rfid_detected(self, rfid: str):
        """Stores the detected RFID and publishes an MQTT message."""
        self.last_rfid = rfid
        self._publish_state(self.current_state, rfid=rfid)

    def clear_last_rfid(self):
        """Clears the last stored RFID."""
        self.last_rfid = None

    def start_countdown(self):
        self.current_state = GameState.COUNTDOWN
        self._publish_state(self.current_state)
        self.countdown = self.countdown_time  # Use the configured countdown time
        self.sound_manager.play_bgm('countdown')  # play_sound -> play_bgm
        
        def countdown_timer():
            while self.countdown > 0 and self.current_state == GameState.COUNTDOWN:
                self.screen_update_callback(f"게임이 곧 시작됩니다.\n\n{self.countdown}")
                self.countdown -= 1
                time.sleep(1)
            if self.current_state == GameState.COUNTDOWN:
                self.start_game()

        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(0)
        self.timer_thread = threading.Thread(target=countdown_timer)
        self.timer_thread.daemon = True
        self.timer_thread.start()

    def start_game(self):
        self.current_state = GameState.PLAYING
        self._publish_state(self.current_state)
        self.sound_manager.play_bgm_loop('playing')  # play_sound_loop -> play_bgm_loop
        self.screen_update_callback("게임 진행 중...")
        if self.state_change_callback:
            self.state_change_callback(GameState.PLAYING)
            
        def play_timer():
            time.sleep(60)  # 60초 대기
            if self.current_state == GameState.PLAYING:
                if self.state_change_callback:
                    self.state_change_callback(GameState.SCORE)
        
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(0)
        self.play_thread = threading.Thread(target=play_timer)
        self.play_thread.daemon = True
        self.play_thread.start()

    def show_score(self, score):
        self.current_state = GameState.SCORE
        self._publish_state(self.current_state, score=score)
        self.sound_manager.play_bgm('score')  # play_sound -> play_bgm
        self.screen_update_callback(f"당신의 점수는?\n\n{score}\n\n태그를 하여\n점수를 획득하세요!")
        
        def score_timer():
            time.sleep(self.score_wait_time)  # Use the configured wait time
            if self.current_state == GameState.SCORE:  # 여전히 SCORE 상태라면
                self.show_waiting()  # WAITING 상태로 전환
        
        # 이전 타이머가 있다면 정리
        if self.score_thread and self.score_thread.is_alive():
            self.score_thread.join(0)
        self.score_thread = threading.Thread(target=score_timer, daemon=True)
        self.score_thread.start()

    def show_result(self, score):
        self.current_state = GameState.RESULT
        self._publish_state(self.current_state, score=score)
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

    def show_waiting(self):
        """게임 상태를 대기 상태로 초기화하고, 마지막 RFID 정보를 리셋."""
        self.current_state = GameState.WAITING
        self.last_rfid = None  # 새 세션을 위해 마지막 RFID 리셋
        self._publish_state(self.current_state)
        self.countdown = self.countdown_time  # Use the configured countdown time
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(0)
        self.timer_thread = None
        self.sound_manager.stop_bgm()
        
        game_title = GameStateManager.get_game_name(self.sound_manager.game_type)

        self.screen_update_callback(f"{game_title}\n\n태그를 하면\n게임이 시작됩니다!")

    def show_init(self):
        """초기화 상태 표시"""
        self.current_state = GameState.INIT
        self._publish_state(self.current_state)
        self.sound_manager.play_bgm_loop('waiting')  # play_sound_loop -> play_bgm_loop
        self.screen_update_callback("시스템 초기화 중...")

    def show_enter(self):
        """입장 상태 표시"""
        self.current_state = GameState.ENTER
        self._publish_state(self.current_state)
        self.sound_manager.play_bgm_loop('enter')  # enter.wav 또는 enter.mp3 필요
        self.screen_update_callback("게임을 시작해주세요!")

    def show_exit(self):
        """퇴장 상태 표시"""
        self.current_state = GameState.EXIT
        self._publish_state(self.current_state)
        self.sound_manager.play_bgm_loop('exit')  # exit.wav 또는 exit.mp3 필요
        self.screen_update_callback("수고하셨습니다!")

    def handle_player_feedback(self, feedback_data: dict):
        """서버로부터 받은 플레이어 피드백 처리"""
        self.current_player_info = feedback_data

        # 클라이언트에서 UI 메시지 생성
        ui_message = self._generate_ui_message(feedback_data)
        # 콜백에 플레이어 정보(feedback_data)를 함께 전달
        self.screen_update_callback(ui_message, feedback_data)

        # 클라이언트에서 사운드 효과 결정
        sound_effect = self._determine_sound_effect(feedback_data)
        if sound_effect:
            self.sound_manager.play_sfx(sound_effect)

        # 표시 시간 결정
        duration = self._get_display_duration(feedback_data)
        import threading
        threading.Timer(duration, self._restore_state_display).start()

    def _generate_ui_message(self, feedback_data: dict) -> str:
        """플레이어 정보를 기반으로 UI 메시지 생성"""
        progress_state = feedback_data.get('progress_state', '')
        nickname = feedback_data.get('nickname')
        is_new_player = feedback_data.get('is_new_player', False)
        game_state = feedback_data.get('game_state')

        if progress_state == 'enter':
            if nickname:
                return f"환영합니다!\n{nickname}님" if is_new_player else f"다시 오셨군요!\n{nickname}님"
            else:
                return "환영합니다!\n신규 플레이어님" if is_new_player else "환영합니다!"

        elif progress_state == 'inprogress':
            if game_state == 'RESULT':
                return f"{nickname}님\n게임 종료!" if nickname else "게임 종료!"
            else:
                return f"{nickname}님\n게임 진행 중" if nickname else "게임 진행 중"

        elif progress_state == 'exit':
            return f"안녕히 가세요!\n{nickname}님" if nickname else "안녕히 가세요!"

        else:
            return 'RFID 인식됨'

    def _determine_sound_effect(self, feedback_data: dict) -> str:
        """플레이어 정보를 기반으로 사운드 효과 결정"""
        progress_state = feedback_data.get('progress_state')
        game_state = feedback_data.get('game_state')

        if progress_state == 'enter':
            return 'player_enter'
        elif progress_state == 'inprogress':
            return 'game_progress' if game_state == 'RESULT' else 'tag_success'
        elif progress_state == 'exit':
            return 'player_exit'
        else:
            return 'tag_success'

    def _get_display_duration(self, feedback_data: dict) -> float:
        """플레이어 정보를 기반으로 표시 시간 결정"""
        progress_state = feedback_data.get('progress_state', '')

        if progress_state in ['enter', 'exit']:
            return 3.0
        else:
            return 2.0

    def _restore_state_display(self):
        """원래 상태 표시로 복구"""
        # 현재 상태에 맞는 기본 메시지로 복구
        if self.current_state == GameState.WAITING:
            game_title = GameStateManager.get_game_name(self.sound_manager.game_type)
            self.screen_update_callback(f"{game_title}\n\n태그를 하면\n게임이 시작됩니다!")
        elif self.current_state == GameState.PLAYING:
            self.screen_update_callback("게임 진행 중...")
        elif self.current_state == GameState.ENTER:
            self.screen_update_callback("게임을 시작해주세요!")
        elif self.current_state == GameState.EXIT:
            self.screen_update_callback("수고하셨습니다!")
