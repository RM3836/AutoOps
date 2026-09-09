"""
端口扫描 + DNS解析 (加分项 - 来自实验07)
功能: TCP并行端口扫描 / 常见服务识别 / DNS域名解析(A/MX/NS/CNAME)
"""
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed


def _scan_one(host, port):
    """扫描单个端口"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        code = sock.connect_ex((host, port))
        status = "open" if code == 0 else "closed"
        service = get_service_name(port)
        sock.close()
        return {"port": port, "status": status, "service": service}
    except Exception:
        return {"port": port, "status": "error", "service": "--"}


def tcp_scan(host, ports):
    """TCP并行端口扫描（ThreadPoolExecutor 加速）
    ports: [22, 80, 443, 3306, ...]
    """
    results = []
    with ThreadPoolExecutor(max_workers=min(len(ports), 20)) as executor:
        futures = {executor.submit(_scan_one, host, p): p for p in ports}
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda x: x["port"])
    return results


def get_service_name(port):
    """常见端口 -> 服务名 + 说明"""
    common = {
        21: "FTP - 文件传输",
        22: "SSH - 安全远程登录",
        23: "Telnet - 远程登录(明文)",
        25: "SMTP - 邮件发送",
        53: "DNS - 域名解析",
        80: "HTTP - 网站服务",
        110: "POP3 - 邮件接收",
        143: "IMAP - 邮件接收",
        443: "HTTPS - 加密网站",
        993: "IMAPS - 加密邮件",
        995: "POP3S - 加密邮件",
        3306: "MySQL - 数据库",
        3389: "RDP - Windows远程桌面",
        5432: "PostgreSQL - 数据库",
        6379: "Redis - 缓存数据库",
        8080: "HTTP备用 - 代理/Web",
        8443: "HTTPS备用 - 加密代理",
        8888: "phpMyAdmin - 数据库管理",
        27017: "MongoDB - NoSQL数据库",
    }
    return common.get(port, f"Port {port}")


def dns_resolve(domain):
    """DNS域名解析（A/MX/NS/CNAME 记录）
    使用 dnspython 库（如可用），否则回退到 socket + dig
    """
    result = {"domain": domain, "A": [], "CNAME": [], "MX": [], "NS": []}

    # A 记录 — socket.getaddrinfo
    try:
        ips = socket.getaddrinfo(domain, None)
        for info in ips:
            ip = info[4][0]
            if ip not in result["A"]:
                result["A"].append(ip)
    except Exception as e:
        result["error"] = str(e)

    # MX / NS / CNAME — 尝试 dnspython，回退到 subprocess dig/nslookup
    try:
        import subprocess

        # NS 记录
        try:
            out = subprocess.check_output(
                ["nslookup", "-type=NS", domain],
                timeout=5, stderr=subprocess.DEVNULL
            ).decode(errors="ignore")
            for line in out.split("\n"):
                line = line.strip()
                if "nameserver =" in line or "nameserver=" in line:
                    ns = line.split("=")[-1].strip().rstrip(".")
                    if ns and ns not in result["NS"]:
                        result["NS"].append(ns)
        except Exception:
            pass

        # MX 记录
        try:
            out = subprocess.check_output(
                ["nslookup", "-type=MX", domain],
                timeout=5, stderr=subprocess.DEVNULL
            ).decode(errors="ignore")
            for line in out.split("\n"):
                line = line.strip()
                if "mail exchanger" in line:
                    parts = line.split("=")
                    if len(parts) >= 2:
                        mx = parts[-1].strip().rstrip(".")
                        if mx and mx not in result["MX"]:
                            result["MX"].append(mx)
        except Exception:
            pass

        # CNAME — 尝试 dnspython
        try:
            import dns.resolver
            answers = dns.resolver.resolve(domain, "CNAME")
            for rdata in answers:
                cname = str(rdata.target).rstrip(".")
                if cname not in result["CNAME"]:
                    result["CNAME"].append(cname)
        except ImportError:
            pass
        except Exception:
            pass

    except Exception:
        pass

    return result


COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995,
                3306, 3389, 5432, 6379, 8080, 8443, 8888, 27017]
