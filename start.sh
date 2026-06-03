#!/bin/bash
# AutoOps 一键启动脚本 (Linux/Mac)
# 用法: ./start.sh 或 bash start.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================"
echo "  AutoOps 一键启动脚本"
echo "========================================"
echo

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 检查 Python
echo "[1/3] 检查 Python..."
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo -e "${RED}[ERROR] 未找到 Python！${NC}"
    echo
    echo "请先安装 Python 3.9+"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  CentOS/RHEL:   sudo yum install python3 python3-pip"
    echo "  Mac:           brew install python3"
    exit 1
fi

PY_VERSION=$($PYTHON --version 2>&1)
echo -e "${GREEN}[OK] $PY_VERSION${NC}"
echo

# 检查是否在虚拟环境
echo "[2/3] 检查环境..."
if [ -n "$VIRTUAL_ENV" ]; then
    echo -e "${GREEN}[OK] 已在虚拟环境: $VIRTUAL_ENV${NC}"
else
    echo -e "${YELLOW}[INFO] 未使用虚拟环境${NC}"
    echo "       建议创建: python3 -m venv venv && source venv/bin/activate"
fi
echo

# 启动项目
echo "[3/3] 启动项目..."
echo
exec $PYTHON -u run.py
