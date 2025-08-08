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


    def _is_broker_alive(self, ip):
        try:
            sock = socket.create_connection((ip, self.port), timeout=self.timeout)
            sock.close()
            return ip
        except:
            return None

    def _load_cached_ip(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                return f.read().strip()
        return None

    def _save_cached_ip(self, ip):
        with open(self.cache_file, 'w') as f:
            f.write(ip)

    def scan(self, start=1, end=254):
        print(f"[SCANNER] 스캔 범위: {self.base_ip}{start} ~ {self.base_ip}{end}")

        # [1단계] 캐시된 IP 우선 테스트
        cached_ip = self._load_cached_ip()
        if cached_ip and self._is_broker_alive(cached_ip):
            print(f"[SCANNER] 캐시된 브로커 사용: {cached_ip}:{self.port}")
            return cached_ip

        # [2단계] 병렬 스캔
        ip_list = [f"{self.base_ip}{i}" for i in range(start, end + 1)]

        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            future_to_ip = {executor.submit(self._is_broker_alive, ip): ip for ip in ip_list}

            for future in as_completed(future_to_ip):
                result = future.result()
                if result:
                    print(f"\n[SCANNER] 브로커 발견: {result}:{self.port}")
                    self._save_cached_ip(result)
                    return result

        print("\n[SCANNER] 브로커를 찾지 못했습니다.")
        return None
   