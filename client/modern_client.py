#!/usr/bin/env python3
"""
智能选品系统 - 按用户需求设计
左侧菜单 + 右侧功能区
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

# 抖音/拼多多配色
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# 配置
SERVER_URL = "http://172.19.251.155:5000"
TRIAL_DURATION = 3600  # 1小时
CONTACT_QQ = "123456789"

# 配置文件保存到系统目录（用户看不到）
def get_config_path():
    """获取配置文件路径（AppData目录）"""
    if platform.system() == 'Windows':
        # Windows: C:\Users\用户名\AppData\Local\智能选品系统
        app_data = os.path.expandvars(r'%LOCALAPPDATA%')
        config_dir = os.path.join(app_data, '智能选品系统')
    else:
        # Linux/Mac: ~/.config/智能选品系统
        home = os.path.expanduser('~')
        config_dir = os.path.join(home, '.config', '智能选品系统')
    
    # 确保目录存在
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    return os.path.join(config_dir, 'config.json')

CONFIG_FILE = get_config_path()

# 配色方案
BG_COLOR = "#1E1E1E"
MENU_BG = "#2D2D30"
MENU_HOVER = "#3E3E42"
MENU_ACTIVE = "#007ACC"
PRIMARY_COLOR = "#FF5722"  # 拼多多橙红
ACCENT_COLOR = "#FFC107"   # 拼多多黄

def get_hardware_id():
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) 
                       for i in range(0, 2*6, 2)][::-1])
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

class SmartSelectionApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("智能选品系统 Pro")
        self.geometry("1400x900")
        self.configure(fg_color=BG_COLOR)
        
        self.hardware_id = get_hardware_id()
        self.server_url = SERVER_URL
        self.client_id = None
        self.is_active = None
        self.trial_start_time = None
        
        # 自动注册
        self.auto_register()
    
    def auto_register(self):
        """自动注册"""
        config = load_config()
        
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
                    
                    config['client_id'] = self.client_id
                    config['hardware_id'] = self.hardware_id
                    config['is_active'] = self.is_active
                    
                    # 确保试用期开始时间正确设置
                    if self.is_active == 0:
                        if 'trial_start_time' not in config:
                            config['trial_start_time'] = time.time()
                        self.trial_start_time = config['trial_start_time']
                    
                    save_config(config)
                    
                    if self.is_active == 1:
                        # 已授权
                        self.create_main_ui(trial_mode=False)
                    elif self.is_active == 0:
                        # 试用模式 - trial_start_time已经设置好了
                        elapsed = time.time() - self.trial_start_time
                        remaining = TRIAL_DURATION - elapsed
                        
                        if remaining > 0:
                            self.create_main_ui(trial_mode=True, remaining_seconds=remaining)
                        else:
                            self.show_expired()
                    else:
                        # 已拒绝
                        self.show_error(result.get('error_code', 103), 
                                      result.get('error', '功能升级中'))
                else:
                    self.show_error(result.get('error_code', 999), 
                                  result.get('error', '连接失败'))
            else:
                self.show_error(998, "服务器错误")
        
        except Exception as e:
            self.show_error(997, f"网络连接失败")
    
    def create_main_ui(self, trial_mode=False, remaining_seconds=0):
        """创建主界面"""
        for widget in self.winfo_children():
            widget.destroy()
        
        # 顶部标题栏
        header = ctk.CTkFrame(self, height=60, fg_color="#00BCD4", corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header,
            text="🛍 智能选品助手",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        )
        title_label.pack(side="left", padx=30, pady=15)
        
        # 试用期提示
        if trial_mode:
            mins = int(remaining_seconds / 60)
            secs = int(remaining_seconds % 60)
            self.trial_label = ctk.CTkLabel(
                header,
                text=f"⏰ 试用版 剩余 {mins}分{secs}秒 | QQ: {CONTACT_QQ}",
                font=ctk.CTkFont(size=14),
                text_color="white"
            )
            self.trial_label.pack(side="right", padx=30)
            self.start_trial_countdown(remaining_seconds)
        else:
            auth_label = ctk.CTkLabel(
                header,
                text=f"✓ 已授权",
                font=ctk.CTkFont(size=14),
                text_color="white"
            )
            auth_label.pack(side="right", padx=30)
        
        # 主容器
        main_container = ctk.CTkFrame(self, fg_color=BG_COLOR)
        main_container.pack(fill="both", expand=True)
        
        # 左侧菜单
        left_menu = ctk.CTkFrame(main_container, width=200, fg_color=MENU_BG, corner_radius=0)
        left_menu.pack(side="left", fill="y")
        left_menu.pack_propagate(False)
        
        # 菜单项
        self.current_page = "smart"
        
        menus = [
            ("📊 智能选品", "smart"),
            ("💰 价格对比", "compare"),
            ("🚀 一键铺货", "listing"),
            ("📁 导出管理", "export")
        ]
        
        ctk.CTkLabel(
            left_menu,
            text="选品系统",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#888"
        ).pack(pady=(20, 30))
        
        for label, page_id in menus:
            btn = ctk.CTkButton(
                left_menu,
                text=label,
                font=ctk.CTkFont(size=14),
                fg_color=MENU_ACTIVE if page_id == self.current_page else "transparent",
                hover_color=MENU_HOVER,
                anchor="w",
                height=45,
                command=lambda p=page_id: self.switch_page(p)
            )
            btn.pack(fill="x", padx=10, pady=5)
        
        # 右侧内容区
        self.content_frame = ctk.CTkFrame(main_container, fg_color=BG_COLOR)
        self.content_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        # 显示智能选品页面
        self.show_smart_selection()
    
    def start_trial_countdown(self, remaining):
        """试用期倒计时"""
        def update():
            elapsed = time.time() - self.trial_start_time
            left = TRIAL_DURATION - elapsed
            
            if left <= 0:
                self.show_expired()
            else:
                mins = int(left / 60)
                secs = int(left % 60)
                if hasattr(self, 'trial_label'):
                    self.trial_label.configure(text=f"⏰ 试用版 剩余 {mins}分{secs}秒 | QQ: {CONTACT_QQ}")
                self.after(1000, update)
        
        update()
    
    def switch_page(self, page_id):
        """切换页面"""
        self.current_page = page_id
        
        # 清空内容区
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        if page_id == "smart":
            self.show_smart_selection()
        elif page_id == "compare":
            self.show_price_compare()
        elif page_id == "listing":
            self.show_auto_listing()
        elif page_id == "export":
            self.show_export_manager()
    
    def show_smart_selection(self):
        """智能选品页面"""
        # 表单区域
        form = ctk.CTkFrame(self.content_frame, fg_color="#2A2A2A", corner_radius=10)
        form.pack(fill="both", expand=True)
        
        # 第一行：榜单类型 + 时间段
        row1 = ctk.CTkFrame(form, fg_color="transparent")
        row1.pack(fill="x", padx=30, pady=(30,15))
        
        ctk.CTkLabel(row1, text="榜单类型:", font=ctk.CTkFont(size=13)).pack(side="left")
        self.rank_type_combo = ctk.CTkComboBox(
            row1,
            values=["搜索榜", "直播榜", "商品卡榜", "达人带货榜", "短视频榜", "实时爆品挖掘榜"],
            width=180
        )
        self.rank_type_combo.pack(side="left", padx=10)
        self.rank_type_combo.set("搜索榜")
        
        ctk.CTkLabel(row1, text="时间段:", font=ctk.CTkFont(size=13)).pack(side="left", padx=(30,0))
        self.time_combo = ctk.CTkComboBox(
            row1,
            values=["近1天", "近7天", "近30天"],
            width=150
        )
        self.time_combo.pack(side="left", padx=10)
        self.time_combo.set("近1天")
        
        # 第二行：品类类型 + 筛选数量
        row2 = ctk.CTkFrame(form, fg_color="transparent")
        row2.pack(fill="x", padx=30, pady=15)
        
        ctk.CTkLabel(row2, text="品类类型:", font=ctk.CTkFont(size=13)).pack(side="left")
        self.category_combo = ctk.CTkComboBox(
            row2,
            values=["不限", "知名品牌", "新锐品牌", "价格带", "自营"],
            width=150
        )
        self.category_combo.pack(side="left", padx=10)
        self.category_combo.set("不限")
        
        ctk.CTkLabel(row2, text="筛选数量:", font=ctk.CTkFont(size=13)).pack(side="left", padx=(30,0))
        self.count_entry = ctk.CTkEntry(row2, width=150)
        self.count_entry.insert(0, "50")
        self.count_entry.pack(side="left", padx=10)
        
        # 第三行：价差阈值
        row3 = ctk.CTkFrame(form, fg_color="transparent")
        row3.pack(fill="x", padx=30, pady=15)
        
        ctk.CTkLabel(row3, text="价差阈值:", font=ctk.CTkFont(size=13)).pack(side="left")
        self.discount_entry = ctk.CTkEntry(row3, width=150)
        self.discount_entry.insert(0, "30")
        self.discount_entry.pack(side="left", padx=10)
        ctk.CTkLabel(row3, text="%  (用于后续拼多多对比)", font=ctk.CTkFont(size=11), text_color="#888").pack(side="left")
        
        # 开始按钮
        start_btn = ctk.CTkButton(
            form,
            text="🚀 开始智能选品",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=PRIMARY_COLOR,
            hover_color="#E64A19",
            height=50,
            width=250,
            command=self.start_selection
        )
        start_btn.pack(pady=30)
        
        # 进度提示
        self.progress_label = ctk.CTkLabel(
            form,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="#888"
        )
        self.progress_label.pack(pady=(0,30))
    
    def show_price_compare(self):
        """价格对比页面"""
        label = ctk.CTkLabel(
            self.content_frame,
            text="💰 价格对比功能\n\n开发中...",
            font=ctk.CTkFont(size=20)
        )
        label.pack(expand=True)
    
    def show_auto_listing(self):
        """一键铺货页面"""
        label = ctk.CTkLabel(
            self.content_frame,
            text="🚀 一键铺货功能\n\n开发中...",
            font=ctk.CTkFont(size=20)
        )
        label.pack(expand=True)
    
    def show_export_manager(self):
        """导出管理页面"""
        label = ctk.CTkLabel(
            self.content_frame,
            text="📁 导出管理功能\n\n开发中...",
            font=ctk.CTkFont(size=20)
        )
        label.pack(expand=True)
    
    def start_selection(self):
        """开始智能选品"""
        # 获取参数
        rank_type = self.rank_type_combo.get()
        time_range = self.time_combo.get()
        category = self.category_combo.get()
        count = self.count_entry.get()
        discount = self.discount_entry.get()
        
        if not count.isdigit():
            messagebox.showwarning("提示", "筛选数量必须是数字")
            return
        
        self.progress_label.configure(text="正在连接抖店...")
        
        # TODO: 调用后端API
        data = {
            'rank_type': rank_type,
            'time_range': time_range,
            'category': category,
            'count': int(count),
            'discount_threshold': float(discount) / 100
        }
        
        # 测试提示
        messagebox.showinfo("提示", f"参数：\n榜单：{rank_type}\n时间：{time_range}\n品类：{category}\n数量：{count}")
        self.progress_label.configure(text="功能开发中...")
    
    def show_expired(self):
        """试用期到期"""
        for widget in self.winfo_children():
            widget.destroy()
        
        center = ctk.CTkFrame(self, fg_color=BG_COLOR)
        center.pack(expand=True)
        
        ctk.CTkLabel(center, text="⏰", font=ctk.CTkFont(size=100)).pack(pady=40)
        ctk.CTkLabel(center, text="错误码: 106", font=ctk.CTkFont(size=24, weight="bold"), text_color="#FF5722").pack(pady=10)
        ctk.CTkLabel(center, text="功能升级中，请联系客服", font=ctk.CTkFont(size=18), text_color="#888").pack(pady=15)
        
        contact = ctk.CTkFrame(center, fg_color="#2A2A2A", corner_radius=15)
        contact.pack(pady=40, padx=60)
        
        ctk.CTkLabel(contact, text="📱 联系客服", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(30,20))
        
        qq_frame = ctk.CTkFrame(contact, fg_color="transparent")
        qq_frame.pack(pady=10)
        ctk.CTkLabel(qq_frame, text=f"QQ: {CONTACT_QQ}", font=ctk.CTkFont(size=16)).pack(side="left", padx=15)
        ctk.CTkButton(qq_frame, text="复制", width=100, command=lambda: self.copy_text(CONTACT_QQ)).pack(side="left")
        
        btn_frame = ctk.CTkFrame(contact, fg_color="transparent")
        btn_frame.pack(pady=(30,40))
        ctk.CTkButton(btn_frame, text="🔄 重新连接", width=140, command=self.auto_register).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="❌ 退出", width=140, fg_color="gray", command=self.quit).pack(side="left", padx=10)
    
    def show_error(self, error_code, error_msg):
        """显示错误"""
        for widget in self.winfo_children():
            widget.destroy()
        
        center = ctk.CTkFrame(self, fg_color=BG_COLOR)
        center.pack(expand=True)
        
        ctk.CTkLabel(center, text="⚠️", font=ctk.CTkFont(size=100)).pack(pady=40)
        ctk.CTkLabel(center, text=f"错误码: {error_code}", font=ctk.CTkFont(size=24, weight="bold"), text_color="#FF5722").pack(pady=10)
        ctk.CTkLabel(center, text=error_msg, font=ctk.CTkFont(size=18), text_color="#888").pack(pady=15)
        
        contact = ctk.CTkFrame(center, fg_color="#2A2A2A", corner_radius=15)
        contact.pack(pady=40, padx=60)
        
        ctk.CTkLabel(contact, text="📱 联系客服", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(30,20))
        
        qq_frame = ctk.CTkFrame(contact, fg_color="transparent")
        qq_frame.pack(pady=10)
        ctk.CTkLabel(qq_frame, text=f"QQ: {CONTACT_QQ}", font=ctk.CTkFont(size=16)).pack(side="left", padx=15)
        ctk.CTkButton(qq_frame, text="复制", width=100, command=lambda: self.copy_text(CONTACT_QQ)).pack(side="left")
        
        btn_frame = ctk.CTkFrame(contact, fg_color="transparent")
        btn_frame.pack(pady=(30,40))
        ctk.CTkButton(btn_frame, text="🔄 重试", width=140, command=self.auto_register).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="❌ 退出", width=140, fg_color="gray", command=self.quit).pack(side="left", padx=10)
    
    def copy_text(self, text):
        try:
            pyperclip.copy(text)
            messagebox.showinfo("提示", f"已复制：{text}")
        except:
            messagebox.showinfo("QQ号", text)

if __name__ == "__main__":
    app = SmartSelectionApp()
    app.mainloop()

