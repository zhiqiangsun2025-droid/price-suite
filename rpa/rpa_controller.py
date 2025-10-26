#!/usr/bin/env python3
"""
桌面应用程序自动化控制器 (RPA)
功能：
1. 自动打开铺货软件
2. 自动输入商品链接
3. 自动点击铺货按钮
4. 导出铺货结果
5. 支持任何 Windows 桌面软件
"""

import pyautogui
import pywinauto
from pywinauto import Application, Desktop
import time
import cv2
import numpy as np
from PIL import Image
import os
import json
from datetime import datetime
import argparse

# ==================== 配置 ====================

class RPAConfig:
    """RPA配置类"""
    
    # 铺货软件配置
    LISTING_SOFTWARE_PATH = r"C:\Program Files\铺货软件\listing.exe"  # 修改为实际路径
    LISTING_SOFTWARE_NAME = "铺货助手"  # 窗口标题
    
    # 延迟设置
    CLICK_DELAY = 0.5  # 点击延迟
    TYPE_DELAY = 0.1   # 输入延迟
    WAIT_TIMEOUT = 10  # 等待超时
    
    # 截图目录
    SCREENSHOT_DIR = "screenshots"
    
    # 模板图片目录（存放按钮截图）
    TEMPLATE_DIR = "templates"

# ==================== 基础RPA工具类 ====================

class RPATools:
    """RPA基础工具"""
    
    def __init__(self):
        # 安全设置：启用fail-safe
        pyautogui.FAILSAFE = True  # 鼠标移到屏幕左上角会停止
        pyautogui.PAUSE = 0.5
        
        # 创建目录
        os.makedirs(RPAConfig.SCREENSHOT_DIR, exist_ok=True)
        os.makedirs(RPAConfig.TEMPLATE_DIR, exist_ok=True)
    
    def take_screenshot(self, filename=None):
        """截取屏幕"""
        if not filename:
            filename = f"screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        path = os.path.join(RPAConfig.SCREENSHOT_DIR, filename)
        screenshot = pyautogui.screenshot()
        screenshot.save(path)
        print(f"📸 截图已保存: {path}")
        return path
    
    def find_image_on_screen(self, template_path, confidence=0.8):
        """
        在屏幕上查找图片
        返回：(x, y) 中心坐标，如果未找到返回 None
        """
        try:
            # 截取屏幕
            screenshot = pyautogui.screenshot()
            screenshot_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # 读取模板
            template = cv2.imread(template_path)
            if template is None:
                print(f"❌ 模板图片不存在: {template_path}")
                return None
            
            # 模板匹配
            result = cv2.matchTemplate(screenshot_np, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= confidence:
                # 计算中心点
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                print(f"✅ 找到图片: {template_path} at ({center_x}, {center_y}), 置信度: {max_val:.2f}")
                return (center_x, center_y)
            else:
                print(f"❌ 未找到图片: {template_path}, 最高置信度: {max_val:.2f}")
                return None
        
        except Exception as e:
            print(f"❌ 图片识别出错: {e}")
            return None
    
    def click_image(self, template_path, confidence=0.8, clicks=1):
        """点击屏幕上的图片"""
        position = self.find_image_on_screen(template_path, confidence)
        if position:
            pyautogui.click(position[0], position[1], clicks=clicks)
            time.sleep(RPAConfig.CLICK_DELAY)
            print(f"🖱️ 已点击: {template_path}")
            return True
        return False
    
    def wait_for_image(self, template_path, timeout=10, confidence=0.8):
        """等待图片出现"""
        print(f"⏳ 等待图片出现: {template_path}")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            position = self.find_image_on_screen(template_path, confidence)
            if position:
                print(f"✅ 图片已出现")
                return position
            time.sleep(0.5)
        
        print(f"❌ 等待超时: {template_path}")
        return None
    
    def type_text(self, text, interval=0.1):
        """输入文本"""
        pyautogui.typewrite(text, interval=interval)
        print(f"⌨️ 已输入: {text}")
    
    def type_chinese(self, text):
        """输入中文（使用粘贴方式）"""
        import pyperclip
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.2)
        print(f"⌨️ 已输入中文: {text}")
    
    def press_key(self, key):
        """按键"""
        pyautogui.press(key)
        time.sleep(0.2)
        print(f"⌨️ 已按键: {key}")
    
    def hotkey(self, *keys):
        """组合键"""
        pyautogui.hotkey(*keys)
        time.sleep(0.2)
        print(f"⌨️ 已按组合键: {'+'.join(keys)}")

# ==================== Windows应用程序控制类 ====================

class WindowsAppController:
    """Windows应用程序控制器"""
    
    def __init__(self, app_path=None, window_title=None):
        self.app_path = app_path
        self.window_title = window_title
        self.app = None
        self.window = None
    
    def start_app(self):
        """启动应用程序"""
        try:
            if self.app_path and os.path.exists(self.app_path):
                print(f"🚀 启动应用: {self.app_path}")
                self.app = Application(backend="uia").start(self.app_path)
                time.sleep(3)  # 等待应用启动
                return True
            else:
                print(f"❌ 应用程序不存在: {self.app_path}")
                return False
        except Exception as e:
            print(f"❌ 启动应用失败: {e}")
            return False
    
    def connect_app(self, title=None):
        """连接到已运行的应用"""
        try:
            title = title or self.window_title
            print(f"🔗 连接到应用: {title}")
            self.app = Application(backend="uia").connect(title=title)
            self.window = self.app.window(title=title)
            return True
        except Exception as e:
            print(f"❌ 连接应用失败: {e}")
            return False
    
    def find_window_by_title(self, title):
        """根据标题查找窗口"""
        try:
            desktop = Desktop(backend="uia")
            windows = desktop.windows()
            for win in windows:
                if title in win.window_text():
                    print(f"✅ 找到窗口: {win.window_text()}")
                    self.window = win
                    return win
            print(f"❌ 未找到窗口: {title}")
            return None
        except Exception as e:
            print(f"❌ 查找窗口出错: {e}")
            return None
    
    def activate_window(self):
        """激活窗口（置顶）"""
        if self.window:
            self.window.set_focus()
            print(f"✅ 窗口已激活")
    
    def click_button(self, button_text):
        """点击按钮（通过文本）"""
        try:
            if self.window:
                button = self.window.child_window(title=button_text, control_type="Button")
                button.click()
                print(f"🖱️ 已点击按钮: {button_text}")
                return True
        except Exception as e:
            print(f"❌ 点击按钮失败: {e}")
            return False
    
    def input_text_to_edit(self, text, control_index=0):
        """在编辑框中输入文本"""
        try:
            if self.window:
                edit_controls = self.window.descendants(control_type="Edit")
                if edit_controls and len(edit_controls) > control_index:
                    edit = edit_controls[control_index]
                    edit.set_focus()
                    edit.set_text(text)
                    print(f"⌨️ 已输入文本到编辑框 [{control_index}]: {text}")
                    return True
        except Exception as e:
            print(f"❌ 输入文本失败: {e}")
            return False

# ==================== 铺货软件自动化类 ====================

class ListingSoftwareAutomator:
    """铺货软件自动化控制器"""
    
    def __init__(self):
        self.rpa = RPATools()
        self.app_controller = WindowsAppController(
            app_path=RPAConfig.LISTING_SOFTWARE_PATH,
            window_title=RPAConfig.LISTING_SOFTWARE_NAME
        )
        self.results = []
    
    def start(self):
        """启动铺货软件"""
        print("\n" + "=" * 60)
        print("🚀 启动铺货软件")
        print("=" * 60)
        
        # 方法1：通过路径启动
        success = self.app_controller.start_app()
        
        # 方法2：如果已经运行，则连接
        if not success:
            success = self.app_controller.connect_app()
        
        # 方法3：通过图像识别（最通用）
        if not success:
            print("⚠️ 使用图像识别模式（需要预先准备模板图片）")
        
        time.sleep(2)
        return success
    
    def input_product_links(self, links):
        """
        批量输入商品链接
        links: 商品链接列表
        """
        print("\n" + "=" * 60)
        print(f"📝 输入商品链接 ({len(links)} 个)")
        print("=" * 60)
        
        for idx, link in enumerate(links, 1):
            print(f"\n[{idx}/{len(links)}] 处理链接: {link[:50]}...")
            
            # 策略1：使用pywinauto定位输入框
            success = self.app_controller.input_text_to_edit(link, control_index=0)
            
            # 策略2：使用图像识别点击输入框
            if not success:
                # 点击"商品链接输入框"模板
                template = os.path.join(RPAConfig.TEMPLATE_DIR, "input_box.png")
                if os.path.exists(template):
                    self.rpa.click_image(template)
                    time.sleep(0.5)
                    
                    # 清空输入框
                    self.rpa.hotkey('ctrl', 'a')
                    self.rpa.press_key('delete')
                    
                    # 输入链接
                    self.rpa.type_text(link)
            
            # 策略3：直接使用坐标（不推荐，但最简单）
            # pyautogui.click(500, 300)  # 替换为实际坐标
            # self.rpa.type_text(link)
            
            time.sleep(0.5)
    
    def click_listing_button(self):
        """点击铺货按钮"""
        print("\n" + "=" * 60)
        print("🖱️ 点击铺货按钮")
        print("=" * 60)
        
        # 策略1：通过按钮文本
        success = self.app_controller.click_button("铺货")
        if success:
            return True
        
        success = self.app_controller.click_button("一键铺货")
        if success:
            return True
        
        # 策略2：通过图像识别
        template = os.path.join(RPAConfig.TEMPLATE_DIR, "listing_button.png")
        if os.path.exists(template):
            success = self.rpa.click_image(template)
            if success:
                return True
        
        # 策略3：使用快捷键（如果软件支持）
        # self.rpa.hotkey('ctrl', 'enter')
        
        print("⚠️ 所有策略都失败，请手动配置")
        return False
    
    def wait_for_completion(self, timeout=60):
        """等待铺货完成"""
        print("\n" + "=" * 60)
        print("⏳ 等待铺货完成...")
        print("=" * 60)
        
        # 策略1：等待"完成"提示
        template = os.path.join(RPAConfig.TEMPLATE_DIR, "completion_message.png")
        if os.path.exists(template):
            position = self.rpa.wait_for_image(template, timeout=timeout)
            if position:
                print("✅ 铺货完成！")
                return True
        
        # 策略2：定时等待
        print(f"⏳ 等待 {timeout} 秒...")
        time.sleep(timeout)
        
        return True
    
    def export_results(self, output_path=None):
        """导出铺货结果"""
        print("\n" + "=" * 60)
        print("📊 导出铺货结果")
        print("=" * 60)
        
        if not output_path:
            output_path = f"listing_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # 策略1：点击导出按钮
        template = os.path.join(RPAConfig.TEMPLATE_DIR, "export_button.png")
        if os.path.exists(template):
            self.rpa.click_image(template)
            time.sleep(1)
        
        # 策略2：使用快捷键
        self.rpa.hotkey('ctrl', 's')
        time.sleep(1)
        
        # 输入文件名
        self.rpa.type_text(output_path)
        self.rpa.press_key('enter')
        
        print(f"✅ 结果已导出: {output_path}")
        return output_path
    
    def run_full_process(self, product_links):
        """
        执行完整的铺货流程
        """
        print("\n" + "=" * 80)
        print("🤖 自动化铺货流程开始")
        print("=" * 80)
        
        try:
            # 1. 启动软件
            self.start()
            
            # 2. 截图记录初始状态
            self.rpa.take_screenshot("step1_started.png")
            
            # 3. 输入商品链接
            self.input_product_links(product_links)
            self.rpa.take_screenshot("step2_links_inputted.png")
            
            # 4. 点击铺货按钮
            self.click_listing_button()
            self.rpa.take_screenshot("step3_listing_clicked.png")
            
            # 5. 等待完成
            self.wait_for_completion()
            self.rpa.take_screenshot("step4_completed.png")
            
            # 6. 导出结果
            result_path = self.export_results()
            self.rpa.take_screenshot("step5_exported.png")
            
            print("\n" + "=" * 80)
            print("✅ 自动化铺货流程完成！")
            print("=" * 80)
            
            return {
                'success': True,
                'result_path': result_path,
                'product_count': len(product_links)
            }
        
        except Exception as e:
            print(f"\n❌ 流程执行出错: {e}")
            self.rpa.take_screenshot("error.png")
            return {
                'success': False,
                'error': str(e)
            }

# ==================== 示例：创建模板图片工具 ====================

class TemplateCreator:
    """模板图片创建工具"""
    
    @staticmethod
    def create_template_interactive():
        """交互式创建模板"""
        print("\n" + "=" * 60)
        print("📸 模板图片创建工具")
        print("=" * 60)
        print("\n使用说明：")
        print("1. 打开铺货软件")
        print("2. 按下 'c' 键截取当前屏幕")
        print("3. 在弹出的图片中，用鼠标选择要识别的区域")
        print("4. 保存为模板图片")
        print("\n按 Enter 开始...")
        input()
        
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        
        # 使用OpenCV显示图片并允许用户选择区域
        cv2.imshow('Screenshot - Select ROI', cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR))
        
        # 让用户选择区域
        roi = cv2.selectROI('Screenshot - Select ROI', cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR))
        
        if roi[2] > 0 and roi[3] > 0:
            # 裁剪选中区域
            x, y, w, h = roi
            template = screenshot_np[y:y+h, x:x+w]
            
            # 保存模板
            template_name = input("\n模板名称（如 listing_button）: ")
            template_path = os.path.join(RPAConfig.TEMPLATE_DIR, f"{template_name}.png")
            cv2.imwrite(template_path, cv2.cvtColor(template, cv2.COLOR_RGB2BGR))
            
            print(f"✅ 模板已保存: {template_path}")
        
        cv2.destroyAllWindows()

# ==================== 主程序 ====================

def main():
    """CLI：从命令行接收 CSV 或以逗号分隔的链接执行铺货"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--links', help='逗号分隔的商品链接列表')
    parser.add_argument('--csv', help='CSV文件路径')
    parser.add_argument('--excel', help='Excel文件路径（客户端使用）')
    parser.add_argument('--column', default='抖音链接', help='读取的列名（默认：抖音链接）')
    args = parser.parse_args()

    links = []
    
    if args.links:
        links = [x.strip() for x in args.links.split(',') if x.strip()]
        print(f'✅ 接收到 {len(links)} 个链接')
    
    elif args.excel and os.path.exists(args.excel):
        try:
            import pandas as pd
            df = pd.read_excel(args.excel)
            column = args.column
            if column not in df.columns:
                possible_columns = ['抖音链接', 'douyin_url', 'url', '链接']
                for col in possible_columns:
                    if col in df.columns:
                        column = col
                        break
                else:
                    print(f'❌ Excel中没有列 "{args.column}"，可用列: {", ".join(df.columns)}')
                    return
            links = df[column].dropna().tolist()
            print(f'✅ 从Excel读取到 {len(links)} 个链接（列: {column}）')
        except ImportError:
            print('❌ 请安装pandas: pip install pandas openpyxl')
            return
        except Exception as e:
            print(f'❌ 读取Excel失败: {e}')
            return
    
    elif args.csv and os.path.exists(args.csv):
        import csv
        with open(args.csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get('url') or row.get('链接') or row.get('pdd_url')
                if url:
                    links.append(url)
        print(f'✅ 从CSV读取到 {len(links)} 个链接')
    
    else:
        print('❌ 请提供链接来源: --links 或 --csv 或 --excel')
        return

    if not links:
        print('❌ 没有可铺货的链接')
        return

    print(f'\n开始自动铺货 {len(links)} 个商品...')
    print('=' * 60)
    
    automator = ListingSoftwareAutomator()
    result = automator.run_full_process(links)
    
    print('=' * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    # 首次使用：创建模板
    # TemplateCreator.create_template_interactive()
    
    # 正常使用：执行自动化
    main()

