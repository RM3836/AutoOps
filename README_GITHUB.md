# AutoOps — 企业级智能自动化运维平台

> 基于 Python + Flask + Docker + Prometheus + Grafana 的一站式服务器运维与可观测性平台

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-supported-blue.svg)](https://docker.com)
[![Prometheus](https://img.shields.io/badge/Prometheus-monitoring-orange.svg)](https://prometheus.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

AutoOps 是一个面向中小规模服务器集群的智能运维平台，覆盖 **指标采集 → 阈值告警 → 批量运维 → 安全审计 → 巡检报告** 完整闭环，并通过 Docker Compose 编排 + Prometheus/Grafana 实现容器化部署与可观测性建设。

---

## ✨ 核心能力

| 能力 | 技术实现 |
|------|----------|
| 系统监控 | `psutil` 采集 CPU/内存/磁盘/网卡/磁盘IO 五维指标，`schedule` 定时调度，前端 Chart.js 实时可视化 |
| 批量运维 | 三层方案：`Paramiko`（SSH 终端/密钥认证）→ `Fabric`（批量命令/文件分发）→ `Ansible`（系统初始化/批量用户管理） |
| 安全审计 | 日志三层检测（关键词 → 正则提取攻击源 IP → IP 聚合判定暴力破解），识别危险命令 |
| 智能告警 | 阈值超限（CPU/内存/磁盘/进程）触发邮件 + Web 双通道告警 |
| 容器化 | Dockerfile + docker-compose 编排，数据卷持久化，一键部署 |
| 可观测性 | `/metrics` 指标端点 + Prometheus 抓取 + Grafana 大盘 + 告警规则（for 1m 防抖动） |

---

## 🚀 快速开始

### 方式一：Docker Compose 一键部署（推荐）

```bash
# 克隆项目
git clone https://github.com/RM3836/AutoOps.git
cd AutoOps

# 一键构建并启动（autoops + prometheus + grafana 三服务）
docker compose up -d --build

# 查看容器状态
docker compose ps
```

启动后访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| AutoOps 面板 | http://localhost:5000 | 运维管理主界面 |
| 指标端点 | http://localhost:5000/metrics | Prometheus 抓取入口 |
| Prometheus | http://localhost:9090 | 监控指标与告警 |
| Grafana | http://localhost:3000 | 可视化大盘（初始 admin/admin123） |

### 方式二：本地 Python 运行

```bash
# Windows
python run.py

# Linux / Mac
bash shell/deploy.sh
# 或
python3 run.py
```

> `run.py` 内置防呆设计：自动检测 Python 版本、换源安装依赖、修复编码、处理端口冲突、重建损坏数据库。

---

## 📦 项目结构

```
AutoOps/
├── app.py                  # 主入口（路由、API、/metrics 端点）
├── run.py                  # 一键启动脚本（防呆设计）
├── Dockerfile              # 应用镜像构建
├── docker-compose.yml      # 三服务编排（autoops/prometheus/grafana）
├── prometheus.yml          # Prometheus 抓取配置
├── alert.rules.yml         # 告警规则
├── requirements.txt        # 依赖清单
│
├── config/                 # 配置模块（settings.py）
├── monitor/                # 系统监控（psutil + schedule）
├── remote/                 # 远程运维（Paramiko/Fabric/SSH密钥）
├── security/               # 日志安全分析
├── alert/                  # 自动告警
├── tools/                  # 运维工具箱（扫描/DNS/进程/报告）
│   └── ansible/            # Ansible Playbook（系统初始化/批量用户）
├── shell/                  # Shell 脚本（deploy.sh/monitor.sh）
├── templates/              # Web 页面模板
├── static/                 # CSS / JS
├── database/               # SQLite 建表脚本
└── docs/                   # 项目文档
```

---

## 🔍 可观测性实现说明

AutoOps 通过新增 `/metrics` 端点，将 `psutil` 实时采集的指标转换为 Prometheus 标准文本格式：

```
# HELP autoops_cpu_usage_percent 当前 CPU 使用率(%)
# TYPE autoops_cpu_usage_percent gauge
autoops_cpu_usage_percent 23.5
```

- **指标类型**：CPU/内存/磁盘/进程数用 `gauge`（瞬时值，可涨可跌），累计流量用 `counter`（只增不减）
- **抓取模型**：Prometheus 采用拉取（pull）模型，每 15 秒抓取一次 `/metrics`
- **告警收敛**：`for: 1m` 表示持续超阈值 1 分钟才触发，避免瞬时抖动误报
- **容器网络**：Prometheus 通过 Compose 服务名 `autoops:5000` 访问应用，而非 `localhost`

---

## 🛠️ 技术栈

**后端：** Python 3.9+ / Flask / psutil / Paramiko / Fabric / schedule

**批量运维：** Ansible（Playbook）/ Fabric / Paramiko

**容器与监控：** Docker / Docker Compose / Prometheus / Grafana

**前端：** Bootstrap 5 / Chart.js / 原生 JavaScript

**数据：** SQLite

---

## 📄 License

本项目采用 [MIT License](LICENSE)。
