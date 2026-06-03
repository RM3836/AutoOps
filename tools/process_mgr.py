"""
进程管理器 (加分项 - 来自实验02)
功能: 查看进程详情 / 按名称杀进程 / 按CPU排序
"""
import psutil


def list_processes(sort_by="cpu", limit=30):
    """列出进程，按CPU或内存排序"""
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent",
                                   "status", "create_time", "username"]):
        try:
            info = p.info
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    key = "cpu_percent" if sort_by == "cpu" else "memory_percent"
    procs.sort(key=lambda x: x.get(key, 0) or 0, reverse=True)
    return procs[:limit]


def get_process_detail(pid):
    """获取进程详细信息"""
    try:
        p = psutil.Process(pid)
        info = p.as_dict(attrs=[
            "pid", "name", "status", "cpu_percent", "memory_percent",
            "create_time", "username", "cmdline", "cwd", "num_threads"
        ])
        info["cmdline"] = " ".join(info.get("cmdline", []) or [])
        return info
    except psutil.NoSuchProcess:
        return None


def kill_process(pid):
    """杀死指定PID的进程"""
    try:
        p = psutil.Process(pid)
        name = p.name()
        p.terminate()
        p.wait(timeout=3)
        return True, f"已终止进程: {name} (PID: {pid})"
    except psutil.NoSuchProcess:
        return False, f"进程不存在: PID {pid}"
    except psutil.AccessDenied:
        return False, f"权限不足: PID {pid}"
    except psutil.TimeoutExpired:
        try:
            p.kill()
            return True, f"已强制杀死进程: PID {pid}"
        except Exception:
            return False, f"无法杀死进程: PID {pid}"


def kill_process_by_name(proc_name):
    """按进程名杀死所有匹配的进程"""
    killed = []
    for p in psutil.process_iter(["pid", "name"]):
        try:
            if p.info["name"] and p.info["name"].lower() == proc_name.lower():
                p.terminate()
                killed.append(p.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return killed
