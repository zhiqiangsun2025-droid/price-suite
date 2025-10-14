@echo off
chcp 65001 >nul
echo ==========================================
echo   智能选品系统 - 停止所有进程
echo ==========================================
echo.

REM 结束客户端EXE
for /f "tokens=2 delims=," %%i in ('tasklist /fo csv ^| findstr /i "智能选品系统.exe"') do (
    echo 停止 客户端进程 PID=%%i
    taskkill /PID %%i /F >nul 2>&1
)

REM 结束便携式Python启动的后端（仅限当前目录下的 portable-python）
set LOCAL_PY=%cd%\portable-python\python.exe
for /f "tokens=2,14 delims=,\"" %%a in ('wmic process where "name='python.exe'" get ProcessId,ExecutablePath /format:csv ^| findstr /i "python.exe"') do (
    set PID=%%a
    set EXE=%%b
    call :KILL_IF_MATCH
)

echo.
echo ✅ 已尝试停止所有相关进程（客户端EXE与后端Python）
echo.
pause
exit /b 0

:KILL_IF_MATCH
if /I "%EXE%"=="%LOCAL_PY%" (
    echo 停止 后端Python进程 PID=%PID%
    taskkill /PID %PID% /F >nul 2>&1
)
exit /b 0

