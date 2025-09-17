import os
import time
import paho.mqtt.client as mqtt
from concurrent.futures import ThreadPoolExecutor, as_completed

from .net_utils import (
    list_candidate_bases,
    is_private_ipv4,
    udp_guess_local_ip,
)

class MqttBrokerScanner:
    """
    - Wi-Fi 대역을 '먼저' 스캔 (preferred_ifaces 연동)
    - 각 후보 IP는 paho-mqtt CONNECT→CONNACK 성공 시에만 '브로커'로 인정
    - TLS/계정 인증 옵션을 스캐너에도 동일하게 적용 가능
    """
    def __init__(
        self,
        port=1883,
        timeout=0.6,
        max_threads=50,
        preferred_ifaces=None,
        cache_file: str = "last_broker_ip.txt",

        # TLS/계정 인증(필요 시)
        ca_certs=None, certfile=None, keyfile=None, tls_insecure=False,
        username=None, password=None,
    ):
        self.port = port
        self.timeout = timeout
        self.max_threads = max_threads
        self.cache_file = cache_file

         # 후보 서브넷: Wi-Fi 우선
        self.candidates = list_candidate_bases(preferred_ifaces=preferred_ifaces)
        if not self.candidates:
            # NIC 탐색 실패 시, 라우팅 기반 IP → /24 추정 or 흔한 대역
            ip = udp_guess_local_ip()
            if ip and is_private_ipv4(ip):
                self.candidates = [".".join(ip.split(".")[:3]) + "."]
            else:
                self.candidates = ["192.168.0.", "192.168.1.", "10.0.0.", "172.16.0."]

        print(f"[SCANNER] candidates={self.candidates}")

        # 보안/인증 옵션
        self.ca_certs = ca_certs
        self.certfile = certfile
        self.keyfile = keyfile
        self.tls_insecure = tls_insecure
        self.username = username
        self.password = password


    # MQTT 브로커 판별
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

        # protocol은 보수적으로 v3.1.1(=MQTTv311) 지정
        client = mqtt.Client(client_id="scan-" + os.urandom(3).hex(), protocol=mqtt.MQTTv311)
        client.on_connect = _on_connect

        # 인증/암호화가 필요한 브로커라면 동일 옵션으로 시도해야 CONNACK 도달
        if self.username:
            client.username_pw_set(self.username, self.password)
        if self.ca_certs:
            client.tls_set(ca_certs=self.ca_certs, certfile=self.certfile, keyfile=self.keyfile)
            client.tls_insecure_set(self.tls_insecure)
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
            try: client.loop_stop()
            except Exception: pass
            try: client.disconnect()
            except Exception: pass

        return ip if result["ok"] else None

    def _load_cached_ip(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception:
                return None

    def _save_cached_ip(self, ip):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                f.write(ip)
        except Exception:
            pass

    def scan(self, start=1, end=254):

        # 1) 캐시된 ip 재검증
        cached_ip = self._load_cached_ip()
        if cached_ip and self._is_broker_alive(cached_ip):
            print(f"[SCANNER] Using cached broker: {cached_ip}:{self.port}")
            return cached_ip

        # 2) Wi-Fi 우선 서브넷부터 순차 스캔
        for base in self.candidates:
            print(f"[SCANNER] Scan range: {base}{start} ~ {base}{end}")

            # (빠른 히트) 게이트웨이 .1 먼저 테스트
            gw = f"{base}1"
            res = self._is_broker_alive(gw)
            if res:
                print(f"[SCANNER] Broker at gateway: {res}:{self.port}")
                self._save_cached_ip(res)
                return res

            # 나머지 병렬 스캔
            ip_list = [f"{base}{i}" for i in range(start, end + 1)]
            with ThreadPoolExecutor(max_workers=self.max_threads) as ex:
                futs = {ex.submit(self._is_broker_alive, ip): ip for ip in ip_list}
                for fut in as_completed(futs):
                    res = fut.result()
                    if res:
                        print(f"[SCANNER] Broker found: {res}:{self.port}")
                        self._save_cached_ip(res)
                        return res

        print("[SCANNER] No broker found.")
        return None
   