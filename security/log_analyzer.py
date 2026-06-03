"""
AutoOps 日志分析与安全检测模块
功能：系统日志采集 / 错误日志分析 / 认证日志分析 / 暴力破解检测
技术栈：re + os + logging
来自课程实验：04log/sysinfo_log_alert.py, log_tofile.py
"""

import os
import re
from config.settings import Config


class LogAnalyzer:
    """日志分析器类
    负责采集平台运行日志和Linux认证日志，
    通过关键词匹配和正则表达式检测安全异常。
    """

    # 可疑关键词列表（用于日志异常检测）
    SUSPICIOUS_KEYWORDS = [
        "Failed password", "authentication failure", "invalid user",
        "segfault", "out of memory", "OOM", "kernel panic",
        "disk full", "No space left", "permission denied",
    ]

    # 攻击模式正则表达式（提取暴力破解攻击源IP）
    ATTACK_PATTERNS = [
        r"Failed password for .+ from (\d+\.\d+\.\d+\.\d+)",
        r"Invalid user .+ from (\d+\.\d+\.\d+\.\d+)",
    ]

    def __init__(self):
        """初始化日志分析器，确保日志目录存在。"""
        self.log_dir = Config.LOG_DIR
        try:
            os.makedirs(self.log_dir, exist_ok=True)
        except OSError as e:
            print(f"[日志模块] 创建目录失败: {e}")

    def get_recent_logs(self, n=100):
        """读取平台运行日志的最近n条。
        Args:
            n (int): 返回的日志条数，默认100
        Returns:
            list: 日志行列表
        """
        try:
            log_file = os.path.join(self.log_dir, "autoops.log")
            if not os.path.exists(log_file):
                return ["[系统] 暂无日志记录"]
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            return [l.strip() for l in lines[-n:]]
        except Exception as e:
            return [f"[错误] 读取日志失败: {e}"]

    def analyze_auth_log(self, log_path=None):
        """分析Linux认证日志，检测暴力破解和异常登录。
        Args:
            log_path (str): 认证日志路径，默认/var/log/auth.log
        Returns:
            list: 告警列表，每项包含level和message
        """
        alerts = []
        # 自动检测日志路径（优先级：参数指定 > 本地logs目录 > Linux系统日志）
        if log_path is None:
            # 首先检查项目本地logs目录（支持Windows环境）
            local_log = os.path.join(self.log_dir, "auth.log")
            if os.path.exists(local_log):
                log_path = local_log
            # 然后检查Linux系统日志路径
            elif os.path.exists("/var/log/secure"):
                log_path = "/var/log/secure"
            elif os.path.exists("/var/log/auth.log"):
                log_path = "/var/log/auth.log"
            else:
                return [{"level": "INFO", "message": "认证日志不可用（未找到日志文件）"}]
        if not os.path.exists(log_path):
            return [{"level": "INFO", "message": f"认证日志不存在: {log_path}"}]
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    # 关键词匹配检测
                    for keyword in self.SUSPICIOUS_KEYWORDS:
                        if keyword.lower() in line.lower():
                            alerts.append({
                                "level": "WARNING",
                                "message": line.strip()[:200]
                            })
                            break
                    # 正则表达式提取攻击源IP
                    for pattern in self.ATTACK_PATTERNS:
                        match = re.search(pattern, line)
                        if match:
                            alerts.append({
                                "level": "CRITICAL",
                                "message": f"疑似暴力破解攻击，来源IP: {match.group(1)}"
                            })
        except PermissionError:
            alerts.append({"level": "ERROR", "message": "权限不足，无法读取认证日志"})
        except Exception as e:
            alerts.append({"level": "ERROR", "message": f"日志分析异常: {e}"})
        return alerts[-50:]

    def analyze_logs(self):
        """综合日志分析，汇总平台日志和安全分析结果。
        Returns:
            dict: 包含platform_logs, auth_alerts, total_suspicious
        """
        result = {
            "platform_logs": self.get_recent_logs(20),
            "auth_alerts": self.analyze_auth_log(),
            "total_suspicious": 0,
        }
        result["total_suspicious"] = len(result["auth_alerts"])
        return result
