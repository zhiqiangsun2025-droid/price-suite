#!/bin/bash
# 完整项目打包脚本（用于迁移到云服务器远程开发）

set -e

echo "========================================"
echo "  完整项目打包工具"
echo "  用于迁移到云服务器进行远程开发"
echo "========================================"
echo ""

# 项目根目录
PROJECT_ROOT="/home/user/projects/shopxo-master/apps/price-suite"
cd "$PROJECT_ROOT"

# 创建打包目录
PACK_NAME="price-suite-full-$(date +%Y%m%d)"
rm -rf "$PACK_NAME"
mkdir -p "$PACK_NAME"

echo "📦 正在打包完整项目..."
echo ""

# ==================== 必需文件 ====================

# 1. 客户端（完整，用于开发）
echo "✓ 复制客户端代码..."
mkdir -p "$PACK_NAME/client"
cp client/modern_client_ultimate.py "$PACK_NAME/client/"
cp client/encryption.py "$PACK_NAME/client/" 2>/dev/null || true
cp client/simple_client.py "$PACK_NAME/client/" 2>/dev/null || true
cp client/config_client.json "$PACK_NAME/client/"
cp client/requirements_modern.txt "$PACK_NAME/client/"
cp client/*.bat "$PACK_NAME/client/" 2>/dev/null || true

# 2. 服务器端（完整）
echo "✓ 复制服务器代码..."
mkdir -p "$PACK_NAME/server"
cp server/*.py "$PACK_NAME/server/" 2>/dev/null || true
cp server/requirements.txt "$PACK_NAME/server/"
cp -r server/templates "$PACK_NAME/server/" 2>/dev/null || true
cp -r server/static "$PACK_NAME/server/" 2>/dev/null || true
cp -r server/tools "$PACK_NAME/server/" 2>/dev/null || true

# 3. RPA模块（完整）
echo "✓ 复制RPA代码..."
mkdir -p "$PACK_NAME/rpa"
cp rpa/*.py "$PACK_NAME/rpa/" 2>/dev/null || true
cp rpa/*.bat "$PACK_NAME/rpa/" 2>/dev/null || true
cp rpa/*.md "$PACK_NAME/rpa/" 2>/dev/null || true

# 4. 文档（完整）
echo "✓ 复制文档..."
cp -r docs "$PACK_NAME/"

# 5. 脚本（完整）
echo "✓ 复制脚本..."
cp -r scripts "$PACK_NAME/"

# 6. GitHub Actions（完整）
echo "✓ 复制CI/CD配置..."
mkdir -p "$PACK_NAME/.github"
cp -r .github/workflows "$PACK_NAME/.github/"

# 7. 配置文件
echo "✓ 复制配置文件..."
cp README.md "$PACK_NAME/"
cp .gitignore "$PACK_NAME/"

# 8. 部署脚本
echo "✓ 创建部署脚本..."
cat > "$PACK_NAME/deploy.sh" << 'DEPLOYSCRIPT'
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
DEPLOYSCRIPT

chmod +x "$PACK_NAME/deploy.sh"

# 9. 创建README
cat > "$PACK_NAME/README-DEPLOY.md" << 'READMESCRIPT'
# 云服务器部署说明

## 快速开始

### 1. 上传项目
```bash
# 本地执行
scp -r price-suite-full-20251024 root@服务器IP:/opt/
```

### 2. 部署
```bash
# 服务器执行
cd /opt/price-suite-full-20251024
./deploy.sh
```

### 3. 启动
```bash
cd server
python3 app.py
```

## 远程开发

### Cursor SSH连接
1. Cursor → Remote-SSH
2. 连接到服务器
3. 打开: /opt/price-suite-full-20251024
4. 开始开发！

## 项目结构
```
price-suite-full-20251024/
├── client/          # 客户端代码（可在服务器开发）
├── server/          # 服务器端代码
├── rpa/             # RPA模块
├── docs/            # 完整文档
├── scripts/         # 工具脚本
├── .github/         # CI/CD配置
└── deploy.sh        # 一键部署脚本
```

## 开发流程
1. Cursor远程编辑代码
2. 测试: python3 server/app.py
3. 客户端: GitHub Actions自动打包EXE
4. 提交: git commit && git push
READMESCRIPT

# ==================== 打包压缩 ====================

echo ""
echo "📦 压缩打包..."
tar --exclude='*.pyc' --exclude='__pycache__' --exclude='.git' \
    -czf "${PACK_NAME}.tar.gz" "$PACK_NAME"

# 计算大小
SIZE=$(du -h "${PACK_NAME}.tar.gz" | cut -f1)

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 完整项目打包完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📦 文件名: ${PACK_NAME}.tar.gz"
echo "📏 大小: $SIZE"
echo ""
echo "📂 包含内容："
echo "   ✓ 客户端代码（完整）"
echo "   ✓ 服务器端代码（完整）"
echo "   ✓ RPA模块（完整）"
echo "   ✓ 文档（完整）"
echo "   ✓ 脚本工具（完整）"
echo "   ✓ CI/CD配置（完整）"
echo "   ✓ 部署脚本（一键部署）"
echo ""
echo "🚀 迁移命令："
echo "   scp ${PACK_NAME}.tar.gz root@服务器IP:/opt/"
echo ""
echo "📝 部署说明："
echo "   解压后查看: ${PACK_NAME}/README-DEPLOY.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

