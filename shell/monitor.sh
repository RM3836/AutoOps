#!/bin/bash
# AutoOps Linux 系统巡检脚本
# 用法: bash shell/monitor.sh

echo "============================================"
echo "  AutoOps 系统巡检报告"
echo "  时间: $(date)"
echo "  主机: $(hostname)"
echo "============================================"

echo ""
echo "--- 系统信息 ---"
uname -a

echo ""
echo "--- 磁盘使用 ---"
df -h

echo ""
echo "--- 内存使用 ---"
free -m

echo ""
echo "--- CPU负载 ---"
uptime

echo ""
echo "--- Top 10 进程(CPU) ---"
ps aux --sort=-%cpu | head -11

echo ""
echo "--- 网络连接 ---"
ss -tlnp | head -20

echo ""
echo "--- 最近登录 ---"
last -10

echo ""
echo "--- 最近失败登录 ---"
lastb -10 2>/dev/null || echo "无法读取"

echo ""
echo "============================================"
echo "  巡检完成"
echo "============================================"
