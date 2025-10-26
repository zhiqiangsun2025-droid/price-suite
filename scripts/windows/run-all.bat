@echo off
chcp 65001 >nul
echo ==========================================
echo   智能选品系统 - 一键启动
echo ==========================================
echo.

REM 检查便携式Python
if not exist "portable-python\python.exe" (
    echo ❌ 未找到便携式Python，请先运行 setup-portable-python.bat
    pause
    exit /b 1
)

REM 检查客户端EXE
if not exist "client\dist\智能选品系统.exe" (
    echo ⚠️  未找到客户端EXE，正在自动编译...
    call build-exe.bat
    if errorlevel 1 (
        echo ❌ 编译失败，无法启动
        pause
        exit /b 1
    )
)

echo [1/2] 后台启动服务器...
start "智能选品系统-后端" /MIN cmd /c "cd /d %~dp0 && run-server.bat"

REM 等待服务器启动
echo 等待服务器启动...
timeout /t 3 /nobreak >nul

REM 检查服务器是否成功启动
portable-python\python.exe -c "import requests; requests.get('http://127.0.0.1:5000/api/health', timeout=2)" 2>nul
if errorlevel 1 (
    echo ⚠️  服务器启动可能失败，但继续启动客户端...
) else (
    echo ✅ 服务器启动成功
)

echo.
echo [2/2] 启动客户端...
start "" "client\dist\智能选品系统.exe"

echo.
echo ==========================================
echo   🎉 启动完成！
echo ==========================================
echo.
echo 后端服务器: http://127.0.0.1:5000 (后台运行)
echo 客户端EXE: 已启动
echo.
echo 如需查看服务器日志，请打开后台窗口
echo 关闭客户端不会停止服务器
echo 完全退出请关闭所有窗口或运行 stop-all.bat
echo.
pause

