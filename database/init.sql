-- =============================================
-- AutoOps 数据库初始化脚本
-- 数据库: SQLite (database/autoops.db)
-- =============================================

-- 服务器状态表
CREATE TABLE IF NOT EXISTS server_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cpu REAL NOT NULL,
    memory REAL NOT NULL,
    disk REAL NOT NULL,
    network_sent REAL,
    network_recv REAL,
    process_count INTEGER,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 告警记录表
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL CHECK(level IN ('INFO','WARNING','CRITICAL','ERROR')),
    module TEXT NOT NULL,
    message TEXT NOT NULL,
    is_resolved INTEGER DEFAULT 0,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SSH主机表
CREATE TABLE IF NOT EXISTS ssh_hosts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname TEXT NOT NULL,
    port INTEGER DEFAULT 22,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'unknown',
    last_check TIMESTAMP
);

-- 操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operator TEXT,
    action TEXT,
    target TEXT,
    result TEXT,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_status_time ON server_status(create_time);
CREATE INDEX IF NOT EXISTS idx_alerts_time ON alerts(create_time);
CREATE INDEX IF NOT EXISTS idx_alerts_level ON alerts(level);
CREATE INDEX IF NOT EXISTS idx_ops_time ON operation_logs(create_time);

-- 插入示例数据
INSERT INTO alerts (level, module, message) VALUES
    ('INFO', '系统监控', '系统启动完成'),
    ('WARNING', '系统监控', 'CPU使用率超过80%阈值'),
    ('CRITICAL', '安全检测', '检测到来自异常IP的SSH登录尝试');
