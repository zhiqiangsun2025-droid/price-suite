#!/bin/bash
# 老版本文件清理脚本
# 功能：安全地清理项目中的老版本文件

set -e  # 遇到错误立即退出

echo "========================================"
echo "  项目老版本文件清理工具"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/home/user/projects/shopxo-master/apps/price-suite"
cd "$PROJECT_ROOT"

echo -e "${YELLOW}📂 当前目录：${NC} $PWD"
echo ""

# 检查Git状态
if [ -d ".git" ]; then
    echo -e "${GREEN}✓${NC} 检测到Git仓库"
else
    echo -e "${RED}✗${NC} 未检测到Git仓库，建议先初始化Git"
    echo "  运行: git init && git add . && git commit -m 'Initial commit'"
    read -p "是否继续？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  第一步：分析项目文件"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 统计老版本文件
echo "🔍 扫描 client/ 目录中的版本文件..."
cd client

OLD_VERSIONS=(
    "modern_client_backup.py"
    "modern_client_final_v2.py"
    "modern_client_final.py"
    "modern_client_old.py"
    "modern_client_v10.10.3.py"
    "modern_client_v2_backup.py"
    "modern_client_v2.py"
    "modern_client_v3_backup.py"
    "modern_client_v3.py"
    "modern_client.py"
)

FOUND_FILES=()
TOTAL_SIZE=0

for file in "${OLD_VERSIONS[@]}"; do
    if [ -f "$file" ]; then
        FOUND_FILES+=("$file")
        SIZE=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
        TOTAL_SIZE=$((TOTAL_SIZE + SIZE))
        echo "  📄 $file ($(numfmt --to=iec-i --suffix=B $SIZE 2>/dev/null || echo "$SIZE bytes"))"
    fi
done

echo ""
if [ ${#FOUND_FILES[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ 未发现需要清理的老版本文件${NC}"
    exit 0
fi

echo -e "${YELLOW}发现 ${#FOUND_FILES[@]} 个老版本文件${NC}"
echo -e "${YELLOW}总大小约：$(numfmt --to=iec-i --suffix=B $TOTAL_SIZE 2>/dev/null || echo "$TOTAL_SIZE bytes")${NC}"
echo ""

# 保留的文件
echo "✅ 将保留以下文件："
echo "  📄 modern_client_ultimate.py (最新优化版本)"
echo "  📄 encryption.py"
echo "  📄 simple_client.py"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  第二步：选择清理方案"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "请选择清理方案："
echo ""
echo "  1) 💥 完全删除（推荐）"
echo "     - 永久删除老版本文件"
echo "     - Git历史中仍可恢复"
echo "     - 项目更清爽"
echo ""
echo "  2) 📦 归档保存（保守）"
echo "     - 移动到 archived_versions/ 目录"
echo "     - 保留文件但不影响主项目"
echo ""
echo "  3) ❌ 取消操作"
echo ""

read -p "请选择 (1/2/3): " -n 1 -r CHOICE
echo ""
echo ""

case $CHOICE in
    1)
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  执行：完全删除方案"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        # 确认
        echo -e "${RED}⚠️  警告：此操作将永久删除以下文件：${NC}"
        for file in "${FOUND_FILES[@]}"; do
            echo "  - $file"
        done
        echo ""
        read -p "确认删除？请输入 YES 继续: " CONFIRM
        
        if [ "$CONFIRM" != "YES" ]; then
            echo "操作已取消"
            exit 0
        fi
        
        echo ""
        echo "🗑️  正在删除老版本文件..."
        
        for file in "${FOUND_FILES[@]}"; do
            if rm -f "$file"; then
                echo "  ✓ 已删除: $file"
            else
                echo "  ✗ 删除失败: $file"
            fi
        done
        
        echo ""
        echo -e "${GREEN}✅ 清理完成！${NC}"
        echo ""
        echo "建议执行以下命令提交更改："
        echo ""
        echo "  cd $PROJECT_ROOT"
        echo "  git add -A"
        echo "  git commit -m '清理老版本文件，仅保留 modern_client_ultimate.py'"
        echo "  git push"
        ;;
        
    2)
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  执行：归档保存方案"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        # 创建归档目录
        ARCHIVE_DIR="archived_versions"
        mkdir -p "$ARCHIVE_DIR"
        
        echo "📦 正在归档老版本文件到 $ARCHIVE_DIR/ ..."
        
        for file in "${FOUND_FILES[@]}"; do
            if mv "$file" "$ARCHIVE_DIR/"; then
                echo "  ✓ 已归档: $file"
            else
                echo "  ✗ 归档失败: $file"
            fi
        done
        
        # 创建README
        cat > "$ARCHIVE_DIR/README.txt" << 'EOF'
# 归档的老版本文件

这些文件已被新版本替代，归档仅供参考。

最新版本：../modern_client_ultimate.py (v10.10.5)

如需使用老版本，请谨慎评估，建议仅用于参考对比。
EOF
        
        echo ""
        echo -e "${GREEN}✅ 归档完成！${NC}"
        echo ""
        echo "归档位置: client/$ARCHIVE_DIR/"
        echo ""
        echo "建议添加到 .gitignore："
        echo "  echo 'client/archived_versions/' >> .gitignore"
        ;;
        
    3)
        echo "操作已取消"
        exit 0
        ;;
        
    *)
        echo "无效选择"
        exit 1
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

