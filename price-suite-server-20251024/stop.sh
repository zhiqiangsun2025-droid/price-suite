#!/bin/bash
# 停止服务器

pkill -f "gunicorn.*app:app" || pkill -f "python3.*app.py"
echo "✅ 服务器已停止"
