@echo off
chcp 65001 >nul
echo ==========================================
echo   智能选品系统 - Windows便携式环境配置
echo ==========================================
echo.

REM 检查是否已存在便携式Python
if exist "portable-python\python.exe" (
    echo ✅ 检测到已安装的便携式Python
    goto :install_deps
)

echo [1/3] 下载便携式Python 3.12...
echo.

REM 创建下载目录
if not exist "downloads" mkdir downloads
cd downloads

REM 下载Python embeddable包（国内镜像）
echo 正在从淘宝镜像下载Python 3.12.0 embeddable版本...
echo 文件大小约 10MB，请稍候...
echo.

powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://npmmirror.com/mirrors/python/3.12.0/python-3.12.0-embed-amd64.zip' -OutFile 'python-embed.zip' -ErrorAction Stop }" 2>nul

if errorlevel 1 (
    echo ⚠️  淘宝镜像下载失败，尝试官方镜像...
    powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.0/python-3.12.0-embed-amd64.zip' -OutFile 'python-embed.zip' }"
)

if not exist "python-embed.zip" (
    echo ❌ 下载失败，请检查网络连接
    pause
    exit /b 1
)

echo ✅ 下载完成
echo.

echo [2/3] 解压Python...
cd ..
if not exist "portable-python" mkdir portable-python
powershell -Command "Expand-Archive -Path 'downloads\python-embed.zip' -DestinationPath 'portable-python' -Force"

REM 修改python312._pth以启用pip
echo import site>> portable-python\python312._pth

echo ✅ Python解压完成
echo.

echo [3/3] 安装pip...
cd portable-python

REM 下载get-pip.py
powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py' }"

REM 安装pip
python.exe get-pip.py -i https://pypi.tuna.tsinghua.edu.cn/simple

REM 配置pip使用清华源
if not exist "%USERPROFILE%\pip" mkdir "%USERPROFILE%\pip"
(
echo [global]
echo index-url = https://pypi.tuna.tsinghua.edu.cn/simple
echo [install]
echo trusted-host = pypi.tuna.tsinghua.edu.cn
) > "%USERPROFILE%\pip\pip.ini"

cd ..

echo ✅ pip安装完成并配置清华源
echo.

:install_deps
echo.
echo ==========================================
echo   安装项目依赖
echo ==========================================
echo.

echo [4/5] 安装服务器依赖...
portable-python\python.exe -m pip install -r server\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [5/5] 安装客户端依赖...
portable-python\python.exe -m pip install -r client\requirements_modern.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
portable-python\python.exe -m pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo ==========================================
echo   🎉 环境配置完成！
echo ==========================================
echo.
echo 便携式Python位置: %cd%\portable-python
echo Python版本: 3.12.0
echo pip已配置清华源
echo.
echo 接下来可以：
echo   1. 运行 build-exe.bat     编译客户端EXE
echo   2. 运行 run-server.bat    启动后端服务器
echo   3. 运行 run-all.bat       同时启动前后端
echo.
pause

