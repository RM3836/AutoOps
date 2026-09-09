# AutoOps 安全日志分析模块重构计划

## 目标

重构 `security/log_analyzer.py`，解决当前的重复告警、无聚合统计、图表假数据等问题，
使其成为一个功能完整的安全检测模块，答辩时能展示"IP聚合分析 + 暴力破解阈值检测 + 实时统计图表"。

## 当前状态分析

### 现有代码

| 文件 | 功能 | 问题 |
|------|------|------|
| `security/log_analyzer.py` | 日志读取 + 关键词匹配 + 正则提取IP | 同一行产生2条告警；100次失败=100条告警无聚合 |
| `static/js/logs.js` | 前端展示分析结果 + 饼图 | 饼图数据写死 `[45,20,10,5]`，不反映真实数据 |
| `templates/logs.html` | 页面布局 | 布局够用，不需要大改 |
| `app.py` 路由 `/api/logs/analyze` | 调用 `log_analyzer.analyze_logs()` | 只返回原始告警列表，无聚合统计 |

### 关键问题

1. **重复告警**：一行日志同时匹配关键词和正则 → 产生2条告警（WARNING + CRITICAL）
2. **无IP聚合**：同一IP攻击100次 → 100条独立告警，无法一眼看出哪个IP最危险
3. **无阈值检测**：没有"单IP失败≥5次判定为暴力破解"的逻辑
4. **图表假数据**：饼图 `[45,20,10,5]` 是硬编码的，不反映实际日志级别分布
5. **告警未入库**：安全分析结果只返回前端，没有写入 `alerts` 表

## 重构方案

### Step 1: 重写 `security/log_analyzer.py`

核心改动：

```
class LogAnalyzer:
    SUSPICIOUS_KEYWORDS = [...]  # 保留
    ATTACK_PATTERNS = [...]       # 保留
    BRUTE_FORCE_THRESHOLD = 5     # 新增：暴力破解阈值

    def analyze_auth_log(self, log_path=None):
        """重构：去重 + IP聚合 + 阈值检测"""
        # 1. 逐行解析，提取 (时间, 用户, IP, 类型)
        # 2. 同一行只记一条，不重复
        # 3. 按IP聚合统计失败次数
        # 4. 失败次数 >= BRUTE_FORCE_THRESHOLD → CRITICAL
        # 5. 返回结构化结果：
        #    {
        #      "raw_alerts": [...],          # 去重后的原始告警（最多50条）
        #      "ip_summary": [               # IP聚合统计
        #        {"ip": "192.168.1.100", "attempts": 5, "users": ["admin","root"], "level": "CRITICAL"},
        #        ...
        #      ],
        #      "stats": {"total": 20, "critical": 3, "warning": 17}  # 统计汇总
        #    }

    def analyze_logs(self):
        """重构：返回值增加 stats 字段，供饼图使用"""
        # ...
        return {
            "platform_logs": [...],
            "auth_alerts": {...},       # 包含 raw_alerts + ip_summary
            "total_suspicious": 20,
            "log_stats": {"INFO": 45, "WARNING": 20, "ERROR": 10, "CRITICAL": 5}  # 真实统计
        }
```

**去重逻辑**：用 `seen = set()` 记录已处理的行内容哈希，同一行不重复产生告警。

**IP聚合逻辑**：用 `dict[ip] = {"count": N, "users": set()}` 聚合，最后排序输出。

### Step 2: 更新 `static/js/logs.js`

```
// 改动1: 饼图使用真实数据
async function loadLogStats() {
    const data = await api("/api/logs/analyze");
    // 用 data.log_stats 更新 Chart.js 数据
    logChart.data.datasets[0].data = [
        data.log_stats.INFO,
        data.log_stats.WARNING,
        data.log_stats.ERROR,
        data.log_stats.CRITICAL
    ];
    logChart.update();
}

// 改动2: 安全分析结果展示IP聚合表
function renderSecurityResult(data) {
    // 显示统计摘要
    // 显示 IP 聚合表格（IP | 失败次数 | 尝试用户名 | 威胁等级）
    // 用颜色标注 CRITICAL 行
}
```

### Step 3: 可选增强（按时间决定是否做）

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 告警自动入库（写alerts表） | 中 | 在 `analyze_auth_log` 返回后调用 `alert_mgr.save_alert()` |
| 登录成功检测 | 低 | 检测 `Accepted password/publickey` 统计正常登录 |
| 时间段分析 | 低 | 按小时聚合攻击频率，前端展示折线图 |

## 涉及文件

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `security/log_analyzer.py` | **重写** | 核心重构：去重 + IP聚合 + 阈值检测 + 统计 |
| `static/js/logs.js` | **修改** | 饼图用真实数据 + IP聚合表格渲染 |
| `templates/logs.html` | **微调** | 可能需要加IP聚合表格的DOM容器 |
| `app.py` | **不改** | 路由层不需要改，调用方式不变 |

## 验证方法

1. **单元验证**：在 Python REPL 中直接实例化 `LogAnalyzer()`，调用 `analyze_auth_log()`，
   检查返回结构是否包含 `raw_alerts`、`ip_summary`、`stats`
2. **前端验证**：启动 `python run.py`，访问 `/logs` 页面，点击"分析日志"，
   确认饼图数据变化 + IP聚合表格正确显示
3. **边界测试**：清空 `logs/auth.log`，确认返回"未发现安全问题"；
   写入1条日志，确认不重复

## 风险

- **向后兼容**：`analyze_logs()` 返回值结构变了，但 `app.py` 只做 `jsonify()` 转发，
  前端 JS 重写后会适配新结构，不影响其他模块
- **性能**：当前日志量小（几百行），纯内存处理无性能问题
