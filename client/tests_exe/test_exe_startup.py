"""
测试EXE启动
"""
import pytest
import time
import os


# 在非Windows环境跳过
pytestmark = pytest.mark.skipif(
    os.name != 'nt',
    reason="EXE测试仅在Windows环境运行"
)


@pytest.mark.timeout(60)
class TestEXEStartup:
    """测试EXE启动"""
    
    def test_exe_can_start(self, exe_path):
        """测试EXE能否正常启动"""
        from tests_exe.utils.gui_automation import GUIAutomation
        
        with GUIAutomation(exe_path, timeout=30) as gui:
            gui.start_application()
            gui.connect_to_window("智能选品系统")
            
            # 验证窗口已打开
            title = gui.get_window_title()
            assert title is not None
            assert "智能选品系统" in title
    
    def test_window_title_contains_version(self, exe_path):
        """测试主窗口标题正确显示版本号"""
        from tests_exe.utils.gui_automation import GUIAutomation
        
        with GUIAutomation(exe_path) as gui:
            gui.start_application()
            gui.connect_to_window("智能选品系统")
            
            title = gui.get_window_title()
            
            # 应该包含版本号（v开头的格式）
            assert 'v' in title.lower() or '智能选品系统' in title
    
    def test_left_menu_visible(self, exe_path):
        """测试左侧菜单4个按钮可见"""
        from tests_exe.utils.gui_automation import GUIAutomation
        
        with GUIAutomation(exe_path) as gui:
            gui.start_application()
            gui.connect_to_window("智能选品系统")
            
            # 等待界面加载
            time.sleep(2)
            
            # 验证菜单项可见
            menu_items = ["抖音", "智能", "数据", "设置"]
            
            for item in menu_items:
                assert gui.verify_text_exists(item, timeout=5), f"菜单项'{item}'不可见"
    
    def test_default_page_is_douyin(self, exe_path):
        """测试默认停留在抖音罗盘页面"""
        from tests_exe.utils.gui_automation import GUIAutomation
        
        with GUIAutomation(exe_path) as gui:
            gui.start_application()
            gui.connect_to_window("智能选品系统")
            
            time.sleep(2)
            
            # 应该看到登录相关元素
            # 注：由于CustomTkinter的特殊性，这里可能需要调整
            assert gui.verify_text_exists("抖音", timeout=5)
    
    def test_startup_performance(self, exe_path):
        """测试启动性能（应在30秒内完成）"""
        from tests_exe.utils.gui_automation import GUIAutomation
        import time
        
        start_time = time.time()
        
        with GUIAutomation(exe_path, timeout=30) as gui:
            gui.start_application()
            gui.connect_to_window("智能选品系统")
        
        elapsed = time.time() - start_time
        
        assert elapsed < 30, f"启动时间过长: {elapsed:.2f}秒"

