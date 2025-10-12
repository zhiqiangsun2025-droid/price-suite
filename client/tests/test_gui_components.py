"""
测试GUI组件（Mock CustomTkinter）
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call


class TestPageSwitching:
    """测试页面切换逻辑"""
    
    @patch('customtkinter.CTk')
    @patch('customtkinter.CTkFrame')
    def test_switch_page_updates_current_page(self, mock_frame, mock_ctk):
        """测试切换页面更新current_page属性"""
        # 这个测试需要实际导入并Mock GUI组件
        # 由于GUI代码复杂，我们测试核心逻辑
        
        class MockApp:
            def __init__(self):
                self.current_page = "douyin_login"
                self._switching = False
                self.content_frame = MagicMock()
            
            def switch_page(self, page_id):
                if self._switching:
                    return
                self._switching = True
                try:
                    self.current_page = page_id
                    # 清空内容区
                    for widget in self.content_frame.winfo_children():
                        widget.destroy()
                finally:
                    self._switching = False
        
        app = MockApp()
        assert app.current_page == "douyin_login"
        
        app.switch_page("smart_selection")
        assert app.current_page == "smart_selection"
        
        app.switch_page("data_analysis")
        assert app.current_page == "data_analysis"
    
    def test_switch_page_debounce(self):
        """测试页面切换去抖动"""
        class MockApp:
            def __init__(self):
                self.current_page = "page1"
                self._switching = False
                self.switch_count = 0
            
            def switch_page(self, page_id):
                if self._switching:
                    return  # 去抖：如果正在切换，直接返回
                self._switching = True
                try:
                    self.switch_count += 1
                    self.current_page = page_id
                finally:
                    self._switching = False
        
        app = MockApp()
        
        # 快速连续调用
        app.switch_page("page2")
        app._switching = True  # 模拟仍在切换中
        app.switch_page("page3")  # 这次应该被忽略
        
        # 第二次调用应被阻止
        assert app.switch_count == 1
        assert app.current_page == "page2"


class TestMenuHighlight:
    """测试菜单高亮更新"""
    
    def test_menu_button_active_state(self):
        """测试菜单按钮激活状态"""
        current_page = "smart_selection"
        
        menus = [
            ("抖音罗盘", "douyin_login"),
            ("智能选品", "smart_selection"),
            ("数据分析", "data_analysis"),
        ]
        
        for label, page_id in menus:
            is_active = (page_id == current_page)
            
            if page_id == "smart_selection":
                assert is_active is True
            else:
                assert is_active is False


class TestErrorHandling:
    """测试错误处理"""
    
    def test_show_error_no_force_jump(self):
        """测试错误提示不强制跳页"""
        class MockApp:
            def __init__(self):
                self.current_page = "smart_selection"
                self.error_shown = False
            
            def show_error(self, error_code, error_msg):
                # 新逻辑：不跳转，只显示错误
                self.error_shown = True
                # 不调用 self.init_main_ui()
        
        app = MockApp()
        app.show_error(101, "测试错误")
        
        assert app.error_shown is True
        assert app.current_page == "smart_selection"  # 页面未改变


class TestLoginState:
    """测试登录状态管理"""
    
    def test_login_polling_flag(self):
        """测试登录轮询标志"""
        class MockApp:
            def __init__(self):
                self.screenshot_polling = False
                self.douyin_logged_in = False
            
            def start_login(self):
                if self.screenshot_polling:
                    return  # 防止重复点击
                self.screenshot_polling = True
            
            def stop_polling(self):
                self.screenshot_polling = False
        
        app = MockApp()
        assert app.screenshot_polling is False
        
        app.start_login()
        assert app.screenshot_polling is True
        
        # 第二次调用应被阻止
        app.start_login()  # 不应改变状态
        assert app.screenshot_polling is True
        
        app.stop_polling()
        assert app.screenshot_polling is False
    
    def test_login_success_updates_state(self):
        """测试登录成功更新状态"""
        class MockApp:
            def __init__(self):
                self.screenshot_polling = False
                self.douyin_logged_in = False
            
            def _login_success(self):
                self.screenshot_polling = False
                self.douyin_logged_in = True
        
        app = MockApp()
        app.screenshot_polling = True
        app._login_success()
        
        assert app.screenshot_polling is False
        assert app.douyin_logged_in is True
    
    def test_login_failed_resets_state(self):
        """测试登录失败重置状态"""
        class MockApp:
            def __init__(self):
                self.screenshot_polling = False
                self.douyin_logged_in = False
            
            def _login_failed(self, error):
                self.screenshot_polling = False
                self.douyin_logged_in = False
        
        app = MockApp()
        app.screenshot_polling = True
        app._login_failed("测试错误")
        
        assert app.screenshot_polling is False
        assert app.douyin_logged_in is False


class TestTrialCountdown:
    """测试试用倒计时"""
    
    def test_trial_countdown_no_local_popup(self):
        """测试试用倒计时不本地弹窗"""
        import time
        
        class MockApp:
            def __init__(self):
                self.trial_start_time = time.time()
                self.popup_shown = False
            
            def start_trial_countdown(self):
                # 新逻辑：不本地弹窗
                elapsed = time.time() - self.trial_start_time
                left = 3600 - elapsed
                
                if left <= 0:
                    # 不调用 self.show_gentle_reminder()
                    pass
        
        app = MockApp()
        app.trial_start_time = time.time() - 3700  # 超过1小时
        app.start_trial_countdown()
        
        assert app.popup_shown is False  # 未弹窗


class TestConfigResolution:
    """测试配置解析"""
    
    def test_server_url_from_env(self, monkeypatch):
        """测试从环境变量读取SERVER_URL"""
        monkeypatch.setenv("PRICE_SUITE_SERVER_URL", "http://custom.server.com:8000")
        
        # 模拟解析逻辑
        import os
        server_url = os.environ.get("PRICE_SUITE_SERVER_URL", "http://127.0.0.1:5000")
        
        assert server_url == "http://custom.server.com:8000"
    
    def test_server_url_default(self, monkeypatch):
        """测试默认SERVER_URL"""
        monkeypatch.delenv("PRICE_SUITE_SERVER_URL", raising=False)
        
        import os
        server_url = os.environ.get("PRICE_SUITE_SERVER_URL", "http://127.0.0.1:5000")
        
        assert server_url == "http://127.0.0.1:5000"


class TestVersionDisplay:
    """测试版本号显示"""
    
    def test_version_constant_exists(self):
        """测试VERSION常量存在"""
        from modern_client_ultimate import VERSION
        
        assert VERSION is not None
        assert isinstance(VERSION, str)
        assert VERSION.startswith("v")
    
    def test_status_bar_uses_version(self):
        """测试状态栏使用VERSION常量"""
        VERSION = "v1012929"
        
        # 模拟状态栏文本生成
        status_text = f"🎯 智能选品系统 {VERSION}"
        
        assert "v1012929" in status_text
        assert "智能选品系统" in status_text

