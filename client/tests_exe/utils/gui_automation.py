"""
GUI自动化工具封装（pywinauto）
"""
import time
import os
from pathlib import Path
try:
    from pywinauto import Application
    from pywinauto.findwindows import ElementNotFoundError
    from pywinauto.timings import TimeoutError
except ImportError:
    # 如果在非Windows环境运行，提供Mock
    class Application:
        pass
    ElementNotFoundError = Exception
    TimeoutError = Exception


class GUIAutomation:
    """GUI自动化操作封装类"""
    
    def __init__(self, exe_path, timeout=30):
        """
        初始化GUI自动化
        
        Args:
            exe_path: EXE文件路径
            timeout: 启动超时时间（秒）
        """
        self.exe_path = exe_path
        self.timeout = timeout
        self.app = None
        self.window = None
    
    def start_application(self):
        """启动应用程序"""
        print(f"启动应用: {self.exe_path}")
        
        if not os.path.exists(self.exe_path):
            raise FileNotFoundError(f"EXE文件不存在: {self.exe_path}")
        
        self.app = Application(backend="uia").start(self.exe_path, timeout=self.timeout)
        time.sleep(3)  # 等待应用完全启动
        
        return self
    
    def connect_to_window(self, title_pattern=None):
        """
        连接到主窗口
        
        Args:
            title_pattern: 窗口标题匹配模式
        """
        if title_pattern:
            self.window = self.app.window(title_re=f".*{title_pattern}.*")
        else:
            # 默认连接到第一个窗口
            self.window = self.app.top_window()
        
        self.window.wait('visible', timeout=self.timeout)
        return self
    
    def click_button(self, button_text, exact=False):
        """
        点击按钮
        
        Args:
            button_text: 按钮文本
            exact: 是否精确匹配
        """
        print(f"点击按钮: {button_text}")
        
        if exact:
            button = self.window.child_window(title=button_text, control_type="Button")
        else:
            button = self.window.child_window(title_re=f".*{button_text}.*", control_type="Button")
        
        button.wait('visible', timeout=10)
        button.click_input()
        time.sleep(0.5)
        
        return self
    
    def fill_textbox(self, control_id=None, text_value="", index=0):
        """
        填充文本框
        
        Args:
            control_id: 控件ID或名称
            text_value: 要填充的文本
            index: 如果有多个文本框，指定索引
        """
        print(f"填充文本框 [索引:{index}]: {text_value[:20]}...")
        
        if control_id:
            textbox = self.window.child_window(auto_id=control_id, control_type="Edit")
        else:
            # 按索引查找所有Edit控件
            textboxes = self.window.descendants(control_type="Edit")
            if index >= len(textboxes):
                raise ValueError(f"文本框索引{index}超出范围")
            textbox = textboxes[index]
        
        textbox.wait('visible', timeout=10)
        textbox.set_focus()
        textbox.set_text(text_value)
        time.sleep(0.3)
        
        return self
    
    def verify_text_exists(self, text, timeout=5):
        """
        验证文本存在
        
        Args:
            text: 要验证的文本
            timeout: 超时时间
        
        Returns:
            bool: 文本是否存在
        """
        print(f"验证文本存在: {text}")
        
        try:
            element = self.window.child_window(title_re=f".*{text}.*", timeout=timeout)
            return element.exists()
        except:
            return False
    
    def wait_for_text(self, text, timeout=10):
        """等待文本出现"""
        print(f"等待文本出现: {text}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.verify_text_exists(text, timeout=1):
                return True
            time.sleep(0.5)
        
        return False
    
    def get_window_title(self):
        """获取窗口标题"""
        if self.window:
            return self.window.window_text()
        return None
    
    def take_screenshot(self, filepath):
        """截图保存"""
        print(f"截图保存到: {filepath}")
        
        if self.window:
            self.window.capture_as_image().save(filepath)
        
        return self
    
    def close_application(self):
        """关闭应用程序"""
        print("关闭应用")
        
        if self.app:
            try:
                self.app.kill()
            except:
                pass
        
        time.sleep(1)
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close_application()


class MenuNavigator:
    """菜单导航辅助类"""
    
    def __init__(self, gui_automation):
        self.gui = gui_automation
    
    def click_menu_item(self, menu_text):
        """点击菜单项"""
        menu_items = {
            "抖音罗盘": "抖音",
            "智能选品": "智能",
            "数据分析": "数据",
            "系统设置": "设置"
        }
        
        search_text = menu_items.get(menu_text, menu_text)
        self.gui.click_button(search_text)
        time.sleep(1)
        
        return self
    
    def verify_page_active(self, page_name):
        """验证页面激活"""
        return self.gui.verify_text_exists(page_name)

