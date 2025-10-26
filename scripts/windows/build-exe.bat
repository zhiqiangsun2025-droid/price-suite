@echo off
chcp 65001 >nul
echo ==========================================
echo   智能选品系统 - 编译客户端EXE
echo ==========================================
echo.

REM 检查便携式Python
if not exist "portable-python\python.exe" (
    echo ❌ 未找到便携式Python，请先运行 setup-portable-python.bat
    pause
    exit /b 1
)

REM 检查PyInstaller
portable-python\python.exe -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo 正在安装PyInstaller...
    portable-python\python.exe -m pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo [1/3] 清理旧文件...
if exist "client\dist" rd /s /q "client\dist"
if exist "client\build" rd /s /q "client\build"
if exist "client\*.spec" del /q "client\*.spec"

echo ✅ 清理完成
echo.

echo [2/3] 编译客户端EXE...
echo 这可能需要 1-2 分钟，请耐心等待...
echo.

cd client

..\portable-python\python.exe -m PyInstaller --noconfirm ^
    --onefile ^
    --windowed ^
    --name "智能选品系统" ^
    --icon=NONE ^
    --add-data "assets;assets" ^
    --hidden-import=customtkinter ^
    --hidden-import=PIL._tkinter_finder ^
    modern_client_ultimate.py

if errorlevel 1 (
    echo ❌ 编译失败，请检查错误信息
    cd ..
    pause
    exit /b 1
)

cd ..

echo.
echo ✅ 编译完成
echo.

echo [3/3] 生成版本信息...
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/: " %%a in ('time /t') do (set mytime=%%a%%b)
set VERSION=%mydate:~-4,4%%mydate:~-8,2%%mydate:~-6,2%_%mytime%

echo.
echo ==========================================
echo   🎉 编译成功！
echo ==========================================
echo.
echo EXE位置: %cd%\client\dist\智能选品系统.exe
echo 文件大小: 
dir "client\dist\智能选品系统.exe" | find ".exe"
echo.
echo 可以直接运行该EXE，或者：
echo   - 复制到桌面使用
echo   - 发送给其他用户
echo.
echo 注意：首次运行需要启动后端服务器（运行 run-server.bat）
echo.
pause

