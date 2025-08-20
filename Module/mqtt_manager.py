from datetime import datetime, timezone
import time
from Module.game_state import GameStateManager
from Module.mqtt_scanner import MqttBrokerScanner
from .mqtt_client import MQTTClient
from .command_handler import CommandDispatcher, CommandType, VolumeCommand


class MQTTManager:
    """MQTT 연결 및 명령 처리를 관리하는 클래스"""
    
    def __init__(self, mqtt_broker_ip=None, device_id=None, game_type=None, sound_manager=None):
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
        self._setup_command_handler(sound_manager)

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
        self._publish_device_register()

    def _setup_mqtt_broker_ip(self, ):
        """MQTTT 브로커 IP 주소  스캔"""
        scanner = MqttBrokerScanner(timeout=0.3, max_threads=50)
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
        
        # IP 주소 기반 토픽 구독 설정
        self.mqtt_client.add_subscription(f"device/{self.mqtt_client.ip_address}/state")
        self.mqtt_client.add_subscription(f"device/{self.mqtt_client.ip_address}/command")
    
        # self.mqtt_client.add_subscription(f"device/{self.mqtt_client.device_id}/ping")
        # self.mqtt_client.add_subscription("broadcast/#")
        
        # 메시지 콜백 설정
        self.mqtt_client.set_message_callback(self._handle_mqtt_command)
    
    def _setup_command_handler(self, sound_manager):
        """MQTT 명령 핸들러 설정"""
        if self.mqtt_client and sound_manager:
            self.command_handler = CommandDispatcher()
            self.command_handler.register(CommandType.VOLUME, VolumeCommand(sound_manager))
    
    def _publish_device_register(self):
        """연결 직후 장치 등록 메시지 강제 발행"""
        if not self.mqtt_client or not self.mqtt_client.is_connected:
            raise RuntimeError("[MQTT] Device registration failed: Not connected yet")

        game_name = GameStateManager.GAME_MESSAGES.get(self.game_type, "칼로링머신")

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
    
    def add_command_handler(self, command_type, handler):
        """새로운 명령 핸들러 추가
        
        Args:
            command_type: 명령 타입
            handler: 핸들러 인스턴스
        """
        if self.command_handler:
            self.command_handler.register(command_type, handler)
    
    def disconnect(self):
        """MQTT 연결 해제"""
        if self.mqtt_client:
            self.mqtt_client.disconnect()