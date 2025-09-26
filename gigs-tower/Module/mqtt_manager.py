from datetime import datetime, timezone
import time
from Module.game_state import GameStateManager
from Module.mqtt_scanner import MqttBrokerScanner
from .mqtt_client import MQTTClient
from .command_handler import CommandDispatcher, CommandType, GameCommand, MuteCommand, PingCommand, VolumeCommand


class MQTTManager:
    """MQTT 연결 및 명령 처리를 관리하는 클래스"""
    
    def __init__(self, mqtt_broker_ip=None, device_id=None, game_type=None, sound_manager=None, game_handler=None, action_handler=None):
        """
        MQTTManager 초기화
        Args:
            mqtt_broker_ip: MQTT 브로커 주소
            device_id: 장치 식별 ID
            sound_manager: 사운드 매니저 인스턴스 (볼륨 명령 처리용)
        """
        self.mqtt_client = None
        self.command_handler = None
        self.game_type = game_type
        self.mqtt_broker_ip = mqtt_broker_ip
        self.game_handler = game_handler
        self.action_handler = action_handler

        if self.mqtt_broker_ip == None:
            self._setup_mqtt_broker_ip()
        
        if not self.mqtt_broker_ip:
             raise RuntimeError("[BROKER] Broker discovery failed: Initial connection required, stopping.")
        
        if not device_id:
            device_id = game_type
        
        self._setup_mqtt_client(self.mqtt_broker_ip, device_id)
        self._setup_command_handler(sound_manager, game_handler)

        # 연결 완료를 블로킹으로 보장
        connected = self.mqtt_client.connect_blocking(
            max_retries=6,
            per_attempt_timeout=5.0,
            base_backoff=0.5,
            max_backoff=8.0,
        )
        if not connected:
            raise RuntimeError("[MQTT] Initial connection failed: Retry attempts exhausted")

        #  연결 직후 장치 등록 메시지 반드시 발행
        self.publish_device_register()

    def _setup_mqtt_broker_ip(self, ):
        """MQTTT 브로커 IP 주소  스캔"""
        scanner = MqttBrokerScanner(timeout=0.6, max_threads=50, preferred_ifaces=["Wi-Fi","wlan0","en0"])
        start_time = time.time()

        self.mqtt_broker_ip =scanner.scan()

        elapsed = round(time.time() - start_time, 2)
        print(f"[BROKER] Search duration: {elapsed}s")
        
        if self.mqtt_broker_ip:
            print(f"[BROKER] Connection target: {self.mqtt_broker_ip}")
        else:
            print("[BROKER] Broker discovery failed")

    def _setup_mqtt_client(self, mqtt_broker_ip, device_id):
        """MQTT 클라이언트 설정 및 연결"""
        self.mqtt_client = MQTTClient(mqtt_broker_ip, 1883, device_id)

        # 기존 구독 토픽들
        self.mqtt_client.add_subscription(f"device/{self.mqtt_client.ip_address}/command")
        self.mqtt_client.add_subscription(f"device/{self.mqtt_client.device_id}/command")
        self.mqtt_client.add_subscription("device/command/broadcast")

        # 새로운 플레이어 피드백 토픽
        self.mqtt_client.add_subscription(f"device/{self.mqtt_client.device_id}/player_feedback")

        # ack / err 메세지 수신 토픽
        self.mqtt_client.add_subscription(f"device/{self.mqtt_client.device_id}/state/ack")
        self.mqtt_client.add_subscription(f"device/{self.mqtt_client.device_id}/state/err")
        self.mqtt_client.add_subscription(f"device/{self.mqtt_client.ip_address}/state/ack")  # device_id 없을 시, 대안
        self.mqtt_client.add_subscription(f"device/{self.mqtt_client.ip_address}/state/err")  # device_id 없을 시, 대안

        # 메시지 콜백 설정
        self.mqtt_client.set_message_callback(self._handle_mqtt_message)

    
    def _setup_command_handler(self, sound_manager, game_handler):
        """MQTT 명령 핸들러 설정"""
        if self.mqtt_client and sound_manager:
            self.command_handler = CommandDispatcher()
            
            self.command_handler.register(CommandType.VOLUME, VolumeCommand(sound_manager))

            self.command_handler.register([
                CommandType.GAME_START,
                CommandType.GAME_STOP,
                CommandType.GAME_RESET
                ], GameCommand(game_handler))
            
            self.command_handler.register([
                CommandType.MUTE_ON,
                CommandType.MUTE_OFF,
                CommandType.MUTE_TOGGLE
                ], MuteCommand(sound_manager))
            
            self.command_handler.register(CommandType.PING, PingCommand(self))

    
    def publish_device_register(self):
        """연결 직후 장치 등록 메시지 강제 발행"""
        if not self.mqtt_client or not self.mqtt_client.is_connected:
            raise RuntimeError("[MQTT] Device registration failed: Not connected yet")

        game_name = GameStateManager.get_game_name(self.game_type, True)

        topic = "device/register"
        payload = {
            "device_id": self.mqtt_client.device_id,
            "ip_address": self.mqtt_client.ip_address,
            "game_type": self.game_type,
            "game_name": game_name,
            "registered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        self.mqtt_client.publish(
            topic, 
            payload, 
            qos=1, 
            retain=True, # 메세지 영속성 설정
            ttl_seconds=3600  # 메세지 만료시간 설정: 1시간
        )
        print(f"[MQTT] Device register published → {topic}: {payload}")

    def _handle_ack_message(self, payload):
        """서버로부터의 정상 응답 처리"""
        try:
            print(f"[MQTT][ACK-DEBUG] Full payload structure: {payload}")

            # payload.data에서 실제 응답 데이터 추출
            ack_data = payload.get('data', {})
            print(f"[MQTT][ACK-DEBUG] ack_data: {ack_data}")

            # 실제 데이터 구조에 맞게 nickname 추출: data.data.nickname
            data_payload = ack_data.get('data', {})
            nickname = data_payload.get('nickname', '')

            print(f"[MQTT] ACK received with nickname: {nickname}")

            # GameActionHandler에 정상 응답 전달
            if hasattr(self, 'action_handler'):
                response_data = {
                    'success': True,
                    'nickname': nickname,
                    'player_info': data_payload,
                    # 정상 응답이므로 모든 에러 플래그는 False
                    'duplicate_player': False,
                    'player_not_found': False,
                    'duplicate_game': False
                }

                # correlationId 추출 - 여러 경로에서 시도
                correlation_id = ack_data.get('correlationId', payload.get('correlationId', ''))
                print(f"[MQTT][ACK-DEBUG] Extracted correlationId: '{correlation_id}'")
                print(f"[MQTT][ACK-DEBUG] Available keys in ack_data: {list(ack_data.keys())}")
                print(f"[MQTT][ACK-DEBUG] Available keys in payload: {list(payload.keys())}")

                # GameActionHandler의 응답 핸들러 호출
                if hasattr(self.action_handler, '_handle_server_response'):
                    if correlation_id:
                        print(f"[MQTT] Calling _handle_server_response with correlationId: {correlation_id}")
                        self.action_handler._handle_server_response(response_data, correlation_id)
                    else:
                        print(f"[MQTT] ERROR: Missing correlationId in ACK response")
                else:
                    print(f"[MQTT] ERROR: game_handler._handle_server_response not available")

        except Exception as e:
            print(f"[MQTT] ACK message handling failed: {e}")

    def _handle_mqtt_message(self, topic, payload):
        """MQTT 메시지 통합 처리 (수정)"""
        try:
            if "command" in topic:
                self._handle_mqtt_command(topic, payload)
            elif topic.endswith("/ack"):
                print(f"[MQTT][ACK] {payload}")
                self._handle_ack_message(payload)  # ACK 메시지도 처리
            elif topic.endswith("/err"):
                print(f"[MQTT][ERR] {payload.get('message', 'Unknown error')}")
                self._handle_error_message(payload)
            else:
                print(f"[MQTT] Unknown topic: {topic}, payload={payload}")
        except Exception as e:
            print(f"[MQTT] Message processing error: {e}")

    def _handle_mqtt_command(self, topic, payload):
        """장치 명령 메시지 처리"""
        try:
            if not self.command_handler:
                print("[MQTT] No command handler available")
                return
            data = payload.get("data") or {}
            command = data.get("command")
            value = data.get("value")
            ts = data.get("timestamp")
            device_id = data.get("deviceId")

            print(f"[MQTT] args: {command}, {value}, {ts}, {device_id}")

            success = self.command_handler.dispatch(command, value, ts, device_id)
            if not success:
                print(f"[MQTT] Command processing failed for topic: {topic}")
        except Exception as e:
            print(f"[MQTT] Error in command handling: {e}")
    
    def is_connected(self):
        """MQTT 연결 상태 확인"""
        return bool(self.mqtt_client and self.mqtt_client.is_connected)

    def get_client(self):
        """MQTT 클라이언트 인스턴스 반환 (GameStateManager에서 사용)"""
        return self.mqtt_client
    
    def set_game_state_manager(self, game_state_manager):
        """GameStateManager 참조 설정"""
        self.game_state_manager = game_state_manager

    def _handle_mqtt_command(self, topic, payload):
        """장치 명령 메시지 처리"""
        try:
            if not self.command_handler:
                print("[MQTT] No command handler available")
                return
            data = payload.get("data") or {}
            command = data.get("command")
            value = data.get("value")
            ts = data.get("timestamp")
            device_id = data.get("deviceId")

            print(f"[MQTT] args: {command}, {value}, {ts}, {device_id}")

            success = self.command_handler.dispatch(command, value, ts, device_id)
            if not success:
                print(f"[MQTT] Command processing failed for topic: {topic}")
        except Exception as e:
            print(f"[MQTT] Error in command handling: {e}")
    

    def _handle_error_message(self, payload):
        try:
            error_data = payload.get('data', {})
            error_code = error_data.get('code')
            error_message = error_data.get('message', 'Unknown error')
            print(f"[MQTT] Error received: {error_code} - {error_message}")

            if hasattr(self, 'action_handler'):
                response_data = {
                    'success': False,
                    'code': error_code,
                    'message': error_message,
                    'duplicate_player': error_code in ['PLAYER_DUPLICATE_ENTER','PLAYERGAME_DUPLICATE'],
                    'player_not_found': error_code in ['PLAYER_NOT_FOUND_GAME','PLAYER_NOT_FOUND_EXIT'],
                    'duplicate_game': error_code == 'GAME_DUPLICATE_EXECUTION',
                }
                correlation_id = error_data.get('correlationId', payload.get('correlationId', ''))
                if hasattr(self.action_handler, '_handle_server_response') and correlation_id:
                    print(f"[MQTT] Calling _handle_server_response for ERROR with correlationId: {correlation_id}")
                    self.action_handler._handle_server_response(response_data, correlation_id)

        except Exception as e:
            print(f"[MQTT] Error message handling failed: {e}")

    def disconnect(self):
        """MQTT 연결 해제"""
        if self.mqtt_client:
            self.mqtt_client.disconnect()
