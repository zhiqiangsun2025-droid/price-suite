#!/bin/bash
# Price Suite 一键重启脚本

echo "========================================"
echo "Price Suite 服务重启脚本"
echo "========================================"

# 停止旧进程
echo "正在停止旧进程..."
OLD_PID=$(ps aux | grep "python.*app.py" | grep -v grep | awk '{print $2}')
if [ -n "$OLD_PID" ]; then
    kill $OLD_PID
    echo "已停止进程: $OLD_PID"
    sleep 2
else
    echo "没有发现运行中的进程"
fi

# 启动新进程
echo "正在启动服务..."
cd "/www/wwwroot/ price-suite/server"
nohup python3 app.py > app_startup.log 2>&1 &
sleep 3

# 检查状态
NEW_PID=$(ps aux | grep "python.*app.py" | grep -v grep | awk '{print $2}')
if [ -n "$NEW_PID" ]; then
    echo "✅ 服务启动成功！"
    echo "进程ID: $NEW_PID"
    echo ""
    
    # 测试服务
    echo "正在测试服务..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/admin/login)
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ 服务响应正常 (HTTP $HTTP_CODE)"
        echo ""
        echo "访问地址: https://price.deepopenai.store"
    else
        echo "⚠️  服务可能未完全启动，请稍后重试"
    fi
else
    echo "❌ 服务启动失败，请查看日志："
    echo "tail -f app.log"
fi

echo "========================================"

