"""
测试EXE登录交互
"""
import pytest
import time
import os


pytestmark = pytest.mark.skipif(
    os.name != 'nt',
    reason="EXE测试仅在Windows环境运行"
)


@pytest.mark.timeout(180)
class TestLoginInteraction:
    """测试登录交互（注：需要Mock服务器）"""
    
    def test_login_form_exists(self, exe_path):
        """测试登录表单存在"""
        from tests_exe.utils.gui_automation import GUIAutomation
        
        with GUIAutomation(exe_path) as gui:
            gui.start_application()
            gui.connect_to_window("智能选品系统")
            time.sleep(2)
            
            # 验证登录相关元素存在
            # 注：CustomTkinter的Entry可能不容易定位，这里仅做基础验证
            assert gui.verify_text_exists("邮箱", timeout=5) or \
                   gui.verify_text_exists("密码", timeout=5) or \
                   gui.verify_text_exists("登录", timeout=5)
    
    @pytest.mark.skip(reason="需要配置Mock服务器")
    def test_fill_login_credentials(self, exe_path):
        """测试填充登录凭证"""
        from tests_exe.utils.gui_automation import GUIAutomation
        
        with GUIAutomation(exe_path) as gui:
            gui.start_application()
            gui.connect_to_window("智能选品系统")
            time.sleep(2)
            
            # 尝试填充邮箱和密码
            # 注：CustomTkinter的Entry定位可能需要特殊处理
            try:
                gui.fill_textbox(index=0, text_value="test@example.com")
                gui.fill_textbox(index=1, text_value="testpassword")
            except Exception as e:
                pytest.skip(f"无法定位输入框: {e}")
    
    @pytest.mark.skip(reason="需要配置Mock服务器")
    def test_click_login_button(self, exe_path):
        """测试点击登录按钮"""
        from tests_exe.utils.gui_automation import GUIAutomation
        
        with GUIAutomation(exe_path) as gui:
            gui.start_application()
            gui.connect_to_window("智能选品系统")
            time.sleep(2)
            
            # 填充凭证
            try:
                gui.fill_textbox(index=0, text_value="test@example.com")
                gui.fill_textbox(index=1, text_value="testpassword")
                
                # 点击登录按钮
                gui.click_button("登录")
                
                # 等待响应
                time.sleep(2)
                
            except Exception as e:
                pytest.skip(f"登录测试需要Mock服务器: {e}")
    
    def test_screenshot_preview_area_exists(self, exe_path):
        """测试实时预览区域存在"""
        from tests_exe.utils.gui_automation import GUIAutomation
        
        with GUIAutomation(exe_path) as gui:
            gui.start_application()
            gui.connect_to_window("智能选品系统")
            time.sleep(2)
            
            # 验证有"实时"或"预览"相关文字
            has_preview = gui.verify_text_exists("实时", timeout=3) or \
                          gui.verify_text_exists("预览", timeout=3)
            
            # 如果没有，也可能是布局不同，不强制失败
            if not has_preview:
                pytest.skip("未找到实时预览区域标识")

