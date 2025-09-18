from datetime import datetime, timezone
import time
from Module.game_state import GameStateManager
from Module.mqtt_scanner import MqttBrokerScanner
from .mqtt_client import MQTTClient
from .command_handler import CommandDispatcher, CommandType, GameCommand, MuteCommand, PingCommand, VolumeCommand


class MQTTManager:
    """MQTT 연결 및 명령 처리를 관리하는 클래스"""
    
    def __init__(self, mqtt_broker_ip=None, device_id=None, game_type=None, sound_manager=None, game_handler=None):
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

        # 새로운 플레이어 피드백 토픽 추가
        self.mqtt_client.add_subscription(f"device/{self.mqtt_client.device_id}/player_feedback")

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
            
            # Ping은 MQTTClient 인스턴스를 직접 주입해야 publish 가능
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

    def _handle_mqtt_message(self, topic, payload):
        """MQTT 메시지 통합 처리"""
        try:
            if "player_feedback" in topic:
                # 플레이어 피드백 메시지 처리
                self._handle_player_feedback(payload)
            elif "command" in topic:
                # 기존 명령 메시지 처리
                self._handle_mqtt_command(topic, payload)
            else:
                print(f"[MQTT] Unknown topic: {topic}")
        except Exception as e:
            print(f"[MQTT] Message processing error: {e}")

    def _handle_player_feedback(self, payload):
        """서버로부터의 플레이어 피드백 처리"""
        try:
            # GameStateManager에 피드백 전달
            if hasattr(self, 'game_state_manager'):
                self.game_state_manager.handle_player_feedback(payload)
            print(f"[MQTT] Player feedback processed: {payload.get('nickname', 'Unknown')}")
        except Exception as e:
            print(f"[MQTT] Player feedback error: {e}")

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

    def disconnect(self):
        """MQTT 연결 해제"""
        if self.mqtt_client:
            self.mqtt_client.disconnect()
