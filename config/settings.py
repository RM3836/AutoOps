"""
AutoOps 配置模块
功能：集中管理所有配置项（端口、阈值、邮件、数据库路径等）
"""

import os


class Config:
    """全局配置类，所有模块从这里读取配置。"""

    # Flask密钥（用于session加密）
    SECRET_KEY = os.environ.get("SECRET_KEY", "autoops-secret-2026")

    # Web服务端口
    PORT = int(os.environ.get("PORT", 5000))

    # 项目根目录
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # SQLite数据库文件路径
    DB_PATH = os.path.join(BASE_DIR, "database", "autoops.db")

    # 日志存储目录
    LOG_DIR = os.path.join(BASE_DIR, "logs")

    # 监控采集间隔（秒）
    MONITOR_INTERVAL = 2

    # ===== 告警阈值配置 =====
    CPU_THRESHOLD = 80.0       # CPU告警阈值 (%)
    MEMORY_THRESHOLD = 85.0    # 内存告警阈值 (%)
    DISK_THRESHOLD = 90.0      # 磁盘告警阈值 (%)

    # ===== 邮件告警SMTP配置 =====
    SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.qq.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 465))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASS = os.environ.get("SMTP_PASS", "")
    ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "")
