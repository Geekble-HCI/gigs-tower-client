import paho.mqtt.client as mqtt
import json
from .local_ip_resolver import LocalIpResolver

class MQTTClient:
    def __init__(self, broker_address, port, client_id):
        self.broker_address = broker_address
        self.port = port
        self.client_id = client_id
        
        # IP 주소 기반 식별자 생성
        try:
            self.ip_address = LocalIpResolver.resolve_ip()
            if not self.ip_address:
                raise Exception("IP 주소를 가져올 수 없습니다")
        except Exception as e:
            print(f"[MQTT] IP 주소 해석 실패: {e}")
            self.ip_address = "unknown"
        
        print(f"[MQTT] Device IP: {self.ip_address}")
        
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        self.client.on_message = self._on_message  # 메시지 수신 콜백 추가
        self.message_callback = None  # 외부 콜백 함수 저장
        self.subscriptions = [] # 구독할 토픽 목록 저장
        self.is_connected = False

    # 구독할 토픽 등록 
    def add_subscription(self, topic, qos=1):
        self.subscriptions.append((topic, qos))

    def _on_connect(self, client, userdata, flags, rc):
        """MQTT 연결 시 자동 호출되는 콜백"""
        if rc == 0:
            self.is_connected = True
            print(f"[MQTT] Connected to {self.broker_address}:{self.port}")
            
            # 저장한 구독 토픽들 구독 처리
            for topic, qos in self.subscriptions:
                self.subscribe(topic, qos)
                print(f"[MQTT] Subscribed to topic: {topic} (QoS {qos})")
        else:
             print(f"[MQTT] Failed to connect: rc={rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        print(f"[MQTT] Disconnected from MQTT Broker with code {rc}")
    
    def _on_publish(self, client, userdata, mid):
        print(f"[MQTT] Publish successful: mid={mid}")

    def _on_message(self, client, userdata, msg):
        """MQTT 메시지 수신 시 내부에서 자동 호출되는 콜백"""
        try:
            topic = msg.topic
            payload_str = msg.payload.decode('utf-8')
            payload = json.loads(payload_str)
            
            # print(f"[MQTT] Received message from topic '{topic}':")
            # print(f"[MQTT] Payload: {json.dumps(payload, indent=2)}")

            # 외부 콜백이 등록되어 있으면 호출
            if self.message_callback:
                self.message_callback(topic, payload)
                
        except json.JSONDecodeError as e:
            print(f"[MQTT] JSON decode error: {e}")
            print(f"[MQTT] Raw payload: {msg.payload}")
        except Exception as e:
            print(f"[MQTT] Message processing error: {e}")

    def set_message_callback(self, callback):
        """외부에서 처리할 메세지 핸들러 등록"""
        self.message_callback = callback

    def connect(self):
        try:
            self.client.connect(self.broker_address, self.port, 60)
            self.client.loop_start() # Start a new thread to process network traffic
        except Exception as e:
            print(f"[MQTT] connection error: {e}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    def publish(self, topic, payload, qos=1, retain=True):
        if not self.is_connected:
            print("[MQTT] Publish skipped: not connected")
            return
        
        try:
            msg_info = self.client.publish(topic, json.dumps(payload), qos, retain)
            if msg_info.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[MQTT] Publish enqueued successfully: topic='{topic}', mid={msg_info.mid}")
            else:
                print(f"[MQTT] Failed to enqueue message: rc={msg_info.rc}")
        except Exception as e:
            print(f"[MQTT] Publish exception: {e}")

    def subscribe(self, topic, qos=1):
        """수동으로 토픽 구독"""
        try:
            self.client.subscribe(topic, qos)
            print(f"[MQTT] Subscribed to topic: {topic}")
        except Exception as e:
            print(f"MQTT subscribe error: {e}")

    

