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
