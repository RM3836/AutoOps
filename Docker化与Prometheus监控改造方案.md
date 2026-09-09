# AutoOps 容器化 + Prometheus 监控改造方案

> 目标：把 AutoOps 从"裸 Python 启动"改造为"Docker Compose 编排 + Prometheus 指标暴露 + Grafana 可视化 + 告警规则"，补齐云运维岗位最核心的两个缺口。
> 预计耗时：1 个半天。全部文件照抄即可，改完能如实写进简历。

---

## 一、改造前先理解：为什么要加 /metrics

你现在的监控数据流是：

```
psutil 采集 → SQLite 数据库 → Flask /api/status 接口 → 前端 Chart.js 轮询
```

问题：**Prometheus 是"拉"模型，它需要你的服务暴露一个标准的 `/metrics` 文本端点**，而你现在没有这个端点。

所以改造的**核心不是写 prometheus.yml（那只是配置），而是给 AutoOps 加一个 `/metrics` 接口**，把 psutil 采集到的 CPU/内存/磁盘实时值，转成 Prometheus 能识别的格式。

这一步做完，你才真正"接入 Prometheus"，而不是"装了个 Prometheus 在旁边空转"。这是面试时区分"真做过"和"只会装"的关键。

---

## 二、改造步骤（共 5 步，逐步照抄）

### 第 1 步：新增 `/metrics` 接口（核心）

在 `app.py` 里，找到 `# ==================== API接口 ====================` 这一行，在它**上方**插入下面这段代码。

同时文件顶部 `from flask import Flask, render_template, jsonify, request, send_file` 这一行后面，加一行 `from flask import Response`（改成从 flask 导入 Response）。

```python
# ==================== Prometheus 指标暴露 ====================
from flask import Response

def prometheus_metrics():
    """生成 Prometheus 标准文本格式的监控指标。
    Prometheus 采用拉取模型，本接口把 psutil 实时采集的指标
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
```

> 关键点：`gauge`（仪表盘，可涨可跌）用于 CPU/内存/磁盘/进程数；`counter`（计数器，只增不减）用于累计流量。这是 Prometheus 的指标类型概念，面试会被问到。

---

### 第 2 步：新增 `Dockerfile`

在 AutoOps **项目根目录**（`D:\software\zhuomian\02_项目文档\AutoOps\`）新建一个文件，命名 `Dockerfile`（无扩展名），内容：

```dockerfile
# AutoOps 容器镜像构建文件
# 基于官方 Python 3.11 精简镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 先复制依赖文件（利用 Docker 层缓存，改动代码不会重新装依赖）
COPY requirements.txt .

# 安装依赖（使用国内镜像加速）
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制整个项目
COPY . .

# 创建数据与日志目录（容器内需要持久化的目录）
RUN mkdir -p database logs data

# 暴露 Web 服务端口
EXPOSE 5000

# 容器启动命令（0.0.0.0 让容器外可访问）
CMD ["python", "app.py"]
```

> 补充：如果依赖里要加 fabric/ansible，先在 requirements.txt 里加上 `fabric>=3.0`，ansible 较重可先不加（它是控制端工具，不一定要装进被监控的容器里）。

---

### 第 3 步：新增 `docker-compose.yml`

同样在项目根目录新建，内容：

```yaml
# AutoOps 容器编排 + 监控栈
version: "3.8"

services:
  # ===== AutoOps 应用本体 =====
  autoops:
    build: .
    container_name: autoops
    ports:
      - "5000:5000"
    volumes:
      # 数据卷持久化：容器删除后数据不丢
      - autoops-db:/app/database
      - autoops-logs:/app/logs
    restart: unless-stopped

  # ===== Prometheus 监控 =====
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      # 挂载配置文件和抓取规则
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./alert.rules.yml:/etc/prometheus/alert.rules.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    restart: unless-stopped

  # ===== Grafana 可视化 =====
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123   # 初始密码，登录后改
    restart: unless-stopped

# 命名数据卷（自动创建，跨容器重启持久化）
volumes:
  autoops-db:
  autoops-logs:
  prometheus-data:
  grafana-data:
```

> 关键点：AutoOps 通过 `hostname=autoops` 被 Prometheus 抓取。在同一个 compose 网络里，服务之间用**服务名**互访，Prometheus 配置里写 `autoops:5000` 即可。

---

### 第 4 步：新增 `prometheus.yml`

项目根目录新建：

```yaml
# Prometheus 主配置
global:
  scrape_interval: 15s      # 每 15 秒抓取一次指标
  evaluation_interval: 15s  # 每 15 秒评估一次告警规则

# 加载告警规则文件
rule_files:
  - "/etc/prometheus/alert.rules.yml"

# 抓取目标
scrape_configs:
  - job_name: "autoops"
    static_configs:
      - targets: ["autoops:5000"]
    metrics_path: "/metrics"
```

> 关键点：`targets` 里写 `autoops:5000`（compose 服务名），**不是** `localhost:5000`。这是容器网络和宿主机网络的区别，面试会考。

---

### 第 5 步：新增 `alert.rules.yml`

项目根目录新建（告警规则，这是"可观测性建设"的落地点）：

```yaml
# Prometheus 告警规则
groups:
  - name: autoops-alerts
    rules:
      # CPU 使用率超过 80% 持续 1 分钟 → 告警
      - alert: HighCPUUsage
        expr: autoops_cpu_usage_percent > 80
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "CPU 使用率过高"
          description: "当前 CPU 使用率 {{ $value }}%，超过 80% 阈值"

      # 内存使用率超过 85% 持续 1 分钟 → 告警
      - alert: HighMemoryUsage
        expr: autoops_memory_usage_percent > 85
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率过高"
          description: "当前内存使用率 {{ $value }}%，超过 85% 阈值"

      # 磁盘使用率超过 90% → 告警
      - alert: HighDiskUsage
        expr: autoops_disk_usage_percent > 90
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "磁盘使用率过高"
          description: "当前磁盘使用率 {{ $value }}%，超过 90% 阈值"
```

> 关键点：`for: 1m` 表示"持续 1 分钟才触发"，避免瞬时抖动误报。这就是 SRE 里常说的"告警收敛/防抖动"，面试加分项。

---

## 三、启动与验证（照做）

```bash
# 1. 进入项目目录
cd D:\software\zhuomian\02_项目文档\AutoOps

# 2. 一键构建并启动三个容器（首次构建会自动拉镜像，需等待）
docker compose up -d --build

# 3. 查看容器状态（应该看到 autoops / prometheus / grafana 三个都是 Up）
docker compose ps

# 4. 验证指标端点（浏览器或 curl 访问，应看到文本指标）
curl http://localhost:5000/metrics
```

验证清单（全部通过才算成功）：

| 验证项 | 地址 | 预期结果 |
|---|---|---|
| AutoOps 面板 | http://localhost:5000 | 正常打开仪表盘 |
| 指标端点 | http://localhost:5000/metrics | 看到 `autoops_cpu_usage_percent` 等文本 |
| Prometheus | http://localhost:9090 | 打开后 Status→Targets，看到 autoops 是 UP |
| Grafana | http://localhost:3000 | admin/admin123 登录 |

---

## 四、Grafana 配置（5 分钟）

1. 登录 Grafana（admin / admin123）
2. **Configuration → Data Sources → Add data source → 选 Prometheus**
3. URL 填 `http://prometheus:9090`（**容器内用服务名**，不是 localhost）
4. 点 Save & Test，显示绿色成功
5. **Create → Dashboard → Add panel**，选数据源 Prometheus，在查询框输入：
   - `autoops_cpu_usage_percent`（CPU 面板）
   - `autoops_memory_usage_percent`（内存面板）
   - `autoops_disk_usage_percent`（磁盘面板）
6. 保存仪表盘，命名为 "AutoOps 监控大盘"

---

## 五、改完简历怎么加（如实写）

### 项目经历新增一条（或并入 AutoOps）

```
- 将 AutoOps 平台 Docker 化，编写 Dockerfile + docker-compose.yml，实现 Flask 应用、Prometheus、Grafana 三服务编排部署与数据卷持久化
- 新增 /metrics 指标端点（gauge/counter 类型），接入 Prometheus 采集 CPU/内存/磁盘/进程指标，Grafana 可视化大盘
- 编写 alert.rules.yml 告警规则（CPU>80%、内存>85%、磁盘>90%，for 1m 防抖动），落地"采集→可视化→告警"可观测性闭环
```

### 技术栈更新

```
DevOps: Docker、Docker Compose、Prometheus、Grafana、GitLab CI/CD、Jenkins
```

**关键：** 上面三条每一句都能在面试现场演示 + 讲出原理，这就是"可观测性建设"的完整证据，不再是"正在学习"。

---

## 六、面试可能被追问 + 标准答案（提前背）

| 问题 | 标准答法 |
|---|---|
| 为什么用 gauge 不用 counter？ | CPU/内存是瞬时值，可涨可跌，用 gauge；流量累计只增，用 counter |
| Prometheus 是推还是拉？ | 拉（pull），它主动去你的 /metrics 端点抓 |
| for: 1m 什么意思？ | 持续 1 分钟超阈值才告警，防瞬时抖动误报 |
| 为什么 targets 写 autoops:5000？ | compose 网络里用服务名互访，容器 IP 会变，服务名是稳定的 |
| 数据卷为什么挂 database？ | 容器是无状态的，删了就丢，挂卷才能持久化 SQLite 数据 |

---

## 七、注意事项（避免踩坑）

1. **Docker Desktop 的 CLI 没进 PATH**（你机器已知问题）：执行 docker 命令前先加 PATH，或在 Docker Desktop 界面里操作。
2. **首次构建可能拉镜像慢**：`prom/prometheus` 和 `grafana/grafana` 镜像较大，用你已配置的镜像加速 `https://docker.1ms.run`。
3. **`/metrics` 里 `monitor.collect_all()` 每次会 sleep 0.5 秒**（因为 `cpu_percent(interval=0.5)`），Prometheus 抓取会稍慢，属正常现象。
4. **Windows 下 SQLite 路径**：容器内是 Linux 环境，`Config.BASE_DIR` 用 `os.path.abspath` 能自动适配 `/app`，无需改代码。
5. **ansible 不建议装进容器**：它是"控制端"工具，装在宿主机（或单独的 ansible 容器）更合理，装进被监控的 Flask 容器里没意义，面试反而会被问为什么。
