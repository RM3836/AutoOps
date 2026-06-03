# AutoOps 部署文档

## 一、环境要求

### 硬件要求
- CPU：1核及以上
- 内存：512MB及以上
- 磁盘：1GB可用空间

### 软件要求
- 操作系统：Windows 10/11、CentOS 7+、Ubuntu 20.04+
- Python：3.10及以上版本
- 浏览器：Chrome / Edge / Firefox

### 依赖包清单
| 包名 | 版本 | 用途 |
|------|------|------|
| flask | >=3.0.0 | Web框架 |
| psutil | >=5.9.0 | 系统监控 |
| paramiko | >=3.4.0 | SSH远程运维 |
| schedule | >=1.2.0 | 定时任务 |

## 二、Windows 部署步骤

```cmd
# 1. 进入项目目录（改实际路径）
cd AutoOps

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 一键启动
python run.py
```

> 提示：如果 `5000` 端口被占用，`run.py` 会自动切换到可用端口并在启动日志中提示实际访问地址。

## 三、Linux (CentOS/Ubuntu) 部署步骤

```bash
# 1. 安装Python3
sudo yum install -y python3 python3-pip    # CentOS
sudo apt install -y python3 python3-pip    # Ubuntu

# 2. 进入项目目录
cd /opt/AutoOps

# 3. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 一键启动
python3 run.py
```

## 四、VMware 虚拟机部署

1. 下载 CentOS 7 ISO 镜像
2. VMware 创建虚拟机（2GB内存、20GB磁盘、NAT网络）
3. 安装系统后配置网络：`vi /etc/sysconfig/network-scripts/ifcfg-ens33`，设置 `ONBOOT=yes`
4. 安装Python3：`yum install -y python3 python3-pip`
5. 上传项目文件（scp或共享文件夹）
6. 按上述Linux步骤部署

## 五、后台运行（Linux生产环境）

```bash
# 方式1：nohup
nohup python3 run.py > /dev/null 2>&1 &

# 方式2：systemd 服务
sudo vi /etc/systemd/system/autoops.service
```

```ini
[Unit]
Description=AutoOps Platform
After=network.target

[Service]
WorkingDirectory=/opt/AutoOps
ExecStart=/opt/AutoOps/venv/bin/python3 run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable autoops
sudo systemctl start autoops
sudo systemctl status autoops
```

## 六、验证部署成功

1. **检查服务状态**：终端显示 `Running on http://0.0.0.0:5000`，如果 5000 被占用则显示自动切换后的端口
2. **健康检查**：浏览器或 `curl http://127.0.0.1:端口号/api/health`，返回 `status=ok`
3. **本机访问**：浏览器打开启动日志里显示的地址，看到暗色仪表盘
4. **局域网访问**：浏览器打开 `http://服务器IP:端口号`
5. **功能验证**：
   （1） 验证告警中心
  告警阈值：
  - CPU > 80%
  - 内存 > 85%
  - 磁盘 > 90%
  - 
  在虚拟机里制造高负载：
   简单方法（不用安装工具）：
  python3 -c "import time; [i*i for i in range(10000000)]"

  # 验证内存高负载
  # 安装 stress 压力测试工具
  sudo dnf install -y stress
  # 制造 CPU 高负载（4核全开，持续60秒）
  stress --cpu 4 --timeout 60

  等待 2-10 秒后，刷新告警中心页面 `http://服务器IP:端口号/alerts`
  应该能看到 CPU使用率过高 的告警。
  ---

  
   - 仪表盘数据正常刷新
   - SSH页面可添加主机
   - 日志页面可查看日志
   - 工具箱可执行扫描

## 七、验收截图清单

启动项目：

```cmd
cd AutoOps
python run.py
```

按下面页面逐一截图：

| 页面 | 地址 | 截图重点 |
|------|------|----------|
| 仪表盘 | `http://localhost:5000/` | CPU/内存/磁盘、趋势图、Top进程 |
| 服务器详情 | `http://localhost:5000/server` | CPU型号核心、内存环形图、磁盘分区Inode、网卡流量、磁盘IO |
| SSH运维 | `http://localhost:5000/ssh` | 主机列表、命令输入、执行结果 |
| 日志分析 | `http://localhost:5000/logs` | 平台日志、安全分析结果、日志统计饼图 |
| 告警中心 | `http://localhost:5000/alerts` | 告警统计、告警记录 |
| 工具箱 | `http://localhost:5000/tools` | 主机扫描、并行端口扫描、DNS解析、报告下载 |

代码验收命令：

```cmd
python -B -m py_compile run.py app.py monitor\system_monitor.py monitor\scheduler.py remote\ssh_manager.py alert\alert_manager.py
```
