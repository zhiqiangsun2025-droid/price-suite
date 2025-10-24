#!/bin/bash
# 服务器部署打包脚本
# 用途：打包所有需要部署到云服务器的文件

set -e

echo "========================================"
echo "  服务器部署打包工具"
echo "========================================"
echo ""

# 项目根目录
PROJECT_ROOT="/home/user/projects/shopxo-master/apps/price-suite"
cd "$PROJECT_ROOT"

# 创建部署包目录
DEPLOY_DIR="price-suite-server-$(date +%Y%m%d)"
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

echo "📦 正在打包服务器端文件..."
echo ""

# 1. 核心服务器代码
echo "✓ 复制服务器代码..."
mkdir -p "$DEPLOY_DIR/server"
cp server/app.py "$DEPLOY_DIR/server/"
cp server/douyin_scraper_v2.py "$DEPLOY_DIR/server/" 2>/dev/null || true
cp server/douyin_scraper.py "$DEPLOY_DIR/server/" 2>/dev/null || true
cp server/ai_matcher.py "$DEPLOY_DIR/server/" 2>/dev/null || true
cp server/admin_tool.py "$DEPLOY_DIR/server/" 2>/dev/null || true
cp server/web_auto_listing.py "$DEPLOY_DIR/server/" 2>/dev/null || true
cp server/app_listing_api.py "$DEPLOY_DIR/server/" 2>/dev/null || true
cp server/requirements.txt "$DEPLOY_DIR/server/"

# 2. 模板和静态文件（如果有）
if [ -d "server/templates" ]; then
    echo "✓ 复制模板文件..."
    cp -r server/templates "$DEPLOY_DIR/server/"
fi

if [ -d "server/static" ]; then
    echo "✓ 复制静态文件..."
    cp -r server/static "$DEPLOY_DIR/server/"
fi

# 3. 启动脚本
echo "✓ 创建启动脚本..."
cat > "$DEPLOY_DIR/start.sh" << 'STARTSCRIPT'
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
STARTSCRIPT

chmod +x "$DEPLOY_DIR/start.sh"

# 4. 停止脚本
cat > "$DEPLOY_DIR/stop.sh" << 'STOPSCRIPT'
#!/bin/bash
# 停止服务器

pkill -f "gunicorn.*app:app" || pkill -f "python3.*app.py"
echo "✅ 服务器已停止"
STOPSCRIPT

chmod +x "$DEPLOY_DIR/stop.sh"

# 5. 部署说明
cat > "$DEPLOY_DIR/README.md" << 'READMESCRIPT'
# 服务器部署包

## 快速部署

### 1. 上传到服务器
```bash
scp -r price-suite-server-* root@your-server:/opt/
```

### 2. 安装系统依赖
```bash
# Ubuntu/Debian
apt-get update
apt-get install -y python3 python3-pip google-chrome-stable

# Chrome Driver（Selenium需要）
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE
```

### 3. 启动服务
```bash
cd /opt/price-suite-server-*
./start.sh
```

### 4. 验证
```bash
curl http://localhost:5000/
```

### 5. 配置防火墙
```bash
# 开放5000端口
ufw allow 5000
```

## 日志查看
```bash
tail -f server/access.log
tail -f server/error.log
```

## 停止服务
```bash
./stop.sh
```

## 重启服务
```bash
./stop.sh && ./start.sh
```

## 环境变量配置（可选）
```bash
export PRICE_SUITE_SERVER_URL="http://your-domain.com:5000"
export ADMIN_PASSWORD="your-admin-password"
```
READMESCRIPT

# 6. .gitignore
cp .gitignore "$DEPLOY_DIR/" 2>/dev/null || true

# 7. 压缩打包
echo ""
echo "📦 压缩打包..."
tar -czf "${DEPLOY_DIR}.tar.gz" "$DEPLOY_DIR"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 打包完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📦 部署包: ${DEPLOY_DIR}.tar.gz"
echo "📏 大小: $(du -h ${DEPLOY_DIR}.tar.gz | cut -f1)"
echo ""
echo "🚀 迁移步骤："
echo "1. scp ${DEPLOY_DIR}.tar.gz root@your-server:/opt/"
echo "2. ssh root@your-server"
echo "3. cd /opt && tar -xzf ${DEPLOY_DIR}.tar.gz"
echo "4. cd ${DEPLOY_DIR} && ./start.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

