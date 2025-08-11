import threading
import time
import paho.mqtt.client as mqtt
import json
from .local_ip_resolver import LocalIpResolver

class MQTTClient:
    """초기 연결을 보장하고, 연결 이후에만 publish되도록 하는 래퍼"""

    def __init__(self, broker_address, port, client_id):
        self.broker_address = broker_address
        self.port = port
        self.client_id = client_id
        
        try:
            self.ip_address = LocalIpResolver.resolve_ip()
            if not self.ip_address:
                raise RuntimeError("IP 주소를 가져올 수 없습니다")
        except Exception as e:
            print(f"[MQTT] IP 주소 해석 실패: {e}")
            self.ip_address = "unknown"
        
        print(f"[MQTT] Device IP: {self.ip_address}")
        
        self.client = mqtt.Client(client_id=self.client_id)

        # 콜백
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        self.client.on_message = self._on_message  # 메시지 수신 콜백 추가

        # 상태/구성
        self.message_callback = None  # 외부 콜백 함수 저장
        self.subscriptions = [] # 구독할 토픽 목록 저장
        self.is_connected = False

        # 초기 연결 동기화용
        self._conn_event = threading.Event()
        self._loop_started = False

     # -------- 외부 API --------
    def add_subscription(self, topic, qos=1):
        """구독 처리할 토픽들 등록"""
        self.subscriptions.append((topic, qos))

    def set_message_callback(self, callback):
        """외부에서 처리할 메세지 핸들러 등록"""
        self.message_callback = callback

    def connect_blocking(
        self,
        max_retries: int = 6,
        per_attempt_timeout: float = 5.0,
        base_backoff: float = 0.5,
        max_backoff: float = 8.0,
        keepalive: int = 60,
    ) -> bool:
        """CONNACK을 받을 때까지(또는 재시도 소진) 블로킹으로 연결 시도"""
        if not self._loop_started:
            try:
                self.client.loop_start()
                self._loop_started = True
            except Exception as e:
                print(f"[MQTT] loop_start 예외: {e}")

        attempt = 0
        while True:
            try:
                print(f"[MQTT] connect 시도 #{attempt+1} → {self.broker_address}:{self.port}")
                self._conn_event.clear()
                self.client.connect(self.broker_address, self.port, keepalive)
            except Exception as e:
                print(f"[MQTT] 소켓 연결 예외: {e}")

            if self._conn_event.wait(timeout=per_attempt_timeout) and self.is_connected:
                print("[MQTT] 초기 연결 완료")
                return True

            if attempt >= max_retries:
                print("[MQTT] 초기 연결 실패: 재시도 한도 초과")
                return False

            delay = min(max_backoff, base_backoff * (2 ** attempt))
            print(f"[MQTT] 재시도 대기 {delay:.1f}s")
            time.sleep(delay)
            attempt += 1

    # def connect(self):
    #     try:
    #         self.client.connect(self.broker_address, self.port, 60)
    #         self.client.loop_start() # Start a new thread to process network traffic
    #     except Exception as e:
    #         print(f"[MQTT] connection error: {e}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    def publish(self, topic, payload, qos=1, retain=True):
        """연결된 상태에서만 실제 발행"""
        if not self.is_connected:
            print("[MQTT] Publish skipped: not connected")
            return
        try:
            msg_info = self.client.publish(topic, json.dumps(payload), qos=qos, retain=retain)
            if hasattr(msg_info, "rc"):
                if msg_info.rc == mqtt.MQTT_ERR_SUCCESS:
                    print(f"[MQTT] Publish enqueued: topic='{topic}', mid={getattr(info, 'mid', None)}")
                else:
                    print(f"[MQTT] Publish rc={msg_info.rc}")
        except Exception as e:
            print(f"[MQTT] Publish exception: {e}")

    def subscribe(self, topic, qos=1):
        """수동으로 토픽 구독"""
        try:
            self.client.subscribe(topic, qos)
            print(f"[MQTT] Subscribed to topic: {topic}")
        except Exception as e:
            print(f"MQTT subscribe error: {e}")

    # -------- 내부 콜백 --------
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT 연결 시 자동 호출되는 콜백"""
        if rc == 0:
            self.is_connected = True
            print(f"[MQTT] Connected to {self.broker_address}:{self.port}")
            
            # 저장한 구독 토픽들 구독 처리
            for topic, qos in self.subscriptions:
                self.subscribe(topic, qos)
            self._conn_event.set()
        else:
             print(f"[MQTT] Failed to connect: rc={rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        self.is_connected = False
        print(f"[MQTT] Disconnected from MQTT Broker with code {rc}")
    
    def _on_publish(self, client, userdata, mid):
        print(f"[MQTT] Publish successful: mid={mid}")

    def _on_message(self, client, userdata, msg):
        """MQTT 메시지 수신 시 내부에서 자동 호출되는 콜백"""
        try:
            payload_str = msg.payload.decode('utf-8')
            payload = json.loads(payload_str)
            if self.message_callback:
                self.message_callback(msg.topic, payload)
        except json.JSONDecodeError as e:
            print(f"[MQTT] JSON decode error: {e}")
            print(f"[MQTT] Raw payload: {msg.payload}")
        except Exception as e:
            print(f"[MQTT] Message processing error: {e}")
