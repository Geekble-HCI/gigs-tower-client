import paho.mqtt.client as mqtt
import socket
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from .local_ip_resolver import LocalIpResolver

class MqttBrokerScanner:
    def __init__(self, port=1883, timeout=0.3, max_threads=50):
        self.port = port
        self.timeout = timeout
        self.max_threads = max_threads
        self.local_ip = LocalIpResolver.resolve_ip()
        self.base_ip = ".".join(self.local_ip.split(".")[:3]) + "."
        self.cache_file = "last_broker_ip.txt"
        print(f"[SCANNER] local_ip={self.local_ip}, base_ip={self.base_ip}")

    def _is_broker_alive(self, ip):
        """
        paho-mqtt로 실제 Connect를 시도해 CONNACK 수신 시 브로커로 인정.
        성공하면 ip 반환, 실패하면 None.
        """
        result = {"ok": False}
        
        def _on_connect(client, userdata, flags, rc, properties=None):
            # rc == 0 이면 연결 성공 (MQTT v3.1.1 기준)
            if rc == 0:
                result["ok"] = True
            # 스캔 용도이므로 바로 끊어 응답만 받고 종료
            try:
                client.disconnect()
            except Exception:
                pass

        client_id = "scan-" + os.urandom(3).hex()     # 짧은 임시 clientId

        # protocol은 보수적으로 v3.1.1(=MQTTv311) 지정
        client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
        client.on_connect = _on_connect

        try:
            # 비동기 연결 + 네트워크 루프 가동
            client.connect_async(ip, self.port, keepalive=10)
            client.loop_start()

            # timeout 내에서 on_connect가 불릴 때까지 기다림
            t0 = time.time()
            while time.time() - t0 < self.timeout:
                if result["ok"]:
                    break
                time.sleep(0.01)

        except Exception:
            result["ok"] = False
        finally:
            # 루프 정리
            try:
                client.loop_stop()
            except Exception:
                pass
            try:
                client.disconnect()
            except Exception:
                pass

        return ip if result["ok"] else None


    def _load_cached_ip(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                return f.read().strip()
        return None

    def _save_cached_ip(self, ip):
        with open(self.cache_file, 'w') as f:
            f.write(ip)

    def scan(self, start=1, end=254):
        print(f"[SCANNER] Scan range: {self.base_ip}{start} ~ {self.base_ip}{end}")

        # [1단계] 캐시된 IP 우선 테스트
        cached_ip = self._load_cached_ip()
        if cached_ip and self._is_broker_alive(cached_ip):
            print(f"[SCANNER] Using cached broker: {cached_ip}:{self.port}")
            return cached_ip

        # [2단계] 병렬 스캔
        ip_list = [f"{self.base_ip}{i}" for i in range(start, end + 1)]

        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            future_to_ip = {executor.submit(self._is_broker_alive, ip): ip for ip in ip_list}

            for future in as_completed(future_to_ip):
                result = future.result()
                if result:
                    print(f"\n[SCANNER] Broker found: {result}:{self.port}")
                    self._save_cached_ip(result)
                    return result

        print("\n[SCANNER] No broker found.")
        return None
   