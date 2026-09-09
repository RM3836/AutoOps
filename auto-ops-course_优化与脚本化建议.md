# auto-ops-course 优化与日常脚本化建议

> 分析对象：`RM3836/auto-ops-course`（自动化运维技术课程代码）
> 分析时间：2026-09-09
> 结论定位：课程代码教学价值完整，但距离「日常可用的运维工具」存在平台绑定、凭证明文、硬编码路径三类差距。

---

## 一、总体评价

| 维度 | 现状 | 评级 |
|------|------|------|
| 技术栈覆盖 | Shell/Python/paramiko/fabric/Ansible/scapy 八模块齐全 | 优秀 |
| 教学价值 | 每模块聚焦一个知识点，注释充分 | 优秀 |
| 工程化程度 | 无参数化、无配置外置、无单元测试 | 偏弱 |
| 跨平台能力 | 大量硬编码 `/proc`、`/dev/null`、`sed -i` | 仅限 Linux |
| 安全性 | 密码/授权码明文写死 | 有风险 |

**一句话结论**：这是合格的课程作业，但要变成「日常能反复使用的脚本」，需要做三件事——**平台解耦、配置外置、参数化封装**。

---

## 二、按优先级排序的优化点

### P0 — 安全与凭据（必须改）

1. **`06batch/paramiko_pwd.py`**：密码 `abc123` 明文写死在代码里。
   - 改为从环境变量或配置文件读取：`os.getenv('SSH_PASSWORD')`。
   - 迁移到 `paramiko_key.py`（密钥认证），密码认证仅保留为示例。

2. **`04log/email_send.py`**：163 邮箱授权码明文。
   - 改为 `os.getenv('MAIL_PASS')`，并补上 `.gitignore` 防止误提交。
   - 收件人、SMTP 主机改为参数或配置文件。

3. **`08comp/pwd_file`、`user_pwd.yml`**：Ansible 密码文件裸存。
   - 至少补 `.gitignore`；推荐改用 `ansible-vault encrypt`。

### P1 — 平台与路径硬编码（日常使用最大障碍）

4. **`01start/sys_mon.py` + `sys_mon.sh`**：直接读 `/proc/stat`、`/proc/meminfo`，Windows 无法运行。
   - 统一改用 `psutil`（`02sysmon/sysinfo_bypsutil.py` 已经实现了跨平台版本），弃用 `/proc` 直读方案。

5. **`02sysmon/webmon_bypycurl.py`**：写死 `/dev/null` 和相对路径 `head.txt`。
   - Windows 下 `/dev/null` 不存在，改为 `os.devnull`；输出文件改到可配置目录。

6. **`02sysmon/baknewfile_bywatchdog.py`**：备份目标 `/bak/` 硬编码，且 `cp` 命令可注入。
   - 目标目录改为命令行参数；`cp` 改为 `shutil.copy2`（保留时间戳），避免 shell 拼接。

7. **`01start/shell/jdk_install.sh`**：`mv /usr/lib/jvm/jdk-17.0.2` 版本号写死。
   - 改为 `$java_tar` 解压后的实际目录名通配匹配（`jdk-*`）。

### P2 — 健壮性与代码质量

8. **`03file/cmp_dirs.py`**：`filecmp.dircmp` 有 `common_files`（同名同内容）未统计，结论不完整。
   - 补充 `common_files` 分类，输出「一致/不一致/独有」三类完整对比。

9. **`07net/dns_rslv.py`**：`except Exception as e` 直接 print，无类型区分，NS 记录打印写错变量（打印的是 `m.to_text()` 而非 `n`）。
   - 区分 `dns.resolver.NoAnswer` / `NXDOMAIN` / `NoNameservers`；修正 NS 记录遍历。

10. **`02sysmon/killproc_bypsutil.py`**：进程名精确匹配，实际常用模糊匹配；跨平台 `p.name()` 需处理 `NoSuchProcess`。
    - 加 `psutil.NoSuchProcess` 捕获，支持子串匹配。

11. **`03file/diff_files.py`**：无编码参数 `open(filename, 'r')`，Windows 默认 GBK 读 UTF-8 文件会乱码。
    - 加 `encoding='utf-8', errors='ignore'`。

12. **`06batch/*` 系列**：`fabric` 已停止维护（`fabric` 1.x vs 2.x API 完全不同），README 里的依赖安装没标版本。
    - 明确 `fabric==1.14.1`（对应 `from fabric.api import` 旧写法），或迁移到 `fabric2`/`paramiko`。

---

## 三、可直接做成日常工具的脚本清单

以下脚本改造后可跨平台、参数化、反复使用，适合你日常运维/学习场景：

| 脚本 | 日常用途 | 改造要点 |
|------|----------|----------|
| `sysinfo_bypsutil.py` | 一键看本机 CPU/内存/磁盘/网络 | 已跨平台，仅需去掉 `psutil.disk_io_counters()` 在部分环境的异常 |
| `host_batchPing.py` | 批量探测内网设备在线状态 | 加 `argparse` 指定主机文件；Windows 下 `ping -n 1` |
| `killproc_bypsutil.py` | 批量杀进程（如清理卡死进程） | 加子串匹配 + 确认交互 + 白名单保护 |
| `webmon_bypycurl.py` | 网站/接口健康检测 | 改用 `requests`，支持多 URL 列表 + 超时告警 |
| `cmp_dirs.py` | 对比两个目录差异（备份校验） | 补 `common_files`，输出结构化结果 |
| `dns_rslv.py` | 域名解析诊断 | 补 A/AAAA/CNAME/MX/NS/TXT 全记录 + 异常分类 |
| `sysinfo_log_alert.py` | 定时监控 + 邮件/微信告警 | 配置外置 + 阈值参数化 + 可选钉钉/企业微信 webhook |

### 推荐优先落地的 3 个「整合脚本」

**1. 系统信息速览 `ops_sysinfo`**
- 合并 `sysinfo_bypsutil.py` 的采集能力，输出彩色表格（CPU/内存/磁盘/网络/进程 TOP5）。
- 跨平台（Windows/Linux 通吃），是你日常最常用的一个。

**2. 批量主机探测 `ops_ping`**
- 整合 `host_batchPing.py`，`argparse` 传入主机文件，支持 `-c` 次数、`-t` 超时、并发（`concurrent.futures`）。
- Windows 自动切换 `ping -n`，Linux 用 `ping -c`。

**3. 目录差异对比 `ops_dircmp`**
- 整合 `cmp_dirs.py` + `diff_files.py`，输出完整对比 + 可选生成 HTML 差异报告。
- 用于备份校验、代码同步前检查。

---

## 四、跨平台适配清单（Windows 优先）

| 原实现 | Linux 依赖 | Windows 替代 |
|--------|-----------|--------------|
| `/proc/stat`、`/proc/meminfo` | 读 proc 文件系统 | `psutil.cpu_percent()` / `psutil.virtual_memory()` |
| `/proc/net/dev` | 读 proc | `psutil.net_io_counters()` |
| `/dev/null` | 空设备 | `os.devnull` |
| `ping -c1 -W1` | 参数 | `ping -n 1 -w 1000` |
| `sed -i`、`awk`、`groupadd` | GNU 工具 | PowerShell 等价命令 / Python 实现 |
| `cp`、`free -m` | 命令 | `shutil` / `psutil` |

---

## 五、建议的下一步行动

1. **短期（1-2 天）**：先落地上文 3 个整合脚本（`ops_sysinfo` / `ops_ping` / `ops_dircmp`），这几个不依赖 Linux，能立刻用在你日常 Windows 环境。
2. **中期**：把 P0 安全项改掉（凭据外置 + `.gitignore`），并给 README 标注依赖版本。
3. **长期**：如果继续深挖，可把这套课程代码升级成你的 `ensp-helper` 或 `security-toolkit` 项目里的「网络自动化」子模块，正好贴合你网络安全测试 / 网络自动化的求职方向。

---

## 附：仓库文件速查（快速定位）

```
01start/   Shell/Python 入门（批量 ping、系统监控、用户管理、JDK 安装）
02sysmon/   psutil/watchdog/pycurl/APScheduler 监控
03file/     JSON/YAML/XML/INI 读写、目录/文件对比
04log/      logging + smtplib 邮件告警
05report/   matplotlib/Dash/openpyxl 可视化
06batch/    paramiko/fabric SSH 批量管理
07net/      scapy/nmap/dns 网络工具
08comp/     Ansible Playbook/Role 综合实战
```
