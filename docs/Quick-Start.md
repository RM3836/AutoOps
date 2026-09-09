# AutoOps Quick Start Guide

> 5 minutes to run, 30 minutes to understand the code

## Step 1: Install Python
Download Python 3.10+ from https://www.python.org/downloads/
**Check "Add Python to PATH" during installation!**

## Step 2: Install Dependencies
Open CMD (Win+R -> cmd), run:
```
cd Desktop\AutoOps
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## Step 3: Start
```
Double-click sim-attack.bat    (generate test logs)
Double-click start.bat         (start the server)
```
Open browser: http://localhost:5000

---

## What is AutoOps?

AutoOps = Enterprise Automation Operations Platform

Your PC's CPU/Memory/Disk -> psutil collects -> Flask displays on web page
                                          |
                                   Over threshold -> Auto alert
                                   Log analysis   -> Detect attacks
                                   SSH remote     -> Execute commands
                                   Toolbox        -> Scan / Report

---

## Project Structure

```
AutoOps/
├── run.py              <- Entry point (start.bat calls this)
├── app.py              <- Flask main file (all routes & APIs)
├── config/settings.py  <- Config (port, thresholds, DB path)
│
├── monitor/            <- Monitoring module
│   ├── system_monitor.py  <- psutil collects CPU/mem/disk/net/IO
│   └── scheduler.py       <- schedule timer (every 2 seconds)
│
├── security/           <- Security module
│   └── log_analyzer.py    <- Log analysis (keywords + regex + IP aggregation)
│
├── remote/             <- SSH module
│   ├── ssh_manager.py     <- Paramiko remote connection
│   └── ssh_key.py         <- Key authentication
│
├── alert/              <- Alert module
│   └── alert_manager.py   <- Threshold check + DB + email
│
├── tools/              <- Toolbox
│   ├── ping_scan.py       <- Host alive scan
│   ├── port_scan.py       <- Parallel port scan (ThreadPoolExecutor)
│   ├── process_mgr.py     <- Process management
│   └── report_gen.py      <- Report generation (HTML/CSV)
│
├── templates/          <- HTML pages (7 files)
│   ├── base.html          <- Layout (navbar + clock + common JS)
│   ├── index.html         <- Dashboard
│   ├── server.html        <- Server details
│   ├── ssh.html           <- SSH operations
│   ├── logs.html          <- Log analysis
│   ├── alerts.html        <- Alert center
│   └── tools.html         <- Toolbox
│
├── static/js/          <- Frontend JS (7 files)
│   ├── common.js          <- Shared functions (api/escapeHtml/getBarColor)
│   ├── dashboard.js       <- Dashboard logic
│   ├── server.js          <- Server details logic
│   └── ...
│
├── database/           <- SQLite database
│   └── init.sql           <- Table creation (4 tables)
│
├── sim-attack.bat      <- Generate test logs (for demo)
└── start.bat           <- One-click start
```

---

## Core Code Quick Read

### 1. How data is collected? -> system_monitor.py
```python
import psutil
cpu = psutil.cpu_percent()           # CPU usage
mem = psutil.virtual_memory()        # Memory info
disk = psutil.disk_usage("/")        # Disk info
net = psutil.net_io_counters()       # Network traffic
```

### 2. How timer works? -> scheduler.py
```python
import schedule, threading
schedule.every(2).seconds.do(collect_and_check)  # Every 2 seconds
threading.Thread(target=run, daemon=True).start() # Background thread
```

### 3. How security analysis works? -> log_analyzer.py
```python
# Layer 1: Keyword matching
KEYWORDS = ["Failed password", "OOM", "segfault"]
# Layer 2: Regex extract IP
PATTERN = r"Failed password for .+ from (\d+\.\d+\.\d+\.\d+)"
# Layer 3: IP aggregation >= 5 times = brute force
```

### 4. How frontend calls backend? -> common.js
```javascript
const data = await api("/api/status");        // GET
const data = await api("/api/tools/ping", {   // POST
    method: "POST",
    body: JSON.stringify({hosts: ["192.168.1.1"]})
});
```

### 5. Database tables -> init.sql
```
server_status   <- Monitor data (cpu/memory/disk/time)
alerts          <- Alert records (level/module/message)
ssh_hosts       <- SSH hosts (hostname/port/username/password)
operation_logs  <- Operation logs (operator/action/target/result)
```

---

## Page <-> API Mapping

| Page | API | Backend |
|------|-----|---------|
| Dashboard | GET /api/status | monitor.collect_all() |
| Dashboard | GET /api/history | Query server_status table |
| Server | GET /api/server/info | monitor.get_server_details() |
| SSH | POST /api/ssh/exec | ssh_mgr.execute() |
| Logs | GET /api/logs/analyze | log_analyzer.analyze_logs() |
| Toolbox | POST /api/tools/portscan | port_scan.tcp_scan() |
| Toolbox | GET /api/tools/report | send_file download |

---

## How to Modify Code?

### Add a new monitor metric?
1. Edit `monitor/system_monitor.py` -> add to collect_all()
2. Edit `templates/index.html` -> add display card
3. Edit `static/js/dashboard.js` -> update DOM

### Add a new page?
1. Create `templates/xxx.html` (copy from tools.html)
2. Add route in `app.py` -> `@app.route("/xxx")`
3. Add nav link in `templates/base.html`
4. Create `static/js/xxx.js`

### Change alert thresholds?
Edit `config/settings.py`:
```python
CPU_THRESHOLD = 80.0       # Alert when CPU > 80%
MEMORY_THRESHOLD = 85.0
DISK_THRESHOLD = 90.0
```

---

## FAQ

| Problem | Solution |
|---------|----------|
| pip install slow | Use mirror: `-i https://pypi.tuna.tsinghua.edu.cn/simple` |
| Port 5000 occupied | Change PORT in config/settings.py to 8080 |
| No log data | Double-click sim-attack.bat first |
| Empty pie chart | Click "Analyze Logs" button |

---

## Tech Stack Quick Reference

| Tech | What it does | Learn at |
|------|-------------|----------|
| Flask | Web framework | flask.palletsprojects.com |
| psutil | System monitoring | psutil.readthedocs.io |
| Paramiko | SSH connection | paramiko.org |
| schedule | Timer tasks | schedule.readthedocs.io |
| SQLite | Database | docs.python.org/3/library/sqlite3 |
| Bootstrap | CSS framework | getbootstrap.com |
| Chart.js | Charts | chartjs.org |
