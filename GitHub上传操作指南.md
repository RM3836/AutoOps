# AutoOps 上传 GitHub 操作指南

> 从零把 AutoOps 推送到 GitHub，作为你的旗舰开源项目。照做即可。

---

## 一、上传前的准备（已完成 ✅）

以下工作我已帮你做完：

| 项目 | 状态 | 说明 |
|---|---|---|
| `Dockerfile` | ✅ | 应用镜像构建 |
| `docker-compose.yml` | ✅ | 三服务编排 |
| `prometheus.yml` | ✅ | 监控抓取配置 |
| `alert.rules.yml` | ✅ | 告警规则 |
| `/metrics` 端点 | ✅ | app.py 已加 Prometheus 指标接口 |
| `.dockerignore` | ✅ | 排除 venv/数据库/日志 |
| `LICENSE` | ✅ | MIT 协议 |
| `README_GITHUB.md` | ✅ | 旗舰版 README |
| 明文密码清理 | ✅ | `batch_users.yml` 明文密码已改为变量 |

---

## 二、上传步骤（照做）

### 第 1 步：确认 git 配置

```bash
git config --global user.name "RM3836"
git config --global user.email "team3836@foxmail.com"
```

> 注意：你的 GitHub 提交邮箱是 `team3836@foxmail.com`（不是 steam3836@foxmail.com），确保一致，否则提交记录不归到你账号。

### 第 2 步：初始化仓库并提交

```bash
cd D:\software\zhuomian\02_项目文档\AutoOps

# 初始化 git 仓库
git init

# 添加所有文件（.gitignore 已排除 venv/数据库/日志）
git add .

# 查看将要提交的文件，确认没有敏感信息
git status

# 首次提交
git commit -m "feat: AutoOps 智能自动化运维平台（Docker + Prometheus + Grafana）"
```

### 第 3 步：创建 GitHub 远程仓库

**方法一：用 gh 命令（推荐）**

```bash
# 创建私有或公开仓库（建议公开，作为作品集展示）
gh repo create AutoOps --public --source=. --push
```

**方法二：网页手动创建**

1. 打开 https://github.com/RM3836
2. 右上角 `+` → `New repository`
3. Repository name 填 `AutoOps`
4. 选 Public（公开）
5. **不要**勾选 "Add a README"（我们已有本地 README）
6. 点 Create repository

然后手动关联推送：

```bash
git remote add origin https://github.com/RM3836/AutoOps.git
git branch -M main
git push -u origin main
```

### 第 4 步：用旗舰版 README 替换

```bash
# 把准备好的 GitHub README 覆盖默认 README
cp README_GITHUB.md README.md
git add README.md
git commit -m "docs: 更新 README，补充 Docker 容器化与可观测性说明"
git push
```

---

## 三、上传后必做的 3 件事（提升专业度）

### 1. 添加项目徽章（已在 README 里）

README 顶部已加了 Python/Docker/Prometheus/License 徽章，打开仓库首页会看到，显得专业。

### 2. 补充 About 描述

仓库首页右侧齿轮 → 填写：
- **Description**: `智能自动化运维平台 - Python/Flask/Docker/Prometheus/Grafana`
- **Website**: 可留空
- **Topics**: 添加 `python` `flask` `docker` `prometheus` `grafana` `devops` `monitoring` `automation` `ansible`

> Topics 很关键：GitHub 会按 topics 推荐，HR 搜 `devops` 或 `monitoring` 时你的仓库更容易被找到。

### 3. 上传运行截图

README 里的截图能大幅提升可信度。建议截 3-4 张：

| 截图 | 内容 | 对应地址 |
|---|---|---|
| 仪表盘 | CPU/内存/磁盘实时监控 | http://localhost:5000 |
| Prometheus | Targets 显示 autoops UP | http://localhost:9090/targets |
| Grafana | 监控大盘曲线 | http://localhost:3000 |
| 指标端点 | /metrics 文本输出 | http://localhost:5000/metrics |

截图后放到仓库 `docs/screenshots/` 目录，在 README 里用 `![](docs/screenshots/dashboard.png)` 引用。

---

## 四、注意事项（避免踩坑）

1. **不要提交 `venv/`** —— `.gitignore` 已排除，但提交前用 `git status` 再确认一次
2. **不要提交 `database/autoops.db`** —— `.gitignore` 已排除（`*.db`），这是运行时生成的数据，不该进仓库
3. **`docker-compose.yml` 里的 `admin123`** —— 这是 Grafana 初始密码，开源项目常见做法，可以保留；若更严谨可改为 `${GF_ADMIN_PASSWORD:-admin123}` 环境变量方式
4. **仓库名用 `AutoOps`** —— 和你本地目录一致，避免混淆；如果 `AutoOps` 已被占用，用 `autoops-platform`
5. **默认分支用 `main`** —— 不要用 `master`（你另一个仓库 auto-ops-course 就是 master，新仓库统一 main 更专业）

---

## 五、完成后你的 GitHub 作品集结构

```
RM3836/
├── AutoOps              ← 旗舰（本次上传）★ 主推
├── netops-toolkit        ← 网络设备自动化补充
├── auto-ops-course       ← 课程学习记录（不主推）
└── security-toolkit      ← 安全项目集
```

简历里 GitHub 链接建议指向 `github.com/RM3836/AutoOps`（旗舰项目），而不是泛泛的账号主页。

---

## 六、简历同步更新

AutoOps 上传 GitHub 后，简历里可以这样写：

```
- 独立开发 AutoOps 智能运维平台（已开源，github.com/RM3836/AutoOps），覆盖监控采集、批量运维、安全告警、巡检报告闭环
- 平台 Docker 化（Dockerfile + docker-compose 三服务编排），接入 Prometheus 采集 + Grafana 可视化 + 告警规则，落地可观测性建设
```
