#!/usr/bin/env python3
"""
AutoOps 自动化运维管理系统 - 主入口模块
功能：Flask Web服务、路由注册、后台监控线程启动、数据库初始化
技术栈：Flask + SQLite + psutil + Paramiko + schedule
"""

import os
import sys
import time
import threading
import sqlite3
import base64
from datetime import datetime

from flask import Flask, render_template, jsonify, request, send_file, Response
from config.settings import Config
from monitor.system_monitor import SystemMonitor
from monitor.scheduler import TaskScheduler
from remote.ssh_manager import SSHManager
from security.log_analyzer import LogAnalyzer
from alert.alert_manager import AlertManager
from tools.ping_scan import batch_ping, scan_subnet
from tools.port_scan import tcp_scan, dns_resolve, COMMON_PORTS
from tools.process_mgr import list_processes, kill_process
from tools.report_gen import generate_html_report, export_csv
from remote.ssh_key import SSHKeyAuth

# 创建Flask应用实例
app = Flask(__name__)
app.config.from_object(Config)

# 配置日志写入文件（供"平台运行日志"面板读取）
import logging
os.makedirs(Config.LOG_DIR, exist_ok=True)
_file_handler = logging.FileHandler(
    os.path.join(Config.LOG_DIR, "autoops.log"), encoding="utf-8"
)
_file_handler.setFormatter(logging.Formatter(
    "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
))
_file_handler.setLevel(logging.INFO)
app.logger.addHandler(_file_handler)
app.logger.setLevel(logging.INFO)

# 初始化各功能模块
monitor = SystemMonitor()      # 系统监控模块
ssh_mgr = SSHManager()         # SSH远程运维模块
log_analyzer = LogAnalyzer()   # 日志分析模块
alert_mgr = AlertManager()     # 自动告警模块
scheduler = TaskScheduler(monitor, alert_mgr)  # schedule定时任务模块
_background_started = False


def init_db():
    """初始化SQLite数据库，创建所有必需的数据表。
    包括：server_status(服务器状态)、alerts(告警记录)、
    ssh_hosts(SSH主机)、operation_logs(操作日志)
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS server_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpu REAL, memory REAL, disk REAL,
            network_sent REAL, network_recv REAL,
            process_count INTEGER,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT, module TEXT, message TEXT,
            is_resolved INTEGER DEFAULT 0,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS ssh_hosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hostname TEXT, port INTEGER DEFAULT 22,
            username TEXT, password TEXT,
            description TEXT, status TEXT DEFAULT 'unknown'
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operator TEXT, action TEXT, target TEXT,
            result TEXT,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"[数据库错误] 初始化失败: {e}")


def background_monitor():
    """后台监控线程：每10秒自动采集系统状态，存入数据库并检查告警阈值。
    此线程作为守护线程运行，随主进程退出自动终止。
    """
    while True:
        try:
            # 采集系统状态数据
            data = monitor.collect_all()
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
            # 检查是否触发告警
            alerts = alert_mgr.check_thresholds(data)
            for a in alerts:
                alert_mgr.save_alert(a)
        except Exception as e:
            print(f"[监控异常] {e}")
        time.sleep(Config.MONITOR_INTERVAL)


def start_background_tasks():
    """启动后台定时任务，避免不同入口重复注册。"""
    global _background_started
    if _background_started:
        return
    scheduler.start()
    _background_started = True


def start_background_services():
    """兼容run.py的一键启动入口。"""
    start_background_tasks()
    app.logger.info("AutoOps 服务启动完成，后台监控已开启")


# ==================== 页面路由 ====================

@app.route("/")
def index():
    """仪表盘首页：展示CPU/内存/磁盘实时监控、趋势图表、进程列表"""
    return render_template("index.html")

@app.route("/ssh")
def ssh_page():
    """SSH远程运维页面：服务器管理、终端命令执行"""
    return render_template("ssh.html")

@app.route("/logs")
def logs_page():
    """日志分析页面：运行日志、安全分析"""
    return render_template("logs.html")

@app.route("/alerts")
def alerts_page():
    """告警中心页面：告警统计、告警记录"""
    return render_template("alerts.html")

@app.route("/tools")
def tools_page():
    """运维工具箱页面（加分项）：主机扫描、端口扫描、DNS、进程管理、报告导出"""
    return render_template("tools.html")

@app.route("/server")
def server_page():
    """服务器详情页面：CPU/内存/磁盘/网卡/IO 详细信息"""
    return render_template("server.html")


# ==================== API接口 ====================

@app.route("/api/status")
def api_status():
    """获取当前系统状态（CPU/内存/磁盘/网络/进程）"""
    try:
        data = monitor.collect_all()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/server/info")
def api_server_info():
    """获取服务器详细信息（CPU型号/内存/磁盘分区/网卡/IO）"""
    try:
        data = monitor.get_server_details()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/health")
def api_health():
    """健康检查接口。
    返回 Python 版本、依赖可用性、数据库可读性和当前应用状态，方便部署验收。
    """
    modules = {}
    for name in ("flask", "psutil", "paramiko", "schedule"):
        try:
            __import__(name)
            modules[name] = True
        except Exception:
            modules[name] = False

    db_ok = False
    db_tables = []
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        db_tables = [row[0] for row in c.fetchall()]
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False

    return jsonify({
        "status": "ok" if db_ok and all(modules.values()) else "degraded",
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "request_host": request.host,
        "server_port": request.host.split(":")[-1] if ":" in request.host else str(Config.PORT),
        "db_ok": db_ok,
        "db_tables": db_tables,
        "modules": modules,
        "current_time": time.strftime("%Y-%m-%d %H:%M:%S"),
    })

# ==================== Prometheus 指标暴露 ====================

def prometheus_metrics():
    """生成 Prometheus 标准文本格式的监控指标。

    Prometheus 采用拉取（pull）模型，本接口把 psutil 实时采集的指标
    暴露为 text/plain 格式，供 Prometheus Server 定期抓取。
    指标命名遵循 Prometheus 命名规范（全小写 + 下划线）。
    """
    try:
        data = monitor.collect_all()
        # 构造指标文本（# HELP / # TYPE 是 Prometheus 规范的注释行）
        lines = [
            "# HELP autoops_cpu_usage_percent 当前 CPU 使用率(%)",
            "# TYPE autoops_cpu_usage_percent gauge",
            f"autoops_cpu_usage_percent {data.get('cpu', 0)}",
            "",
            "# HELP autoops_memory_usage_percent 当前内存使用率(%)",
            "# TYPE autoops_memory_usage_percent gauge",
            f"autoops_memory_usage_percent {data.get('memory', 0)}",
            "",
            "# HELP autoops_disk_usage_percent 当前磁盘使用率(%)",
            "# TYPE autoops_disk_usage_percent gauge",
            f"autoops_disk_usage_percent {data.get('disk', 0)}",
            "",
            "# HELP autoops_process_count 当前系统进程总数",
            "# TYPE autoops_process_count gauge",
            f"autoops_process_count {data.get('process_count', 0)}",
            "",
            "# HELP autoops_network_recv_mb 累计接收流量(MB)",
            "# TYPE autoops_network_recv_mb counter",
            f"autoops_network_recv_mb {data.get('network_recv', 0)}",
            "",
        ]
        return Response("\n".join(lines), mimetype="text/plain; version=0.0.4")
    except Exception as e:
        return Response(f"# error: {e}", mimetype="text/plain")


@app.route("/metrics")
def api_metrics():
    """Prometheus 抓取入口。"""
    return prometheus_metrics()


@app.route("/api/history")
def api_history():
    """获取最近60条历史监控数据（用于趋势图表）"""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        c = conn.cursor()
        c.execute("SELECT cpu,memory,disk,create_time FROM server_status ORDER BY id DESC LIMIT 60")
        rows = c.fetchall()
        conn.close()
        rows.reverse()
        return jsonify([{"cpu":r[0],"memory":r[1],"disk":r[2],"time":r[3]} for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/alerts")
def api_alerts():
    """获取最近50条告警记录"""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id,level,module,message,is_resolved,create_time FROM alerts ORDER BY id DESC LIMIT 50")
        rows = c.fetchall()
        conn.close()
        return jsonify([
            {
                "id": r[0],
                "level": r[1],
                "module": r[2],
                "message": r[3],
                "resolved": bool(r[4]),
                "time": r[5],
            }
            for r in rows
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/alerts/resolve/<int:alert_id>", methods=["POST"])
def api_alert_resolve(alert_id):
    """将指定告警标记为已处理。"""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE alerts SET is_resolved = 1 WHERE id = ?", (alert_id,))
        updated = c.rowcount
        conn.commit()
        conn.close()
        if updated == 0:
            return jsonify({"ok": False, "message": "告警不存在"}), 404
        return jsonify({"ok": True, "message": "已标记为已处理"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/processes")
def api_processes():
    """获取系统进程列表（按CPU排序）"""
    try:
        return jsonify(monitor.get_top_processes())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== SSH相关API ====================

@app.route("/api/ssh/hosts", methods=["GET"])
def api_ssh_hosts():
    """获取已保存的SSH服务器列表"""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id,hostname,port,username,description,status FROM ssh_hosts")
        rows = c.fetchall()
        conn.close()
        return jsonify([{"id":r[0],"hostname":r[1],"port":r[2],"username":r[3],"desc":r[4],"status":r[5]} for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/ssh/add", methods=["POST"])
def api_ssh_add():
    """添加SSH服务器到数据库"""
    try:
        d = request.json
        conn = sqlite3.connect(Config.DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO ssh_hosts (hostname,port,username,password,description) VALUES (?,?,?,?,?)",
            (d["hostname"], d.get("port",22), d["username"], base64.b64encode(d["password"].encode()).decode(), d.get("description","")))
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/ssh/delete/<int:host_id>", methods=["DELETE"])
def api_ssh_delete(host_id):
    """删除SSH服务器"""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM ssh_hosts WHERE id=?", (host_id,))
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/ssh/exec", methods=["POST"])
def api_ssh_exec():
    """SSH远程执行命令，结果记入操作日志"""
    try:
        d = request.json
        host_id = d["host_id"]
        command = d["command"]
        conn = sqlite3.connect(Config.DB_PATH)
        c = conn.cursor()
        c.execute("SELECT hostname,port,username,password FROM ssh_hosts WHERE id=?", (host_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return jsonify({"error": "主机不存在"}), 404
        # 解码base64编码的密码
        pwd = base64.b64decode(row[3].encode()).decode()
        result = ssh_mgr.exec_command(row[0], row[1], row[2], pwd, command)
        # 记录操作日志（审计）
        conn = sqlite3.connect(Config.DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO operation_logs (operator,action,target,result) VALUES (?,?,?,?)",
            (row[2], "ssh_exec", f"{row[0]}:{command}", result[:500]))
        conn.commit()
        conn.close()
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== 日志相关API ====================

@app.route("/api/logs")
def api_logs():
    """获取平台运行日志"""
    try:
        return jsonify(log_analyzer.get_recent_logs())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/logs/analyze")
def api_log_analyze():
    """执行日志安全分析（检测暴力破解、异常行为等）"""
    try:
        result = log_analyzer.analyze_logs()
        app.logger.info(f"安全分析完成：检测到 {result['total_suspicious']} 条可疑事件")
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== 工具箱API（加分项）====================

@app.route("/api/tools/ping", methods=["POST"])
def api_ping():
    """批量主机存活检测（支持列表模式和子网扫描模式）"""
    try:
        d = request.json
        mode = d.get("mode", "list")
        if mode == "subnet":
            results = scan_subnet(d.get("subnet", "192.168.1"), d.get("start", 1), d.get("end", 254))
        else:
            results = batch_ping(d.get("hosts", []))
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tools/portscan", methods=["POST"])
def api_portscan():
    """TCP端口扫描（返回端口状态和服务识别）"""
    try:
        d = request.json
        host = d.get("host", "127.0.0.1")
        ports = d.get("ports", COMMON_PORTS)
        results = tcp_scan(host, ports)
        return jsonify({"host": host, "ports": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tools/dns", methods=["POST"])
def api_dns():
    """DNS域名解析"""
    try:
        d = request.json
        return jsonify(dns_resolve(d.get("domain", "")))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tools/processes", methods=["GET"])
def api_processes_list():
    """获取进程列表（支持按CPU/内存排序）"""
    try:
        sort_by = request.args.get("sort", "cpu")
        limit = int(request.args.get("limit", 30))
        return jsonify(list_processes(sort_by, limit))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tools/kill", methods=["POST"])
def api_kill_process():
    """终止指定PID的进程"""
    try:
        d = request.json
        ok, msg = kill_process(d.get("pid"))
        return jsonify({"ok": ok, "message": msg})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tools/report", methods=["GET"])
def api_report():
    """生成HTML巡检报告并下载"""
    try:
        data = monitor.collect_all()
        filepath = os.path.join(Config.LOG_DIR, "report.html")
        generate_html_report(data, filepath)
        return send_file(filepath, as_attachment=True, download_name="AutoOps_Report.html")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tools/export/csv", methods=["GET"])
def api_export_csv():
    """导出监控数据为CSV文件并下载"""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        c = conn.cursor()
        c.execute("SELECT cpu,memory,disk,create_time FROM server_status ORDER BY id DESC LIMIT 100")
        rows = c.fetchall()
        conn.close()
        data = [{"cpu":r[0],"memory":r[1],"disk":r[2],"time":r[3]} for r in rows]
        filepath = os.path.join(Config.LOG_DIR, "sysinfo.csv")
        export_csv(data, filepath)
        return send_file(filepath, as_attachment=True, download_name="AutoOps_Data.csv")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tools/sftp", methods=["POST"])
def api_sftp():
    """SFTP文件列表查看"""
    try:
        d = request.json
        files = SSHKeyAuth.sftp_listdir(
            d["hostname"], d.get("port", 22),
            d["username"], d["password"], d.get("path", "/")
        )
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== 启动入口 ====================
if __name__ == "__main__":
    # 初始化数据库
    init_db()
    # 启动schedule后台定时任务（守护线程，主进程退出自动终止）
    start_background_tasks()
    print("=" * 50)
    print("  AutoOps 自动化运维管理系统")
    print("=" * 50)
    print(f"  访问地址: http://localhost:{Config.PORT}")
    print(f"  数据库:   {Config.DB_PATH}")
    print("=" * 50)
    app.run(host="0.0.0.0", port=Config.PORT, debug=False)
