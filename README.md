# 🛍️ 智能选品铺货系统

## 项目简介

基于AI的电商智能选品和自动铺货系统，支持抖音/淘宝商品爬取、拼多多价格对比、自动铺货。

## 主要功能

- 🔍 **智能选品**: 自动爬取抖音/淘宝热销商品
- 🤖 **AI匹配**: 智能匹配拼多多同款商品（文本+图片相似度）
- 💰 **价格对比**: 自动计算价差，筛选高利润商品
- 📊 **数据分析**: 销量增长、价格趋势分析
- 🚀 **自动铺货**: RPA自动操作铺货软件
- 🔐 **安全防护**: 多层防破解，核心逻辑在服务器

## 技术栈

- **后端**: Python + Flask + SQLite + Selenium + AI匹配
- **客户端**: Python + CustomTkinter（现代化GUI）
- **RPA**: PyAutoGUI + pywinauto + OpenCV
- **部署**: 宝塔面板 / Docker / 手动部署

## 快速开始

### 服务器部署（宝塔面板）

1. 安装Python项目管理器
2. 上传 `server/` 文件夹
3. 创建项目，设置启动文件 `app.py`
4. 安装依赖: `pip install -r requirements.txt`
5. 启动服务

### 客户端打包

#### Windows环境:
```batch
cd client
.\build_windows.bat
```

#### GitHub Actions（自动打包）:
推送代码后自动打包，下载exe即可

### 虚拟机部署

推荐使用VMware/VirtualBox创建Windows虚拟机，配置：
- CPU: 2核
- 内存: 4GB
- 硬盘: 60GB

## 文档

- [宝塔面板部署指南](宝塔面板部署指南.md)
- [完整部署流程](完整部署流程.md)
- [前后端分工清单](前后端分工清单.md)
- [数据流向详解](数据流向详解.md)
- [安全防护指南](SECURITY_GUIDE.md)
- [虚拟机部署指南](虚拟机部署指南.md)

## 系统架构

```
客户端 → 服务器（爬虫+AI） → 客户端（显示） → Excel → RPA → 铺货
```

## 下载exe

[![Build Windows EXE](https://github.com/你的用户名/price-suite/actions/workflows/build-windows.yml/badge.svg)](https://github.com/你的用户名/price-suite/actions)

点击上方徽章 → Actions → 最新运行 → Artifacts → 下载exe

## License

MIT

