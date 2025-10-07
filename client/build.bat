@echo off
REM Windows 客户端打包脚本
REM 将 Python 程序打包为 .exe 可执行文件

echo ======================================
echo   商品价格对比系统 - 客户端打包
echo ======================================

REM 检查 Python
python --version
if errorlevel 1 (
    echo 错误: 未安装 Python
    pause
    exit /b 1
)

REM 安装 PyInstaller
echo.
echo [1/3] 安装打包工具...
pip install pyinstaller requests -i https://pypi.tuna.tsinghua.edu.cn/simple

REM 打包程序
echo.
echo [2/3] 正在打包...
pyinstaller --onefile ^
    --windowed ^
    --icon=icon.ico ^
    --name="价格对比系统" ^
    --add-data="client_config.json;." ^
    client_app.py

REM 复制配置文件
echo.
echo [3/3] 复制配置文件...
if not exist "dist" mkdir dist
copy client_config.json dist\ 2>nul

echo.
echo ======================================
echo   ✅ 打包完成！
echo ======================================
echo.
echo 可执行文件位于: dist\价格对比系统.exe
echo.
pause

