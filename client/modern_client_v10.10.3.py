#!/usr/bin/env python3
"""
智能选品铺货系统 - 终极版客户端
仿微信UI + 智能选品 + 实时画面
版本：v10.10.3
"""

VERSION = "v10.10.3"

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

# 浅色主题（仿微信）
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

# ==================== 配置（硬编码） ====================
SERVER_URL = "http://172.19.251.155:5000"  # 硬编码，不暴露给客户
TRIAL_DURATION = 3600  # 1小时试用
CONTACT_QQ = "123456789"

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

# ======== 表单统一规范（视觉对齐） ========
FORM_LABEL_W = 128   # 标签列宽
FORM_ROW_H   = 44    # 行高（视觉对齐）
CTRL_H       = 38    # 控件高度（Entry/Combo）
ROW_GAP      = 12    # 行间距（用于需要时的外边距）

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

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_hardware_id():
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                       for elements in range(0, 2*6, 2)][::-1])
        if platform.system() == 'Windows':
            try:
                output = subprocess.check_output("wmic diskdrive get serialnumber", shell=True).decode()
                disk_serial = output.split('\n')[1].strip()
            except:
                disk_serial = "UNKNOWN"
        else:
            disk_serial = "UNKNOWN"
        hardware_string = f"{mac}_{disk_serial}_{platform.node()}"
        return hashlib.sha256(hardware_string.encode()).hexdigest()[:32]
    except:
        return "HARDWARE_ERROR"

def setup_form_grid(frame, rows: int):
    """为表单容器设置统一Grid规范（两列、若干行）。"""
    try:
        frame.grid_columnconfigure(0, minsize=FORM_LABEL_W)
    except Exception:
        pass
    frame.grid_columnconfigure(1, weight=1)
    for r in range(rows):
        try:
            frame.grid_rowconfigure(r, minsize=FORM_ROW_H)
        except Exception:
            pass

# ==================== 主应用 ====================

class UltimateApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 窗口配置
        self.title(f"🎯 智能选品系统 · 终极版 {VERSION}")
        self.geometry("1400x900")
        self.configure(fg_color=Theme.BG_PRIMARY)
        
        # 数据
        self.hardware_id = get_hardware_id()
        self.client_id = None
        self.is_active = None
        self.trial_start_time = None
        self.douyin_logged_in = False  # 抖音登录状态
        self.rank_options = {}  # 动态获取的选项
        self.server_url = SERVER_URL  # 统一服务器地址
        self.menu_frame = None  # 左侧菜单单例
        
        # 自动注册并初始化
        self.auto_register()
    
    def sync_auth_status(self):
        """同步后台授权状态（启动时调用）"""
        try:
            response = requests.get(
                f"{SERVER_URL}/api/check-auth",
                headers={
                    'X-Client-ID': self.client_id,
                    'X-Hardware-ID': self.hardware_id
                },
                timeout=5
            )
            
            if response.ok:
                data = response.json()
                if data.get('success'):
                    new_is_active = data.get('is_active', 0)
                    
                    # 更新配置文件
                    config = load_config()
                    old_is_active = config.get('is_active', 0)
                    
                    if new_is_active != old_is_active:
                        print(f"[调试] 授权状态已更新: {old_is_active} → {new_is_active}")
                        config['is_active'] = new_is_active
                        save_config(config)
                        
                        # 如果变成已批准，清除试用时间
                        if new_is_active == 1:
                            config.pop('trial_start_time', None)
                            self.trial_start_time = None
                            save_config(config)
                            print(f"[调试] 已批准，清除试用时间限制")

                    # 同步内存中的 is_active，避免后续读取旧值
                    self.is_active = new_is_active
                    
        except Exception as e:
            print(f"[调试] 同步授权状态失败: {e}")
    
    def auto_register(self):
        """自动注册"""
        config = load_config()
        
        if 'client_id' in config:
            self.client_id = config['client_id']
            
            # 🔥 重要：启动时同步后台授权状态
            self.sync_auth_status()
            
            # 重新读取配置，确保拿到最新状态
            config = load_config()
            self.is_active = config.get('is_active', 0)
            self.trial_start_time = config.get('trial_start_time')
            
            # 恢复登录状态
            if config.get('douyin_logged_in', False):
                self.douyin_logged_in = True
                print(f"[调试] 从配置文件恢复登录状态: 已登录")
            
            self.init_main_ui()
        else:
            try:
                response = requests.post(
                    f"{SERVER_URL}/api/register",
                    json={'hardware_id': self.hardware_id},
                    timeout=10
                )
                
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
                        self.init_main_ui()
                    else:
                        self.show_error(101, result.get('error', '注册失败'))
                else:
                    self.show_error(101, f'服务器错误：{response.status_code}')
            
            except Exception as e:
                self.show_error(101, f'连接服务器失败：{str(e)}')
    
    def init_main_ui(self):
        """初始化主UI"""
        # 顶部状态栏
        self.create_status_bar()
        
        # 主容器
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # 左侧菜单（只创建一次）
        if not self.menu_frame or not self.menu_frame.winfo_exists():
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
            text="🎯 智能选品系统 v2.0",
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
        """静默检查授权（不显示倒计时）"""
        def update():
            if not hasattr(self, 'trial_start_time') or self.trial_start_time is None:
                return
            
            elapsed = time.time() - self.trial_start_time
            left = TRIAL_DURATION - elapsed
            
            if left <= 0:
                # 试用期结束，仅当仍未批准时才提示
                if self.is_active == 0:
                    self.show_gentle_reminder()
            else:
                self.after(60000, update)  # 每分钟检查一次（不是每秒）
        
        update()
    
    def create_left_menu(self, parent):
        """创建左侧菜单（仿微信风格）"""
        # 若已存在菜单，先安全移除再创建，避免双列
        try:
            if self.menu_frame and self.menu_frame.winfo_exists():
                self.menu_frame.destroy()
        except Exception:
            pass

        menu = ctk.CTkFrame(parent, width=200, fg_color=Theme.BG_SECONDARY, corner_radius=0)
        menu.pack(side="left", fill="y")
        menu.pack_propagate(False)
        self.menu_frame = menu
        
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
        
        for label, page_id in menus:
            self.create_menu_btn(menu, label, page_id)
    
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
    
    def darken_color(self, hex_color, factor=0.8):
        """使颜色变暗"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def switch_page(self, page_id):
        """切换页面"""
        self.current_page = page_id
        
        # 🔥 只清空内容区，不重建菜单！
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # 显示对应页面
        if page_id == "douyin_login":
            self.show_douyin_login()
        elif page_id == "smart_selection":
            self.show_smart_selection()
        elif page_id == "data_analysis":
            self.show_data_analysis()
        elif page_id == "settings":
            self.show_settings()
    
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
        
        # 右侧：登录状态 + 退出按钮
        status_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        status_frame.pack(side="right")
        
        self.douyin_status_label = ctk.CTkLabel(
            status_frame,
            text="⭕ 未登录",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=Theme.TEXT_SECONDARY
        )
        self.douyin_status_label.pack(side="left", padx=(0, 10))
        
        # 退出登录按钮（仅登录后显示）
        self.douyin_logout_btn = ctk.CTkButton(
            status_frame,
            text="🚪 退出登录",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=Theme.ORANGE,
            hover_color=self.darken_color(Theme.ORANGE),
            width=100,
            height=32,
            corner_radius=8,
            command=self.logout_douyin
        )
        # 默认隐藏，登录后才显示
        if not self.douyin_logged_in:
            self.douyin_logout_btn.pack_forget()
        
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
        ).pack(pady=(30,12))

        # 表单容器（Grid，两列：标签固定 + 控件自适应）
        form_frame = ctk.CTkFrame(left, fg_color="transparent")
        form_frame.pack(fill="x", padx=24, pady=(8, 8))
        setup_form_grid(form_frame, rows=2)

        # 行样式
        label_font = ctk.CTkFont(size=14)
        entry_font = ctk.CTkFont(size=14)

        # 邮箱
        email_label = ctk.CTkLabel(form_frame, text="📧 邮箱账号", font=label_font, width=120, anchor="e", text_color=Theme.TEXT_PRIMARY)
        email_label.grid(row=0, column=0, sticky="e", padx=(0, 12), pady=(6, 6))

        self.email_entry = ctk.CTkEntry(form_frame, height=CTRL_H, font=entry_font, placeholder_text="请输入抖店邮箱", justify="left")
        if not hasattr(self, "_email_prefilled"):
            self._email_prefilled = True
            self.email_entry.insert(0, "doudianpuhuo3@163.com")
        self.email_entry.grid(row=0, column=1, sticky="we", padx=(0, 0), pady=(6, 6))

        # 密码
        pwd_label = ctk.CTkLabel(form_frame, text="🔑 登录密码", font=label_font, width=120, anchor="e", text_color=Theme.TEXT_PRIMARY)
        pwd_label.grid(row=1, column=0, sticky="e", padx=(0, 12), pady=(6, 6))

        self.pwd_entry = ctk.CTkEntry(form_frame, height=CTRL_H, show="*", font=entry_font, placeholder_text="请输入密码", justify="left")
        if not hasattr(self, "_pwd_prefilled"):
            self._pwd_prefilled = True
            self.pwd_entry.insert(0, "Ping99re.com")
        self.pwd_entry.grid(row=1, column=1, sticky="we", padx=(0, 0), pady=(6, 6))

        # 操作按钮区域
        btn_area = ctk.CTkFrame(left, fg_color="transparent")
        btn_area.pack(fill="x", padx=24, pady=(12, 8))

        self.douyin_login_btn = ctk.CTkButton(
            btn_area,
            text="🚀 开始登录",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=Theme.RED,
            hover_color=self.darken_color(Theme.RED),
            height=48,
            width=320,
            corner_radius=10,
            command=self.start_douyin_login
        )
        self.douyin_login_btn.pack(pady=(0, 10))

        # 进度提示
        self.douyin_progress_label = ctk.CTkLabel(
            btn_area,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=Theme.YELLOW
        )
        self.douyin_progress_label.pack(pady=(0, 10))
        
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
            self.douyin_logout_btn.pack(side="left", padx=(10, 0))

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
    
    def _login_thread(self, email, password):
        """登录线程"""
        try:
            print(f"[调试] 登录线程启动，email={email}")
            headers = {
                'X-Client-ID': self.client_id,
                'X-Hardware-ID': self.hardware_id,
                'Content-Type': 'application/json'
            }
            
            print(f"[调试] 准备发送登录请求到 {SERVER_URL}/api/douyin-login-start")
            # 登录
            response = requests.post(
                f"{SERVER_URL}/api/douyin-login-start",
                headers=headers,
                json={'email': email, 'password': password},
                timeout=60
            )
            
            print(f"[调试] 收到响应，状态码: {response.status_code}")
            if not response.ok:
                raise Exception(f"登录失败：{response.status_code}")
            
            result = response.json()
            print(f"[调试] 响应内容: {result}")
            if not result.get('success'):
                raise Exception(result.get('error', '登录失败'))
            
            status = result.get('status')
            message = result.get('message', '')
            
            # 验证码处理
            if status == 'need_code':
                print(f"[调试] 需要验证码")
                self.after(0, lambda: self.douyin_progress_label.configure(text="📧 需要邮箱验证码，请查收..."))
                
                code = self.after(0, self.show_code_dialog)
                if not code:
                    self.after(0, self._login_cancelled)
                    return
                
                # 提交验证码
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
            print(f"[调试] 登录成功")
            self.douyin_logged_in = True
            self.after(0, self._login_success)
        
        except Exception as e:
            print(f"[调试] 登录异常: {e}")
            import traceback
            traceback.print_exc()
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
        
        # 显示退出登录按钮
        self.douyin_logout_btn.pack(side="left", padx=(10, 0))
        
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
    
    def poll_screenshot(self):
        """轮询获取截图（带状态指示）"""
        if not self.screenshot_polling:
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
                    timeout=5
                )
                
                if response.ok:
                    result = response.json()
                    if result.get('success') and result.get('screenshot'):
                        self.display_screenshot(result['screenshot'])
                        # 更新状态为成功
                        if hasattr(self, 'screenshot_status'):
                            self.after(0, lambda: self.screenshot_status.configure(
                                text="✅ 已更新", 
                                text_color=Theme.GREEN
                            ))
                
                # 3秒后再次轮询
                if self.screenshot_polling:
                    self.after(3000, self.poll_screenshot)
            except Exception as e:
                print(f"[调试] 截图轮询异常: {e}")
                # 3秒后再次轮询
                if self.screenshot_polling:
                    self.after(3000, self.poll_screenshot)

        threading.Thread(target=task, daemon=True).start()
    
    def display_screenshot(self, base64_img):
        """显示截图"""
        try:
            img_data = base64.b64decode(base64_img)
            img = Image.open(BytesIO(img_data))
            
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
            
            self.screenshot_label.configure(image=ctk_img, text="")
            self.screenshot_label.image = ctk_img
        except:
            pass
    
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
    
    def logout_douyin(self):
        """退出抖音登录"""
        # 确认对话框
        result = messagebox.askyesno(
            "退出登录",
            "确定要退出登录吗？\n\n退出后可以切换其他抖店账号"
        )
        
        if not result:
            return
        
        try:
            # 1. 通知后端关闭浏览器实例
            try:
                response = requests.post(
                    f"{self.server_url}/api/douyin-cleanup",
                    headers={
                        'X-Client-ID': self.client_id,
                        'X-Hardware-ID': self.hardware_id
                    },
                    timeout=5
                )
                print(f"[调试] 后端清理响应: {response.status_code}")
            except Exception as e:
                print(f"[调试] 后端清理失败: {e}")
            
            # 2. 清除前端登录状态
            self.douyin_logged_in = False
            
            # 3. 清除配置文件中的登录状态
            config = load_config()
            config['douyin_logged_in'] = False
            config.pop('login_timestamp', None)
            save_config(config)
            
            # 4. 重置UI状态
            self.douyin_login_btn.configure(text="🚀 开始登录", fg_color=Theme.RED, state="normal")
            self.douyin_status_label.configure(text="⭕ 未登录", text_color=Theme.TEXT_SECONDARY)
            self.douyin_progress_label.configure(text="")
            
            # 隐藏退出登录按钮
            self.douyin_logout_btn.pack_forget()
            
            # 5. 清空输入框（可选）
            self.email_entry.delete(0, 'end')
            self.pwd_entry.delete(0, 'end')
            
            messagebox.showinfo("退出成功", "✅ 已退出登录\n\n可以重新登录其他抖店账号")
            
        except Exception as e:
            print(f"[调试] 退出登录异常: {e}")
            messagebox.showerror("错误", f"退出登录失败：{str(e)}")
    
    # ==================== 页面2：智能选品 ====================
    
    def show_smart_selection(self):
        """智能选品页面（左右分栏布局）"""
        if not self.douyin_logged_in:
            # 未登录提示
            warning_frame = ctk.CTkFrame(self.content_frame, fg_color=Theme.CARD_BG, corner_radius=15)
            warning_frame.pack(expand=True, padx=100, pady=100)
            
            ctk.CTkLabel(
                warning_frame,
                text="⚠️  需要先登录",
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color=Theme.ORANGE
            ).pack(pady=(40, 10))
            
            ctk.CTkLabel(
                warning_frame,
                text="请点击左侧【抖音罗盘】菜单进行登录",
                font=ctk.CTkFont(size=14),
                text_color=Theme.TEXT_SECONDARY
            ).pack(pady=(0, 30))
            
            ctk.CTkButton(
                warning_frame,
                text="前往登录",
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color=Theme.PRIMARY,
                width=150,
                height=40,
                command=lambda: self.switch_page("douyin_login")
            ).pack(pady=(0, 40))
            return
        
        container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题栏
        header = ctk.CTkFrame(container, fg_color="transparent", height=60)
        header.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            header,
            text="🎯 智能选品",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=Theme.PRIMARY
        ).pack(side="left")
        
        # 左右分栏
        cols = ctk.CTkFrame(container, fg_color="transparent")
        cols.pack(fill="both", expand=True)
        
        # ========== 左侧：筛选条件（350px固定宽度）==========
        left_panel = ctk.CTkFrame(cols, width=350, fg_color=Theme.CARD_BG, corner_radius=15)
        left_panel.pack(side="left", fill="y", padx=(0, 15))
        left_panel.pack_propagate(False)
        
        # 左侧标题
        ctk.CTkLabel(
            left_panel,
            text="📋 筛选条件",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=Theme.PRIMARY
        ).pack(pady=(20, 15), padx=20, anchor="w")
        
        # 可滚动的筛选区域
        form = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # 左侧筛选表单：改为 Grid 对齐
        setup_form_grid(form, rows=8)

        label_font = ctk.CTkFont(size=14, weight="bold")
        ctrl_font = ctk.CTkFont(size=14)

        # 榜单类型
        ctk.CTkLabel(form, text="📊 榜单类型", font=label_font, text_color=Theme.TEXT_PRIMARY, anchor="e").grid(row=0, column=0, sticky="e", padx=(6, 10), pady=(8, 6))
        self.rank_type_var = ctk.StringVar(value="搜索榜")
        self.rank_type_combo = ctk.CTkComboBox(form, variable=self.rank_type_var, values=["搜索榜", "直播榜", "商品卡榜"], height=CTRL_H, font=ctrl_font, fg_color=Theme.BG_SECONDARY, button_color=Theme.PRIMARY)
        self.rank_type_combo.grid(row=0, column=1, sticky="we", padx=(0, 6), pady=(8, 6))

        # 时间段
        ctk.CTkLabel(form, text="📅 时间段", font=label_font, text_color=Theme.TEXT_PRIMARY, anchor="e").grid(row=1, column=0, sticky="e", padx=(6, 10), pady=(6, 6))
        self.time_range_var = ctk.StringVar(value="近1天")
        self.time_range_combo = ctk.CTkComboBox(form, variable=self.time_range_var, values=["近1天", "近7天", "近30天"], height=CTRL_H, font=ctrl_font, fg_color=Theme.BG_SECONDARY, button_color=Theme.PRIMARY)
        self.time_range_combo.grid(row=1, column=1, sticky="we", padx=(0, 6), pady=(6, 6))

        # 品类类型
        ctk.CTkLabel(form, text="🏷️ 品类类型", font=label_font, text_color=Theme.TEXT_PRIMARY, anchor="e").grid(row=2, column=0, sticky="e", padx=(6, 10), pady=(6, 6))
        self.category_var = ctk.StringVar(value="不限")
        self.category_combo = ctk.CTkComboBox(form, variable=self.category_var, values=["不限", "知名品牌", "新锐品牌"], height=CTRL_H, font=ctrl_font, fg_color=Theme.BG_SECONDARY, button_color=Theme.PRIMARY)
        self.category_combo.grid(row=2, column=1, sticky="we", padx=(0, 6), pady=(6, 6))

        # 首次上榜
        ctk.CTkLabel(form, text="⭐ 筛选选项", font=label_font, text_color=Theme.TEXT_PRIMARY, anchor="e").grid(row=3, column=0, sticky="e", padx=(6, 10), pady=(6, 6))
        self.first_time_var = ctk.BooleanVar(value=False)
        self.first_time_switch = ctk.CTkSwitch(form, text="只要首次上榜", variable=self.first_time_var, font=ctrl_font, progress_color=Theme.PRIMARY)
        self.first_time_switch.grid(row=3, column=1, sticky="w", padx=(0, 6), pady=(6, 6))

        # 爬取数量
        ctk.CTkLabel(form, text="🔢 爬取数量", font=label_font, text_color=Theme.TEXT_PRIMARY, anchor="e").grid(row=4, column=0, sticky="e", padx=(6, 10), pady=(6, 6))
        self.limit_var = ctk.StringVar(value="50")
        self.limit_entry = ctk.CTkEntry(form, textvariable=self.limit_var, height=CTRL_H, font=ctrl_font, placeholder_text="1-200")
        self.limit_entry.grid(row=4, column=1, sticky="we", padx=(0, 6), pady=(6, 6))

        # 保留前N名
        ctk.CTkLabel(form, text="🏆 保留前N名", font=label_font, text_color=Theme.TEXT_PRIMARY, anchor="e").grid(row=5, column=0, sticky="e", padx=(6, 10), pady=(6, 12))
        self.top_n_var = ctk.StringVar(value="0")
        self.top_n_entry = ctk.CTkEntry(form, textvariable=self.top_n_var, height=CTRL_H, font=ctrl_font, placeholder_text="0=全部")
        self.top_n_entry.grid(row=5, column=1, sticky="we", padx=(0, 6), pady=(6, 12))

        # 操作按钮
        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.grid(row=6, column=0, columnspan=2, sticky="we", pady=(6, 8))
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)

        self.start_btn = ctk.CTkButton(btn_row, text="🚀 开始选品", font=ctk.CTkFont(size=16, weight="bold"), fg_color=Theme.PRIMARY, hover_color=self.darken_color(Theme.PRIMARY), height=48, width=320, corner_radius=10, command=self.start_selection)
        self.start_btn.grid(row=0, column=0, sticky="we", padx=(0, 6))

        self.export_btn = ctk.CTkButton(btn_row, text="⬇️ 导出结果", font=ctk.CTkFont(size=14, weight="bold"), fg_color=Theme.SECONDARY, hover_color=self.darken_color(Theme.SECONDARY), height=48, corner_radius=10, command=self.export_results if hasattr(self, 'export_results') else lambda: None)
        self.export_btn.grid(row=0, column=1, sticky="we", padx=(6, 0))

        # 进度提示
        self.selection_progress = ctk.CTkLabel(form, text="", font=ctk.CTkFont(size=12), text_color=Theme.PRIMARY)
        self.selection_progress.grid(row=7, column=0, columnspan=2, sticky="w", padx=(6, 6), pady=(4, 6))
        
        # ========== 右侧：实时画面+结果 ==========
        right_panel = ctk.CTkFrame(cols, fg_color=Theme.CARD_BG, corner_radius=15)
        right_panel.pack(side="right", fill="both", expand=True)
        
        # 右侧标题
        right_header = ctk.CTkFrame(right_panel, fg_color="transparent", height=50)
        right_header.pack(fill="x", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(
            right_header,
            text="📊 实时进度",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=Theme.PRIMARY
        ).pack(side="left")
        
        # 结果区域（可滚动）
        self.result_frame = ctk.CTkScrollableFrame(right_panel, fg_color=Theme.BG_PRIMARY, corner_radius=10)
        self.result_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.result_label = ctk.CTkLabel(
            self.result_frame,
            text="📋\n\n点击左侧【开始选品】\n查看实时抓取进度和结果",
            font=ctk.CTkFont(size=14),
            text_color=Theme.TEXT_HINT,
            justify="center"
        )
        self.result_label.pack(expand=True, pady=50)
    
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
    
    def _selection_thread(self):
        """选品线程"""
        try:
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
            
            response = requests.post(
                f"{SERVER_URL}/api/douyin-scrape",
                headers=headers,
                json=data,
                timeout=120
            )
            
            if not response.ok:
                raise Exception(f"请求失败：{response.status_code}")
            
            result = response.json()
            if not result.get('success'):
                raise Exception(result.get('error', '爬取失败'))
            
            products = result.get('products', [])
            
            if not products:
                self.after(0, lambda: self._selection_failed("未找到符合条件的商品"))
                return
            
            # 导出Excel
            self.after(0, lambda: self.selection_progress.configure(text="📊 正在导出Excel..."))
            
            excel_file = self.export_to_excel(products)
            
            # 成功
            self.after(0, lambda: self._selection_success(products, excel_file))
        
        except Exception as e:
            self.after(0, lambda: self._selection_failed(str(e)))
    
    def _selection_success(self, products, excel_file):
        """选品成功"""
        self.start_btn.configure(state="normal", text="🚀 开始智能选品")
        self.selection_progress.configure(text=f"✅ 成功获取 {len(products)} 个商品！")
        
        # 显示结果
        self.result_label.configure(
            text=f"✅ 成功获取 {len(products)} 个商品\n\n已导出到：{excel_file}\n\n可用于RPA自动铺货"
        )
        
        # 成功动画
        self.show_success_animation(
            f"选品成功！",
            f"获取 {len(products)} 个商品\n已导出Excel文件",
            None
        )
    
    def _selection_failed(self, error):
        """选品失败"""
        self.start_btn.configure(state="normal", text="🚀 开始智能选品")
        self.selection_progress.configure(text="❌ 选品失败")
        messagebox.showerror("选品失败", error)
    
    def export_to_excel(self, products):
        """导出Excel"""
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
            desktop = os.path.expanduser('~')
        
        filepath = os.path.join(desktop, filename)
        
        # 写入Excel
        df.to_excel(filepath, index=False, engine='openpyxl')
        
        return filepath
    
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
            text=f"或添加QQ: {CONTACT_QQ}",
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
    
    def show_error(self, error_code, error_msg):
        """显示错误（友好版，不占满屏幕）"""
        # 只显示一个小提示，不影响主界面
        messagebox.showinfo(
            "提示",
            "软件正在初始化，请稍候...\n如有疑问请联系客服"
        )
        # 不退出软件，继续显示主界面
        self.init_main_ui()

if __name__ == "__main__":
    app = UltimateApp()
    app.mainloop()

