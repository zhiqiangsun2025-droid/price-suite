@echo off
REM Windows 桌面自动化（RPA）环境安装脚本

echo ╔═══════════════════════════════════════════════════════════╗
echo ║   🤖 Windows 桌面自动化（RPA）- 环境安装               ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM 检查 Python
echo [1/6] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未安装 Python
    echo.
    echo 请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version
echo ✅ Python 已安装
echo.

REM 升级 pip
echo [2/6] 升级 pip...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.

REM 安装核心库
echo [3/6] 安装核心自动化库...
pip install pyautogui pillow -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.

REM 安装图像处理库
echo [4/6] 安装图像识别库...
pip install opencv-python numpy -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.

REM 安装 Windows GUI 自动化
echo [5/6] 安装 Windows GUI 自动化库...
pip install pywinauto -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.

REM 安装辅助库
echo [6/6] 安装辅助库...
pip install pyperclip -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.

REM 创建必要目录
echo 创建项目目录...
if not exist "screenshots" mkdir screenshots
if not exist "templates" mkdir templates
if not exist "logs" mkdir logs

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║   ✅ 安装完成！                                          ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo 已安装的库：
echo   ✅ PyAutoGUI       - 鼠标键盘控制
echo   ✅ OpenCV          - 图像识别
echo   ✅ pywinauto       - Windows GUI 自动化
echo   ✅ Pillow          - 图像处理
echo   ✅ pyperclip       - 剪贴板操作
echo.
echo 下一步：
echo   1. 查看 README_RPA.md 了解详细文档
echo   2. 运行 python quick_example.py 查看示例
echo   3. 开始自动化你的铺货软件！
echo.
echo 提示：
echo   - 将鼠标移到屏幕左上角可紧急停止程序
echo   - 首次使用建议在虚拟机中测试
echo   - 遇到问题请查看文档或联系技术支持
echo.

pause

