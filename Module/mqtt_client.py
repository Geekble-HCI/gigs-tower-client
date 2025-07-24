import paho.mqtt.client as mqtt
import json

class MQTTClient:
    def __init__(self, broker_address, port, client_id):
        self.broker_address = broker_address
        self.port = port
        self.client_id = client_id
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected to MQTT Broker: {self.broker_address}")
        else:
            print(f"Failed to connect, return code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        print(f"Disconnected from MQTT Broker with code {rc}")

    def connect(self):
        try:
            self.client.connect(self.broker_address, self.port, 60)
            self.client.loop_start() # Start a new thread to process network traffic
        except Exception as e:
            print(f"MQTT connection error: {e}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    def publish(self, topic, payload, qos=1, retain=True):
        try:
            self.client.publish(topic, json.dumps(payload), qos, retain)
            print(f"Published to topic '{topic}': {payload}")
        except Exception as e:
            print(f"MQTT publish error: {e}")
