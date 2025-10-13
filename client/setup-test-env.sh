#!/bin/bash
# 智能选品系统 - 测试环境一键安装脚本
# 适用于 Linux / WSL / macOS

set -e

echo "=========================================="
echo "  智能选品系统 - 测试环境安装"
echo "=========================================="
echo ""

# 检测操作系统
OS_TYPE=$(uname -s)

echo "检测到操作系统: $OS_TYPE"
echo ""

# 安装系统依赖（tkinter）
echo "[1/3] 安装系统依赖..."
if [[ "$OS_TYPE" == "Linux" ]]; then
    if command -v apt-get &> /dev/null; then
        echo "使用 apt-get 安装 python3-tk..."
        sudo apt-get update -qq
        sudo apt-get install -y python3-tk tk-dev
    elif command -v yum &> /dev/null; then
        echo "使用 yum 安装 python3-tkinter..."
        sudo yum install -y python3-tkinter tk-devel
    elif command -v pacman &> /dev/null; then
        echo "使用 pacman 安装 tk..."
        sudo pacman -S --noconfirm tk
    else
        echo "⚠️  未检测到支持的包管理器，请手动安装 tkinter"
    fi
elif [[ "$OS_TYPE" == "Darwin" ]]; then
    echo "macOS 通常自带 tkinter，跳过系统依赖安装"
else
    echo "⚠️  不支持的操作系统: $OS_TYPE"
fi
echo "✅ 系统依赖安装完成"
echo ""

# 安装Python测试依赖
echo "[2/3] 安装 Python 测试依赖..."
pip install -q -r requirements_test.txt
echo "✅ 测试依赖安装完成"
echo ""

# 安装客户端运行时依赖
echo "[3/3] 安装客户端运行时依赖..."
pip install -q customtkinter requests pillow pandas openpyxl cryptography pyperclip
echo "✅ 客户端依赖安装完成"
echo ""

echo "=========================================="
echo "  🎉 测试环境安装完成！"
echo "=========================================="
echo ""
echo "快速开始:"
echo "  1. 运行单元测试:  pytest tests/ -v"
echo "  2. 查看覆盖率:    pytest tests/ --cov=. --cov-report=html"
echo "  3. 打开报告:      xdg-open htmlcov/index.html"
echo ""
echo "详细文档: 测试文档.md"
echo ""

