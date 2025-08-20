import threading
import time
import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes
import json
from .local_ip_resolver import LocalIpResolver

class MQTTClient:
    """초기 연결을 보장하고, 연결 이후에만 publish되도록 하는 래퍼"""

    def __init__(self, broker_address, port, device_id):
        self.broker_address = broker_address
        self.port = port
        self.device_id = device_id
        
        try:
            self.ip_address = LocalIpResolver.resolve_ip()
            if not self.ip_address:
                raise RuntimeError("Unable to get IP address")
        except Exception as e:
            print(f"[MQTT] IP address resolution failed: {e}")
            self.ip_address = "unknown"
        
        print(f"[MQTT] Device IP: {self.ip_address}")
        
        self.client = mqtt.Client(
            client_id=self.device_id,
            protocol=mqtt.MQTTv5    
        )

        # 콜백
        self.client.on_connect = self._on_connect_v5
        self.client.on_disconnect = self._on_disconnect_v5
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
                print(f"[MQTT] loop_start exception: {e}")

        attempt = 0
        while True:
            try:
                print(f"[MQTT] connect attempt #{attempt+1} → {self.broker_address}:{self.port}")
                self._conn_event.clear()
                self.client.connect(self.broker_address, self.port, keepalive)
            except Exception as e:
                print(f"[MQTT] socket connection exception: {e}")

            if self._conn_event.wait(timeout=per_attempt_timeout) and self.is_connected:
                print("[MQTT] Initial connection established")
                return True

            if attempt >= max_retries:
                print("[MQTT] Initial connection failed: Retry limit exceeded")
                return False

            delay = min(max_backoff, base_backoff * (2 ** attempt))
            print(f"[MQTT] Waiting for retry {delay:.1f}s")
            time.sleep(delay)
            attempt += 1

    def disconnect(self):
        """정상 종료(남은 네트워크 작업 정리 후 쓰레드 종료)"""
        self.client.loop_stop()
        self.client.disconnect()

    def publish(self, topic, payload, qos=1, retain=False, ttl_seconds: int | None = None):
        """
        연결된 상태에서만 발행 가능
         - ttl_seconds: 보관 메시지 자동 만료 설정 (MQTT v5 Message Expiry Interval)
         - 한글 깨짐 방지: ensure_ascii=False + UTF-8 인코딩
        """
        if not self.is_connected:
            print("[MQTT] Publish skipped: not connected")
            return
        
        properties = None
        if ttl_seconds is not None:
            properties = Properties(PacketTypes.PUBLISH)
            properties.MessageExpiryInterval = int(ttl_seconds)
            properties.PayloadFormatIndicator = 1
            properties.ContentType = "application/json; charset=utf-8"
        
        try:
            if isinstance(payload, (dict, list)):
                data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            elif isinstance(payload, str):
                data = payload.encode("utf-8")
            elif isinstance(payload, (bytes, bytearray)):
                data = payload
            else:
                data = json.dumps(payload, ensure_ascii=False).encode("utf-8")


            msg_info = self.client.publish(
                topic, 
                data,
                qos=qos, 
                retain=retain,
                properties=properties
            )
            if hasattr(msg_info, "rc"):
                if msg_info.rc == mqtt.MQTT_ERR_SUCCESS:
                    printable = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
                    print(f"[MQTT] Publish enqueued → topic='{topic}', payload={printable}, mid={getattr(msg_info, 'mid', None)}")
                else:
                     print(f"[MQTT] Publish rc={msg_info.rc} (topic='{topic}')")
        except Exception as e:
            print(f"[MQTT] Publish exception: {e}")

    def subscribe(self, topic, qos=1):
        """수동으로 토픽 구독"""
        try:
            self.client.subscribe(topic, qos)
            print(f"[MQTT] Subscribed to topic: {topic} (qos={qos})")
        except Exception as e:
            print(f"MQTT subscribe error: {e}")

    # -------- 내부 콜백 --------
    def _on_connect_v5(self, client, userdata, flags, reason_code, properties):
        """연결 성공/실패 콜백 (MQTT v5)"""
        if reason_code == mqtt.MQTT_ERR_SUCCESS or int(reason_code) == 0:
            self.is_connected = True
            print(f"[MQTT] Connected to {self.broker_address}:{self.port} (reason_code={reason_code})")
        
            for topic, qos in self.subscriptions:
                self.subscribe(topic, qos)
            self._conn_event.set()
        else:
            print(f"[MQTT] Failed to connect: reason_code={reason_code}")
            # 연결 실패 시에도 wait()가 깨어날 수 있게 이벤트 set (재시도 루프로)
            self._conn_event.set()

    def _on_disconnect_v5(self, client, userdata, reason_code, properties):
        self.is_connected = False
        print(f"[MQTT] Disconnected (reason_code={reason_code})")
    
    def _on_publish(self, client, userdata, mid):
        print(f"[MQTT] Publish successful: mid={mid}")

    def _on_message(self, client, userdata, msg):
        """MQTT 메시지 수신 시 내부에서 자동 호출되는 콜백"""
        try:
            payload_str = msg.payload.decode('utf-8')
            payload = json.loads(payload_str)
            if self.message_callback:
                self.message_callback(msg.topic, payload)
            print(f"[DEBUG] Receive message: {payload}")
        except json.JSONDecodeError as e:
            print(f"[MQTT] JSON decode error: {e}")
            print(f"[MQTT] Raw payload: {msg.payload}")
        except Exception as e:
            print(f"[MQTT] Message processing error: {e}")
