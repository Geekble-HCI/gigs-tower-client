from .mqtt_client import MQTTClient
from .command_handler import CommandDispatcher, CommandType, VolumeCommand


class MQTTManager:
    """MQTT 연결 및 명령 처리를 관리하는 클래스"""
    
    def __init__(self, mqtt_broker=None, mqtt_client_id=None, sound_manager=None):
        """
        MQTTManager 초기화
        
        Args:
            mqtt_broker: MQTT 브로커 주소
            mqtt_client_id: MQTT 클라이언트 ID
            sound_manager: 사운드 매니저 인스턴스 (볼륨 명령 처리용)
        """
        self.mqtt_client = None
        self.command_handler = None
        
        if mqtt_broker:
            self._setup_mqtt_client(mqtt_broker, mqtt_client_id)
            self._setup_command_handler(sound_manager)
    
    def _setup_mqtt_client(self, mqtt_broker, mqtt_client_id):
        """MQTT 클라이언트 설정 및 연결"""
        # MQTT 브로커 topic 및 연결 설정
        self.mqtt_client = MQTTClient(mqtt_broker, 1883, mqtt_client_id)
        
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
        
        # 연결 시작
        self.mqtt_client.connect()
    
    def _setup_command_handler(self, sound_manager):
        """MQTT 명령 핸들러 설정"""
        if self.mqtt_client and sound_manager:
            self.command_handler = CommandDispatcher()
            self.command_handler.register(CommandType.VOLUME, VolumeCommand(sound_manager))
    
    def _handle_mqtt_command(self, topic, payload):
        """
        MQTT 명령 메시지 처리
        
        Args:
            topic: MQTT 토픽
            payload: 메시지 페이로드
        """
        try:
            if self.command_handler:
                command = payload['data']['command']
                value = payload['data']['value']
                time = payload['data']['timestamp']
                deviceId = payload['data']['deviceId']

                print(f"[MQTT] args: {command}, {value}, {time}, {deviceId}")

                success = self.command_handler.dispatch(command, value, time, deviceId)
                if not success:
                    print(f"[MQTT] Command processing failed for topic: {topic}")
            else:
                print("[MQTT] No command handler available")
        except Exception as e:
            print(f"[MQTT] Error in command handling: {e}")
    
    def is_connected(self):
        """MQTT 연결 상태 확인"""
        return self.mqtt_client is not None
    
    def get_client(self):
        """MQTT 클라이언트 인스턴스 반환 (GameStateManager에서 사용)"""
        return self.mqtt_client
    
    def add_command_handler(self, command_type, handler):
        """
        새로운 명령 핸들러 추가
        
        Args:
            command_type: 명령 타입
            handler: 핸들러 인스턴스
        """
        if self.command_handler:
            self.command_handler.register(command_type, handler)
    
    def disconnect(self):
        """MQTT 연결 해제"""
        if self.mqtt_client:
            # 연결 해제 로직 (MQTTClient에 disconnect 메서드가 있다면)
            # self.mqtt_client.disconnect()
            pass
