#!/bin/bash
# 云服务器部署脚本

echo "========================================"
echo "  Price Suite 服务器部署"
echo "========================================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未安装Python3"
    echo "执行: apt-get install -y python3 python3-pip"
    exit 1
fi

# 安装系统依赖
echo "📦 安装系统依赖..."
apt-get update
apt-get install -y google-chrome-stable chromium-chromedriver

# 安装Python依赖
echo "📦 安装Python依赖（服务器）..."
cd server
pip3 install -r requirements.txt

cd ..

echo ""
echo "✅ 部署完成！"
echo ""
echo "🚀 启动服务器："
echo "   cd server && python3 app.py"
echo ""
echo "或使用gunicorn生产模式："
echo "   cd server && gunicorn -w 4 -b 0.0.0.0:5000 app:app"
echo ""
