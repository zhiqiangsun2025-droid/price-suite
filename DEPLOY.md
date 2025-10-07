# Price Suite 部署指南

## 结构

```
apps/price-suite/
  server/   # Flask 服务 + 可视化授权后台
  client/   # Windows 客户端（Tkinter GUI）
  rpa/      # Windows RPA 控制器（PyAutoGUI/pywinauto/OpenCV）
```

## 1) 服务器

```bash
cd apps/price-suite/server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export ADMIN_PASSWORD=admin123   # 可自定义
python app.py
# 访问 http://<服务器IP>:5000/admin/login  (密码见上)
```

## 2) 客户端（Windows）

- 将 `apps/price-suite/client` 拷贝到 Windows（如 `C:\price-client`）
- 安装 Python 3.10+
- `pip install requests`
- 运行 `python client_app.py`
- 首次激活输入：服务器地址、client_id
- UI：淘宝爬取 / 价格对比 / 自动选品 / 导出管理

## 3) RPA（Windows）

- 将 `apps/price-suite/rpa` 拷贝到 `C:\rpa`
- 安装依赖：`pip install pyautogui pywinauto opencv-python pillow pyperclip`
- 配置 `rpa_controller.py` 中铺货软件路径与模板图片
- 手动或用 GUI 生成模板图片到 `templates/`
- 命令行执行：

```bash
python C:\rpa\rpa_controller.py --csv C:\Users\<你>\Desktop\pdd_links.csv
```

## 4) 串联

- 客户端完成“价格对比”后，在“自动选品”页点击“一键选品→对比→铺货”，
- 程序将导出 `pdd_links.csv` 到桌面并自动调用 `rpa_controller.py`。

## 5) 授权与规则

- 后台：/admin/clients 列表、/admin/clients/new 新增、/admin/logs 日志
- IP 白名单：/admin/ipwl/<client_id>
- 选品规则：/admin/rules（按你的图片配置筛选逻辑）

## 6) 生产建议

- 使用 gunicorn/pm2/supervisor 常驻
- Nginx 反代 + HTTPS
- 定期备份 `authorization.db`
- 将 SECRET_KEY/ADMIN_PASSWORD 放入环境变量



