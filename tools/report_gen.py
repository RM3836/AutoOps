"""
报告生成器 (加分项 - 来自实验03/05)
功能: HTML巡检报告 / CSV导出 / SQLite导出
"""
import os
import csv
import sqlite3
import json
from datetime import datetime


def export_csv(data_list, filepath):
    """导出数据到CSV
    data_list: [{"cpu": 45.2, "memory": 60.1, ...}, ...]
    """
    if not data_list:
        return False
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=data_list[0].keys())
        writer.writeheader()
        writer.writerows(data_list)
    return filepath


def export_sqlite(data_list, db_path, table="server_status"):
    """导出数据到SQLite"""
    if not data_list:
        return False
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    cols = data_list[0].keys()
    col_defs = ", ".join([f"{k} REAL" for k in cols])
    c.execute(f"CREATE TABLE IF NOT EXISTS {table} (id INTEGER PRIMARY KEY AUTOINCREMENT, {col_defs})")
    placeholders = ", ".join(["?" for _ in cols])
    for row in data_list:
        c.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})",
                  [row[k] for k in cols])
    conn.commit()
    conn.close()
    return db_path


def generate_html_report(data, filepath="report.html"):
    """生成HTML巡检报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>AutoOps 巡检报告</title>
<style>
body {{ font-family: "Microsoft YaHei", sans-serif; margin: 40px; background: #f5f5f5; }}
.container {{ max-width: 900px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
h1 {{ color: #0f3460; border-bottom: 3px solid #00d4aa; padding-bottom: 10px; }}
h2 {{ color: #16213e; margin-top: 30px; }}
table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
th {{ background: #0f3460; color: white; }}
.warning {{ color: #d29922; font-weight: bold; }}
.critical {{ color: #da3633; font-weight: bold; }}
.good {{ color: #00d4aa; font-weight: bold; }}
.footer {{ margin-top: 30px; color: #888; font-size: 12px; text-align: center; }}
</style></head><body><div class="container">
<h1>⚡ AutoOps 运维巡检报告</h1>
<p><strong>巡检时间:</strong> {now}</p>
<table>
<tr><th>指标</th><th>当前值</th><th>状态</th></tr>"""
    for key, val in data.items():
        if isinstance(val, (int, float)) and key in ["cpu", "memory", "disk"]:
            if val > 90:
                status = '<span class="critical">严重</span>'
            elif val > 70:
                status = '<span class="warning">警告</span>'
            else:
                status = '<span class="good">正常</span>'
            html += f"<tr><td>{key.upper()}</td><td>{val}%</td><td>{status}</td></tr>"
        elif isinstance(val, (int, float)):
            html += f"<tr><td>{key}</td><td>{val}</td><td>--</td></tr>"
    html += "</table>"
    html += f'<div class="footer">AutoOps 自动化运维管理系统 | 生成时间: {now}</div>'
    html += "</div></body></html>"
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return filepath
