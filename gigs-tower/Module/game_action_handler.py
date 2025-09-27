import time
from datetime import datetime
from .events import GameEvent, EventType, InputSource
from .game_state import GameState, GameStateManager
from .error_type import ErrorType

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
        print(f"[Action][TRACE] ★★★ RFID '{rfid}' detected from {ev.source}, state={current} ★★★")
        print(f"[Action][TRACE] Event details: {vars(ev)}")
        print(f"[Action][TRACE] Call stack info - This will help identify who called this function")
        import traceback
        print(f"[Action][TRACE] Stack trace: {traceback.format_stack()[-3:-1]}")

        # 마스터 카드 특권 (모든 예외 무시)
        MASTER_CARDS_UID = {"A736C701", "A3B60E02", "DCA30E02", "C25AC601", "8D37B001", "6265B501", "QWER1234"}
        is_master_card = rfid in MASTER_CARDS_UID

        if is_master_card:
            # 마스터키: 모든 제약 무시하고 테스트 가능
            self._handle_master_card(rfid, current)
            return
        
        # 게임 실행 중 태그 차단
        if current in [GameState.PLAYING, GameState.COUNTDOWN]:
            self.gsm.screen_update_callback(f"게임이 진행 중 입니다.\n(태그 불가)")
            import threading
            threading.Timer(1, self.gsm.restore_state_display).start()
            print(f"[Action] Ignored RFID '{rfid}' tag When Game is Playing")
            return
        
        #  # 중복 태그 방지
        if rfid == self.gsm.session_rfid and current not in [GameState.PLAYING, GameState.SCORE]:
            self.gsm.screen_update_callback(f"이미 처리가 되었습니다.\n(RFID: {rfid})")
            self.gsm.sound_manager.play_sfx('get') # TODO: 사운드 변경
            import threading
            threading.Timer(1.5, self.gsm.restore_state_display).start()
            print(f"[Action] Duplicate RFID '{rfid}' ignored in state {current}")
            return
        
        # ===== 항상 TAG 발행 → 서버 검증 수행 (단일 경로) =====
        game_type = self.gsm.game_type
        print(f"[Action][TRACE] Starting server validation for RFID '{rfid}' (game_type={game_type}, state={current})")

        # 서버 검증 (publish TAG + 응답대기)
        error_result = self._validate_tag_request(rfid)
        if error_result:
            # 네트워크 에러인 경우 특별 처리
            if error_result.get('network_error'):
                error_type = ErrorType.NETWORK_ERROR
                error_message = f"서버 연결 실패\n{error_result['error_message']}\n잠시 후 다시 시도해주세요."
            else:
                error_type = error_result['type']
                error_message = error_result['message']

            # 복구 타겟은 상황에 맞게: RFID_REQUIRED 류는 WAITING 복귀가 자연스러움
            recovery_target = current
            if error_type in (getattr(ErrorType, 'RFID_REQUIRED', 'RFID_REQUIRED'),):
                recovery_target = GameState.WAITING
            self.gsm.show_error(error_type, error_message, recovery_target)
            return

        # 검증 통과 후 상태별 처리 (서버 응답 정보 활용)
        server_response = getattr(self, '_server_response', {})
        nickname = server_response.get('nickname', '')

        fallback_name = f"Player_{rfid[-4:]}"
        self.gsm.session_nickname = nickname or fallback_name
        self.gsm.session_rfid = rfid

        # 화면 상태와 무관하게, game_type으로 처리 (TAG → PlayerProgressState는 GSM가 생성)
        if game_type == 7:      # ENTER 장치
            self._handle_enter_success(rfid, nickname)
        elif game_type == 8:    # EXIT 장치
            self._handle_exit_success(rfid, nickname)
        elif game_type in (1,2,3,4,5,6):  # 게임 장치
            self._handle_waiting_success(rfid, nickname)  # COUNTDOWN 시작

        elif current == GameState.PLAYING:
            print("[Action] PLAYING -> RESULT")
            score = getattr(self._gigs.score_manager, "get_total_score", lambda: 0)()
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
                if is_master_command  and getattr(self.gsm, 'game_blocked', False):
                    self.gsm.clear_error()           

                print("[GameCmd] WAITING -> COUNTDOWN")
                self._gigs.serial_handler.send_message('-1')
                print("[GameCmd] 2 -- Sending serial message '-1' via serial_handler")
                self.gsm.start_countdown(force=is_master_command)

        elif ev.kind == EventType.GAME_STOP:
            if cs == GameState.PLAYING:
                # 일관성을 위해 score_provider 우선 사용, 없으면 기존 gigs에서 조회
                score = 0
                if getattr(self.gsm, "score_provider", None):
                    try:
                        score = int(self.gsm.score_provider())
                    except Exception as e:
                        print(f"[GameCmd] score_provider failed: {e}")
                elif hasattr(self._gigs, "score_manager"):
                    score = getattr(self._gigs.score_manager, "get_total_score", lambda: 0)()
                self.gsm.show_score(score, rfid=(self.gsm.session_rfid))
            else:
                print(f"[GameCmd] STOP ignored in {cs}")

        elif ev.kind == EventType.GAME_RESET:
            print("[GameCmd] RESET -> WAITING")
            self.gsm.show_waiting()

    def _handle_master_card(self, rfid: str, current_state: str):
        """마스터키 특권으로 모든 예외 무시"""

        print(f"[MASTER] Master card detected: {rfid}")

        # 에러 상태 자동 클리어
        if self.gsm.current_state == GameState.ERROR:
            self.gsm.recover_from_error()
            print("[MASTER] Error state cleared by master card")

        if current_state == GameState.WAITING:
            self.gsm.countdown_time = 3      # 짧은 카운트다운
            ev = GameEvent(kind=EventType.GAME_START, source=InputSource.SERIAL, raw=rfid)
            self.on_command(ev)

        # 게임 진행 중이면 강제 종료
        if current_state in [GameState.PLAYING, GameState.COUNTDOWN]:
            ev = GameEvent(kind=EventType.GAME_STOP, source=InputSource.SERIAL, raw=rfid)
            self.on_command(ev)

        print("[MASTER] Tag processed with master privileges")

        # 테스트 모드 표시
        self.gsm.screen_update_callback(f"마스터 모드\n\n(RFID: {rfid})")
        import threading
        threading.Timer(1, self.gsm.restore_state_display).start()

    def _validate_tag_request(self, rfid: str) -> dict | None:
        """WAITING 상태에서 태그 요청 검증 (서버 필수)"""
        game_type = self.gsm.sound_manager.game_type

        try:
            # 서버에 검증 요청 (필수)
            validation_result = self._request_server_validation(rfid, game_type)

            # 네트워크 에러인 경우 바로 반환
            if validation_result.get('network_error'):
                return validation_result
            
             # 서버에서 일반 오류를 명시적으로 보낸 경우 → 그대로 노출
            if validation_result.get('error') or validation_result.get('success') is False:
                return {
                    'type': getattr(ErrorType, 'SERVER_ERROR', 'SERVER_ERROR'),
                    'message': validation_result.get('message') or validation_result.get('error_message') or "서버 오류가 발생했습니다."
                }

            # 게임 타입별 검증 결과 처리
            if game_type == 7:  # 입장
                if validation_result.get('duplicate_player'):
                    return {
                        'type': ErrorType.PLAYER_DUPLICATE_ENTER,
                        'message': "이미 입장한 플레이어입니다.\n(중복 입장이 불가능합니다.)\n\n게임을 시작해주세요!"
                    }

            elif game_type in [1, 2, 3, 4, 5, 6]:  # 일반 게임
                if validation_result.get('duplicate_game'):
                    return {
                        'type': ErrorType.GAME_DUPLICATE_EXECUTION,
                        'message': "이미 게임을 실행 하셨습니다.\n\n관리자에게 문의 바랍니다.\n(각 게임 1번만 실행 가능)"
                    }
                elif validation_result.get('player_not_found'):
                    return {
                        'type': ErrorType.PLAYER_NOT_FOUND_GAME,
                        'message': "입장 처리가 필요합니다.\n먼저 입장 타워에서\n태그해주세요."
                    }

            elif game_type == 8:  # 퇴장
                if validation_result.get('player_not_found'):
                    return {
                        'type': ErrorType.PLAYER_NOT_FOUND_EXIT,
                        'message': "플레이어를 찾을 수 없습니다.\n(퇴장 완료)"
                    }

        except Exception as e:
            # 예외 발생 시 네트워크 에러로 처리
            return {
                'network_error': True,
                'error_message': f"검증 실패: {str(e)}",
                'should_block': True
            }

        return None 
    
    def _request_server_validation(self, rfid: str, game_type: int) -> dict:
        """서버 검증 요청 (기존 MQTT 구조 활용)"""
        start_time = time.time()  # 응답 시간 측정 시작

        try:
            if not self.gsm.mqtt_client or not self.gsm.mqtt_client.is_connected:
                raise Exception("MQTT 연결이 끊어져 있습니다")

            # TAG 상태 전송하고 correlationId 받아오기
            correlation_id = self.gsm.publish_rfid_detected(rfid)
            print(f"[Validation][TRACE] TAG sent with correlationId: {correlation_id} for RFID '{rfid}' game_type {game_type}")

            # correlationId가 None이면 응답을 기대하지 않음 (서버에서 응답하지 않는 경우)
            if correlation_id is None:
                print(f"[Validation][TRACE] No response expected for this message")
                return None  # 검증 통과로 처리

            # 서버 응답 대기 (3초 타임아웃)
            print(f"[Validation][TRACE] Starting wait for response with correlationId: {correlation_id}")
            response = self._wait_for_server_response(correlation_id, timeout=3.0)

            if response is None:
                # 서버 응답 타임아웃 시 에러 처리
                raise Exception("서버 응답 시간 초과 (3초)")

            # 응답 받은 후 로그 기록
            self._track_response_time(start_time)
            self._log_validation_attempt(rfid, game_type, response)

            return response

        except Exception as e:
            print(f"[Validation] Server validation failed: {e}")
            # 에러 시에도 로그 기록
            error_response = self._create_network_error(str(e))
            self._log_validation_attempt(rfid, game_type, error_response)
            return error_response
        
    def _wait_for_server_response(self, expected_correlation_id: str, timeout: float) -> dict:
        """서버 응답 대기 (/err 또는 정상 응답)"""
        # 응답 저장소 초기화
        if not hasattr(self, '_pending_responses'):
            self._pending_responses = {}

        print(f"[Validation] Waiting for response with correlationId: {expected_correlation_id}")

        # 응답 대기 (폴링 방식)
        start_time = time.time()
        check_count = 0
        while time.time() - start_time < timeout:
            check_count += 1

            # 매 10번째 체크마다 현재 상태 로그
            if check_count % 10 == 0:
                pending_ids = list(self._pending_responses.keys()) if hasattr(self, '_pending_responses') else []
                elapsed = round(time.time() - start_time, 2)
                print(f"[Validation][DEBUG] Elapsed: {elapsed}s, Pending IDs: {pending_ids}")

            if expected_correlation_id in self._pending_responses:
                response = self._pending_responses.pop(expected_correlation_id)
                elapsed = round(time.time() - start_time, 3)
                print(f"[Validation] Matched response received for {expected_correlation_id} (took {elapsed}s)")
                # 성공적으로 응답 받았으므로 old responses 정리
                self._cleanup_old_responses()
                return response
            time.sleep(0.1)  # 100ms 간격으로 체크

        # 타임아웃 발생시 상세 정보 로그
        pending_ids = list(self._pending_responses.keys()) if hasattr(self, '_pending_responses') else []
        print(f"[Validation] Response timeout for {expected_correlation_id}")
        print(f"[Validation][DEBUG] Final pending IDs: {pending_ids}")
        print(f"[Validation][DEBUG] Total checks performed: {check_count}")

        # 타임아웃된 경우 해당 correlationId 제거
        self._pending_responses.pop(expected_correlation_id, None)
        return None  # 타임아웃

    def _cleanup_old_responses(self):
        """오래된 응답들 정리 (5개 이상 쌓이면 정리)"""
        if hasattr(self, '_pending_responses') and len(self._pending_responses) > 5:
            # 가장 오래된 항목들 제거 (딕셔너리에서 임의로 일부 제거)
            keys_to_remove = list(self._pending_responses.keys())[:3]
            for key in keys_to_remove:
                self._pending_responses.pop(key, None)
            print(f"[Validation] Cleaned up {len(keys_to_remove)} old responses")
    
    def _create_network_error(self, error_message: str) -> dict:
        """네트워크 에러 응답 생성"""
        return {
            'network_error': True,
            'error_message': error_message,
            'should_block': True  # 게임 진행 차단
        }
    
    def _handle_server_response(self, response_data: dict, correlation_id: str):
        """서버 응답 처리 (mqtt_manager에서 호출)"""
        if not hasattr(self, '_pending_responses'):
            self._pending_responses = {}

        print(f"[Validation] Response stored for correlationId: {correlation_id}")
        self._pending_responses[correlation_id] = response_data

        # 성공 응답인 경우 서버 정보 저장 (nickname 등)
        if response_data.get('success'):
            self._server_response = response_data
            print(f"[Validation] Server response saved with nickname: {response_data.get('nickname', 'N/A')}")

    def _log_validation_attempt(self, rfid: str, game_type: int, result: dict):
        """검증 시도 로그 (디버깅용)"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "rfid": rfid,
            "game_type": game_type,
            "device_id": self.gsm.device_id,
            "validation_result": result,
            "server_connected": bool(self.gsm.mqtt_client and self.gsm.mqtt_client.is_connected),
            "response_time": getattr(self, '_last_response_time', 0)
        }
        print(f"[Validation Log] {log_entry}")

    def _track_response_time(self, start_time: float):
        """응답 시간 추적 (성능 모니터링용)"""
        self._last_response_time = round(time.time() - start_time, 3)
        print(f"[Performance] Server response time: {self._last_response_time}s")

    def _handle_enter_success(self, rfid: str, nickname: str = None):
        """입장 처리 성공 시 실행 (서버에서 받은 nickname 사용)"""
        self.gsm.sound_manager.play_sfx('get')
        temp_message = f"플레이어 입장\n\n안녕하세요!\n(RFID: {rfid})"
        self.gsm.screen_update_callback(temp_message)
        import threading
        threading.Timer(1.5, lambda: self.gsm.show_enter()).start()
        print(f"[Action] Player Enter (RFID '{rfid}')")

    def _handle_exit_success(self, rfid: str, recieve_data: str = None):
        """퇴장 처리 성공 시 실행 (서버에서 받은 nickname 사용)"""
        self.gsm.sound_manager.play_sfx('get')

        print(f"[Action] Player EXIT: recieve data'{recieve_data}')")
        display_name = recieve_data.get('nickname', f"Player_{rfid[-4:]}") if recieve_data else f"Player_{rfid[-4:]}"
        print(f"{display_name}")
        temp_message = f"안녕히 가세요!\n{display_name}님\n(RFID: {rfid})"
        self.gsm.screen_update_callback(temp_message)
        import threading
        threading.Timer(1.5, lambda: self.gsm.show_exit()).start()
        print(f"[Action] Player EXIT: {display_name} (RFID '{rfid}')")

    def _handle_waiting_success(self, rfid: str,  nickname: str | None = None):
        """대기 상태 처리 성공 시 실행"""
        if getattr(self.gsm, 'game_blocked', False):
            print("[Action] Game is blocked due to error - countdown cancelled")
            return
        
        def _safe_name():
            if nickname and isinstance(nickname, str) and nickname.strip():
                return nickname.strip()
            if getattr(self.gsm, "session_nickname", None):
                return self.gsm.session_nickname
            if getattr(self.gsm, "session_rfid", None):
                return f"Player_{self.gsm.session_rfid[-4:]}"
            return "플레이어"

        name = _safe_name()
        self.gsm.session_nickname = name
        self.gsm.session_rfid = rfid

        print("[Action] WAITING -> COUNTDOWN")
        self._gigs.serial_handler.send_message('-1')
        print("[Action] 2 -- Sending serial message '-1' via serial_handler")
        self.gsm.start_countdown(nickname=name)