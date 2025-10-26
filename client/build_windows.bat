@echo off
chcp 65001 >nul
echo ========================================
echo 智能选品系统 - Windows打包脚本
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未安装Python
    echo 请从 https://www.python.org/ 下载安装Python 3.8+
    pause
    exit /b 1
)

echo [1/4] 安装依赖...
pip install -r requirements_modern.txt
pip install pyinstaller pyautogui pywinauto opencv-python pandas openpyxl pyperclip

echo.
echo [2/4] 清理旧文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "智能选品系统.spec" del /q "智能选品系统.spec"

echo.
echo [3/4] 开始打包...
echo 这可能需要几分钟，请耐心等待...
echo.

pyinstaller --onefile ^
    --windowed ^
    --name="智能选品系统" ^
    --icon=app.ico ^
    --add-data="../rpa/rpa_controller.py;rpa" ^
    --add-data="../rpa/templates;rpa/templates" ^
    --hidden-import=customtkinter ^
    --hidden-import=PIL ^
    --hidden-import=pandas ^
    --hidden-import=openpyxl ^
    --hidden-import=pyautogui ^
    --hidden-import=pywinauto ^
    --hidden-import=cv2 ^
    --hidden-import=requests ^
    --hidden-import=cryptography ^
    --clean ^
    modern_client.py

if errorlevel 1 (
    echo.
    echo ❌ 打包失败！
    pause
    exit /b 1
)

echo.
echo [4/4] 打包完成！
echo.
echo ========================================
echo ✅ 成功生成: dist\智能选品系统.exe
echo ========================================
echo.
echo 文件信息:
dir dist\智能选品系统.exe
echo.
echo 下一步:
echo 1. 测试运行: dist\智能选品系统.exe
echo 2. 复制到虚拟机或客户电脑
echo 3. 双击运行即可（无需安装Python）
echo.
pause



