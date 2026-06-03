"""
AutoOps 自动告警模块
功能：CPU过高告警 / 内存不足告警 / 磁盘满告警 / 邮件通知 / 日志记录
技术栈：smtplib + sqlite3 + logging
来自课程实验：04log/email_send.py, sysinfo_log_alert.py
"""

import smtplib
import sqlite3
import logging
from email.mime.text import MIMEText
from datetime import datetime
from config.settings import Config

logger = logging.getLogger("autoops.alert")


class AlertManager:
    """自动告警管理器类
    实时监控系统指标，超过阈值自动触发告警。
    支持三种告警方式：Web页面展示、邮件通知、日志记录。
    告警级别：INFO（信息）、WARNING（警告）、CRITICAL（严重）
    """

    def __init__(self):
        """初始化告警管理器，加载告警阈值配置。"""
        self.thresholds = {
            "cpu": Config.CPU_THRESHOLD,       # CPU告警阈值: 80%
            "memory": Config.MEMORY_THRESHOLD,  # 内存告警阈值: 85%
            "disk": Config.DISK_THRESHOLD,      # 磁盘告警阈值: 90%
        }

    def check_thresholds(self, data):
        """检查系统指标是否超过告警阈值。
        Args:
            data (dict): 系统状态数据，包含cpu, memory, disk
        Returns:
            list: 触发的告警列表，每项包含level, module, message
        """
        alerts = []
        try:
            if data.get("cpu", 0) > self.thresholds["cpu"]:
                alerts.append({
                    "level": "WARNING",
                    "module": "系统监控",
                    "message": f"CPU使用率过高: {data['cpu']}% (阈值: {self.thresholds['cpu']}%)"
                })
            if data.get("memory", 0) > self.thresholds["memory"]:
                alerts.append({
                    "level": "WARNING",
                    "module": "系统监控",
                    "message": f"内存使用率过高: {data['memory']}% (阈值: {self.thresholds['memory']}%)"
                })
            if data.get("disk", 0) > self.thresholds["disk"]:
                alerts.append({
                    "level": "CRITICAL",
                    "module": "系统监控",
                    "message": f"磁盘使用率过高: {data['disk']}% (阈值: {self.thresholds['disk']}%)"
                })
        except Exception as e:
            alerts.append({"level": "ERROR", "module": "告警模块", "message": f"阈值检查异常: {e}"})
        return alerts

    def save_alert(self, alert):
        """保存告警到数据库并记录日志，严重告警发送邮件。
        Args:
            alert (dict): 告警信息，包含level, module, message
        """
        try:
            conn = sqlite3.connect(Config.DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO alerts (level, module, message) VALUES (?,?,?)",
                (alert["level"], alert["module"], alert["message"]))
            conn.commit()
            conn.close()
            logger.warning(f"[告警] {alert['level']} | {alert['module']} | {alert['message']}")
            # CRITICAL级别发送邮件通知
            if alert["level"] == "CRITICAL":
                self.send_email_alert(alert)
        except sqlite3.Error as e:
            logger.error(f"保存告警失败: {e}")

    def send_email_alert(self, alert):
        """发送邮件告警通知（需要配置SMTP参数）。
        Args:
            alert (dict): 告警信息
        """
        if not Config.SMTP_USER or not Config.ALERT_EMAIL:
            logger.info("邮件未配置，跳过邮件告警")
            return
        try:
            msg = MIMEText(
                f"告警级别: {alert['level']}\n"
                f"模块: {alert['module']}\n"
                f"详情: {alert['message']}\n"
                f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "plain", "utf-8"
            )
            msg["Subject"] = f"[AutoOps告警] {alert['level']} - {alert['module']}"
            msg["From"] = Config.SMTP_USER
            msg["To"] = Config.ALERT_EMAIL
            with smtplib.SMTP_SSL(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
                server.login(Config.SMTP_USER, Config.SMTP_PASS)
                server.sendmail(Config.SMTP_USER, [Config.ALERT_EMAIL], msg.as_string())
            logger.info(f"邮件告警已发送: {alert['message']}")
        except smtplib.SMTPException as e:
            logger.error(f"邮件发送失败: {e}")
        except Exception as e:
            logger.error(f"邮件告警异常: {e}")

    def get_recent_alerts(self, n=20):
        """获取最近n条告警记录。
        Args:
            n (int): 返回条数，默认20
        Returns:
            list: 告警记录列表
        """
        try:
            conn = sqlite3.connect(Config.DB_PATH)
            c = conn.cursor()
            c.execute("SELECT level,module,message,create_time FROM alerts ORDER BY id DESC LIMIT ?", (n,))
            rows = c.fetchall()
            conn.close()
            return [{"level":r[0],"module":r[1],"message":r[2],"time":r[3]} for r in rows]
        except sqlite3.Error as e:
            return [{"level":"ERROR","module":"数据库","message":str(e)}]
