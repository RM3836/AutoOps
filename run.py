#!/usr/bin/env python3
"""
AutoOps 一键启动脚本 (防呆版)
自动检查依赖 -> 修复问题 -> 初始化数据库 -> 启动服务
用法: python run.py

防呆设计:
- 自动检测并创建缺失目录
- 自动换源安装依赖（默认源 -> 清华 -> 阿里 -> 中科大）
- 自动修复编码问题
- 自动处理数据库初始化失败
- 端口占用检测
- 详细的错误提示和解决建议
"""
import os
import sys
import subprocess
import sqlite3
import importlib
import platform
import shutil
import builtins

# ============================================================
# 路径配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "autoops.db")
SQL_PATH = os.path.join(DB_DIR, "init.sql")
REQ_PATH = os.path.join(BASE_DIR, "requirements.txt")
LOG_DIR = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "data")

# 国内镜像源（解决下载慢的问题）
MIRRORS = [
    "https://pypi.tuna.tsinghua.edu.cn/simple",
    "https://mirrors.aliyun.com/pypi/simple",
    "https://pypi.mirrors.ustc.edu.cn/simple",
]

# 需要的目录列表
REQUIRED_DIRS = [DB_DIR, LOG_DIR, DATA_DIR]

# 依赖包列表
REQUIRED_PACKAGES = ["flask", "psutil", "paramiko", "schedule"]


def _safe_print(*args, sep=" ", end="\n", file=None, flush=False):
    """兼容 Windows 控制台和重定向输出的安全打印函数。"""
    stream = file if file is not None else sys.stdout
    text = sep.join(str(arg) for arg in args) + end
    try:
        stream.write(text)
        if flush:
            stream.flush()
    except Exception:
        try:
            buffer = getattr(stream, "buffer", None)
            if buffer is not None:
                buffer.write(text.encode("utf-8", errors="replace"))
                if flush:
                    buffer.flush()
        except Exception:
            pass


# 让本模块的 print 在 Windows 环境下更稳
print = _safe_print


def banner():
    """打印启动横幅"""
    print("=" * 50)
    print("  AutoOps 自动化运维管理系统 (防呆版)")
    print("  作者: YURM")
    print("=" * 50)
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  系统: {platform.system()} {platform.release()}")
    print("=" * 50)


def fix_encoding():
    """修复 Windows 编码问题"""
    if platform.system() == "Windows":
        # 设置环境变量，避免编码问题
        os.environ["PYTHONIOENCODING"] = "utf-8"
        os.environ["PYTHONUTF8"] = "1"

    # 尽量把标准输出切到 UTF-8，避免控制台输出中断
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        try:
            if stream is not None and hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def ensure_directories():
    """确保所有必要的目录存在"""
    print("\n[0/4] 检查目录结构...")
    for dir_path in REQUIRED_DIRS:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"  [FIX] 创建目录: {os.path.basename(dir_path)}")
            except Exception as e:
                print(f"  [WARN] 创建目录失败 {dir_path}: {e}")
    print("  [OK] 目录结构完整")


def check_python():
    """检查 Python 版本"""
    print("\n[1/4] 检查 Python 版本...")
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 9):
        print(f"  [ERROR] Python 版本过低: {major}.{minor}")
        print("  需要 Python 3.9+，请升级后重试")
        print("  下载地址: https://www.python.org/downloads/")
        sys.exit(1)
    print(f"  [OK] Python {major}.{minor}")


def check_port(port=5000):
    """检查端口是否被占用"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except Exception:
        return False


def find_available_port(start_port=5000, max_attempts=10):
    """查找可用端口"""
    for port in range(start_port, start_port + max_attempts):
        if not check_port(port):
            return port
    return None


def fix_sql_file(sql_path):
    """修复 SQL 文件编码和语法问题"""
    try:
        # 尝试不同编码读取
        encodings = ['utf-8', 'gbk', 'utf-8-sig', 'latin-1']
        content = None

        for encoding in encodings:
            try:
                with open(sql_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            return None

        # 过滤掉可能导致问题的注释行
        lines = []
        for line in content.split('\n'):
            stripped = line.strip()
            # 保留 SQL 语句，过滤纯注释行
            if stripped.startswith('--') and not any(keyword in stripped.upper() for keyword in ['CREATE', 'INSERT', 'TABLE']):
                continue
            lines.append(line)

        return '\n'.join(lines)

    except Exception as e:
        print(f"  [WARN] SQL 文件读取失败: {e}")
        return None


def install_package(pkg_name, quiet=True):
    """安装单个包，自动尝试多个镜像源

    Args:
        pkg_name: 包名
        quiet: 是否静默安装

    Returns:
        bool: 是否安装成功
    """
    stdout = subprocess.DEVNULL if quiet else None
    stderr = subprocess.DEVNULL if quiet else None

    # 先尝试默认源（或已配置的源）
    cmd = [sys.executable, "-m", "pip", "install", pkg_name]
    if quiet:
        cmd.append("-q")

    try:
        subprocess.check_call(cmd, stdout=stdout, stderr=stderr)
        return True
    except subprocess.CalledProcessError:
        pass

    # 默认源失败，尝试国内镜像
    for mirror in MIRRORS:
        mirror_name = mirror.split('/')[2]
        try:
            print(f"    尝试镜像: {mirror_name}...")
            subprocess.check_call(
                cmd + ["-i", mirror, "--trusted-host", mirror_name],
                stdout=stdout,
                stderr=stderr
            )
            return True
        except subprocess.CalledProcessError:
            continue

    return False


def upgrade_pip():
    """升级 pip 并配置镜像源"""
    print("\n[2/4] 配置 pip...")

    # 升级 pip
    print("  [INFO] 升级 pip...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip", "-q"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("  [OK] pip 已升级")
    except subprocess.CalledProcessError:
        print("  [WARN] pip 升级失败，继续使用当前版本")

    # 配置镜像源
    print("  [INFO] 配置国内镜像源...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "config", "set", "global.index-url",
             "https://pypi.tuna.tsinghua.edu.cn/simple"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        subprocess.check_call(
            [sys.executable, "-m", "pip", "config", "set", "global.trusted-host",
             "pypi.tuna.tsinghua.edu.cn"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("  [OK] 已配置清华镜像源")
    except Exception:
        print("  [WARN] 镜像源配置失败，使用默认源")


def check_deps():
    """检查并安装依赖（防呆版）"""
    print("\n[3/4] 检查依赖...")

    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
            print(f"  [OK] {pkg}")
        except ImportError:
            missing.append(pkg)
            print(f"  [MISSING] {pkg}")

    if not missing:
        print("  [OK] 所有依赖已安装")
        return

    print(f"\n  需要安装: {', '.join(missing)}")
    print("  正在安装，请稍候...")

    # 方式1: 从 requirements.txt 安装（带编码修复）
    success = False
    if os.path.exists(REQ_PATH):
        print("  [INFO] 尝试从 requirements.txt 安装...")

        # 读取并修复 requirements.txt
        try:
            with open(REQ_PATH, 'r', encoding='utf-8') as f:
                req_content = f.read()
        except UnicodeDecodeError:
            # 尝试 GBK 编码
            try:
                with open(REQ_PATH, 'r', encoding='gbk') as f:
                    req_content = f.read()
                # 保存为 UTF-8
                with open(REQ_PATH, 'w', encoding='utf-8') as f:
                    f.write(req_content)
                print("  [FIX] 修复 requirements.txt 编码 (GBK -> UTF-8)")
            except Exception:
                req_content = None

        if req_content:
            # 尝试直接安装
            cmd = [sys.executable, "-m", "pip", "install", "-r", REQ_PATH, "-q"]
            try:
                subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                success = True
            except subprocess.CalledProcessError:
                # 尝试用镜像
                for mirror in MIRRORS:
                    mirror_name = mirror.split('/')[2]
                    try:
                        print(f"  使用镜像: {mirror_name}...")
                        subprocess.check_call(
                            cmd + ["-i", mirror, "--trusted-host", mirror_name],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        success = True
                        break
                    except subprocess.CalledProcessError:
                        continue

    # 方式2: 逐个安装（最终保障）
    if not success:
        print("  [INFO] 逐个安装依赖包...")
        all_ok = True
        for pkg in missing:
            print(f"  安装 {pkg}...")
            if install_package(pkg):
                print(f"  [OK] {pkg}")
            else:
                print(f"  [FAIL] {pkg}")
                all_ok = False

        if not all_ok:
            print("\n" + "=" * 50)
            print("  [ERROR] 部分依赖安装失败！")
            print()
            print("  请手动执行以下命令：")
            print(f"  pip install {' '.join(missing)}")
            print()
            print("  如果网络慢，使用国内镜像：")
            print(f"  pip install {' '.join(missing)} -i https://pypi.tuna.tsinghua.edu.cn/simple")
            print("=" * 50)
            sys.exit(1)

    # 验证安装
    print("\n  验证安装...")
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
            print(f"  [OK] {pkg}")
        except ImportError:
            print(f"  [FAIL] {pkg} 安装后仍无法导入")
            print("  请重启终端后重试")
            sys.exit(1)

    print("  [OK] 依赖安装完成")


def init_database():
    """初始化数据库（防呆版）"""
    print("\n[4/4] 初始化数据库...")

    # 确保目录存在
    os.makedirs(DB_DIR, exist_ok=True)

    # 检查数据库是否已存在且有效
    if os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 0:
        try:
            # 验证数据库完整性
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()

            if tables:
                print("  [OK] 数据库已存在且完整")
                return
            else:
                print("  [WARN] 数据库为空，重新初始化...")
                os.remove(DB_PATH)
        except Exception as e:
            print(f"  [WARN] 数据库验证失败: {e}")
            # 备份损坏的数据库
            backup_path = DB_PATH + ".bak"
            try:
                shutil.copy2(DB_PATH, backup_path)
                print(f"  [INFO] 已备份损坏的数据库到: {backup_path}")
            except Exception:
                pass
            os.remove(DB_PATH)

    # 检查 SQL 文件
    if not os.path.exists(SQL_PATH):
        print(f"  [ERROR] 找不到建表脚本: {SQL_PATH}")
        print("  请确认 database/init.sql 文件存在")

        # 尝试创建最小化的数据库（schema 与 app.py init_db 一致）
        print("  [INFO] 尝试创建最小化数据库...")
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS server_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpu REAL, memory REAL, disk REAL,
                    network_sent REAL, network_recv REAL,
                    process_count INTEGER,
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT, module TEXT, message TEXT,
                    is_resolved INTEGER DEFAULT 0,
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS ssh_hosts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hostname TEXT, port INTEGER DEFAULT 22,
                    username TEXT, password TEXT,
                    description TEXT, status TEXT DEFAULT 'unknown'
                );
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operator TEXT, action TEXT, target TEXT,
                    result TEXT,
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.close()
            print("  [OK] 最小化数据库创建成功")
            return
        except Exception as e:
            print(f"  [ERROR] 最小化数据库创建失败: {e}")
            sys.exit(1)

    # 读取并修复 SQL 文件
    print("  [INFO] 读取建表脚本...")
    sql_content = fix_sql_file(SQL_PATH)

    if sql_content is None:
        print("  [ERROR] SQL 文件读取失败")
        sys.exit(1)

    # 执行 SQL
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.executescript(sql_content)
        conn.commit()
        conn.close()
        print("  [OK] 数据库初始化完成")
    except Exception as e:
        print(f"  [ERROR] 数据库初始化失败: {e}")
        print()
        print("  可能的原因：")
        print("  1. SQL 文件语法错误")
        print("  2. 数据库文件被占用")
        print("  3. 磁盘空间不足")
        print()
        print("  解决方法：")
        print("  1. 检查 database/init.sql 文件")
        print("  2. 关闭其他可能占用数据库的程序")
        print("  3. 检查磁盘空间")
        sys.exit(1)


def start_server():
    """启动 Web 服务（防呆版）"""
    print("\n" + "=" * 50)
    print("  启动服务...")
    print("=" * 50)

    os.chdir(BASE_DIR)
    sys.path.insert(0, BASE_DIR)

    # 加载配置
    try:
        from config.settings import Config
    except ImportError as e:
        print(f"  [ERROR] 配置文件加载失败: {e}")
        print("  请确认 config/settings.py 文件存在")
        sys.exit(1)

    # 检查端口
    port = Config.PORT
    if check_port(port):
        print(f"  [WARN] 端口 {port} 已被占用！")
        print()

        # 尝试查找可用端口
        available_port = find_available_port(port + 1)
        if available_port:
            print(f"  [INFO] 可用端口: {available_port}")
            print("  [INFO] 已自动切换到可用端口")
            port = available_port
        else:
            print("  [ERROR] 未找到可用端口")
            print("  请关闭占用端口的程序后重试")
            sys.exit(1)

    # 显示启动信息
    print()
    print("=" * 50)
    print(f"  访问地址: http://localhost:{port}")
    print(f"  数据库:   {DB_PATH}")
    print("  按 Ctrl+C 停止服务")
    print("=" * 50)
    print()

    # 启动应用
    try:
        from app import app, init_db, start_background_services
        init_db()
        start_background_services()
        app.run(host="0.0.0.0", port=port, debug=False)
    except KeyboardInterrupt:
        print("\n  服务已停止")
    except Exception as e:
        print(f"\n  [ERROR] 启动失败: {e}")
        print()
        print("  常见问题排查：")
        print("  1. 检查 config/settings.py 配置是否正确")
        print("  2. 检查 app.py 是否有语法错误")
        print("  3. 查看 logs/ 目录下的日志文件")
        print("  4. 确认所有依赖包已正确安装")
        sys.exit(1)


if __name__ == "__main__":
    try:
        # 初始化
        fix_encoding()
        banner()
        ensure_directories()
        check_python()
        upgrade_pip()
        check_deps()
        init_database()
        start_server()
    except KeyboardInterrupt:
        print("\n  已取消")
    except Exception as e:
        print(f"\n  [ERROR] 未预期的错误: {e}")
        print()
        print("  请尝试以下步骤：")
        print("  1. 删除 venv 目录，重新运行")
        print("  2. 删除 database/autoops.db，重新运行")
        print("  3. 检查 Python 版本是否 >= 3.9")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)
