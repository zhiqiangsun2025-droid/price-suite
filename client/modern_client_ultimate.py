#!/usr/bin/env python3
"""
智能选品铺货系统 - 终极版客户端
仿微信UI + 智能选品 + 实时画面
版本：20251023001
"""

VERSION = "20251023001"

import customtkinter as ctk
import requests
import json
import uuid
import hashlib
import platform
import subprocess
from datetime import datetime
import time
import os
from tkinter import messagebox
import threading
import pandas as pd
from PIL import Image
from io import BytesIO
import base64
import webbrowser
import logging
import traceback
from typing import Optional, Dict, List, Any

# ==================== 日志配置 ====================
# 配置日志系统
def setup_logging():
    """设置日志系统"""
    log_dir = os.path.join(os.path.expanduser('~'), '.config', '智能选品系统')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'client.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

# 浅色主题（仿微信）
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

# ==================== 配置（可覆盖） ====================
def _resolve_server_url() -> str:
    """从环境变量/配置文件解析后端地址，默认回落到本机。
    优先级：环境变量 PRICE_SUITE_SERVER_URL > 同目录 config_client.json.server_url > 默认 http://127.0.0.1:5000
    """
    try:
        import os, json
        import logging
        
        env_url = os.environ.get("PRICE_SUITE_SERVER_URL")
        if env_url and env_url.strip():
            return env_url.strip()
        
        # 配置文件位于当前脚本同级目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cfg_path = os.path.join(script_dir, "config_client.json")
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                url = (data or {}).get("server_url")
                if url and isinstance(url, str) and url.strip():
                    return url.strip()
    except Exception as e:
        # 记录错误但不中断
        try:
            logging.warning(f"解析服务器地址失败: {e}")
        except:
            pass
    
    # 默认使用本地服务器
    return "http://127.0.0.1:5000"

SERVER_URL = _resolve_server_url()

# ==================== 常量配置 ====================
class Config:
    """应用配置常量"""
    # 试用时长
    TRIAL_DURATION = 3600  # 1小时试用（秒）
    TRIAL_CHECK_INTERVAL = 60000  # 试用检查间隔（毫秒）
    
    # 联系方式
    CONTACT_QQ = "123456789"
    
    # 窗口配置
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 900
    
    # 截图轮询
    SCREENSHOT_POLL_INTERVAL = 5000  # 截图轮询间隔（毫秒）
    SCREENSHOT_REQUEST_TIMEOUT = 5  # 截图请求超时（秒）
    SCREENSHOT_MAX_WIDTH = 800  # 截图最大宽度
    SCREENSHOT_MAX_HEIGHT = 600  # 截图最大高度
    
    # 请求超时
    LOGIN_TIMEOUT = 60  # 登录请求超时（秒）
    SCRAPE_TIMEOUT = 120  # 爬取请求超时（秒）
    REGISTER_TIMEOUT = 10  # 注册请求超时（秒）
    
    # 验证码输入超时
    CODE_INPUT_TIMEOUT = 60  # 验证码输入超时（秒）

# 仿微信配色
class Theme:
    # 背景色（浅色系）
    BG_PRIMARY = "#EDEDED"        # 主背景（浅灰）
    BG_SECONDARY = "#F7F7F7"      # 次级背景
    CARD_BG = "#FFFFFF"           # 卡片背景（白色）
    
    # 主色调（微信风格）
    PRIMARY = "#07C160"           # 微信绿
    SECONDARY = "#576B95"         # 微信蓝
    RED = "#FA5151"               # 错误红
    ORANGE = "#FA9D3B"            # 警告橙
    YELLOW = "#FFC300"            # 提示黄
    CYAN = "#10AEFF"              # 信息蓝
    GREEN = "#07C160"             # 成功绿
    
    # 文字（深色系）
    TEXT_PRIMARY = "#191919"      # 主文字（深黑）
    TEXT_SECONDARY = "#666666"    # 次级文字
    TEXT_HINT = "#999999"         # 提示文字
    
    # 边框
    BORDER = "#E5E5E5"            # 边框颜色

# ==================== 工具函数 ====================

def get_config_path():
    """配置文件路径（系统隐藏目录）"""
    if platform.system() == 'Windows':
        app_data = os.path.expandvars(r'%LOCALAPPDATA%')
        config_dir = os.path.join(app_data, '智能选品系统')
    else:
        config_dir = os.path.join(os.path.expanduser('~'), '.config', '智能选品系统')
    
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    return os.path.join(config_dir, 'config.json')

CONFIG_FILE = get_config_path()

def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info("配置文件加载成功")
                return config
        except json.JSONDecodeError as e:
            logger.error(f"配置文件JSON格式错误: {e}")
            return {}
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}
    return {}

def save_config(config: Dict[str, Any]) -> None:
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info("配置文件保存成功")
    except Exception as e:
        logger.error(f"保存配置文件失败: {e}")
        raise

def get_hardware_id() -> str:
    """获取硬件指纹ID"""
    try:
        # 获取MAC地址
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                       for elements in range(0, 2*6, 2)][::-1])
        
        # 获取磁盘序列号（仅Windows）
        disk_serial = "UNKNOWN"
        if platform.system() == 'Windows':
            try:
                output = subprocess.check_output(
                    "wmic diskdrive get serialnumber", 
                    shell=True, 
                    stderr=subprocess.DEVNULL
                ).decode()
                lines = output.strip().split('\n')
                if len(lines) > 1:
                    disk_serial = lines[1].strip()
            except Exception as e:
                logger.warning(f"获取磁盘序列号失败: {e}")
                disk_serial = "UNKNOWN"
        
        # 组合硬件信息
        hardware_string = f"{mac}_{disk_serial}_{platform.node()}"
        hardware_id = hashlib.sha256(hardware_string.encode()).hexdigest()[:32]
        logger.info(f"硬件ID生成成功: {hardware_id}")
        return hardware_id
    except Exception as e:
        logger.error(f"生成硬件ID失败: {e}")
        return "HARDWARE_ERROR"

# ==================== 主应用 ====================

class UltimateApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 窗口配置
        self.title(f"🎯 智能选品系统 · 终极版 {VERSION}")
        self.geometry(f"{Config.WINDOW_WIDTH}x{Config.WINDOW_HEIGHT}")
        self.configure(fg_color=Theme.BG_PRIMARY)
        
        # 数据
        self.hardware_id = get_hardware_id()
        self.client_id = None
        self.is_active = None
        self.trial_start_time = None
        self.douyin_logged_in = False  # 抖音登录状态
        self.rank_options = {}  # 动态获取的选项
        
        # 自动注册并初始化
        self.auto_register()
    
    def auto_register(self) -> None:
        """自动注册并初始化客户端"""
        config = load_config()
        
        if 'client_id' in config:
            self.client_id = config['client_id']
            self.is_active = config.get('is_active', 0)
            
            if 'trial_start_time' in config:
                self.trial_start_time = config['trial_start_time']
            
            # 恢复登录状态
            if config.get('douyin_logged_in', False):
                self.douyin_logged_in = True
                logger.info("从配置文件恢复登录状态: 已登录")
            
            logger.info(f"使用已有客户端ID: {self.client_id}, 激活状态: {self.is_active}")
            self.init_main_ui()
        else:
            logger.info("首次运行，开始注册客户端")
            try:
                response = requests.post(
                    f"{SERVER_URL}/api/register",
                    json={'hardware_id': self.hardware_id},
                    timeout=Config.REGISTER_TIMEOUT
                )
                
                logger.info(f"注册响应状态: {response.status_code}")
                
                if response.ok:
                    result = response.json()
                    if result.get('success'):
                        self.client_id = result['client_id']
                        self.is_active = result['is_active']
                        
                        config['client_id'] = self.client_id
                        config['is_active'] = self.is_active
                        
                        if self.is_active == 0:
                            config['trial_start_time'] = time.time()
                            self.trial_start_time = config['trial_start_time']
                        
                        save_config(config)
                        logger.info(f"注册成功，客户端ID: {self.client_id}")
                        self.init_main_ui()
                    else:
                        error_msg = result.get('error', '注册失败')
                        logger.error(f"注册失败: {error_msg}")
                        self.show_error(101, error_msg)
                else:
                    logger.error(f"服务器返回错误: {response.status_code}")
                    self.show_error(101, f'服务器错误：{response.status_code}')
            
            except requests.Timeout:
                logger.error("注册请求超时")
                self.show_error(101, '连接服务器超时，请检查网络连接')
            except requests.RequestException as e:
                logger.error(f"注册网络异常: {e}")
                self.show_error(101, f'网络错误：{str(e)}')
            except Exception as e:
                logger.error(f"注册异常: {e}\n{traceback.format_exc()}")
                self.show_error(101, f'连接服务器失败：{str(e)}')
    
    def init_main_ui(self):
        """初始化主UI"""
        # 顶部状态栏
        self.create_status_bar()
        
        # 主容器
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # 左侧菜单
        self.create_left_menu(main_container)
        
        # 右侧内容区
        self.content_frame = ctk.CTkFrame(main_container, fg_color=Theme.BG_PRIMARY)
        self.content_frame.pack(side="right", fill="both", expand=True)
        
        # 默认显示登录页
        self.show_douyin_login()
        
        # 启动倒计时
        if self.is_active == 0:
            self.start_trial_countdown()
    
    def create_status_bar(self):
        """创建状态栏（简洁版，无授权提示）"""
        status_bar = ctk.CTkFrame(self, fg_color=Theme.BG_SECONDARY, height=50, corner_radius=0)
        status_bar.pack(fill="x", side="top")
        
        # 只显示软件名称和版本（不显示授权状态）
        title = ctk.CTkLabel(
            status_bar,
            text=f"🎯 智能选品系统 {VERSION}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        title.pack(side="left", padx=20, pady=12)
        
        # 右侧显示当前日期（显得更专业）
        from datetime import datetime
        date_str = datetime.now().strftime("%Y年%m月%d日")
        date_label = ctk.CTkLabel(
            status_bar,
            text=date_str,
            font=ctk.CTkFont(size=12),
            text_color=Theme.TEXT_SECONDARY
        )
        date_label.pack(side="right", padx=20, pady=12)
    
    def start_trial_countdown(self):
        """静默检查授权（不再本地弹窗，仅依赖后端指令）。"""
        def update():
            if not hasattr(self, 'trial_start_time') or self.trial_start_time is None:
                return

            # 若本地判断试用结束，交由后端接口在需要时返回403+show_popup
            elapsed = time.time() - self.trial_start_time
            left = Config.TRIAL_DURATION - elapsed
            if left > 0:
                self.after(Config.TRIAL_CHECK_INTERVAL, update)  # 定期检查
            # 结束则不做任何本地弹窗动作，由后续 API 调用按后端返回处理

        update()
    
    def create_left_menu(self, parent):
        """创建左侧菜单（仿微信风格）"""
        menu = ctk.CTkFrame(parent, width=200, fg_color=Theme.BG_SECONDARY, corner_radius=0)
        menu.pack(side="left", fill="y")
        menu.pack_propagate(False)
        
        # Logo区域（优化间距）
        logo_frame = ctk.CTkFrame(menu, fg_color="transparent", height=100)
        logo_frame.pack(fill="x", pady=(30, 20))
        
        ctk.CTkLabel(
            logo_frame,
            text="🎯",
            font=ctk.CTkFont(size=48)  # 更大的图标
        ).pack(pady=(0, 5))
        
        ctk.CTkLabel(
            logo_frame,
            text="智能选品系统",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=Theme.PRIMARY  # 使用主色调
        ).pack()
        
        # 菜单项（优化图标和文字）
        self.current_page = "douyin_login"
        
        menus = [
            ("📱  抖音罗盘", "douyin_login"),
            ("🎯  智能选品", "smart_selection"),
            ("📊  数据分析", "data_analysis"),
            ("⚙️  系统设置", "settings"),
        ]
        
        # 添加间距
        ctk.CTkFrame(menu, height=10, fg_color="transparent").pack()
        
        # 存储按钮引用以便后续更新
        self.menu_buttons = {}
        for label, page_id in menus:
            btn = self.create_menu_btn(menu, label, page_id)
            self.menu_buttons[page_id] = btn
    
    def create_menu_btn(self, parent, label, page_id):
        """创建菜单按钮（微信风格）"""
        is_active = (page_id == self.current_page)
        
        btn = ctk.CTkButton(
            parent,
            text=label,
            font=ctk.CTkFont(size=14, weight="bold" if is_active else "normal"),
            fg_color=Theme.PRIMARY if is_active else "transparent",
            hover_color=Theme.PRIMARY if not is_active else self.darken_color(Theme.PRIMARY),
            text_color="white" if is_active else Theme.TEXT_PRIMARY,
            anchor="w",
            height=48,
            corner_radius=8,
            border_width=0,
            command=lambda: self.switch_page(page_id)
        )
        btn.pack(fill="x", padx=12, pady=6)
        return btn
    
    def darken_color(self, hex_color, factor=0.8):
        """使颜色变暗"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def switch_page(self, page_id: str) -> None:
        """切换页面（优化：不重建菜单，仅更新高亮）"""
        # 去抖：防止重复点击导致状态错乱
        if getattr(self, "_switching", False):
            logger.debug("页面切换中，忽略重复请求")
            return
        
        if self.current_page == page_id:
            logger.debug(f"已在当前页面: {page_id}")
            return
        
        self._switching = True
        try:
            logger.info(f"切换页面: {self.current_page} -> {page_id}")
            old_page = self.current_page
            self.current_page = page_id
            
            # 清空内容区
            for widget in self.content_frame.winfo_children():
                widget.destroy()

            # 优化：只更新菜单按钮状态，不重建整个菜单
            self.update_menu_highlight()
        finally:
            self._switching = False
        
        # 显示对应页面
        if page_id == "douyin_login":
            self.show_douyin_login()
        elif page_id == "smart_selection":
            self.show_smart_selection()
        elif page_id == "data_analysis":
            self.show_data_analysis()
        elif page_id == "settings":
            self.show_settings()
    
    def update_menu_highlight(self) -> None:
        """更新菜单按钮高亮状态（不重建）"""
        if not hasattr(self, 'menu_buttons'):
            return
        
        for page_id, btn in self.menu_buttons.items():
            is_active = (page_id == self.current_page)
            btn.configure(
                font=ctk.CTkFont(size=14, weight="bold" if is_active else "normal"),
                fg_color=Theme.PRIMARY if is_active else "transparent",
                hover_color=Theme.PRIMARY if not is_active else self.darken_color(Theme.PRIMARY),
                text_color="white" if is_active else Theme.TEXT_PRIMARY
            )
    
    # ==================== 页面1：抖音罗盘登录 ====================
    
    def show_douyin_login(self):
        """抖音罗盘登录页面"""
        container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=30)
        
        # 标题
        title_frame = ctk.CTkFrame(container, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0,30))
        
        ctk.CTkLabel(
            title_frame,
            text="📱 抖音商品罗盘登录",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=Theme.RED
        ).pack(side="left")
        
        # 登录状态
        self.douyin_status_label = ctk.CTkLabel(
            title_frame,
            text="⭕ 未登录",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        )
        self.douyin_status_label.pack(side="right")
        
        # 左右分栏
        cols = ctk.CTkFrame(container, fg_color="transparent")
        cols.pack(fill="both", expand=True)
        
        # 左侧：登录表单
        left = ctk.CTkFrame(cols, fg_color=Theme.CARD_BG, corner_radius=20)
        left.pack(side="left", fill="both", expand=True, padx=(0,15))
        
        ctk.CTkLabel(
            left,
            text="🔐 登录信息",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=Theme.ORANGE
        ).pack(pady=(30,20))
        
        # 邮箱
        ctk.CTkLabel(left, text="📧 邮箱账号", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=40, pady=(10,5))
        self.email_entry = ctk.CTkEntry(left, width=400, height=45, font=ctk.CTkFont(size=14), placeholder_text="请输入抖店邮箱")
        self.email_entry.pack(padx=40)
        
        # 密码
        ctk.CTkLabel(left, text="🔑 登录密码", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=40, pady=(20,5))
        self.pwd_entry = ctk.CTkEntry(left, width=400, height=45, show="*", font=ctk.CTkFont(size=14), placeholder_text="请输入密码")
        self.pwd_entry.pack(padx=40)
        
        # 开始登录按钮
        self.douyin_login_btn = ctk.CTkButton(
            left,
            text="🚀 开始登录",
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=Theme.RED,
            hover_color=self.darken_color(Theme.RED),
            height=55,
            width=250,
            corner_radius=30,
            command=self.start_douyin_login
        )
        self.douyin_login_btn.pack(pady=30)
        
        # 进度提示
        self.douyin_progress_label = ctk.CTkLabel(
            left,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=Theme.YELLOW
        )
        self.douyin_progress_label.pack(pady=(0,30))
        
        # 右侧：实时截图预览
        right = ctk.CTkFrame(cols, fg_color=Theme.CARD_BG, corner_radius=15)
        right.pack(side="right", fill="both", expand=True, padx=(15,0))
        
        right_header = ctk.CTkFrame(right, fg_color="transparent", height=60)
        right_header.pack(fill="x", padx=20, pady=(20,10))
        
        ctk.CTkLabel(
            right_header,
            text="📺 实时页面预览",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=Theme.PRIMARY
        ).pack(side="left")
        
        # 刷新状态指示
        self.screenshot_status = ctk.CTkLabel(
            right_header,
            text="⏸ 未启动",
            font=ctk.CTkFont(size=12),
            text_color=Theme.TEXT_HINT
        )
        self.screenshot_status.pack(side="right")
        
        # 截图显示区域（添加边框）
        screenshot_container = ctk.CTkFrame(right, fg_color=Theme.BG_PRIMARY, corner_radius=10)
        screenshot_container.pack(fill="both", expand=True, padx=20, pady=(10,20))
        
        self.screenshot_label = ctk.CTkLabel(
            screenshot_container,
            text="🌐\n\n点击【开始登录】后\n将显示实时页面截图\n\n让您全程掌握登录进度",
            font=ctk.CTkFont(size=14),
            text_color=Theme.TEXT_HINT,
            justify="center"
        )
        self.screenshot_label.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 停止截图轮询的标志
        self.screenshot_polling = False
        
        # 如果已经登录，显示登录状态
        if self.douyin_logged_in:
            self.douyin_login_btn.configure(text="✅ 已登录", fg_color=Theme.GREEN)
            self.douyin_status_label.configure(text="✅ 已登录", text_color=Theme.GREEN)
            self.douyin_progress_label.configure(text="登录状态已保持", text_color=Theme.GREEN)

    def start_douyin_login(self):
        """开始登录抖音，并启动截图轮询"""
        if self.screenshot_polling:
            self.show_error_toast("错误", "登录正在进行中，请勿重复点击。")
            return

        email = self.email_entry.get()
        password = self.pwd_entry.get()
        
        if not email or not password:
            messagebox.showwarning("提示", "请输入邮箱和密码")
            return
        
        # 禁用按钮
        self.douyin_login_btn.configure(state="disabled", text="登录中...")
        self.douyin_progress_label.configure(text="🔄 正在连接抖店...")
        self.douyin_status_label.configure(text="🔄 登录中...", text_color=Theme.YELLOW)
        
        # 设置轮询标志并启动
        self.screenshot_polling = True
        self.poll_screenshot()
        
        # 异步登录
        threading.Thread(target=self._login_thread, args=(email, password), daemon=True).start()
    
    def _login_thread(self, email: str, password: str) -> None:
        """登录线程"""
        try:
            logger.info(f"登录线程启动，email={email}")
            headers = {
                'X-Client-ID': self.client_id,
                'X-Hardware-ID': self.hardware_id,
                'Content-Type': 'application/json'
            }
            
            logger.info(f"准备发送登录请求到 {SERVER_URL}/api/douyin-login-start")
            # 登录
            response = requests.post(
                f"{SERVER_URL}/api/douyin-login-start",
                headers=headers,
                json={'email': email, 'password': password},
                timeout=Config.LOGIN_TIMEOUT
            )
            
            logger.info(f"收到响应，状态码: {response.status_code}")
            if response.status_code == 403:
                try:
                    body = response.json()
                    if body.get('show_popup'):
                        self.after(0, self.show_gentle_reminder)
                except Exception as e:
                    logger.warning(f"解析403响应失败: {e}")
                raise Exception(f"登录失败：{response.status_code}")
            
            result = response.json()
            logger.info(f"响应内容: {result}")
            if not result.get('success'):
                raise Exception(result.get('error', '登录失败'))
            
            status = result.get('status')
            message = result.get('message', '')
            
            # 验证码处理
            if status == 'need_code':
                logger.info("需要验证码")
                self.after(0, lambda: self.douyin_progress_label.configure(text="📧 需要邮箱验证码，请查收..."))
                
                # 修复：正确获取验证码输入
                code_result = {"value": None, "completed": threading.Event()}
                
                def show_dialog():
                    code_result["value"] = self.show_code_dialog()
                    code_result["completed"].set()
                
                self.after(0, show_dialog)
                
                # 等待对话框完成
                if not code_result["completed"].wait(timeout=Config.CODE_INPUT_TIMEOUT):
                    logger.warning("验证码输入超时")
                    self.after(0, self._login_cancelled)
                    return
                
                code = code_result["value"]
                if not code:
                    logger.info("用户取消输入验证码")
                    self.after(0, self._login_cancelled)
                    return
                
                # 提交验证码
                logger.info(f"提交验证码: {code}")
                self.after(0, lambda: self.douyin_progress_label.configure(text="🔄 正在提交验证码..."))
                
                response = requests.post(
                    f"{SERVER_URL}/api/douyin-submit-code",
                    headers=headers,
                    json={'code': code},
                    timeout=30
                )
                
                result = response.json()
                if not result.get('success'):
                    raise Exception(result.get('message', '验证码错误'))
            
            # 登录成功
            logger.info("登录成功")
            self.douyin_logged_in = True
            self.after(0, self._login_success)
        
        except Exception as e:
            logger.error(f"登录异常: {e}\n{traceback.format_exc()}")
            self.after(0, lambda: self._login_failed(str(e)))
    
    def _login_success(self):
        """登录成功"""
        self.screenshot_polling = False
        self.douyin_logged_in = True
        
        # 保存登录状态到配置文件
        config = load_config()
        config['douyin_logged_in'] = True
        config['login_timestamp'] = time.time()
        save_config(config)
        
        # 更新UI
        self.douyin_login_btn.configure(state="normal", text="✓ 已登录", fg_color=Theme.GREEN)
        self.douyin_progress_label.configure(text="✅ 登录成功！", text_color=Theme.GREEN)
        self.douyin_status_label.configure(text="✅ 已登录", text_color=Theme.GREEN)
        
        # 显示成功提示
        messagebox.showinfo("登录成功", "🎉 登录成功！\n\n现在可以开始智能选品了")
        
        # 自动跳转到智能选品页面
        self.after(500, lambda: self.switch_page("smart_selection"))
    
    def _login_failed(self, error):
        """登录失败"""
        self.screenshot_polling = False
        self.douyin_login_btn.configure(state="normal", text="🚀 重新登录")
        self.douyin_progress_label.configure(text="❌ 登录失败")
        self.douyin_status_label.configure(text="❌ 未登录", text_color=Theme.RED)
        messagebox.showerror("登录失败", error)
    
    def _login_cancelled(self):
        """取消登录"""
        self.screenshot_polling = False
        self.douyin_login_btn.configure(state="normal", text="🚀 开始登录")
        self.douyin_progress_label.configure(text="")
        self.douyin_status_label.configure(text="⭕ 未登录", text_color=Theme.TEXT_SECONDARY)
    
    def poll_screenshot(self) -> None:
        """轮询获取截图（带状态指示）"""
        if not self.screenshot_polling:
            logger.debug("截图轮询已停止")
            return

        def task():
            try:
                # 更新状态
                if hasattr(self, 'screenshot_status'):
                    self.after(0, lambda: self.screenshot_status.configure(text="🔄 正在刷新..."))
                
                headers = {
                    'X-Client-ID': self.client_id,
                    'X-Hardware-ID': self.hardware_id,
                }
                
                response = requests.post(
                    f"{SERVER_URL}/api/douyin-screenshot",
                    headers=headers,
                    timeout=Config.SCREENSHOT_REQUEST_TIMEOUT
                )
                
                if response.status_code == 403:
                    logger.warning("截图请求被拒绝（403）")
                    try:
                        body = response.json()
                        if body.get('show_popup'):
                            self.after(0, self.show_gentle_reminder)
                    except Exception as e:
                        logger.error(f"解析403响应失败: {e}")
                elif response.ok:
                    result = response.json()
                    if result.get('success') and result.get('screenshot'):
                        self.display_screenshot(result['screenshot'])
                        # 更新状态为成功
                        if hasattr(self, 'screenshot_status'):
                            self.after(0, lambda: self.screenshot_status.configure(
                                text="✅ 已更新", 
                                text_color=Theme.GREEN
                            ))
                else:
                    logger.warning(f"截图请求失败: {response.status_code}")
                
                # 定期轮询
                if self.screenshot_polling:
                    self.after(Config.SCREENSHOT_POLL_INTERVAL, self.poll_screenshot)
            except requests.Timeout:
                logger.warning("截图请求超时")
                if self.screenshot_polling:
                    self.after(Config.SCREENSHOT_POLL_INTERVAL, self.poll_screenshot)
            except Exception as e:
                logger.error(f"截图轮询异常: {e}")
                if self.screenshot_polling:
                    self.after(Config.SCREENSHOT_POLL_INTERVAL, self.poll_screenshot)

        threading.Thread(target=task, daemon=True).start()
    
    def display_screenshot(self, base64_img: str) -> None:
        """显示截图"""
        try:
            img_data = base64.b64decode(base64_img)
            img = Image.open(BytesIO(img_data))
            
            # 限制图片大小以防止内存占用过大
            if img.width > Config.SCREENSHOT_MAX_WIDTH or img.height > Config.SCREENSHOT_MAX_HEIGHT:
                img.thumbnail((Config.SCREENSHOT_MAX_WIDTH, Config.SCREENSHOT_MAX_HEIGHT), Image.Resampling.LANCZOS)
            
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
            
            self.screenshot_label.configure(image=ctk_img, text="")
            self.screenshot_label.image = ctk_img
            logger.debug(f"截图显示成功，尺寸: {img.width}x{img.height}")
        except Exception as e:
            logger.error(f"显示截图失败: {e}")
            # 显示错误提示
            if hasattr(self, 'screenshot_label'):
                self.screenshot_label.configure(text="❌ 截图加载失败", image=None)
    
    def show_code_dialog(self):
        """验证码输入对话框"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("输入验证码")
        dialog.geometry("450x280")
        dialog.configure(fg_color=Theme.CARD_BG)
        dialog.transient(self)
        dialog.grab_set()
        
        # 居中
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 225
        y = (dialog.winfo_screenheight() // 2) - 140
        dialog.geometry(f'450x280+{x}+{y}')
        
        code_value = {"value": None}
        
        ctk.CTkLabel(
            dialog,
            text="📧 请输入邮箱验证码",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=Theme.ORANGE
        ).pack(pady=(30,10))
        
        ctk.CTkLabel(
            dialog,
            text="验证码已发送至您的邮箱\n请查收邮件",
            font=ctk.CTkFont(size=13),
            text_color=Theme.TEXT_SECONDARY
        ).pack(pady=(0,25))
        
        code_entry = ctk.CTkEntry(
            dialog,
            width=250,
            height=45,
            font=ctk.CTkFont(size=16),
            placeholder_text="输入验证码"
        )
        code_entry.pack(pady=15)
        code_entry.focus()
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=25)
        
        def submit():
            code_value["value"] = code_entry.get()
            dialog.destroy()
        
        ctk.CTkButton(
            btn_frame,
            text="✓ 确定",
            width=130,
            height=45,
            fg_color=Theme.GREEN,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=submit
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="✗ 取消",
            width=130,
            height=45,
            fg_color=Theme.TEXT_SECONDARY,
            command=lambda: [setattr(code_value, 'value', None), dialog.destroy()]
        ).pack(side="left", padx=10)
        
        code_entry.bind("<Return>", lambda e: submit())
        
        dialog.wait_window()
        return code_value["value"]
    
    # ==================== 页面2：智能选品 ====================
    
    def show_smart_selection(self):
        """智能选品页面"""
        if not self.douyin_logged_in:
            # 未登录提示
            ctk.CTkLabel(
                self.content_frame,
                text="⚠️\n\n请先登录抖音罗盘\n\n点击左侧菜单进行登录",
                font=ctk.CTkFont(size=20),
                text_color=Theme.YELLOW,
                justify="center"
            ).pack(expand=True)
            return
        
        container = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=30)
        
        # 标题
        ctk.CTkLabel(
            container,
            text="🎯 智能选品 · 半自动模式",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=Theme.ORANGE
        ).pack(pady=(0,30))
        
        # 表单卡片
        form = ctk.CTkFrame(container, fg_color=Theme.CARD_BG, corner_radius=20)
        form.pack(fill="x", pady=10)
        
        # 第一行：榜单类型 + 时间段
        row1 = ctk.CTkFrame(form, fg_color="transparent")
        row1.pack(fill="x", padx=40, pady=(30,15))
        
        ctk.CTkLabel(row1, text="📊 榜单类型", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0,5))
        self.rank_type_var = ctk.StringVar(value="搜索榜")
        self.rank_type_combo = ctk.CTkComboBox(
            row1,
            variable=self.rank_type_var,
            values=["搜索榜", "直播榜", "商品卡榜", "达人带货榜", "短视频榜", "实时爆品挖掘榜"],
            width=250,
            height=40,
            font=ctk.CTkFont(size=13),
            button_color=Theme.ORANGE,
            button_hover_color=self.darken_color(Theme.ORANGE)
        )
        self.rank_type_combo.pack(anchor="w")
        
        ctk.CTkLabel(row1, text="📅 时间段", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(20,5))
        self.time_range_var = ctk.StringVar(value="近1天")
        self.time_range_combo = ctk.CTkComboBox(
            row1,
            variable=self.time_range_var,
            values=["近1天", "近7天", "近30天"],
            width=200,
            height=40,
            font=ctk.CTkFont(size=13),
            button_color=Theme.CYAN,
            button_hover_color=self.darken_color(Theme.CYAN)
        )
        self.time_range_combo.pack(anchor="w")
        
        # 第二行：品类类型 + 首次上榜
        row2 = ctk.CTkFrame(form, fg_color="transparent")
        row2.pack(fill="x", padx=40, pady=15)
        
        ctk.CTkLabel(row2, text="🏷️ 品类类型", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0,5))
        self.category_var = ctk.StringVar(value="不限")
        self.category_combo = ctk.CTkComboBox(
            row2,
            variable=self.category_var,
            values=["不限", "知名品牌", "新锐品牌", "价格带", "自营"],
            width=200,
            height=40,
            font=ctk.CTkFont(size=13),
            button_color=Theme.YELLOW,
            button_hover_color=self.darken_color(Theme.YELLOW)
        )
        self.category_combo.pack(anchor="w")
        
        ctk.CTkLabel(row2, text="⭐ 首次上榜筛选", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(20,5))
        self.first_time_var = ctk.BooleanVar(value=False)
        self.first_time_switch = ctk.CTkSwitch(
            row2,
            text="只筛选首次上榜商品",
            variable=self.first_time_var,
            font=ctk.CTkFont(size=13),
            progress_color=Theme.GREEN
        )
        self.first_time_switch.pack(anchor="w")
        
        # 第三行：数量控制
        row3 = ctk.CTkFrame(form, fg_color="transparent")
        row3.pack(fill="x", padx=40, pady=15)
        
        left_col = ctk.CTkFrame(row3, fg_color="transparent")
        left_col.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(left_col, text="🔢 爬取数量", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0,5))
        self.limit_var = ctk.StringVar(value="50")
        self.limit_entry = ctk.CTkEntry(
            left_col,
            textvariable=self.limit_var,
            width=150,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.limit_entry.pack(anchor="w")
        
        right_col = ctk.CTkFrame(row3, fg_color="transparent")
        right_col.pack(side="right", fill="x", expand=True)
        
        ctk.CTkLabel(right_col, text="🏆 只保留前N名", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0,5))
        self.top_n_var = ctk.StringVar(value="0")
        self.top_n_entry = ctk.CTkEntry(
            right_col,
            textvariable=self.top_n_var,
            width=150,
            height=40,
            font=ctk.CTkFont(size=14),
            placeholder_text="0表示全部"
        )
        self.top_n_entry.pack(anchor="w")
        
        # 开始按钮
        self.start_btn = ctk.CTkButton(
            form,
            text="🚀 开始智能选品",
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color=Theme.ORANGE,
            hover_color=self.darken_color(Theme.ORANGE),
            height=60,
            width=300,
            corner_radius=30,
            command=self.start_selection
        )
        self.start_btn.pack(pady=30)
        
        # 进度提示
        self.selection_progress = ctk.CTkLabel(
            form,
            text="",
            font=ctk.CTkFont(size=14),
            text_color=Theme.YELLOW
        )
        self.selection_progress.pack(pady=(0,30))
        
        # 结果表格区域
        self.result_frame = ctk.CTkFrame(container, fg_color=Theme.CARD_BG, corner_radius=20)
        self.result_frame.pack(fill="both", expand=True, pady=(20,0))
        
        ctk.CTkLabel(
            self.result_frame,
            text="📋 选品结果",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=Theme.CYAN
        ).pack(pady=20)
        
        self.result_label = ctk.CTkLabel(
            self.result_frame,
            text="暂无数据\n\n请点击上方【开始智能选品】按钮",
            font=ctk.CTkFont(size=14),
            text_color=Theme.TEXT_HINT
        )
        self.result_label.pack(pady=40)
    
    def start_selection(self):
        """开始智能选品"""
        # 验证输入
        try:
            limit = int(self.limit_var.get())
            top_n = int(self.top_n_var.get())
        except:
            messagebox.showwarning("提示", "请输入有效的数字")
            return
        
        if limit < 1 or limit > 200:
            messagebox.showwarning("提示", "爬取数量应在1-200之间")
            return
        
        # 禁用按钮
        self.start_btn.configure(state="disabled", text="选品中...")
        self.selection_progress.configure(text="🔄 正在爬取商品数据...")
        
        # 异步执行
        threading.Thread(target=self._selection_thread, daemon=True).start()
    
    def _selection_thread(self) -> None:
        """选品线程"""
        try:
            logger.info("开始智能选品")
            headers = {
                'X-Client-ID': self.client_id,
                'X-Hardware-ID': self.hardware_id,
                'Content-Type': 'application/json'
            }
            
            data = {
                'rank_type': self.rank_type_var.get(),
                'time_range': self.time_range_var.get(),
                'category': self.category_var.get() if self.category_var.get() != "不限" else None,
                'brand_type': None,
                'limit': int(self.limit_var.get()),
                'first_time_only': self.first_time_var.get(),
                'top_n': int(self.top_n_var.get())
            }
            
            logger.info(f"选品参数: {data}")
            
            response = requests.post(
                f"{SERVER_URL}/api/douyin-scrape",
                headers=headers,
                json=data,
                timeout=Config.SCRAPE_TIMEOUT
            )
            
            logger.info(f"选品响应状态: {response.status_code}")
            
            if response.status_code == 403:
                logger.warning("选品请求被拒绝（403）")
                try:
                    body = response.json()
                    if body.get('show_popup'):
                        self.after(0, self.show_gentle_reminder)
                except Exception:
                    pass
                raise Exception("授权验证失败，请联系客服")
            
            if not response.ok:
                raise Exception(f"请求失败：HTTP {response.status_code}")
            
            result = response.json()
            if not result.get('success'):
                error_msg = result.get('error', '爬取失败')
                logger.error(f"选品失败: {error_msg}")
                raise Exception(error_msg)
            
            products = result.get('products', [])
            logger.info(f"获取到 {len(products)} 个商品")
            
            if not products:
                self.after(0, lambda: self._selection_failed("未找到符合条件的商品"))
                return
            
            # 导出Excel
            self.after(0, lambda: self.selection_progress.configure(text="📊 正在导出Excel..."))
            
            excel_file = self.export_to_excel(products)
            logger.info(f"Excel导出成功: {excel_file}")
            
            # 成功
            self.after(0, lambda: self._selection_success(products, excel_file))
        
        except requests.Timeout:
            logger.error("选品请求超时")
            self.after(0, lambda: self._selection_failed("请求超时，请稍后重试"))
        except requests.RequestException as e:
            logger.error(f"网络请求异常: {e}")
            self.after(0, lambda: self._selection_failed(f"网络错误：{str(e)}"))
        except Exception as e:
            logger.error(f"选品异常: {e}\n{traceback.format_exc()}")
            self.after(0, lambda: self._selection_failed(str(e)))
    
    def _selection_success(self, products, excel_file):
        """选品成功"""
        self.start_btn.configure(state="normal", text="🚀 开始智能选品")
        self.selection_progress.configure(text=f"✅ 成功获取 {len(products)} 个商品！")
        
        # 显示结果
        self.result_label.configure(
            text=f"✅ 成功获取 {len(products)} 个商品\n\n已导出到：{excel_file}\n\n可用于RPA自动铺货"
        )
        
        # 保存当前Excel文件路径（用于RPA）
        self.last_excel_file = excel_file
        
        # 显示成功对话框，带RPA铺货选项
        self.show_success_with_rpa_option(products, excel_file)
    
    def show_success_with_rpa_option(self, products, excel_file):
        """显示成功对话框，带RPA铺货选项"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("选品成功")
        dialog.geometry("500x400")
        dialog.configure(fg_color=Theme.CARD_BG)
        dialog.transient(self)
        dialog.grab_set()
        
        # 居中
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 250
        y = (dialog.winfo_screenheight() // 2) - 200
        dialog.geometry(f'500x400+{x}+{y}')
        
        # 成功图标
        ctk.CTkLabel(dialog, text="✅", font=ctk.CTkFont(size=80)).pack(pady=(30,20))
        
        # 标题
        ctk.CTkLabel(
            dialog,
            text="选品成功！",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=Theme.GREEN
        ).pack(pady=10)
        
        # 信息
        ctk.CTkLabel(
            dialog,
            text=f"成功获取 {len(products)} 个商品\n已导出Excel文件",
            font=ctk.CTkFont(size=14),
            text_color=Theme.TEXT_SECONDARY
        ).pack(pady=10)
        
        # 按钮区域
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=30)
        
        # 一键铺货按钮
        ctk.CTkButton(
            btn_frame,
            text="🤖 一键铺货",
            width=180,
            height=50,
            fg_color=Theme.ORANGE,
            hover_color=self.darken_color(Theme.ORANGE),
            font=ctk.CTkFont(size=16, weight="bold"),
            command=lambda: [dialog.destroy(), self.handle_rpa_listing(excel_file)]
        ).pack(side="left", padx=10)
        
        # 关闭按钮
        ctk.CTkButton(
            btn_frame,
            text="关闭",
            width=140,
            height=50,
            fg_color=Theme.TEXT_SECONDARY,
            font=ctk.CTkFont(size=14),
            command=dialog.destroy
        ).pack(side="left", padx=10)
        
        # 3秒后自动关闭
        self.after(3000, dialog.destroy)
    
    def handle_rpa_listing(self, excel_file):
        """处理RPA铺货"""
        # 检查RPA模块是否存在
        script_dir = os.path.dirname(os.path.abspath(__file__))
        rpa_script = os.path.join(script_dir, '..', 'rpa', 'rpa_controller.py')
        
        if os.path.exists(rpa_script):
            # RPA模块存在，启动
            try:
                # 使用subprocess启动RPA脚本
                if platform.system() == 'Windows':
                    subprocess.Popen([
                        'python', rpa_script,
                        '--excel', excel_file,
                        '--column', '商品链接'
                    ], creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    subprocess.Popen([
                        'python3', rpa_script,
                        '--excel', excel_file,
                        '--column', '商品链接'
                    ])
                
                messagebox.showinfo(
                    "RPA已启动",
                    "RPA铺货程序已在后台启动！\n\n请不要操作鼠标和键盘，让程序自动完成。"
                )
            except Exception as e:
                messagebox.showerror("启动失败", f"启动RPA失败：{e}")
        else:
            # RPA模块不存在，提示下载
            result = messagebox.askyesno(
                "需要RPA增强包",
                "一键铺货功能需要安装RPA增强包\n\n"
                "RPA增强包是独立的自动化工具，可选安装。\n\n"
                "是否前往下载页面？"
            )
            if result:
                webbrowser.open("https://github.com/zhiqiangsun2025-droid/price-suite/releases")
    
    def _selection_failed(self, error):
        """选品失败"""
        self.start_btn.configure(state="normal", text="🚀 开始智能选品")
        self.selection_progress.configure(text="❌ 选品失败")
        messagebox.showerror("选品失败", error)
    
    def export_to_excel(self, products: List[Dict[str, Any]]) -> str:
        """导出Excel
        
        Args:
            products: 商品列表
            
        Returns:
            str: Excel文件路径
        """
        try:
            logger.info(f"开始导出 {len(products)} 个商品到Excel")
            
            # 创建DataFrame
            data = []
            for idx, p in enumerate(products, 1):
                data.append({
                    '序号': idx,
                    '排名': p.get('rank', idx),
                    '商品ID': p.get('product_id', ''),
                    '商品名称': p.get('title', ''),
                    '商品链接': p.get('url', ''),
                    '价格': p.get('price', ''),
                    '销量': p.get('sales', ''),
                    'GMV': p.get('gmv', ''),
                    '店铺名称': p.get('shop_name', ''),
                    '是否首次上榜': '是' if p.get('is_first_time') else '否',
                    '增长率': p.get('growth_rate', ''),
                    '商品图片': p.get('image', '')
                })
            
            df = pd.DataFrame(data)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"抖音选品结果_{timestamp}.xlsx"
            
            # 保存到桌面
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            if not os.path.exists(desktop):
                logger.warning(f"桌面目录不存在: {desktop}，使用用户目录")
                desktop = os.path.expanduser('~')
            
            filepath = os.path.join(desktop, filename)
            
            # 写入Excel
            df.to_excel(filepath, index=False, engine='openpyxl')
            
            logger.info(f"Excel文件导出成功: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"导出Excel失败: {e}\n{traceback.format_exc()}")
            raise Exception(f"导出Excel失败: {str(e)}")
    
    # ==================== 其他页面 ====================
    
    def show_data_analysis(self):
        """数据分析页面"""
        ctk.CTkLabel(
            self.content_frame,
            text="📊 数据分析\n\n功能开发中...",
            font=ctk.CTkFont(size=24),
            text_color=Theme.TEXT_SECONDARY
        ).pack(expand=True)
    
    def show_settings(self):
        """系统设置"""
        ctk.CTkLabel(
            self.content_frame,
            text="⚙️ 系统设置\n\n功能开发中...",
            font=ctk.CTkFont(size=24),
            text_color=Theme.TEXT_SECONDARY
        ).pack(expand=True)
    
    # ==================== 动画效果 ====================
    
    def show_success_animation(self, title, message, on_continue=None):
        """成功动画"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("成功")
        dialog.geometry("450x350")
        dialog.configure(fg_color=Theme.CARD_BG)
        dialog.transient(self)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 225
        y = (dialog.winfo_screenheight() // 2) - 175
        dialog.geometry(f'450x350+{x}+{y}')
        
        ctk.CTkLabel(dialog, text="✅", font=ctk.CTkFont(size=80)).pack(pady=(40,20))
        ctk.CTkLabel(dialog, text=title, font=ctk.CTkFont(size=24, weight="bold"), text_color=Theme.GREEN).pack(pady=10)
        ctk.CTkLabel(dialog, text=message, font=ctk.CTkFont(size=14), text_color=Theme.TEXT_SECONDARY).pack(pady=10)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=40)
        
        if on_continue:
            ctk.CTkButton(
                btn_frame,
                text="继续 →",
                width=150,
                height=50,
                fg_color=Theme.ORANGE,
                font=ctk.CTkFont(size=16, weight="bold"),
                command=lambda: [dialog.destroy(), on_continue()]
            ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="关闭",
            width=120,
            height=50,
            fg_color=Theme.TEXT_SECONDARY,
            command=dialog.destroy
        ).pack(side="left", padx=10)
        
        self.after(3000, dialog.destroy)
    
    def show_gentle_reminder(self):
        """友好提示（带二维码，用于获客）"""
        # 创建一个弹窗（稍大一点，显示二维码）
        dialog = ctk.CTkToplevel(self)
        dialog.title("提示")
        dialog.geometry("450x550")
        dialog.configure(fg_color=Theme.CARD_BG)
        dialog.transient(self)
        dialog.grab_set()
        
        # 居中
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 225
        y = (dialog.winfo_screenheight() // 2) - 275
        dialog.geometry(f'450x550+{x}+{y}')
        
        ctk.CTkLabel(
            dialog,
            text="💡 温馨提示",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=Theme.ORANGE
        ).pack(pady=(30,15))
        
        ctk.CTkLabel(
            dialog,
            text="软件功能升级中\n如需咨询请扫码联系客服",
            font=ctk.CTkFont(size=14),
            text_color=Theme.TEXT_SECONDARY,
            justify="center"
        ).pack(pady=10)
        
        # 二维码区域（占位图）
        qr_frame = ctk.CTkFrame(dialog, fg_color=Theme.BG_SECONDARY, width=280, height=280, corner_radius=15)
        qr_frame.pack(pady=20)
        qr_frame.pack_propagate(False)
        
        # 二维码标题
        ctk.CTkLabel(
            qr_frame,
            text="扫码添加客服微信",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=Theme.GREEN
        ).pack(pady=(20,10))
        
        # 二维码图片（这里用文字占位，实际使用时替换为真实二维码）
        qr_placeholder = ctk.CTkFrame(qr_frame, fg_color="white", width=200, height=200, corner_radius=10)
        qr_placeholder.pack(pady=10)
        qr_placeholder.pack_propagate(False)
        
        ctk.CTkLabel(
            qr_placeholder,
            text="📱\n\n微信二维码\n\n扫码咨询",
            font=ctk.CTkFont(size=14),
            text_color="black",
            justify="center"
        ).pack(expand=True)
        
        # 提示文字
        ctk.CTkLabel(
            dialog,
            text=f"或添加QQ: {Config.CONTACT_QQ}",
            font=ctk.CTkFont(size=12),
            text_color=Theme.TEXT_HINT
        ).pack(pady=5)
        
        # 按钮
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="知道了",
            width=140,
            height=45,
            fg_color=Theme.ORANGE,
            hover_color=self.darken_color(Theme.ORANGE),
            font=ctk.CTkFont(size=14, weight="bold"),
            command=dialog.destroy
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="继续使用",
            width=140,
            height=45,
            fg_color=Theme.GREEN,
            hover_color=self.darken_color(Theme.GREEN),
            font=ctk.CTkFont(size=14, weight="bold"),
            command=dialog.destroy
        ).pack(side="left", padx=5)
    
    def show_error(self, error_code: int, error_msg: str) -> None:
        """显示错误提示（友好版，不打断流程）
        
        Args:
            error_code: 错误代码
            error_msg: 错误消息
        """
        try:
            logger.error(f"显示错误 [{error_code}]: {error_msg}")
            messagebox.showwarning(
                "提示", 
                f"{error_msg or '发生错误'}\n\n如有疑问请联系客服"
            )
        except Exception as e:
            logger.error(f"显示错误对话框失败: {e}")
        # 保持当前页面，不强制跳回
    
    def show_error_toast(self, title: str, message: str) -> None:
        """显示Toast风格的错误提示（轻量级）
        
        Args:
            title: 标题
            message: 消息
        """
        logger.warning(f"{title}: {message}")
        # 这里可以扩展为非模态的Toast通知
        # 暂时使用messagebox
        try:
            messagebox.showinfo(title, message)
        except Exception as e:
            logger.error(f"显示Toast失败: {e}")

if __name__ == "__main__":
    app = UltimateApp()
    app.mainloop()

