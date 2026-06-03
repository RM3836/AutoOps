"""
AutoOps 系统监控模块
功能：CPU / 内存 / 磁盘 / 网络 / 进程 实时监控
技术栈：psutil
来自课程实验：02sysmon/sysinfo_bypsutil.py
"""

import psutil
import time
import platform


class SystemMonitor:
    """系统资源监控器类
    封装psutil库，提供系统各项指标的采集方法。
    """

    def collect_all(self):
        """采集所有系统指标，返回汇总字典。
        Returns:
            dict: 包含cpu, memory, disk, network_sent, network_recv,
                  process_count, boot_time, platform, cpu_count,
                  memory_total, memory_used, disk_total, disk_used
        """
        try:
            net = psutil.net_io_counters()
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            return {
                "cpu": psutil.cpu_percent(interval=0.5),
                "memory": mem.percent,
                "disk": disk.percent,
                "network_sent": round(net.bytes_sent / 1024 / 1024, 2),
                "network_recv": round(net.bytes_recv / 1024 / 1024, 2),
                "process_count": len(psutil.pids()),
                "boot_time": psutil.boot_time(),
                "platform": platform.platform(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": round(mem.total / 1024**3, 2),
                "memory_used": round(mem.used / 1024**3, 2),
                "disk_total": round(disk.total / 1024**3, 2),
                "disk_used": round(disk.used / 1024**3, 2),
            }
        except Exception as e:
            return {"cpu": 0, "memory": 0, "disk": 0, "error": str(e)}

    def get_top_processes(self, n=10):
        """获取CPU占用最高的前N个进程。
        Args:
            n (int): 返回的进程数量，默认10
        Returns:
            list: 进程信息列表，每项包含pid, name, cpu_percent, memory_percent
        """
        try:
            procs = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                try:
                    procs.append(p.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            procs.sort(key=lambda x: x.get("cpu_percent", 0) or 0, reverse=True)
            return procs[:n]
        except Exception as e:
            return [{"error": str(e)}]

    def cpu_monitor(self):
        """独立CPU监控，返回CPU使用率百分比。
        Returns:
            float: CPU使用率 (0-100)
        """
        try:
            return psutil.cpu_percent(interval=1)
        except Exception:
            return 0.0

    def memory_monitor(self):
        """独立内存监控，返回内存详情。
        Returns:
            dict: 包含total_gb, used_gb, percent
        """
        try:
            mem = psutil.virtual_memory()
            return {
                "total_gb": round(mem.total / 1024**3, 2),
                "used_gb": round(mem.used / 1024**3, 2),
                "percent": mem.percent
            }
        except Exception as e:
            return {"total_gb": 0, "used_gb": 0, "percent": 0, "error": str(e)}

    def disk_monitor(self):
        """独立磁盘监控，返回磁盘详情。
        Returns:
            dict: 包含total_gb, used_gb, percent
        """
        try:
            disk = psutil.disk_usage("/")
            return {
                "total_gb": round(disk.total / 1024**3, 2),
                "used_gb": round(disk.used / 1024**3, 2),
                "percent": disk.percent
            }
        except Exception as e:
            return {"total_gb": 0, "used_gb": 0, "percent": 0, "error": str(e)}

    def get_server_details(self):
        """采集服务器详细信息，供服务器详情页使用。
        Returns:
            dict: 包含 cpu_info, memory_info, disk_info, network_info, io_info
        """
        result = {}
        try:
            # ===== CPU 信息 =====
            cpu_freq = psutil.cpu_freq()
            cpu_percent_per_core = psutil.cpu_percent(interval=0.5, percpu=True)
            try:
                import subprocess
                if platform.system() == "Windows":
                    cpu_model = platform.processor()
                else:
                    cpu_model = subprocess.check_output(
                        ["cat", "/proc/cpuinfo"], timeout=3, stderr=subprocess.DEVNULL
                    ).decode(errors="ignore")
                    for line in cpu_model.split("\n"):
                        if "model name" in line:
                            cpu_model = line.split(":")[1].strip()
                            break
            except Exception:
                cpu_model = platform.processor() or "Unknown"

            result["cpu_info"] = {
                "model": cpu_model,
                "physical_cores": psutil.cpu_count(logical=False) or 0,
                "logical_cores": psutil.cpu_count(logical=True) or 0,
                "freq_current": round(cpu_freq.current, 0) if cpu_freq else 0,
                "freq_max": round(cpu_freq.max, 0) if cpu_freq else 0,
                "usage_total": psutil.cpu_percent(interval=0.5),
                "usage_per_core": cpu_percent_per_core,
            }

            # ===== 内存信息 =====
            mem = psutil.virtual_memory()
            try:
                swap = psutil.swap_memory()
            except Exception:
                swap = None
            result["memory_info"] = {
                "total_gb": round(mem.total / 1024**3, 2),
                "used_gb": round(mem.used / 1024**3, 2),
                "available_gb": round(mem.available / 1024**3, 2),
                "percent": mem.percent,
                "buffers_mb": round(getattr(mem, "buffers", 0) / 1024**2, 1),
                "cached_mb": round(getattr(mem, "cached", 0) / 1024**2, 1),
                "swap_total_gb": round(swap.total / 1024**3, 2) if swap else 0,
                "swap_used_gb": round(swap.used / 1024**3, 2) if swap else 0,
                "swap_percent": swap.percent if swap else 0,
            }

            # ===== 磁盘分区信息 =====
            partitions = []
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    try:
                        inodes = psutil.disk_usage(part.mountpoint)
                        # psutil 没有直接提供 inode，用 os.statvfs（Linux）
                        import os
                        if hasattr(os, "statvfs"):
                            st = os.statvfs(part.mountpoint)
                            inodes_total = st.f_files
                            inodes_free = st.f_ffree
                            inodes_used = inodes_total - inodes_free
                        else:
                            inodes_total = inodes_free = inodes_used = 0
                    except Exception:
                        inodes_total = inodes_free = inodes_used = 0

                    partitions.append({
                        "mountpoint": part.mountpoint,
                        "device": part.device,
                        "fstype": part.fstype,
                        "opts": part.opts[:60] if part.opts else "",
                        "total_gb": round(usage.total / 1024**3, 2),
                        "used_gb": round(usage.used / 1024**3, 2),
                        "free_gb": round(usage.free / 1024**3, 2),
                        "percent": usage.percent,
                        "inodes_total": inodes_total,
                        "inodes_used": inodes_used,
                        "inodes_free": inodes_free,
                    })
                except (PermissionError, OSError):
                    continue
            result["disk_info"] = partitions

            # ===== 网卡流量信息 =====
            net_io = psutil.net_io_counters(pernic=True)
            net_addrs = psutil.net_if_addrs()
            interfaces = []
            for nic, counters in net_io.items():
                if nic.lower().startswith("lo") or nic.lower().startswith("loopback"):
                    continue
                addrs = net_addrs.get(nic, [])
                ipv4 = ""
                for a in addrs:
                    if a.family.name == "AF_INET":
                        ipv4 = a.address
                        break
                interfaces.append({
                    "name": nic,
                    "ipv4": ipv4,
                    "bytes_sent_mb": round(counters.bytes_sent / 1024**2, 2),
                    "bytes_recv_mb": round(counters.bytes_recv / 1024**2, 2),
                    "packets_sent": counters.packets_sent,
                    "packets_recv": counters.packets_recv,
                    "errin": counters.errin,
                    "errout": counters.errout,
                    "dropin": counters.dropin,
                    "dropout": counters.dropout,
                })
            result["network_info"] = interfaces

            # ===== 磁盘 IO 信息 =====
            try:
                disk_io = psutil.disk_io_counters(perdisk=True)
                io_list = []
                for dev, counters in disk_io.items():
                    # 只取真实磁盘（跳过 loop/sr/ram 等）
                    if dev.startswith("loop") or dev.startswith("sr") or dev.startswith("ram"):
                        continue
                    io_list.append({
                        "device": dev,
                        "read_count": counters.read_count,
                        "write_count": counters.write_count,
                        "read_mb": round(counters.read_bytes / 1024**2, 2),
                        "write_mb": round(counters.write_bytes / 1024**2, 2),
                        "read_time_ms": counters.read_time,
                        "write_time_ms": counters.write_time,
                    })
                result["io_info"] = io_list
            except Exception:
                result["io_info"] = []

        except Exception as e:
            result["error"] = str(e)
        return result
