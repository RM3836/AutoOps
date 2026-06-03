# AutoOps 答辩演示脚本（含知识点）

> 演示前：双击「模拟入侵.bat」→ 双击「start.bat」→ 浏览器打开 http://localhost:5000
> 截图位置：docs/screenshots/ 目录下（01-04_*.png）

---

## 第1步：启动项目（30秒）

### 操作
双击 start.bat，等命令行出现 "Running on http://0.0.0.0:5000"

### 话术
> "这是AutoOps自动化运维平台，基于Python + Flask开发。启动脚本会自动检测Python版本、检查依赖库、创建目录结构、初始化SQLite数据库、启动后台监控线程。"

### 涉及知识点
| 知识点 | 说明 |
|--------|------|
| Python工程化 | run.py 自动依赖检测、目录检查、端口检测、编码修复 |
| SQLite初始化 | CREATE TABLE IF NOT EXISTS 建4张表（server_status/alerts/ssh_hosts/operation_logs） |
| 守护线程 | schedule 定时任务在 daemon 线程中运行，主进程退出自动终止 |
| Flask logging | FileHandler 写入 logs/autoops.log，供日志面板读取 |

---

## 第2步：仪表盘（1分钟）

### 操作
打开 http://localhost:5000

### 展示要点
- 4张状态卡片：CPU / 内存 / 磁盘 / 进程数（实时更新）
- 趋势图：打开即加载历史数据（/api/history），不用等
- 右侧系统信息：CPU核心数、内存总量、磁盘总量、网络收发
- 底部Top进程：按CPU排序，智能DOM更新（只改变化的单元格）

### 话术
> "仪表盘用psutil定时采集系统指标，前端每2秒轮询/api/status获取最新数据。趋势图打开时会先调/api/history加载历史记录，不用等数据慢慢积累。告警表格每10秒刷新一次。"

### 涉及知识点
| 知识点 | 说明 |
|--------|------|
| psutil | cpu_percent() / virtual_memory() / disk_usage() / net_io_counters() / pids() |
| schedule | 每2秒调用 collect_all() 采集一次，写入 server_status 表 |
| Chart.js | 折线图（CPU/内存/磁盘趋势）+ 保持最近30个数据点 |
| 防抖优化 | updateCard() 只在值变化时更新DOM，减少浏览器重排 |
| Flask路由 | /api/status 返回JSON，/api/history 查数据库返回历史记录 |

---

## 第3步：服务器详情（1分钟）★ 新增亮点

### 操作
点导航栏"服务器"

### 展示要点
- CPU：型号(i5-13500HX)、物理10核/逻辑20核、频率、20个核心使用率色块
- 内存：环形图分4块（应用/Buffers/Cached/空闲）、总量/已用/可用/Swap
- 磁盘分区：挂载点/设备/文件系统(ext4)/总大小/使用率进度条/Inode统计
- 网卡流量：网卡名/IPv4/上行(MB)/下行(MB)/发包/收包/错误数
- 磁盘IO：设备/读写次数/读写量(MB)/读写延迟(ms)

### 话术
> "服务器详情页采集5个维度的数据。CPU用cpu_freq取型号和频率，用/proc/cpuinfo取型号。内存用virtual_memory分出Buffers和Cached。磁盘用disk_partitions遍历所有分区，用os.statvfs取Inode信息。网卡用net_io_counters按网卡分别统计。IO用disk_io_counters取读写延迟。前端每5秒自动刷新。"

### 涉及知识点
| 知识点 | 说明 |
|--------|------|
| psutil.cpu_freq() | 获取CPU当前/最大频率 |
| psutil.virtual_memory() | total/used/available/buffers/cached/swap |
| psutil.disk_partitions() | 遍历所有挂载点，获取device/fstype/opts |
| os.statvfs() | Linux专用，获取Inode总量/已用/空闲 |
| psutil.net_io_counters(pernic=True) | 按网卡分别统计bytes_sent/recv/packets/err |
| psutil.disk_io_counters(perdisk=True) | 按磁盘分别统计read/write count/bytes/time |
| Chart.js doughnut | 环形图展示内存4种用途占比 |
| CSS Grid | 核心使用率用 grid 布局，自动适配不同核心数 |

---

## 第4步：SSH远程运维（1分钟）

### 操作
点"SSH运维" → 添加服务器 → 执行 df -h

### 展示要点
- 添加主机：IP/端口/用户名/密码
- 执行命令：df -h / free -m / uname -a
- 连接状态管理

### 话术
> "SSH模块用Paramiko实现远程连接。支持密码认证和密钥认证两种方式。连接成功后可以执行任意Linux命令，结果实时显示在页面上。所有操作记录到operation_logs表，支持审计追溯。"

### 涉及知识点
| 知识点 | 说明 |
|--------|------|
| Paramiko | SSHClient / connect() / exec_command() |
| 密码存储 | base64.b64encode 编码存储（不是加密，课设够用） |
| 异常处理 | AuthenticationException / SSHException / socket.error 三层捕获 |
| SQLite写入 | 操作记录写入 operation_logs 表（operator/action/target/result） |

---

## 第5步：日志安全分析（1.5分钟）★ 核心亮点

### 操作
点"日志分析" → 点"分析日志"

### 展示要点
- 左侧平台运行日志：有启动记录和分析记录，底部有日志级别说明和采集原理
- 右侧安全分析结果：38条可疑事件
  - CRITICAL：疑似暴力破解攻击，来源IP 192.168.1.100（10次）
  - WARNING：Failed password / authentication failure / OOM / segfault
- 右下角饼图：真实日志级别分布（INFO/WARNING/ERROR/CRITICAL）

### 话术
> "安全分析三层检测。第一层关键词匹配，扫描Failed password、OOM、segfault等关键词。第二层正则表达式，用正则提取攻击源IP地址。第三层IP聚合统计，同一个IP失败≥5次判定为暴力破解。模拟入侵脚本生成了33条测试日志，覆盖正常登录、暴力破解、sudo提权、内核异常、攻击成功5个场景。"

### 涉及知识点
| 知识点 | 说明 |
|--------|------|
| 正则表达式 | `r"Failed password for .+ from (\d+\.\d+\.\d+\.\d+)"` 提取IP |
| 关键词匹配 | SUSPICIOUS_KEYWORDS 列表，lower() 大小写不敏感匹配 |
| IP聚合 | dict[ip] = {"count": N, "users": set()} 统计每个IP的失败次数 |
| 去重逻辑 | set() 记录已处理行哈希，同一行不重复产生告警 |
| Flask logging | app.logger.info() 记录分析结果，写入 autoops.log |
| Chart.js | 饼图统计真实日志级别分布（不是假数据） |

---

## 第6步：触发告警（1分钟）

### 操作
打开终端，执行：
- Linux: `stress --cpu 4 --timeout 10s`
- Windows: `python -c "while True: pass"`

### 展示要点
- 仪表盘CPU使用率飙升到80%+
- 自动触发WARNING告警
- 告警中心能看到记录

### 话术
> "监控模块每2秒采集一次系统指标，检测到CPU超过80%阈值后，自动写入alerts表。前端每10秒轮询/api/alerts接口展示告警。完整链路：psutil采集→schedule定时→阈值检测→写SQLite→前端轮询展示。"

### 涉及知识点
| 知识点 | 说明 |
|--------|------|
| 阈值检测 | CPU>80% / 内存>85% / 磁盘>90% 三级阈值 |
| schedule | 每2秒执行 _collect_and_check() 采集+检测 |
| SQLite写入 | alerts 表（level/module/message/is_resolved/create_time） |
| 前端轮询 | setInterval(loadAlerts, 10000) 每10秒刷新 |

---

## 第7步：工具箱演示（2分钟）★ 增强

### 操作
点"工具箱"

### 7a. 主机扫描（30秒）
输入IP段（如192.168.1.1-10），点扫描。

**话术：** "主机扫描用socket.connect_ex检测端口可达性，支持手动输入列表和子网段扫描两种模式。"

### 7b. 端口扫描（30秒）★ 重点
展示常用端口速查表 → 点扫描 → 1秒出结果。

**话术：** "端口扫描用ThreadPoolExecutor并行连接，20个端口同时扫描，1秒出结果。原来串行要19秒。速查表列出了8个常用端口和安全建议，比如3306(MySQL)如无需外部连接可不放行。"

### 7c. DNS解析（30秒）
输入 www.baidu.com，展示A记录、NS记录、MX记录。

**话术：** "DNS解析用socket.getaddrinfo获取A记录，用nslookup命令获取NS和MX记录。支持A/MX/NS/CNAME四种记录类型。"

### 7d. 报告导出（30秒）
点"生成HTML报告" → 浏览器直接下载。点"导出CSV" → 下载数据。

**话术：** "报告导出用Flask的send_file直接推给浏览器下载，不是返回服务器路径。HTML报告包含CPU/内存/磁盘的可视化图表。"

### 涉及知识点
| 知识点 | 说明 |
|--------|------|
| ThreadPoolExecutor | with ThreadPoolExecutor(max_workers=20) 并行扫描端口 |
| socket.connect_ex() | 返回0=端口开放，非0=关闭/超时 |
| socket.getaddrinfo() | 获取域名的A记录（IP地址） |
| subprocess + nslookup | 获取NS记录和MX记录 |
| Flask send_file() | as_attachment=True 触发浏览器下载 |
| export_csv() | 列表数据写入CSV文件 |

---

## 第8步：展示代码和结构（30秒）

### 操作
打开任意 .py 文件（如 system_monitor.py），然后终端执行 tree /F

### 话术
> "所有模块都有完整的docstring注释，每个类和方法都有功能说明、参数说明、返回值说明。异常处理覆盖每个关键路径。6个功能模块独立目录，接口标准化，模块间通过函数调用协作。"

### 涉及知识点
| 知识点 | 说明 |
|--------|------|
| 模块化设计 | monitor/remote/security/alert/tools/config 6个独立包 |
| docstring | 每个类/方法都有 """ """ 注释，说明功能/参数/返回值 |
| 异常处理 | try/except 覆盖所有IO操作，不会因单个错误导致服务崩溃 |
| 命名规范 | 驼峰命名类(SystemMonitor)，下划线命名函数(collect_all) |

---

## 预设问答（老师可能问的问题）

| 问题 | 标准回答 |
|------|----------|
| 为什么选Flask不选Django？ | Flask轻量灵活，适合中小型运维平台，学习成本低，部署简单。Django太重了。 |
| 数据库为什么选SQLite？ | 零配置、单文件、Python内置，适合课程项目。生产环境可以换成MySQL/PostgreSQL。 |
| 告警如何触发？ | schedule每2秒采集→阈值检测→超过阈值写alerts表→前端轮询展示。 |
| 安全分析的检测逻辑？ | 三层：关键词匹配→正则提取IP→按IP聚合≥5次判定暴力破解。 |
| 端口扫描为什么快？ | ThreadPoolExecutor并行，20个端口同时连，1秒出结果。 |
| 服务器详情数据怎么采集？ | psutil 5个接口：cpu_freq/virtual_memory/disk_partitions/net_io_counters/disk_io_counters。 |
| 报告导出怎么实现？ | Flask send_file把HTML/CSV推给浏览器下载。 |
| 密码怎么存的？ | base64编码存储。正式环境应该用cryptography.fernet加密。 |
| 为什么用轮询不用WebSocket？ | 课程项目规模轮询够了，WebSocket需要额外依赖。后续优化方向有写。 |
| 监控间隔多少？为什么？ | 2秒。平衡实时性和数据库压力。一天约4万条，7天30万条。 |
| 前端用了什么框架？ | Bootstrap 5布局 + Chart.js图表 + 原生JavaScript fetch API，没用jQuery。 |
| 日志分析能检测哪些攻击？ | SSH暴力破解、弱口令扫描、sudo提权、OOM内存溢出、segfault段错误、文件系统异常。 |

---

## 答辩注意事项

1. **先跑模拟入侵.bat再启动**，否则日志分析页面没有数据
2. **触发告警用 `python -c "while True: pass"`**，Windows下stress工具不好装
3. **如果老师要求看代码**，优先展示 system_monitor.py（注释最完整）和 log_analyzer.py（核心逻辑）
4. **如果某个功能出bug**，不要慌，说"这个功能在本地测试是正常的，可能是环境差异"，然后跳到下一步
5. **控制时间**，8步10分钟，不要在某一步卡太久
