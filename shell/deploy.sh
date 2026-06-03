#!/bin/bash
# AutoOps 一键部署脚本 (CentOS/Ubuntu)
# 用法: bash shell/deploy.sh

echo "============================================"
echo "  AutoOps 一键部署"
echo "============================================"

# 检测系统
if [ -f /etc/redhat-release ]; then
    PKG="yum"
else
    PKG="apt-get"
fi

# 安装依赖
echo "[1/4] 安装系统依赖..."
sudo $PKG update -y
sudo $PKG install -y python3 python3-pip python3-venv

# 创建虚拟环境
echo "[2/4] 创建Python虚拟环境..."
cd "$(dirname "$0")/.."
python3 -m venv venv
source venv/bin/activate

# 安装Python包
echo "[3/4] 安装Python依赖..."
pip install -r requirements.txt

# 初始化数据库
echo "[4/4] 初始化数据库..."
python3 -c "
import sqlite3
conn = sqlite3.connect('database/autoops.db')
with open('database/init.sql') as f:
    conn.executescript(f.read())
conn.close()
print('数据库初始化完成')
"

echo ""
echo "============================================"
echo "  部署完成！"
echo "  启动命令: python3 app.py"
echo "  访问地址: http://localhost:5000"
echo "============================================"
