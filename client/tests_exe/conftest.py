"""
EXE测试配置和fixtures
"""
import pytest
import os
import time
from pathlib import Path


@pytest.fixture(scope="session")
def exe_path():
    """查找最新的EXE文件"""
    dist_dir = Path(__file__).parent.parent / "dist"
    
    if not dist_dir.exists():
        pytest.skip("dist目录不存在，请先构建EXE")
    
    # 查找所有EXE文件
    exe_files = list(dist_dir.glob("*.exe"))
    
    if not exe_files:
        pytest.skip("未找到EXE文件，请先构建")
    
    # 返回最新的EXE
    latest_exe = max(exe_files, key=lambda p: p.stat().st_mtime)
    return str(latest_exe)


@pytest.fixture(scope="session")
def screenshots_dir(tmp_path_factory):
    """创建截图保存目录"""
    screenshot_dir = tmp_path_factory.mktemp("screenshots")
    return screenshot_dir


@pytest.fixture
def save_screenshot_on_failure(request, screenshots_dir):
    """测试失败时自动截图"""
    yield
    
    if request.node.rep_call.failed:
        from PIL import ImageGrab
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        test_name = request.node.name
        screenshot_path = screenshots_dir / f"{test_name}_{timestamp}.png"
        
        try:
            screenshot = ImageGrab.grab()
            screenshot.save(screenshot_path)
            print(f"\n截图已保存: {screenshot_path}")
        except Exception as e:
            print(f"\n保存截图失败: {e}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """为fixture提供测试结果"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)

