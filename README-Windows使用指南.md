# 智能选品系统 - Windows 使用指南

## 📋 目录

- [快速开始](#快速开始)
- [详细步骤](#详细步骤)
- [常用操作](#常用操作)
- [故障排除](#故障排除)
- [开发说明](#开发说明)

---

## 🚀 快速开始

### 方式A：使用便携式环境（推荐）

```batch
# 1. 配置环境（首次运行）
setup-portable-python.bat

# 2. 编译客户端
build-exe.bat

# 3. 一键启动前后端
run-all.bat
```

### 方式B：下载预编译EXE

1. 访问 GitHub Actions: https://github.com/zhiqiangsun2025-droid/price-suite/actions
2. 找到最新成功的构建
3. 下载 Artifacts 中的 `智能选品系统_vXXXXXXX.exe`
4. 运行 `run-server.bat` 启动后端
5. 双击下载的 EXE

---

## 📦 详细步骤

### 第一步：环境配置

#### 1.1 下载项目代码

**选项1：从WSL复制**
```powershell
# 在 Windows PowerShell 中执行
xcopy \\wsl$\Ubuntu\home\user\projects\shopxo-master\apps\price-suite C:\price-suite /E /I
```

**选项2：从GitHub克隆**
```powershell
cd C:\
git clone https://github.com/zhiqiangsun2025-droid/price-suite.git
cd price-suite
```

#### 1.2 配置便携式Python环境

双击运行 `setup-portable-python.bat`

**该脚本会自动：**
- ✅ 下载 Python 3.12.0 便携版（约10MB）
- ✅ 配置 pip 使用清华镜像源
- ✅ 安装所有项目依赖
- ✅ 无需管理员权限
- ✅ 不污染系统环境

**耗时**: 约 3-5 分钟（取决于网速）

---

### 第二步：编译客户端

双击运行 `build-exe.bat`

**编译过程：**
1. 清理旧文件
2. 使用 PyInstaller 打包
3. 生成单文件 EXE

**输出位置**: `client\dist\智能选品系统.exe`

**耗时**: 约 1-2 分钟

---

### 第三步：运行系统

#### 方式1：一键启动（推荐）

双击 `run-all.bat`

- 自动启动后端（后台）
- 自动启动客户端
- 一步到位

#### 方式2：分别启动

```batch
# 启动后端
run-server.bat

# 启动客户端（另开窗口）
client\dist\智能选品系统.exe
```

---

## 🔧 常用操作

### 更新依赖

```batch
# 更新所有依赖到最新版本
install-deps.bat
```

### 重新编译

```batch
# 重新编译客户端EXE
build-exe.bat
```

### 停止所有服务

```batch
# 停止后端服务器
stop-all.bat
```

### 访问管理后台

启动服务器后访问：
```
http://127.0.0.1:5000/admin/login
```

---

## 🛠️ 故障排除

### 问题1：setup-portable-python.bat 下载失败

**原因**: 网络问题或镜像源不可用

**解决方案**:
1. 检查网络连接
2. 尝试使用VPN
3. 手动下载Python后放入 `downloads\` 目录

### 问题2：编译失败 "ModuleNotFoundError"

**原因**: 缺少依赖

**解决方案**:
```batch
# 重新安装依赖
install-deps.bat
```

### 问题3：服务器启动失败 "端口被占用"

**原因**: 5000端口已被使用

**解决方案**:
```batch
# 查找并关闭占用端口的进程
netstat -ano | findstr :5000
taskkill /PID <进程ID> /F
```

### 问题4：客户端显示 "服务器错误500"

**原因**: 后端未启动或地址配置错误

**解决方案**:
1. 确保 `run-server.bat` 正在运行
2. 检查 `client\config_client.json` 中的 `server_url`
3. 默认应为: `http://127.0.0.1:5000`

### 问题5：EXE被杀毒软件拦截

**原因**: PyInstaller打包的EXE可能误报

**解决方案**:
1. 添加到杀毒软件白名单
2. 使用 `--clean` 重新编译
3. 直接运行 Python 源码而不是 EXE

---

## 💻 开发说明

### 目录结构

```
price-suite/
├── portable-python/        # 便携式Python环境
├── downloads/              # 下载缓存
├── server/                 # 后端服务器
│   ├── app.py             # 主程序
│   └── requirements.txt   # 依赖列表
├── client/                 # 客户端
│   ├── modern_client_ultimate.py  # 主程序
│   ├── dist/              # 编译输出
│   └── requirements_modern.txt
├── setup-portable-python.bat  # 环境配置
├── build-exe.bat             # 编译脚本
├── run-server.bat            # 启动后端
├── run-all.bat               # 一键启动
├── stop-all.bat              # 停止服务
└── install-deps.bat          # 安装依赖
```

### 使用 Cursor 编辑

1. 用 Cursor 打开项目文件夹
2. 修改代码后保存
3. 运行 `build-exe.bat` 重新编译
4. 运行 `run-all.bat` 测试效果

### 便携式Python特点

- **位置**: `portable-python\`
- **Python版本**: 3.12.0
- **pip配置**: 清华镜像源
- **特性**: 
  - ✅ 完全独立，不影响系统
  - ✅ 可运行任何Python项目
  - ✅ 删除文件夹即卸载

### 依赖管理

**服务器依赖** (`server\requirements.txt`):
- Flask
- Selenium
- APScheduler
- 其他...

**客户端依赖** (`client\requirements_modern.txt`):
- CustomTkinter
- Pillow
- Pandas
- Requests
- 其他...

### 版本号规则

GitHub Actions 自动构建：
- 格式: `MMDDXXX`
- 示例: `1014001`
- 说明: 10月14日第001个构建

本地编译：
- 格式: `YYYYMMDD_HHMM`
- 示例: `20251014_1530`

---

## 📊 性能优化

### 编译优化

```batch
# 方式1：标准编译（较慢，体积小）
build-exe.bat

# 方式2：快速编译（调试用）
portable-python\python.exe -m PyInstaller --onefile modern_client_ultimate.py
```

### 运行优化

1. 首次运行后，EXE启动速度会变快
2. 服务器可配置为Windows服务（自动启动）
3. 客户端支持配置服务器地址（多机协作）

---

## 🔗 相关链接

- **GitHub仓库**: https://github.com/zhiqiangsun2025-droid/price-suite
- **GitHub Actions**: https://github.com/zhiqiangsun2025-droid/price-suite/actions
- **测试文档**: `client\测试文档.md`
- **Linux文档**: `README.md`

---

## 📞 技术支持

如遇问题：
1. 查看 `故障排除` 章节
2. 检查 `server\logs\` 日志文件
3. 提交 GitHub Issue

---

## 🎯 下一步

配置完成后，你可以：

1. ✅ 使用便携式Python运行其他Python项目
2. ✅ 修改代码后快速重新编译
3. ✅ 在Windows上用Cursor直接开发
4. ✅ 分发EXE给其他用户使用

---

*最后更新: 2025-10-14*

