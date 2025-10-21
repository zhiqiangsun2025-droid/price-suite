#!/bin/bash
# 测试运行脚本 - Linux/WSL环境

set -e

echo "========================================"
echo "  智能选品系统 - 测试运行器"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 切换到项目目录
cd "$(dirname "$0")"

echo -e "${YELLOW}📂 当前目录：${NC} $PWD"
echo ""

# 检查pytest是否安装
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest未安装${NC}"
    echo "请运行: pip install pytest pytest-cov pytest-mock"
    exit 1
fi

echo -e "${GREEN}✓ pytest已安装${NC}"
echo ""

# 显示菜单
echo "请选择测试类型："
echo ""
echo "  1) 🧪 运行所有单元测试"
echo "  2) 🔗 运行集成测试"
echo "  3) 📊 生成覆盖率报告"
echo "  4) ⚡ 快速测试（仅关键功能）"
echo "  5) 🌐 运行所有测试"
echo ""

read -p "请选择 (1-5): " -n 1 -r CHOICE
echo ""
echo ""

case $CHOICE in
    1)
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  运行单元测试"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        cd client
        pytest tests/test_utils.py tests/test_config.py -v
        ;;
        
    2)
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  运行集成测试"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        cd client
        pytest tests/test_api_client.py -v
        ;;
        
    3)
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  生成覆盖率报告"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        cd client
        pytest tests/ --cov=. --cov-report=html --cov-report=term
        echo ""
        echo -e "${GREEN}✅ 覆盖率报告已生成${NC}"
        echo "HTML报告位置: client/htmlcov/index.html"
        ;;
        
    4)
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  快速测试"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        cd client
        pytest tests/ -v -k "test_config or test_hardware"
        ;;
        
    5)
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  运行所有测试"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        cd client
        pytest tests/ -v --tb=short
        ;;
        
    *)
        echo "无效选择"
        exit 1
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  测试完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

