# -*- coding: utf-8 -*-
import os
import socket
import ipaddress
import platform
import subprocess
import re

try:
    import psutil  # optional
except ImportError:
    psutil = None

WIFI_HINTS = ["wi-fi", "wifi", "wlan", "wireless", "무선"]
EXCLUDE_HINTS = [
    "docker", "vmnet", "bridge", "vbox", "hyper-v", "vethernet",
    "bluetooth", "tailscale", "ham", "loopback", "llw", "awdl", "utun", "tap", "tun"
]

def windows_wifi_ifnames():
    """Windows에서 활성 무선 인터페이스 이름(예: 'Wi-Fi')을 netsh로 추출."""
    if platform.system() != "Windows":
        return []
    try:
        out = subprocess.check_output(
            ["netsh", "wlan", "show", "interfaces"],
            shell=False, text=True, encoding="utf-8", errors="ignore"
        )
    except Exception:
        return []
    names = []
    for line in out.splitlines():
        m = re.search(r"(?:^|\s)(?:Name|이름|인터페이스\s*이름)\s*:\s*(.+)$",
                      line.strip(), flags=re.I)
        if m:
            names.append(m.group(1).strip())
    return [n for n in names if n]

def is_private_ipv4(ip: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
        return (ip_obj.version == 4
                and ip_obj.is_private
                and not ip_obj.is_loopback
                and not ip_obj.is_link_local)
    except Exception:
        return False

def list_ipv4_by_iface(preferred_ifaces=None):
    """
    활성 사설 IPv4를 (무선 우선) 정렬해 (ifname, ip, netmask) 리스트로 반환.
    우선순위: preferred_ifaces → (Windows) netsh 무선명 → Wi-Fi 이름 힌트 → 기타
    """
    preferred_ifaces = [i.lower() for i in (preferred_ifaces or [])]
    wifi, others = [], []
    win_wifi_l = [w.lower() for w in windows_wifi_ifnames()]

    def push(ifname, ip, netmask):
        if not is_private_ipv4(ip) or not netmask:
            return
        lname = ifname.lower()
        if any(x in lname for x in EXCLUDE_HINTS):
            return
        # 우선순위
        if preferred_ifaces and any(p in lname for p in preferred_ifaces):
            wifi.append((ifname, ip, netmask)); return
        if win_wifi_l and any(w in lname for w in win_wifi_l):
            wifi.append((ifname, ip, netmask)); return
        if any(h in lname for h in WIFI_HINTS):
            wifi.append((ifname, ip, netmask)); return
        others.append((ifname, ip, netmask))

    if psutil:
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()
        for ifname, lst in addrs.items():
            if ifname in stats and not stats[ifname].isup:
                continue
            for a in lst:
                if getattr(a, "family", None) == socket.AF_INET:
                    push(ifname, a.address, a.netmask)

    return wifi + others

def list_candidate_bases(preferred_ifaces=None):
    """
    스캔용 서브넷 base('a.b.c.') 목록을 Wi-Fi 우선으로 반환, 중복 제거.
    """
    bases, seen = [], set()
    for ifname, ip, netmask in list_ipv4_by_iface(preferred_ifaces):
        try:
            net = ipaddress.ip_network(f"{ip}/{netmask}", strict=False)
        except Exception:
            continue
        if net.num_addresses < 4:
            continue
        base = ".".join(ip.split(".")[:3]) + "."
        if base not in seen:
            bases.append(base)
            seen.add(base)
    return bases

def udp_guess_local_ip():
    """
    UDP 더미 연결 기반 로컬 IP 추정(라우팅 테이블 활용).
    인터넷 연결이 없어도 바인딩 결과로 IP를 얻을 때가 많음.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # 실제 송신 없음
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None