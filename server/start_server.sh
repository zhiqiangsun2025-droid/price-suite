#!/bin/bash
# 服务器启动脚本

echo "======================================="
echo "  商品价格对比系统 - 服务器启动"
echo "======================================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未安装 Python3"
    exit 1
fi

# 检查依赖
echo ""
echo "[1/3] 检查依赖..."
if [ ! -f "requirements.txt" ]; then
    echo "❌ 错误: 找不到 requirements.txt"
    exit 1
fi

# 安装依赖（如果需要）
pip3 install -r requirements.txt --quiet

# 检查配置
echo ""
echo "[2/3] 检查配置..."
if grep -q "your-secret-key-change-this" app.py; then
    echo "⚠️  警告: 请修改 SECRET_KEY 为你自己的密钥！"
    echo "   编辑 app.py，找到 SECRET_KEY = 'your-secret-key-change-this'"
    read -p "   是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 启动服务器
echo ""
echo "[3/3] 启动服务器..."
echo "======================================="
echo "  服务器信息"
echo "======================================="
echo "  地址: http://0.0.0.0:5000"
echo "  管理后台: /admin/login  (默认密码：admin123，可用ADMIN_PASSWORD覆盖)"
echo "  管理工具: python3 admin_tool.py"
echo "  停止服务: Ctrl+C"
echo "======================================="
echo ""

# 使用 gunicorn 启动（生产环境推荐）
if command -v gunicorn &> /dev/null; then
    echo "使用 gunicorn 启动..."
    gunicorn -w 4 -b 0.0.0.0:5000 --access-logfile access.log --error-logfile error.log app:app
else
    echo "使用 Flask 开发服务器启动..."
    python3 app.py
fi

