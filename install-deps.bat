@echo off
chcp 65001 >nul
echo ==========================================
echo   智能选品系统 - 安装/更新依赖
echo ==========================================
echo.

REM 检查便携式Python
if not exist "portable-python\python.exe" (
    echo ❌ 未找到便携式Python，请先运行 setup-portable-python.bat
    pause
    exit /b 1
)

echo [1/3] 安装服务器依赖...
portable-python\python.exe -m pip install -r server\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade

echo.
echo [2/3] 安装客户端依赖...
portable-python\python.exe -m pip install -r client\requirements_modern.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade

echo.
echo [3/3] 安装构建工具...
portable-python\python.exe -m pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade

echo.
echo ==========================================
echo   ✅ 依赖安装/更新完成！
echo ==========================================
echo.
pause

