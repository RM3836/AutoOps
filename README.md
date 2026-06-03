# AutoOps 企业级智能自动化运维平台

> 基于 Python + Flask + Paramiko 的企业服务器智能运维与安全监控系统

作者：YURM | GitHub: [YURM](https://github.com/RM3836)

---

## 一键启动（推荐）

### Windows 用户

**方式1：双击启动（最简单，推荐）**
```
双击 start.bat
```

**方式2：命令行启动**
```cmd
cd AutoOps
python run.py
```

### Linux / Mac 用户

```bash
cd /path/to/AutoOps
chmod +x shell/deploy.sh
bash shell/deploy.sh
```

或直接：
```bash
python3 run.py
```

### 启动后访问

浏览器打开：http://localhost:5000

---

## 防呆设计（自动修复）

本项目内置了完善的防呆设计，自动处理常见问题：

### 自动检测与修复

| 问题 | 自动处理方式 |
|------|-------------|
| **Python 未安装** | 提示下载地址 |
| **Python 版本过低** | 提示升级到 3.9+ |
| **目录缺失** | 自动创建 database/logs/data 目录 |
| **虚拟环境不存在** | 自动创建 venv |
| **pip 版本过低** | 自动升级 pip |
| **pip 下载慢** | 自动配置清华镜像源 |
| **依赖安装失败** | 自动换源重试（清华 → 阿里 → 中科大） |
| **requirements.txt 编码错误** | 自动检测并修复（GBK → UTF-8） |
| **数据库损坏** | 自动备份并重建 |
| **SQL 文件语法错误** | 自动过滤注释行 |
| **端口被占用** | 自动查找可用端口 |
| **Windows 编码问题** | 自动设置 UTF-8 环境 |

### 错误恢复流程

```
安装失败 → 尝试默认源 → 尝试清华源 → 尝试阿里源 → 尝试中科大源 → 逐个安装 → 提示手动命令
```

---

## 功能模块

| 模块 | 功能 | 核心技术 |
|------|------|----------|
| 系统监控 | CPU / 内存 / 磁盘 / 网络 / 进程 实时监控 | psutil |
| 服务器详情 | CPU型号核心 / 内存Buffers-Cache / 磁盘分区Inode / 网卡流量 / 磁盘IO | psutil + os.statvfs |
| SSH远程运维 | SSH登录 / 密钥认证 / 命令执行 / SFTP | Paramiko |
| 日志分析 | 日志采集 / 关键词匹配 / 正则提取IP / 暴力破解检测 | logging + re |
| 自动告警 | 阈值告警 / 邮件通知 / 日志记录 / Web提示 | schedule |
| Web可视化 | 仪表盘 / 服务器详情 / 实时图表 / 暗色主题 | Flask + Chart.js |
| 运维工具箱 | 主机扫描 / 并行端口扫描 / DNS(A-MX-NS) / 进程管理 / 报告下载 | socket + ThreadPoolExecutor |

---

## 项目目录

```
AutoOps/
├── start.bat               # Windows 一键启动（双击运行，防呆设计）
├── app.py                  # 主入口（路由、API）
├── run.py                  # 启动脚本（自动检查依赖，防呆设计）
├── requirements.txt        # 依赖清单
│
├── config/                 # 配置模块
│   └── settings.py         # 全局配置
│
├── monitor/                # 系统监控模块 (psutil)
├── remote/                 # SSH远程运维模块 (Paramiko)
├── security/               # 日志分析模块
├── alert/                  # 自动告警模块
├── tools/                  # 运维工具箱
│   ├── ping_scan.py        # 批量主机检测
│   ├── port_scan.py        # 端口扫描
│   ├── process_mgr.py      # 进程管理
│   └── report_gen.py       # 报告生成
│
├── templates/              # Web页面模板
├── static/                 # CSS / JS
├── database/               # 数据库SQL
├── shell/                  # Linux运维脚本
│   └── deploy.sh           # Linux 一键部署脚本
└── docs/                   # 项目文档
```

---

## 技术栈

**后端：** Python 3.9+ / Flask / SQLite / psutil / Paramiko / schedule

**前端：** Bootstrap 5 / Chart.js / 原生JavaScript fetch API

---

## 常见问题

### Q: 双击 start.bat 闪退？
A: 右键选择"以管理员身份运行"，或在命令行中运行查看错误信息

### Q: 提示 "No module named xxx"？
A: 运行 `python run.py` 会自动安装缺失依赖，如果失败会提示手动安装命令

### Q: pip install 很慢？
A: 脚本会自动配置清华镜像源，如果仍然慢，手动执行：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: 端口 5000 被占用？
A: 脚本会自动检测并提示使用其他端口，或修改 `config/settings.py` 中的 PORT 配置

### Q: Windows 编码报错？
A: 双击 `start.bat` 启动，已自动处理编码问题

### Q: 数据库初始化失败？
A: 脚本会自动备份损坏的数据库并重建，如果 SQL 文件有问题会创建最小化数据库

---

## 答辩演示流程（10分钟）

1. **启动项目**（30秒）：双击「模拟入侵.bat」→ 双击 `start.bat`
2. **仪表盘**（1分钟）：CPU/内存/磁盘实时监控 + 趋势图 + 进程列表
3. **服务器详情**（1分钟）：CPU型号20核 / 内存环形图 / 磁盘分区Inode / 网卡流量 / 磁盘IO
4. **SSH运维**（1分钟）：添加服务器 → 执行命令
5. **日志安全分析**（1.5分钟）：38条告警 / IP聚合 / 暴力破解检测 / 饼图统计
6. **触发告警**（1分钟）：CPU高占用 → 自动弹出告警
7. **工具箱**（2分钟）：主机扫描 / 并行端口扫描 / DNS解析 / 报告下载
8. **展示代码**（30秒）：docstring注释 + 模块化结构

---

## 运行验证与截图命令

```cmd
cd AutoOps
双击 模拟入侵.bat
python run.py
```

启动成功后访问 `http://localhost:5000`，建议依次截图：

```text
http://localhost:5000/         仪表盘
http://localhost:5000/server   服务器详情
http://localhost:5000/ssh      SSH远程运维
http://localhost:5000/logs     日志分析
http://localhost:5000/alerts   告警中心
http://localhost:5000/tools    运维工具箱
```

核心验收点：`psutil` 5维度采集系统指标，`Paramiko` 执行 SSH 命令，`schedule` 后台定时采集并触发告警，`SQLite` 保存监控、告警、SSH主机和操作日志，`ThreadPoolExecutor` 并行端口扫描，`Flask logging` 运行日志文件记录。

---

## 更新日志

- 2026-06-01: 添加防呆设计，自动换源，自动修复编码问题
- 2026-06-02: 修复 SQLite 初始化脚本，接入 schedule 后台定时任务
- 2026-05-31: 添加一键启动脚本
- 2026-05-25: 初始化项目，完成基础框架
