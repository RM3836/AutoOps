"""
AutoOps 定时任务调度模块
功能：定时采集系统状态 / 定时巡检 / 定时清理历史数据
技术栈：schedule（课程核心库第3个）
来自课程实验：02sysmon/sysinfo_byapscheduer.py
"""

import schedule
import time
import threading
import sqlite3
import logging
from datetime import datetime
from config.settings import Config

logger = logging.getLogger("autoops.scheduler")


class TaskScheduler:
    """定时任务调度器类
    使用schedule库实现定时任务管理，支持：
    - 定时采集系统状态
    - 定时清理过期数据
    - 自定义定时任务
    """

    def __init__(self, monitor, alert_mgr):
        """初始化调度器。
        Args:
            monitor: SystemMonitor实例
            alert_mgr: AlertManager实例
        """
        self.monitor = monitor
        self.alert_mgr = alert_mgr
        self._running = False

    def start(self):
        """启动定时任务调度器（后台线程）。
        注册所有定时任务后，在后台线程中循环执行。
        """
        if self._running:
            return
        self._running = True
        # 注册定时任务
        schedule.every(Config.MONITOR_INTERVAL).seconds.do(self._collect_and_check)
        schedule.every().day.at("00:00").do(self._cleanup_old_data)
        schedule.every().hour.do(self._hourly_report)
        logger.info("定时任务调度器已启动")
        # 后台线程执行调度循环
        t = threading.Thread(target=self._run_loop, daemon=True)
        t.start()

    def stop(self):
        """停止定时任务调度器。"""
        self._running = False

    def _run_loop(self):
        """调度循环（内部方法），持续检查并执行到期任务。"""
        while self._running:
            try:
                schedule.run_pending()
            except Exception as e:
                logger.error(f"调度执行异常: {e}")
            time.sleep(1)

    def _collect_and_check(self):
        """采集系统状态并检查告警阈值（每10秒执行一次）。"""
        try:
            data = self.monitor.collect_all()
            # 存入数据库
            conn = sqlite3.connect(Config.DB_PATH)
            c = conn.cursor()
            c.execute(
                "INSERT INTO server_status (cpu,memory,disk,network_sent,network_recv,process_count) VALUES (?,?,?,?,?,?)",
                (data["cpu"], data["memory"], data["disk"],
                 data["network_sent"], data["network_recv"], data["process_count"])
            )
            conn.commit()
            conn.close()
            # 检查告警
            alerts = self.alert_mgr.check_thresholds(data)
            for a in alerts:
                self.alert_mgr.save_alert(a)
        except Exception as e:
            logger.error(f"定时采集异常: {e}")

    def _cleanup_old_data(self):
        """清理7天前的历史数据（每天0点执行）。"""
        try:
            conn = sqlite3.connect(Config.DB_PATH)
            c = conn.cursor()
            c.execute("DELETE FROM server_status WHERE create_time < datetime('now', '-7 days')")
            c.execute("DELETE FROM alerts WHERE create_time < datetime('now', '-30 days')")
            conn.commit()
            conn.close()
            logger.info("历史数据清理完成")
        except sqlite3.Error as e:
            logger.error(f"数据清理失败: {e}")

    def _hourly_report(self):
        """每小时生成状态摘要（整点执行）。"""
        try:
            data = self.monitor.collect_all()
            logger.info(
                f"[整点巡检] CPU:{data['cpu']}% | "
                f"内存:{data['memory']}% | "
                f"磁盘:{data['disk']}% | "
                f"进程:{data['process_count']}"
            )
        except Exception as e:
            logger.error(f"整点巡检异常: {e}")
