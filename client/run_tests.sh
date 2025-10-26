#!/bin/bash
set -e

echo "========================================"
echo "智能选品系统 - 单元测试套件"
echo "========================================"

echo "[1/2] 安装测试依赖..."
pip install -r requirements_test.txt -q

echo "[2/2] 运行单元测试..."
pytest tests/ -v --cov=. --cov-report=html

echo ""
echo "✓ 测试通过"
echo ""
echo "========================================"
echo "测试完成！查看报告: htmlcov/index.html"
echo "========================================"

