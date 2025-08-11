from datetime import datetime, timezone
import time
from Module.mqtt_scanner import MqttBrokerScanner
from .mqtt_client import MQTTClient
from .command_handler import CommandDispatcher, CommandType, VolumeCommand


class MQTTManager:
    """MQTT 연결 및 명령 처리를 관리하는 클래스"""
    
    def __init__(self, mqtt_broker_ip=None, mqtt_client_id=None, sound_manager=None):
        """
        MQTTManager 초기화
        Args:
            mqtt_broker_ip: MQTT 브로커 주소
            mqtt_client_id: MQTT 클라이언트 ID
            sound_manager: 사운드 매니저 인스턴스 (볼륨 명령 처리용)
        """
        self.mqtt_client = None
        self.command_handler = None
        self.mqtt_broker_ip = mqtt_broker_ip

        if self.mqtt_broker_ip == None:
            self._setup_mqtt_broker_ip()
        
        if not self.mqtt_broker_ip:
             raise RuntimeError("[BROKER] 브로커 탐색 실패: 초기 연결이 필수이므로 중단합니다.")
        
        self._setup_mqtt_client(self.mqtt_broker_ip, mqtt_client_id)
        self._setup_command_handler(sound_manager)

        # 연결 완료를 블로킹으로 보장
        connected = self.mqtt_client.connect_blocking(
            max_retries=6,
            per_attempt_timeout=5.0,
            base_backoff=0.5,
            max_backoff=8.0,
        )
        if not connected:
            raise RuntimeError("[MQTT] 초기 연결 실패: 재시도 소진")

        #  연결 직후 장치 등록 메시지 반드시 발행
        self._publish_device_register()

    def _setup_mqtt_broker_ip(self, ):
        """MQTTT 브로커 IP 주소  스캔"""
        scanner = MqttBrokerScanner(timeout=0.3, max_threads=50)
        start_time = time.time()

        self.mqtt_broker_ip =scanner.scan()

        elapsed = round(time.time() - start_time, 2)
        print(f"[BROKER] 검색 소요 시간: {elapsed}초")
        
        if self.mqtt_broker_ip:
            print(f"[BROKER] 연결 시도 대상: {self.mqtt_broker_ip}")
        else:
            print("[BROKER] 브로커 탐색 실패")

    def _setup_mqtt_client(self, mqtt_broker_ip, mqtt_client_id):
        """MQTT 클라이언트 설정 및 연결"""
        self.mqtt_client = MQTTClient(mqtt_broker_ip, 1883, mqtt_client_id)
        
        # IP 주소 기반 토픽 구독 설정
        self.mqtt_client.add_subscription(f"device/{self.mqtt_client.ip_address}/state")
        self.mqtt_client.add_subscription(f"device/{self.mqtt_client.ip_address}/command")
        
        # 글로벌 토픽도 유지 (관리용) - 현재는 주석 처리
        # self.mqtt_client.add_subscription("device/+/state")
        # self.mqtt_client.add_subscription("device/+/command")
        # self.mqtt_client.add_subscription(f"device/{self.mqtt_client.client_id}/ping")
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
            raise RuntimeError("[MQTT] 장치등록 실패: 아직 연결되지 않음")

        # if self.mqtt_client.ip_address in (None, "", "unknown"):
            # print("[MQTT] 경고: IP 주소가 unknown 상태지만 등록을 시도합니다.")

        topic = "device/register"
        payload = {
            "client_id": self.mqtt_client.client_id,
            "ip_address": self.mqtt_client.ip_address,
            "registered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        self.mqtt_client.publish(topic, payload, qos=1, retain=True)
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