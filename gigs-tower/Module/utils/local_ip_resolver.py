import subprocess
import re
import platform

from .net_utils import (
    list_ipv4_by_iface,
    udp_guess_local_ip,
    is_private_ipv4,
)



class LocalIpResolver:
    @staticmethod
    def resolve_ip(preferred_ifaces=None) -> str:
        """
        무선 NIC(사설 IPv4)를 **우선** 반환.
        - preferred_ifaces: ["Wi-Fi","wlan0","en0"] 등 인터페이스 힌트.
        - 1순위: 무선 NIC들(정렬된 리스트의 첫번째)
        - 2순위: UDP 더미 연결 기반 라우팅 IP
        - 3순위: 127.0.0.1
        """
        lst = list_ipv4_by_iface(preferred_ifaces)
        if lst:
            # 무선 우선 정렬되어 있으므로 첫 항목의 ip 반환
            _, ip, _ = lst[0]
            return ip

        ip = udp_guess_local_ip()
        if ip and (is_private_ipv4(ip) or ip not in ("127.0.0.1", "0.0.0.0")):
            return ip

        return "127.0.0.1"