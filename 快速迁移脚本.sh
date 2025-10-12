#!/bin/bash

# ============================================
# Price-Suite 项目独立迁移脚本
# ============================================

set -e  # 遇到错误立即退出

echo "================================================"
echo "  Price-Suite 项目独立迁移脚本"
echo "================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 变量定义
OLD_PATH="/home/user/projects/shopxo-master/apps/price-suite"
NEW_PATH="/home/user/projects/price-suite"
BACKUP_PATH="$HOME/backups/price-suite-backup-$(date +%Y%m%d-%H%M%S)"

# 检查当前目录
CURRENT_DIR=$(pwd)
echo -e "${BLUE}[信息] 当前目录: $CURRENT_DIR${NC}"
echo ""

# 步骤1：备份
echo -e "${YELLOW}[步骤1/8] 创建备份...${NC}"
mkdir -p "$HOME/backups"
if [ -d "$OLD_PATH" ]; then
    cp -r "$OLD_PATH" "$BACKUP_PATH"
    echo -e "${GREEN}✓ 备份完成: $BACKUP_PATH${NC}"
else
    echo -e "${RED}✗ 源目录不存在: $OLD_PATH${NC}"
    exit 1
fi
echo ""

# 步骤2：创建新目录
echo -e "${YELLOW}[步骤2/8] 创建独立项目目录...${NC}"
mkdir -p "$NEW_PATH"
echo -e "${GREEN}✓ 目录已创建: $NEW_PATH${NC}"
echo ""

# 步骤3：移动文件
echo -e "${YELLOW}[步骤3/8] 移动项目文件...${NC}"
# 使用rsync保持权限和结构
if command -v rsync &> /dev/null; then
    rsync -av --progress "$OLD_PATH/" "$NEW_PATH/"
    echo -e "${GREEN}✓ 文件已复制（使用rsync）${NC}"
else
    cp -r "$OLD_PATH/"* "$NEW_PATH/"
    echo -e "${GREEN}✓ 文件已复制（使用cp）${NC}"
fi
echo ""

# 步骤4：初始化Git
echo -e "${YELLOW}[步骤4/8] 检查Git仓库...${NC}"
cd "$NEW_PATH"
if [ -d ".git" ]; then
    echo -e "${GREEN}✓ Git仓库已存在${NC}"
    git remote -v
else
    echo -e "${BLUE}初始化新的Git仓库...${NC}"
    git init
    git add .
    git commit -m "Initial commit: 项目独立迁移"
    echo -e "${GREEN}✓ Git仓库已初始化${NC}"
fi
echo ""

# 步骤5：创建.gitignore
echo -e "${YELLOW}[步骤5/8] 创建.gitignore文件...${NC}"
cat > "$NEW_PATH/.gitignore" << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# 日志和数据库
*.log
*.db
*.sqlite
*.sqlite3

# 临时文件
tmp/
temp/
*.tmp

# RPA截图
rpa/screenshots/
rpa/templates/*.png

# 打包文件
dist/
build/
*.spec

# 敏感信息
.env
config_local.py
*.key
*.pem
EOF
echo -e "${GREEN}✓ .gitignore已创建${NC}"
echo ""

# 步骤6：创建虚拟环境
echo -e "${YELLOW}[步骤6/8] 配置Python虚拟环境...${NC}"
cd "$NEW_PATH/server"

if [ -d "venv" ]; then
    echo -e "${BLUE}删除旧的虚拟环境...${NC}"
    rm -rf venv
fi

echo -e "${BLUE}创建新的虚拟环境...${NC}"
python3 -m venv venv

echo -e "${BLUE}激活虚拟环境并安装依赖...${NC}"
source venv/bin/activate

if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✓ 服务器依赖已安装${NC}"
else
    echo -e "${YELLOW}⚠ 未找到requirements.txt${NC}"
fi

deactivate
echo ""

# 步骤7：创建Cursor配置
echo -e "${YELLOW}[步骤7/8] 创建Cursor工作区配置...${NC}"
mkdir -p "$NEW_PATH/.vscode"
cat > "$NEW_PATH/.vscode/settings.json" << 'EOF'
{
  "python.defaultInterpreterPath": "server/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/.venv": true,
    "**/venv": true
  },
  "search.exclude": {
    "**/venv": true,
    "**/node_modules": true,
    "**/__pycache__": true
  },
  "terminal.integrated.cwd": "${workspaceFolder}"
}
EOF
echo -e "${GREEN}✓ Cursor配置已创建${NC}"
echo ""

# 步骤8：验证
echo -e "${YELLOW}[步骤8/8] 验证迁移结果...${NC}"
cd "$NEW_PATH"

# 检查目录结构
echo -e "${BLUE}检查目录结构...${NC}"
for dir in server client rpa; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓ $dir/ 存在${NC}"
    else
        echo -e "${RED}✗ $dir/ 不存在${NC}"
    fi
done

# 检查重要文件
echo -e "\n${BLUE}检查重要文件...${NC}"
for file in README.md server/app.py client/modern_client_v10.10.3.py rpa/rpa_controller.py; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file 存在${NC}"
    else
        echo -e "${RED}✗ $file 不存在${NC}"
    fi
done

# 检查Git状态
echo -e "\n${BLUE}检查Git状态...${NC}"
if [ -d ".git" ]; then
    echo -e "${GREEN}✓ Git仓库正常${NC}"
    echo "分支信息:"
    git branch -a
else
    echo -e "${RED}✗ Git仓库异常${NC}"
fi

echo ""
echo "================================================"
echo -e "${GREEN}✓ 迁移完成！${NC}"
echo "================================================"
echo ""
echo -e "${BLUE}新项目位置: $NEW_PATH${NC}"
echo -e "${BLUE}备份位置: $BACKUP_PATH${NC}"
echo ""
echo -e "${YELLOW}下一步操作：${NC}"
echo "1. 在Cursor中打开新项目:"
echo -e "   ${GREEN}cursor $NEW_PATH${NC}"
echo ""
echo "2. 或者使用命令行启动服务器:"
echo -e "   ${GREEN}cd $NEW_PATH/server${NC}"
echo -e "   ${GREEN}source venv/bin/activate${NC}"
echo -e "   ${GREEN}python app.py${NC}"
echo ""
echo "3. 验证一切正常后，可以删除旧目录:"
echo -e "   ${YELLOW}rm -rf $OLD_PATH${NC}"
echo ""
echo -e "${BLUE}详细文档: $NEW_PATH/项目独立迁移指南.md${NC}"
echo ""

