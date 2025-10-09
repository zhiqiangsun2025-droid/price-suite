@echo off
REM 安全打包脚本 - 多重防破解
REM 需要先安装: pip install pyinstaller pyarmor

echo ========================================
echo 客户端安全打包工具
echo ========================================

REM 1. 使用PyArmor混淆代码（强力保护）
echo [1/4] 代码混淆中...
pyarmor obfuscate --recursive modern_client.py

REM 2. 使用PyInstaller打包（加密）
echo [2/4] 打包exe中...
cd dist
pyinstaller --onefile ^
    --windowed ^
    --name="智能选品系统" ^
    --icon=../app.ico ^
    --key="RANDOM-ENCRYPTION-KEY-32CHARS" ^
    --add-data="../templates;templates" ^
    --add-data="../config;config" ^
    --hidden-import=customtkinter ^
    --hidden-import=PIL ^
    --hidden-import=requests ^
    --strip ^
    --clean ^
    modern_client.py

REM 3. 使用UPX压缩（进一步混淆）
echo [3/4] UPX压缩中...
upx --best --ultra-brute "dist/智能选品系统.exe"

REM 4. 生成文件哈希（防篡改）
echo [4/4] 生成校验文件...
certutil -hashfile "dist/智能选品系统.exe" SHA256 > "dist/智能选品系统.exe.sha256"

echo ========================================
echo 打包完成！
echo 输出: dist/智能选品系统.exe
echo ========================================
pause



