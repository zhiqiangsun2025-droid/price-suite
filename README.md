# 🛍️ 智能选品铺货系统

**当前版本**: 20251023003 | **状态**: ✅ 生产就绪

## 项目简介

基于AI的电商智能选品和自动铺货系统，支持抖音/淘宝商品爬取、拼多多价格对比、自动铺货。

## 🎉 v10.10.5 更新亮点

- ✅ **修复20+重大Bug** - 包括安全漏洞、内存泄漏、验证码逻辑等
- ✅ **性能提升30-50%** - 优化UI渲染、减少服务器压力
- ✅ **完整日志系统** - 所有关键操作可追踪
- ✅ **自动化测试** - CI/CD集成，确保代码质量
- ✅ **GitHub Actions自动打包** - 推送代码自动生成EXE

详细内容请查看 [代码修复报告](docs/代码修复报告-v10.10.5.md)

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

## 📚 文档

### 快速上手
- [快速操作指南](docs/快速操作指南.md) ⭐ **推荐先看**
- [项目优化建议](docs/项目优化建议.md)
- [修复验证通过](docs/修复验证通过.md)

### 部署指南
- [宝塔面板部署指南](宝塔面板部署指南.md)
- [完整部署流程](完整部署流程.md)
- [虚拟机部署指南](虚拟机部署指南.md)

### 开发文档
- [前后端分工清单](前后端分工清单.md)
- [数据流向详解](数据流向详解.md)
- [安全防护指南](SECURITY_GUIDE.md)
- [测试文档](client/tests/README.md)

### 更新日志
- [v10.10.5 代码修复报告](docs/代码修复报告-v10.10.5.md)

## 系统架构

```
客户端 → 服务器（爬虫+AI） → 客户端（显示） → Excel → RPA → 铺货
```

## 📦 下载EXE

[![Build Windows EXE](https://github.com/zhiqiangsun2025-droid/price-suite/actions/workflows/build-windows-exe.yml/badge.svg)](https://github.com/zhiqiangsun2025-droid/price-suite/actions)

### 方式1：GitHub Actions自动打包（推荐）
1. 访问 [Actions页面](https://github.com/zhiqiangsun2025-droid/price-suite/actions)
2. 选择最新的 "自动打包Windows EXE" 工作流
3. 下载 Artifacts 中的 `智能选品系统-Windows-v10.10.5`

### 方式2：本地打包（Windows环境）
```bash
cd client
pip install -r requirements_modern.txt
pip install pyinstaller
pyinstaller modern_client_ultimate.py --onefile --windowed
```

## 🧪 测试

```bash
# 运行单元测试
cd client
pytest tests/ -v

# 运行集成测试
pytest tests/test_api_client.py -v

# 生成覆盖率报告
pytest tests/ --cov=. --cov-report=html
```

详细测试说明见 [测试文档](client/tests/README.md)

## License

MIT



