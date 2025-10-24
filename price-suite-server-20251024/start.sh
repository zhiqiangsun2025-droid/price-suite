#!/bin/bash
# 服务器启动脚本

cd server

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "❌ 未安装Python3"
    exit 1
fi

echo "📦 安装依赖..."
pip3 install -r requirements.txt

echo "🚀 启动服务器..."
# 使用gunicorn生产模式
if command -v gunicorn &> /dev/null; then
    gunicorn -w 4 -b 0.0.0.0:5000 app:app --daemon --access-logfile access.log --error-logfile error.log
    echo "✅ 服务器已在后台启动（端口5000）"
    echo "📋 日志文件："
    echo "   - access.log (访问日志)"
    echo "   - error.log (错误日志)"
else
    # 开发模式
    python3 app.py &
    echo "✅ 服务器已启动（开发模式，端口5000）"
fi

echo ""
echo "查看日志：tail -f server/access.log"
echo "停止服务：./stop.sh"
