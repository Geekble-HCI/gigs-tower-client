import subprocess
import re
import platform

class LocalIpResolver:

    @staticmethod
    def resolve_ip():
        # OS: window
        def get_ip_windows():
            result = subprocess.run(['ipconfig'], stdout=subprocess.PIPE, text=True)
            output = result.stdout
            # IPv4 주소 라인 추출
            matches = re.findall(r'IPv4.*?:\s*([\d.]+)', output)
            for ip in matches:
                if not ip.startswith("127."):
                    return ip
            return None

        # OS: linux, macOS
        def get_ip_unix():
            # macOS용 ifconfig 방법 시도
            try:
                result = subprocess.run(['ifconfig'], stdout=subprocess.PIPE, text=True)
                lines = result.stdout.splitlines()
                for line in lines:
                    if 'inet ' in line and '127.0.0.1' not in line:
                        ip = line.strip().split()[1]
                        if ip and not ip.startswith("127."):
                            return ip
            except Exception as e:
                print(f"[IP] ifconfig failed: {e}")
            
            # Linux hostname -I 방법 시도
            try:
                result = subprocess.run(['hostname', '-I'], stdout=subprocess.PIPE, text=True)
                ips = result.stdout.strip().split()
                for ip in ips:
                    if not ip.startswith("127."):
                        return ip
            except Exception as e:
                print(f"[IP] hostname -I failed: {e}")
                
            # Linux ip addr 방법 시도
            try:
                result = subprocess.run(['ip', 'addr'], stdout=subprocess.PIPE, text=True)
                lines = result.stdout.splitlines()
                for line in lines:
                    if 'inet ' in line and not '127.0.0.1' in line:
                        return line.strip().split(' ')[1].split('/')[0]
            except Exception as e:
                print(f"[IP] ip addr failed: {e}")
                
            return None

        system = platform.system()
        if system == 'Windows':
            return get_ip_windows()
        elif system in ['Linux', 'Darwin']:  # Darwin = macOS
            return get_ip_unix()
        else:
            raise Exception(f"Unsupported OS: {system}")