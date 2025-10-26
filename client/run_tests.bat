@echo off
chcp 65001 > nul
echo ========================================
echo 智能选品系统 - 自动化测试套件
echo ========================================

echo [1/3] 安装测试依赖...
pip install -r requirements_test.txt -q
if %ERRORLEVEL% neq 0 (
    echo 依赖安装失败！
    pause
    exit /b 1
)

echo [2/3] 运行单元测试...
pytest tests/ -v --cov=. --cov-report=html
if %ERRORLEVEL% neq 0 (
    echo 单元测试失败！
    echo 查看报告: htmlcov/index.html
    pause
    exit /b 1
)

echo.
echo ✓ 单元测试通过
echo.

echo [3/3] 运行EXE测试（需要先构建EXE）...
if exist dist\智能选品系统*.exe (
    pip install -r requirements_test_exe.txt -q
    pytest tests_exe/ -v --tb=short
    if %ERRORLEVEL% neq 0 (
        echo ⚠ EXE测试失败（可能需要Windows环境）
    ) else (
        echo ✓ EXE测试通过
    )
) else (
    echo ⚠ 未找到EXE文件，跳过EXE测试
    echo   请先运行: pyinstaller modern_client_ultimate.py
)

echo.
echo ========================================
echo 测试完成！
echo 覆盖率报告: htmlcov/index.html
echo ========================================
pause

