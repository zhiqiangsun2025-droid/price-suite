#!/usr/bin/env python3
"""
智能选品铺货系统 - 优化版客户端
配色参考：抖音(黑+红)、拼多多(橙红+黄)
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

# 抖音/拼多多混合配色方案
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# 配置
SERVER_URL = "http://172.19.251.155:5000"
CONFIG_FILE = "client_config.json"
TRIAL_DURATION = 3600  # 1小时试用
CONTACT_QQ = "123456789"

# 自定义颜色
class Colors:
    # 抖音风格
    DOUYIN_BG = "#000000"          # 纯黑背景
    DOUYIN_PRIMARY = "#FE2C55"     # 抖音红
    DOUYIN_SECONDARY = "#00F2EA"   # 抖音青
    
    # 拼多多风格  
    PDD_PRIMARY = "#FF5E3A"        # 拼多多橙红
    PDD_SECONDARY = "#FFD01E"      # 拼多多黄
    
    # 混合配色
    BG_DARK = "#1A1A1A"           # 深黑背景
    CARD_BG = "#2A2A2A"           # 卡片背景
    PRIMARY = "#FF5E3A"           # 主色（拼多多橙）
    SECONDARY = "#FE2C55"         # 次要色（抖音红）
    ACCENT = "#FFD01E"            # 强调色（拼多多黄）
    SUCCESS = "#00D668"           # 成功绿
    WARNING = "#FF9500"           # 警告橙
    DANGER = "#FF3B30"            # 危险红
    TEXT_PRIMARY = "#FFFFFF"      # 主文字
    TEXT_SECONDARY = "#8E8E93"    # 次要文字

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

class ModernPriceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 窗口配置
        self.title("智能选品助手")
        self.geometry("1300x850")
        self.configure(fg_color=Colors.BG_DARK)
        
        # 数据
        self.hardware_id = get_hardware_id()
        self.server_url = SERVER_URL
        self.client_id = None
        self.is_active = None
        self.expires_at = None
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
                    config['expires_at'] = self.expires_at
                    
                    if self.is_active == 0 and 'trial_start_time' not in config:
                        config['trial_start_time'] = time.time()
                    
                    save_config(config)
                    
                    if self.is_active == 1:
                        self.create_main_ui()
                    elif self.is_active == 0:
                        self.trial_start_time = config.get('trial_start_time', time.time())
                        self.check_trial()
                    else:
                        self.show_error("error_code" in result and result["error_code"] or 103, 
                                      result.get('error', '功能升级中'))
                else:
                    self.show_error(result.get('error_code', 999), 
                                  result.get('error', '连接失败'))
            else:
                self.show_error(998, f"服务器错误")
        
        except Exception as e:
            self.show_error(997, f"网络连接失败")
    
    def check_trial(self):
        """检查试用期"""
        elapsed = time.time() - self.trial_start_time
        remaining = TRIAL_DURATION - elapsed
        
        if remaining > 0:
            self.create_main_ui(trial=True, remaining=remaining)
        else:
            self.show_error(106, "试用期已结束")
    
    def create_main_ui(self, trial=False, remaining=0):
        """创建主界面"""
        for widget in self.winfo_children():
            widget.destroy()
        
        # 顶部状态栏
        if trial:
            self.create_trial_bar(remaining)
        else:
            self.create_auth_bar()
        
        # 主容器
        main = ctk.CTkFrame(self, fg_color=Colors.BG_DARK)
        main.pack(fill="both", expand=True)
        
        # Logo区域
        logo_frame = ctk.CTkFrame(main, fg_color="transparent", height=150)
        logo_frame.pack(fill="x", padx=40, pady=(30, 20))
        
        # 大标题（抖音风格）
        title = ctk.CTkLabel(
            logo_frame,
            text="🛍 智能选品助手",
            font=ctk.CTkFont(size=48, weight="bold"),
            text_color=Colors.PRIMARY
        )
        title.pack(pady=10)
        
        subtitle = ctk.CTkLabel(
            logo_frame,
            text="AI驱动·爆款发掘·一键铺货",
            font=ctk.CTkFont(size=16),
            text_color=Colors.TEXT_SECONDARY
        )
        subtitle.pack()
        
        # 功能卡片区
        cards_frame = ctk.CTkFrame(main, fg_color="transparent")
        cards_frame.pack(fill="both", expand=True, padx=40, pady=20)
        
        # 左侧功能卡片
        left_panel = ctk.CTkFrame(cards_frame, fg_color="transparent")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0,10))
        
        # 智能选品卡片（大卡片，抖音红）
        card1 = self.create_feature_card(
            left_panel,
            "🎯 智能选品",
            "AI分析爆款趋势\n自动对比全网价格",
            Colors.DOUYIN_PRIMARY,
            self.smart_selection
        )
        card1.pack(fill="both", expand=True, pady=(0,20))
        
        # 价格对比卡片
        card2 = self.create_feature_card(
            left_panel,
            "💰 价格对比",
            "实时抓取商品价格\n计算利润空间",
            Colors.PDD_PRIMARY,
            self.price_compare
        )
        card2.pack(fill="both", expand=True)
        
        # 右侧功能卡片
        right_panel = ctk.CTkFrame(cards_frame, fg_color="transparent")
        right_panel.pack(side="right", fill="both", expand=True, padx=(10,0))
        
        # 一键铺货卡片
        card3 = self.create_feature_card(
            right_panel,
            "🚀 一键铺货",
            "自动导入商品\n批量上架店铺",
            Colors.PDD_SECONDARY,
            self.auto_listing
        )
        card3.pack(fill="both", expand=True, pady=(0,20))
        
        # 数据统计卡片
        card4 = self.create_feature_card(
            right_panel,
            "📊 数据统计",
            "销量分析·利润追踪\n店铺诊断报告",
            Colors.DOUYIN_SECONDARY,
            self.data_stats
        )
        card4.pack(fill="both", expand=True)
        
        # 底部信息栏
        footer = ctk.CTkFrame(main, fg_color=Colors.CARD_BG, height=50)
        footer.pack(fill="x", side="bottom")
        
        footer_text = ctk.CTkLabel(
            footer,
            text="© 2025 智能选品系统 | 技术支持：AI Lab",
            font=ctk.CTkFont(size=12),
            text_color=Colors.TEXT_SECONDARY
        )
        footer_text.pack(pady=15)
        
        # 如果是试用模式，启动倒计时
        if trial:
            self.start_countdown(remaining)
    
    def create_auth_bar(self):
        """已授权状态栏"""
        bar = ctk.CTkFrame(self, fg_color=Colors.SUCCESS, height=60, corner_radius=0)
        bar.pack(fill="x", side="top")
        
        text = f"✓ 已授权 | 到期：{self.expires_at if self.expires_at else '永久'}"
        label = ctk.CTkLabel(
            bar,
            text=text,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        label.pack(pady=18)
    
    def create_trial_bar(self, remaining):
        """试用期状态栏"""
        self.trial_bar = ctk.CTkFrame(self, fg_color=Colors.WARNING, height=70, corner_radius=0)
        self.trial_bar.pack(fill="x", side="top")
        
        mins = int(remaining / 60)
        secs = int(remaining % 60)
        self.trial_label = ctk.CTkLabel(
            self.trial_bar,
            text=f"⏰ 试用版 剩余 {mins}分{secs}秒",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        )
        self.trial_label.pack(pady=10)
        
        hint = ctk.CTkLabel(
            self.trial_bar,
            text=f"完整体验请联系 QQ: {CONTACT_QQ}",
            font=ctk.CTkFont(size=12),
            text_color="white"
        )
        hint.pack()
    
    def start_countdown(self, remaining):
        """倒计时"""
        def update():
            elapsed = time.time() - self.trial_start_time
            left = TRIAL_DURATION - elapsed
            
            if left <= 0:
                self.show_error(106, "试用期已结束")
            else:
                mins = int(left / 60)
                secs = int(left % 60)
                self.trial_label.configure(text=f"⏰ 试用版 剩余 {mins}分{secs}秒")
                self.after(1000, update)
        
        update()
    
    def create_feature_card(self, parent, title, desc, color, command):
        """创建功能卡片"""
        card = ctk.CTkFrame(parent, fg_color=Colors.CARD_BG, corner_radius=20)
        
        # 标题
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=color
        )
        title_label.pack(pady=(30,15))
        
        # 描述
        desc_label = ctk.CTkLabel(
            card,
            text=desc,
            font=ctk.CTkFont(size=14),
            text_color=Colors.TEXT_SECONDARY
        )
        desc_label.pack(pady=(0,25))
        
        # 按钮
        btn = ctk.CTkButton(
            card,
            text="立即使用",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=color,
            hover_color=self.darken_color(color),
            height=50,
            width=200,
            corner_radius=25,
            command=command
        )
        btn.pack(pady=(0,30))
        
        return card
    
    def darken_color(self, hex_color, factor=0.8):
        """加深颜色"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def smart_selection(self):
        messagebox.showinfo("智能选品", "AI选品功能开发中...")
    
    def price_compare(self):
        messagebox.showinfo("价格对比", "价格对比功能开发中...")
    
    def auto_listing(self):
        messagebox.showinfo("一键铺货", "自动铺货功能开发中...")
    
    def data_stats(self):
        messagebox.showinfo("数据统计", "数据分析功能开发中...")
    
    def show_error(self, error_code, error_msg):
        """显示错误"""
        for widget in self.winfo_children():
            widget.destroy()
        
        center = ctk.CTkFrame(self, fg_color=Colors.BG_DARK)
        center.pack(expand=True)
        
        # 错误图标
        icon = ctk.CTkLabel(
            center,
            text="⚠️",
            font=ctk.CTkFont(size=120)
        )
        icon.pack(pady=40)
        
        # 错误码
        code_label = ctk.CTkLabel(
            center,
            text=f"错误码: {error_code}",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=Colors.DANGER
        )
        code_label.pack(pady=10)
        
        # 错误信息
        msg_label = ctk.CTkLabel(
            center,
            text=error_msg,
            font=ctk.CTkFont(size=18),
            text_color=Colors.TEXT_SECONDARY
        )
        msg_label.pack(pady=15)
        
        # 联系方式卡片
        contact = ctk.CTkFrame(center, fg_color=Colors.CARD_BG, corner_radius=20)
        contact.pack(pady=40, padx=60)
        
        ctk.CTkLabel(
            contact,
            text="📱 联系客服",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=Colors.PRIMARY
        ).pack(pady=(30,20))
        
        # QQ
        qq_frame = ctk.CTkFrame(contact, fg_color="transparent")
        qq_frame.pack(pady=10)
        
        ctk.CTkLabel(
            qq_frame,
            text=f"QQ: {CONTACT_QQ}",
            font=ctk.CTkFont(size=16),
            text_color=Colors.TEXT_PRIMARY
        ).pack(side="left", padx=15)
        
        ctk.CTkButton(
            qq_frame,
            text="复制",
            width=100,
            height=35,
            fg_color=Colors.PRIMARY,
            command=lambda: self.copy_text(CONTACT_QQ)
        ).pack(side="left")
        
        # 按钮
        btn_frame = ctk.CTkFrame(contact, fg_color="transparent")
        btn_frame.pack(pady=(30,40))
        
        ctk.CTkButton(
            btn_frame,
            text="🔄 重新连接",
            width=140,
            height=45,
            fg_color=Colors.SUCCESS,
            command=self.auto_register
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="❌ 退出",
            width=140,
            height=45,
            fg_color=Colors.TEXT_SECONDARY,
            command=self.quit
        ).pack(side="left", padx=10)
    
    def copy_text(self, text):
        try:
            pyperclip.copy(text)
            # 简单提示
            messagebox.showinfo("提示", f"已复制：{text}")
        except:
            messagebox.showinfo("QQ号", text)

if __name__ == "__main__":
    app = ModernPriceApp()
    app.mainloop()

