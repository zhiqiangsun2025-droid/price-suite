#!/usr/bin/env python3
"""
智能选品铺货系统 - 新版客户端
特性：
1. 自动注册
2. 试用期机制（1小时）
3. 友好提示
4. 三重验证
"""

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
import pyperclip

# 设置外观
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# 配置
SERVER_URL = "http://172.19.251.155:5000"  # 修改为你的服务器地址
CONFIG_FILE = "client_config.json"
TRIAL_DURATION = 3600  # 试用期：1小时（秒）
CONTACT_QQ = "123456789"  # 修改为你的QQ
CONTACT_WECHAT = "your_wechat"  # 修改为你的微信
CONTACT_EMAIL = "your@email.com"  # 修改为你的邮箱

def get_hardware_id():
    """获取硬件ID"""
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

def load_config():
    """加载配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config):
    """保存配置"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

class SmartPriceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 基础配置
        self.title("智能选品铺货系统 Pro")
        self.geometry("1200x800")
        
        # 获取硬件ID
        self.hardware_id = get_hardware_id()
        self.server_url = SERVER_URL
        
        # 初始化变量
        self.client_id = None
        self.is_active = None
        self.expires_at = None
        self.trial_start_time = None
        
        # 自动注册/验证
        self.auto_register_and_verify()
    
    def auto_register_and_verify(self):
        """自动注册并验证"""
        # 加载本地配置
        config = load_config()
        
        # 尝试注册/验证
        try:
            response = requests.post(
                f"{self.server_url}/api/register",
                json={'hardware_id': self.hardware_id},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result['success']:
                    self.client_id = result['client_id']
                    self.is_active = result['is_active']
                    self.expires_at = result.get('expires_at')
                    
                    # 保存配置
                    config['client_id'] = self.client_id
                    config['hardware_id'] = self.hardware_id
                    config['is_active'] = self.is_active
                    config['expires_at'] = self.expires_at
                    
                    # 如果是新注册，记录试用开始时间
                    if self.is_active == 0 and 'trial_start_time' not in config:
                        config['trial_start_time'] = time.time()
                    
                    save_config(config)
                    
                    # 根据状态决定界面
                    if self.is_active == 1:
                        # 已授权
                        self.create_main_ui()
                    elif self.is_active == 0:
                        # 待审核 - 进入试用模式
                        self.trial_start_time = config.get('trial_start_time', time.time())
                        self.check_trial_status()
                    else:
                        # 已拒绝
                        self.show_rejected_dialog()
                else:
                    self.show_error_dialog(result.get('error', '注册失败'))
            else:
                self.show_error_dialog(f"服务器错误：{response.status_code}")
        
        except Exception as e:
            self.show_error_dialog(f"网络错误：{str(e)}")
    
    def check_trial_status(self):
        """检查试用期状态"""
        elapsed = time.time() - self.trial_start_time
        remaining = TRIAL_DURATION - elapsed
        
        if remaining > 0:
            # 还在试用期
            self.create_main_ui(trial_mode=True, remaining_seconds=remaining)
        else:
            # 试用期已到
            self.show_trial_expired_dialog()
    
    def create_main_ui(self, trial_mode=False, remaining_seconds=0):
        """创建主界面"""
        # 清空窗口
        for widget in self.winfo_children():
            widget.destroy()
        
        # 顶部状态栏
        if trial_mode:
            self.create_trial_banner(remaining_seconds)
        else:
            self.create_authorized_banner()
        
        # 主容器
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题
        title = ctk.CTkLabel(
            main_container,
            text="🛍️ 智能选品系统",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=20)
        
        # 功能区
        self.create_function_area(main_container)
        
        # 如果是试用模式，启动倒计时
        if trial_mode:
            self.start_trial_countdown(remaining_seconds)
    
    def create_authorized_banner(self):
        """创建已授权状态栏"""
        banner = ctk.CTkFrame(self, fg_color="#28A745", height=40)
        banner.pack(fill="x", side="top")
        
        expires_text = f"到期：{self.expires_at}" if self.expires_at else "永久授权"
        label = ctk.CTkLabel(
            banner,
            text=f"✓ 已授权 | {expires_text}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white"
        )
        label.pack(pady=10)
    
    def create_trial_banner(self, remaining_seconds):
        """创建试用期状态栏"""
        self.trial_banner = ctk.CTkFrame(self, fg_color="#FFA500", height=50)
        self.trial_banner.pack(fill="x", side="top")
        
        minutes = int(remaining_seconds / 60)
        self.trial_label = ctk.CTkLabel(
            self.trial_banner,
            text=f"⏰ 试用版：剩余 {minutes} 分钟 | 请联系管理员获取授权",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white"
        )
        self.trial_label.pack(pady=15)
    
    def start_trial_countdown(self, remaining_seconds):
        """启动试用倒计时"""
        def update_countdown():
            elapsed = time.time() - self.trial_start_time
            remaining = TRIAL_DURATION - elapsed
            
            if remaining <= 0:
                # 试用期到了
                self.show_trial_expired_dialog()
            else:
                # 更新显示
                minutes = int(remaining / 60)
                seconds = int(remaining % 60)
                self.trial_label.configure(
                    text=f"⏰ 试用版：剩余 {minutes}分{seconds}秒 | 请联系管理员获取授权"
                )
                # 每秒更新一次
                self.after(1000, update_countdown)
        
        update_countdown()
    
    def create_function_area(self, parent):
        """创建功能区"""
        # 功能按钮区
        btn_frame = ctk.CTkFrame(parent)
        btn_frame.pack(pady=30, fill="x")
        
        # 智能选品按钮
        btn1 = ctk.CTkButton(
            btn_frame,
            text="🔍 智能选品",
            font=ctk.CTkFont(size=16),
            height=50,
            width=200,
            command=self.start_intelligent_selection
        )
        btn1.pack(pady=10)
        
        # 手动搜索按钮
        btn2 = ctk.CTkButton(
            btn_frame,
            text="🔎 手动搜索",
            font=ctk.CTkFont(size=16),
            height=50,
            width=200,
            command=self.start_manual_search
        )
        btn2.pack(pady=10)
        
        # 历史记录按钮
        btn3 = ctk.CTkButton(
            btn_frame,
            text="📊 历史记录",
            font=ctk.CTkFont(size=16),
            height=50,
            width=200,
            command=self.show_history
        )
        btn3.pack(pady=10)
        
        # 说明文字
        info = ctk.CTkLabel(
            parent,
            text="提示：选品功能将自动对比淘宝和拼多多价格，为您找出高利润商品",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        info.pack(pady=20)
    
    def start_intelligent_selection(self):
        """智能选品"""
        messagebox.showinfo("提示", "智能选品功能开发中...")
    
    def start_manual_search(self):
        """手动搜索"""
        messagebox.showinfo("提示", "手动搜索功能开发中...")
    
    def show_history(self):
        """历史记录"""
        messagebox.showinfo("提示", "历史记录功能开发中...")
    
    def show_trial_expired_dialog(self):
        """显示试用期到期对话框"""
        # 清空窗口
        for widget in self.winfo_children():
            widget.destroy()
        
        # 中心容器
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.pack(expand=True)
        
        # 图标
        icon = ctk.CTkLabel(
            center,
            text="⏰",
            font=ctk.CTkFont(size=100)
        )
        icon.pack(pady=30)
        
        # 标题
        title = ctk.CTkLabel(
            center,
            text="试用期已结束",
            font=ctk.CTkFont(size=36, weight="bold")
        )
        title.pack(pady=20)
        
        # 说明
        msg = ctk.CTkLabel(
            center,
            text="感谢您的试用！\n如需继续使用，请联系开发者获取授权",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        msg.pack(pady=15)
        
        # 联系方式卡片
        contact_card = ctk.CTkFrame(center, corner_radius=15)
        contact_card.pack(pady=30, padx=50)
        
        ctk.CTkLabel(
            contact_card,
            text="📮 联系方式",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(25,15))
        
        # QQ
        qq_frame = ctk.CTkFrame(contact_card, fg_color="transparent")
        qq_frame.pack(pady=10)
        ctk.CTkLabel(qq_frame, text=f"QQ：{CONTACT_QQ}", font=ctk.CTkFont(size=14)).pack(side="left", padx=10)
        ctk.CTkButton(
            qq_frame,
            text="复制",
            width=80,
            command=lambda: self.copy_and_notify(CONTACT_QQ, "QQ号")
        ).pack(side="left")
        
        # 微信
        wx_frame = ctk.CTkFrame(contact_card, fg_color="transparent")
        wx_frame.pack(pady=10)
        ctk.CTkLabel(wx_frame, text=f"微信：{CONTACT_WECHAT}", font=ctk.CTkFont(size=14)).pack(side="left", padx=10)
        ctk.CTkButton(
            wx_frame,
            text="复制",
            width=80,
            command=lambda: self.copy_and_notify(CONTACT_WECHAT, "微信号")
        ).pack(side="left")
        
        # 邮箱
        email_frame = ctk.CTkFrame(contact_card, fg_color="transparent")
        email_frame.pack(pady=(10,25))
        ctk.CTkLabel(email_frame, text=f"邮箱：{CONTACT_EMAIL}", font=ctk.CTkFont(size=14)).pack(side="left", padx=10)
        ctk.CTkButton(
            email_frame,
            text="复制",
            width=80,
            command=lambda: self.copy_and_notify(CONTACT_EMAIL, "邮箱")
        ).pack(side="left")
        
        # 按钮
        btn_frame = ctk.CTkFrame(center, fg_color="transparent")
        btn_frame.pack(pady=25)
        
        ctk.CTkButton(
            btn_frame,
            text="🔄 重新检查授权",
            command=self.auto_register_and_verify,
            width=150,
            height=40
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="❌ 退出程序",
            command=self.quit,
            fg_color="gray",
            width=150,
            height=40
        ).pack(side="left", padx=10)
    
    def show_rejected_dialog(self):
        """显示已拒绝对话框"""
        for widget in self.winfo_children():
            widget.destroy()
        
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.pack(expand=True)
        
        ctk.CTkLabel(center, text="⛔", font=ctk.CTkFont(size=100)).pack(pady=30)
        ctk.CTkLabel(center, text="授权申请已被拒绝", font=ctk.CTkFont(size=32, weight="bold")).pack(pady=20)
        ctk.CTkLabel(center, text="如有疑问，请联系管理员", font=ctk.CTkFont(size=16), text_color="gray").pack(pady=10)
        
        ctk.CTkButton(center, text="退出", command=self.quit, width=150, height=40).pack(pady=30)
    
    def show_error_dialog(self, error_msg):
        """显示错误对话框"""
        for widget in self.winfo_children():
            widget.destroy()
        
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.pack(expand=True)
        
        ctk.CTkLabel(center, text="❌", font=ctk.CTkFont(size=100)).pack(pady=30)
        ctk.CTkLabel(center, text="连接错误", font=ctk.CTkFont(size=32, weight="bold")).pack(pady=20)
        ctk.CTkLabel(center, text=error_msg, font=ctk.CTkFont(size=14), text_color="gray").pack(pady=10)
        
        btn_frame = ctk.CTkFrame(center, fg_color="transparent")
        btn_frame.pack(pady=30)
        
        ctk.CTkButton(btn_frame, text="重试", command=self.auto_register_and_verify, width=120).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="退出", command=self.quit, fg_color="gray", width=120).pack(side="left", padx=10)
    
    def copy_and_notify(self, text, label):
        """复制并提示"""
        try:
            pyperclip.copy(text)
            # 创建提示
            toast = ctk.CTkToplevel(self)
            toast.title("")
            toast.geometry("250x80")
            toast.resizable(False, False)
            
            # 居中显示
            toast.update_idletasks()
            x = self.winfo_x() + (self.winfo_width() - 250) // 2
            y = self.winfo_y() + (self.winfo_height() - 80) // 2
            toast.geometry(f"+{x}+{y}")
            
            ctk.CTkLabel(toast, text=f"✓ 已复制{label}", font=ctk.CTkFont(size=16)).pack(pady=25)
            
            # 2秒后关闭
            self.after(2000, toast.destroy)
        except:
            messagebox.showinfo("提示", f"{label}：{text}")

if __name__ == "__main__":
    app = SmartPriceApp()
    app.mainloop()

