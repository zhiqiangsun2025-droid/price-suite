"""
测试EXE页面导航
"""
import pytest
import time
import os


pytestmark = pytest.mark.skipif(
    os.name != 'nt',
    reason="EXE测试仅在Windows环境运行"
)


@pytest.mark.timeout(120)
class TestPageNavigation:
    """测试页面导航"""
    
    def test_navigate_to_smart_selection(self, exe_path):
        """测试导航到智能选品页"""
        from tests_exe.utils.gui_automation import GUIAutomation, MenuNavigator
        
        with GUIAutomation(exe_path) as gui:
            gui.start_application()
            gui.connect_to_window("智能选品系统")
            time.sleep(2)
            
            nav = MenuNavigator(gui)
            nav.click_menu_item("智能选品")
            
            # 验证页面切换成功
            time.sleep(1)
            assert gui.verify_text_exists("智能", timeout=5)
    
    def test_navigate_to_data_analysis(self, exe_path):
        """测试导航到数据分析页"""
        from tests_exe.utils.gui_automation import GUIAutomation, MenuNavigator
        
        with GUIAutomation(exe_path) as gui:
            gui.start_application()
            gui.connect_to_window("智能选品系统")
            time.sleep(2)
            
            nav = MenuNavigator(gui)
            nav.click_menu_item("数据分析")
            
            time.sleep(1)
            assert gui.verify_text_exists("数据", timeout=5)
    
    def test_navigate_to_settings(self, exe_path):
        """测试导航到系统设置页"""
        from tests_exe.utils.gui_automation import GUIAutomation, MenuNavigator
        
        with GUIAutomation(exe_path) as gui:
            gui.start_application()
            gui.connect_to_window("智能选品系统")
            time.sleep(2)
            
            nav = MenuNavigator(gui)
            nav.click_menu_item("系统设置")
            
            time.sleep(1)
            assert gui.verify_text_exists("设置", timeout=5)
    
    def test_navigate_back_to_douyin(self, exe_path):
        """测试能返回抖音罗盘页"""
        from tests_exe.utils.gui_automation import GUIAutomation, MenuNavigator
        
        with GUIAutomation(exe_path) as gui:
            gui.start_application()
            gui.connect_to_window("智能选品系统")
            time.sleep(2)
            
            nav = MenuNavigator(gui)
            
            # 先导航到其他页
            nav.click_menu_item("智能选品")
            time.sleep(1)
            
            # 再返回抖音罗盘
            nav.click_menu_item("抖音罗盘")
            time.sleep(1)
            
            assert gui.verify_text_exists("抖音", timeout=5)
    
    def test_multiple_page_switches(self, exe_path):
        """测试多次页面切换"""
        from tests_exe.utils.gui_automation import GUIAutomation, MenuNavigator
        
        with GUIAutomation(exe_path) as gui:
            gui.start_application()
            gui.connect_to_window("智能选品系统")
            time.sleep(2)
            
            nav = MenuNavigator(gui)
            
            # 连续切换多个页面
            pages = ["智能选品", "数据分析", "系统设置", "抖音罗盘"]
            
            for page in pages:
                nav.click_menu_item(page)
                time.sleep(0.8)
            
            # 最后应该在抖音罗盘页
            assert gui.verify_text_exists("抖音", timeout=5)
    
    def test_page_switch_performance(self, exe_path):
        """测试页面切换响应时间"""
        from tests_exe.utils.gui_automation import GUIAutomation, MenuNavigator
        import time
        
        with GUIAutomation(exe_path) as gui:
            gui.start_application()
            gui.connect_to_window("智能选品系统")
            time.sleep(2)
            
            nav = MenuNavigator(gui)
            
            start_time = time.time()
            nav.click_menu_item("智能选品")
            elapsed = time.time() - start_time
            
            # 页面切换应该在1秒内完成
            assert elapsed < 1.0, f"页面切换时间过长: {elapsed:.2f}秒"

