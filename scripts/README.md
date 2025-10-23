# 脚本说明

## Windows脚本 (windows/)

| 文件 | 作用 | 使用场景 |
|------|------|---------|
| `install-deps.bat` | 安装Python依赖 | 首次部署 |
| `run-server.bat` | 启动Flask服务器 | Windows本地测试服务器 |
| `run-all.bat` | 启动客户端+服务器 | 一键启动完整环境 |
| `stop-all.bat` | 停止所有服务 | 关闭所有进程 |
| `setup-portable-python.bat` | 配置便携Python | 无需安装Python环境 |
| `build-exe.bat` | 手动打包客户端 | 本地打包（备用，已有GitHub Actions自动打包） |

## Linux脚本 (linux/)

| 文件 | 作用 | 使用场景 |
|------|------|---------|
| `run_tests.sh` | 运行单元测试 | 开发时测试 |
| `cleanup-old-versions.sh` | 清理老版本文件 | 项目维护 |
| `快速迁移脚本.sh` | 迁移部署 | 服务器迁移 |

## 使用方法

### Windows环境
```cmd
REM 首次安装
scripts\windows\install-deps.bat

REM 启动服务器
scripts\windows\run-server.bat

REM 启动完整环境
scripts\windows\run-all.bat

REM 手动打包（可选）
scripts\windows\build-exe.bat
```

### Linux环境
```bash
# 运行测试
./scripts/linux/run_tests.sh

# 清理项目
./scripts/linux/cleanup-old-versions.sh
```

## 推荐方式

### 开发和打包
- ✅ **推荐**：使用GitHub Actions自动打包
- ⚠️ **备用**：使用build-exe.bat手动打包

### 测试
- ✅ **Linux**：使用run_tests.sh
- ✅ **Windows**：使用client/run_tests.bat

