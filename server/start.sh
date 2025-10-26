#!/bin/bash

echo "======================================"
echo "智能选品系统 - 服务器启动脚本"
echo "======================================"

# 停止旧进程
pkill -9 -f "app.py" 2>/dev/null

# 启动服务器
cd "$(dirname "$0")"

# 激活虚拟环境
source 5e1ffe1ab6a7e684d88c3fcffbe8e2fb_venv/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null || true

python3 app.py

echo "服务器已启动！"
echo "管理后台: http://localhost:5000/admin/login"
echo "默认密码: admin123"
