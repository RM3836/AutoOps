"""
批量主机存活检测 (加分项 - 来自实验01)
功能: 批量Ping检测网段主机，返回存活状态
"""
import subprocess
import platform
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed


def ping_host(host, count=1, timeout=1):
    """Ping 单个主机"""
    flag = "-n" if platform.system() == "Windows" else "-c"
    t_flag = "-w" if platform.system() == "Windows" else "-W"
    cmd = ["ping", flag, str(count), t_flag, str(timeout), host]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+3)
        alive = result.returncode == 0
        return {"host": host, "alive": alive}
    except Exception:
        return {"host": host, "alive": False}


def batch_ping(hosts, max_workers=50):
    """批量Ping多个主机
    hosts: ["192.168.1.1", "192.168.1.2", ...]
    """
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(ping_host, h): h for h in hosts}
        for future in as_completed(futures):
            results.append(future.result())
    # 排序: 存活的在前
    results.sort(key=lambda x: (not x["alive"], x["host"]))
    return results


def scan_subnet(subnet_base, start=1, end=254):
    """扫描子网存活主机
    subnet_base: "192.168.1" -> 扫描 192.168.1.1 ~ 192.168.1.254
    """
    hosts = [f"{subnet_base}.{i}" for i in range(start, end+1)]
    return batch_ping(hosts)


def resolve_hostname(ip):
    """IP反解主机名"""
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return "--"
