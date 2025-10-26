@echo off
chcp 65001 >nul
echo ==========================================
echo   智能选品系统 - 启动后端服务器
echo ==========================================
echo.

REM 检查便携式Python
if not exist "portable-python\python.exe" (
    echo ❌ 未找到便携式Python，请先运行 setup-portable-python.bat
    pause
    exit /b 1
)

REM 检查是否已有服务器在运行
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo ⚠️  检测到已有Python进程在运行
    echo 如需重启服务器，请先关闭旧进程
    echo.
)

echo [1/2] 检查服务器依赖...
portable-python\python.exe -c "import flask" 2>nul
if errorlevel 1 (
    echo 正在安装服务器依赖...
    portable-python\python.exe -m pip install -r server\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo ✅ 依赖安装完成
)

echo.
echo [2/2] 启动服务器...
echo.
echo ==========================================
echo   服务器信息
echo ==========================================
echo 访问地址: http://127.0.0.1:5000
echo 管理后台: http://127.0.0.1:5000/admin/login
echo.
echo 按 Ctrl+C 停止服务器
echo ==========================================
echo.

cd server
..\portable-python\python.exe app.py

cd ..
echo.
echo 服务器已停止
pause

