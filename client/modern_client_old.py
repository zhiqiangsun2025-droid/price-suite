#!/usr/bin/env python3
"""
现代化客户端 - CustomTkinter版本
美观、现代、支持深色模式
"""

import customtkinter as ctk
import requests
import json
import uuid
import hashlib
import platform
import subprocess
from datetime import datetime
import csv
import os
from tkinter import filedialog, messagebox
from PIL import Image

# 设置外观
ctk.set_appearance_mode("dark")  # "dark" / "light" / "system"
ctk.set_default_color_theme("blue")  # "blue" / "dark-blue" / "green"

# 配置
SERVER_URL = "http://你的服务器IP:5000"
CLIENT_ID_FILE = "client_config.json"

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
        hardware_id = hashlib.sha256(hardware_string.encode()).hexdigest()[:32]
        return hardware_id
    except Exception as e:
        return "HARDWARE_ERROR"

def load_client_config():
    if os.path.exists(CLIENT_ID_FILE):
        with open(CLIENT_ID_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_client_config(config):
    with open(CLIENT_ID_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

class ModernPriceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 窗口配置
        self.title("智能选品铺货系统 Pro")
        self.geometry("1400x900")
        
        # 获取硬件ID
        self.hardware_id = get_hardware_id()
        
        # 加载配置
        config = load_client_config()
        if config and config.get('client_id'):
            self.client_id = config['client_id']
            self.server_url = config.get('server_url', SERVER_URL)
            self.create_main_ui()
        else:
            self.show_activation()
    
    def show_activation(self):
        """激活对话框"""
        # 清空窗口
        for widget in self.winfo_children():
            widget.destroy()
        
        # 中心容器
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.pack(expand=True)
        
        # 标题
        title = ctk.CTkLabel(
            center_frame, 
            text="🚀 软件激活",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(pady=30)
        
        # 卡片容器
        card = ctk.CTkFrame(center_frame, corner_radius=15)
        card.pack(padx=40, pady=20, fill="both")
        
        # 服务器地址
        ctk.CTkLabel(card, text="服务器地址", font=ctk.CTkFont(size=14)).pack(pady=(20,5))
        self.server_entry = ctk.CTkEntry(card, width=400, height=40, placeholder_text="http://服务器IP:5000")
        self.server_entry.insert(0, SERVER_URL)
        self.server_entry.pack(pady=5)
        
        # 客户端ID
        ctk.CTkLabel(card, text="客户端ID（由管理员提供）", font=ctk.CTkFont(size=14)).pack(pady=(15,5))
        self.client_id_entry = ctk.CTkEntry(card, width=400, height=40, placeholder_text="请输入32位客户端ID")
        self.client_id_entry.pack(pady=5)
        
        # 硬件ID（只读）
        ctk.CTkLabel(card, text="硬件ID（自动生成）", font=ctk.CTkFont(size=14)).pack(pady=(15,5))
        hardware_entry = ctk.CTkEntry(card, width=400, height=40)
        hardware_entry.insert(0, self.hardware_id)
        hardware_entry.configure(state="disabled")
        hardware_entry.pack(pady=5)
        
        # 激活按钮
        activate_btn = ctk.CTkButton(
            card,
            text="激活软件",
            height=45,
            width=200,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.activate
        )
        activate_btn.pack(pady=30)
    
    def activate(self):
        """激活"""
        server_url = self.server_entry.get().strip()
        client_id = self.client_id_entry.get().strip()
        
        if not server_url or not client_id:
            messagebox.showerror("错误", "请填写完整信息")
            return
        
        # 保存配置
        config = {
            'server_url': server_url,
            'client_id': client_id,
            'hardware_id': self.hardware_id,
            'activated_at': datetime.now().isoformat()
        }
        save_client_config(config)
        
        self.server_url = server_url
        self.client_id = client_id
        
        # 进入主界面
        self.create_main_ui()
    
    def create_main_ui(self):
        """创建主界面"""
        # 清空窗口
        for widget in self.winfo_children():
            widget.destroy()
        
        # 侧边栏
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        # Logo区域
        logo_label = ctk.CTkLabel(
            self.sidebar,
            text="🛍️ 选品系统",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        logo_label.pack(pady=30, padx=20)
        
        # 导航按钮
        self.nav_buttons = []
        
        btn1 = ctk.CTkButton(
            self.sidebar,
            text="📊 智能选品",
            command=lambda: self.show_page("selection"),
            corner_radius=8,
            height=40
        )
        btn1.pack(pady=10, padx=20, fill="x")
        self.nav_buttons.append(btn1)
        
        btn2 = ctk.CTkButton(
            self.sidebar,
            text="🔄 价格对比",
            command=lambda: self.show_page("compare"),
            corner_radius=8,
            height=40
        )
        btn2.pack(pady=10, padx=20, fill="x")
        self.nav_buttons.append(btn2)
        
        btn3 = ctk.CTkButton(
            self.sidebar,
            text="🚀 一键铺货",
            command=lambda: self.show_page("listing"),
            corner_radius=8,
            height=40
        )
        btn3.pack(pady=10, padx=20, fill="x")
        self.nav_buttons.append(btn3)
        
        btn4 = ctk.CTkButton(
            self.sidebar,
            text="📁 导出管理",
            command=lambda: self.show_page("export"),
            corner_radius=8,
            height=40
        )
        btn4.pack(pady=10, padx=20, fill="x")
        self.nav_buttons.append(btn4)
        
        # 设置按钮
        settings_btn = ctk.CTkButton(
            self.sidebar,
            text="⚙️ 系统设置",
            command=lambda: self.show_page("settings"),
            corner_radius=8,
            height=40,
            fg_color="transparent",
            border_width=2
        )
        settings_btn.pack(side="bottom", pady=20, padx=20, fill="x")
        
        # 主内容区
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(side="left", fill="both", expand=True)
        
        # 默认显示选品页
        self.show_page("selection")
    
    def show_page(self, page_name):
        """切换页面"""
        # 清空主区域
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 根据页面名显示不同内容
        if page_name == "selection":
            self.create_selection_page()
        elif page_name == "compare":
            self.create_compare_page()
        elif page_name == "listing":
            self.create_listing_page()
        elif page_name == "export":
            self.create_export_page()
        elif page_name == "settings":
            self.create_settings_page()
    
    def create_selection_page(self):
        """智能选品页面"""
        # 标题
        title = ctk.CTkLabel(
            self.main_frame,
            text="🎯 智能选品助手",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=30)
        
        # 配置卡片
        config_card = ctk.CTkFrame(self.main_frame, corner_radius=15)
        config_card.pack(padx=40, pady=20, fill="x")
        
        # 第一行：类目和时间
        row1 = ctk.CTkFrame(config_card, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(row1, text="商品类目:", font=ctk.CTkFont(size=14)).pack(side="left", padx=10)
        self.category_entry = ctk.CTkEntry(row1, width=200, placeholder_text="如：女装/连衣裙")
        self.category_entry.pack(side="left", padx=10)
        
        ctk.CTkLabel(row1, text="时间段:", font=ctk.CTkFont(size=14)).pack(side="left", padx=10)
        self.timerange_combo = ctk.CTkComboBox(row1, values=["近1天", "近3天", "近7天", "近30天"], width=150)
        self.timerange_combo.pack(side="left", padx=10)
        
        # 第二行：筛选条件
        row2 = ctk.CTkFrame(config_card, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(row2, text="筛选数量:", font=ctk.CTkFont(size=14)).pack(side="left", padx=10)
        self.count_entry = ctk.CTkEntry(row2, width=100, placeholder_text="50")
        self.count_entry.insert(0, "50")
        self.count_entry.pack(side="left", padx=10)
        
        ctk.CTkLabel(row2, text="价差阈值:", font=ctk.CTkFont(size=14)).pack(side="left", padx=10)
        self.discount_entry = ctk.CTkEntry(row2, width=100, placeholder_text="30")
        self.discount_entry.insert(0, "30")
        self.discount_entry.pack(side="left", padx=10)
        ctk.CTkLabel(row2, text="%", font=ctk.CTkFont(size=14)).pack(side="left")
        
        # 第三行：销量增长筛选
        row3 = ctk.CTkFrame(config_card, fg_color="transparent")
        row3.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(row3, text="最小销量增长:", font=ctk.CTkFont(size=14)).pack(side="left", padx=10)
        self.growth_entry = ctk.CTkEntry(row3, width=100, placeholder_text="20")
        self.growth_entry.insert(0, "20")
        self.growth_entry.pack(side="left", padx=10)
        ctk.CTkLabel(row3, text="%", font=ctk.CTkFont(size=14)).pack(side="left")
        
        self.official_check = ctk.CTkCheckBox(row3, text="包含官方/自营", font=ctk.CTkFont(size=14))
        self.official_check.pack(side="left", padx=20)
        self.official_check.select()
        
        # 开始按钮
        start_btn = ctk.CTkButton(
            config_card,
            text="🚀 开始智能选品",
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.start_intelligent_selection
        )
        start_btn.pack(pady=20)
        
        # 进度显示
        self.progress_label = ctk.CTkLabel(
            self.main_frame,
            text="等待开始...",
            font=ctk.CTkFont(size=14)
        )
        self.progress_label.pack(pady=10)
        
        self.progress_bar = ctk.CTkProgressBar(self.main_frame, width=800)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        # 结果显示区（使用文本框模拟表格）
        result_frame = ctk.CTkFrame(self.main_frame, corner_radius=15)
        result_frame.pack(padx=40, pady=20, fill="both", expand=True)
        
        self.result_text = ctk.CTkTextbox(result_frame, font=ctk.CTkFont(size=12))
        self.result_text.pack(fill="both", expand=True, padx=10, pady=10)
    
    def create_compare_page(self):
        """价格对比页面"""
        title = ctk.CTkLabel(
            self.main_frame,
            text="💰 价格对比分析",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=30)
        
        # TODO: 实现对比界面
    
    def create_listing_page(self):
        """一键铺货页面"""
        title = ctk.CTkLabel(
            self.main_frame,
            text="🚀 一键铺货",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=30)
        
        # TODO: 实现铺货界面
    
    def create_export_page(self):
        """导出管理页面"""
        title = ctk.CTkLabel(
            self.main_frame,
            text="📁 导出管理",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=30)
    
    def create_settings_page(self):
        """设置页面"""
        title = ctk.CTkLabel(
            self.main_frame,
            text="⚙️ 系统设置",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=30)
        
        # 主题切换
        theme_frame = ctk.CTkFrame(self.main_frame, corner_radius=15)
        theme_frame.pack(padx=40, pady=20, fill="x")
        
        ctk.CTkLabel(theme_frame, text="外观主题:", font=ctk.CTkFont(size=16)).pack(side="left", padx=20, pady=20)
        
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["深色模式", "浅色模式", "跟随系统"],
            command=self.change_theme
        )
        theme_menu.pack(side="left", padx=20)
    
    def change_theme(self, new_theme):
        """切换主题"""
        theme_map = {
            "深色模式": "dark",
            "浅色模式": "light",
            "跟随系统": "system"
        }
        ctk.set_appearance_mode(theme_map[new_theme])
    
    def start_intelligent_selection(self):
        """开始智能选品"""
        # 获取参数
        category = self.category_entry.get().strip()
        timerange = self.timerange_combo.get()
        count = int(self.count_entry.get() or 50)
        discount = float(self.discount_entry.get() or 30) / 100
        growth = float(self.growth_entry.get() or 20) / 100
        allow_official = self.official_check.get()
        
        if not category:
            messagebox.showwarning("提示", "请输入商品类目")
            return
        
        # 创建进度显示区（如果不存在）
        if not hasattr(self, 'progress_steps'):
            self.create_progress_steps()
        
        # 重置所有步骤
        self.reset_progress_steps()
        
        # 在新线程中执行（避免UI冻结）
        import threading
        thread = threading.Thread(target=self._do_intelligent_selection, args=(
            category, timerange, count, discount, growth, allow_official
        ))
        thread.daemon = True
        thread.start()
    
    def create_progress_steps(self):
        """创建进度步骤显示"""
        steps_frame = ctk.CTkFrame(self.main_frame, corner_radius=15)
        steps_frame.pack(padx=40, pady=10, fill="x")
        
        self.progress_steps = []
        steps = [
            ("🔗 连接服务器", "connecting"),
            ("🔍 搜索抖音商品", "searching"),
            ("🤖 AI智能匹配", "matching"),
            ("💰 价格对比分析", "comparing"),
            ("✅ 完成", "done")
        ]
        
        for idx, (text, key) in enumerate(steps):
            step_frame = ctk.CTkFrame(steps_frame, fg_color="transparent")
            step_frame.pack(side="left", expand=True, padx=5, pady=10)
            
            # 状态图标
            icon_label = ctk.CTkLabel(
                step_frame,
                text="⭕",
                font=ctk.CTkFont(size=24)
            )
            icon_label.pack()
            
            # 步骤文字
            text_label = ctk.CTkLabel(
                step_frame,
                text=text,
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            text_label.pack()
            
            self.progress_steps.append({
                'key': key,
                'icon': icon_label,
                'text': text_label,
                'status': 'pending'  # pending/running/done/error
            })
    
    def reset_progress_steps(self):
        """重置进度步骤"""
        for step in self.progress_steps:
            step['icon'].configure(text="⭕", text_color="gray")
            step['text'].configure(text_color="gray")
            step['status'] = 'pending'
    
    def update_progress_step(self, key, status):
        """更新进度步骤状态"""
        icons = {
            'pending': '⭕',
            'running': '🔄',
            'done': '✅',
            'error': '❌'
        }
        colors = {
            'pending': 'gray',
            'running': 'blue',
            'done': 'green',
            'error': 'red'
        }
        
        for step in self.progress_steps:
            if step['key'] == key:
                step['status'] = status
                step['icon'].configure(
                    text=icons[status],
                    text_color=colors[status]
                )
                step['text'].configure(text_color=colors[status])
                
                # 添加旋转动画（如果是running）
                if status == 'running':
                    self.animate_step(step)
                break
    
    def animate_step(self, step):
        """添加旋转动画"""
        if step['status'] == 'running':
            current = step['icon'].cget('text')
            animations = ['🔄', '🔃', '🔄', '🔃']
            next_idx = (animations.index(current) + 1) % len(animations) if current in animations else 0
            step['icon'].configure(text=animations[next_idx])
            
            # 继续动画
            self.after(200, lambda: self.animate_step(step))
    
    def _do_intelligent_selection(self, category, timerange, count, discount, growth, allow_official):
        """执行智能选品（后台线程）"""
        try:
            # 步骤1: 连接服务器
            self.update_progress_step('connecting', 'running')
            self.progress_label.configure(text="🔗 正在连接服务器...")
            self.progress_bar.set(0.1)
            
            headers = {
                'X-Client-ID': self.client_id,
                'X-Hardware-ID': self.hardware_id
            }
            
            data = {
                'category': category,
                'timerange': timerange,
                'count': count,
                'discount_threshold': discount,
                'growth_threshold': growth,
                'allow_official': allow_official
            }
            
            # 步骤2: 搜索抖音商品
            self.update_progress_step('connecting', 'done')
            self.update_progress_step('searching', 'running')
            self.progress_label.configure(text="🔍 服务器正在搜索抖音商品...")
            self.progress_bar.set(0.3)
            
            # 调用API
            response = requests.post(
                f"{self.server_url}/api/intelligent-selection",
                headers=headers,
                json=data,
                timeout=600
            )
            
            # 步骤3: AI匹配
            self.update_progress_step('searching', 'done')
            self.update_progress_step('matching', 'running')
            self.progress_label.configure(text="🤖 正在AI智能匹配拼多多商品...")
            self.progress_bar.set(0.6)
            
            result = response.json()
            
            # 步骤4: 价格对比
            self.update_progress_step('matching', 'done')
            self.update_progress_step('comparing', 'running')
            self.progress_label.configure(text="💰 正在进行价格对比分析...")
            self.progress_bar.set(0.85)
            
            if result.get('success'):
                products = result.get('data', [])
                self.current_result = products
                
                # 步骤5: 完成
                self.update_progress_step('comparing', 'done')
                self.update_progress_step('done', 'done')
                self.progress_bar.set(1.0)
                self.progress_label.configure(text=f"✅ 完成！找到 {len(products)} 个符合条件的商品")
                
                # 显示结果
                self.display_results(products)
                
                # 启用按钮
                self.enable_action_buttons()
            else:
                raise Exception(result.get('error', '选品失败'))
        
        except Exception as e:
            # 错误处理
            for step in self.progress_steps:
                if step['status'] == 'running':
                    self.update_progress_step(step['key'], 'error')
            
            self.progress_bar.set(0)
            self.progress_label.configure(text=f"❌ 失败: {str(e)}")
            self.after(0, lambda: messagebox.showerror("错误", f"服务器错误: {str(e)}"))
    
    def display_results(self, products):
        """显示结果"""
        self.result_text.delete("1.0", "end")
        
        # 表头
        header = f"{'序号':<4} {'商品标题':<30} {'抖音价':<8} {'拼多多':<8} {'价差':<8} {'销量增长':<10} {'相似度':<8}\n"
        self.result_text.insert("end", header)
        self.result_text.insert("end", "="*100 + "\n")
        
        # 数据行
        for idx, p in enumerate(products, 1):
            row = (
                f"{idx:<4} "
                f"{p.get('title', '')[:28]:<30} "
                f"¥{p.get('douyin_price', 0):<7.2f} "
                f"¥{p.get('pdd_price', 0):<7.2f} "
                f"{p.get('discount_rate', ''):<8} "
                f"{p.get('growth_rate', ''):<10} "
                f"{p.get('similarity', ''):<8}\n"
            )
            self.result_text.insert("end", row)
    
    def enable_action_buttons(self):
        """启用导出和铺货按钮"""
        if not hasattr(self, 'export_btn'):
            # 创建按钮区
            btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            btn_frame.pack(pady=20)
            
            self.export_btn = ctk.CTkButton(
                btn_frame,
                text="📊 导出Excel",
                command=self.export_to_excel,
                width=150,
                height=40
            )
            self.export_btn.pack(side="left", padx=10)
            
            self.listing_btn = ctk.CTkButton(
                btn_frame,
                text="🚀 一键铺货",
                command=self.start_listing,
                width=150,
                height=40,
                fg_color="green"
            )
            self.listing_btn.pack(side="left", padx=10)
    
    def export_to_excel(self):
        """导出Excel到桌面"""
        try:
            import pandas as pd
            from datetime import datetime
            
            if not hasattr(self, 'current_result') or not self.current_result:
                messagebox.showwarning("提示", "没有可导出的数据")
                return
            
            # 转成DataFrame
            df = pd.DataFrame(self.current_result)
            
            # 处理拼多多多链接
            df['pdd_urls'] = df['pdd_urls'].apply(lambda x: '\n'.join(x) if isinstance(x, list) else x)
            
            # 选择和排序列
            df = df[[
                'title', 'douyin_url', 'douyin_price', 'douyin_sales', 'growth_rate',
                'pdd_urls', 'pdd_price', 'discount_rate', 'similarity'
            ]]
            
            # 重命名（中文）
            df.columns = [
                '商品标题', '抖音链接', '抖音价格', '抖音销量', '销量增长',
                '拼多多链接', '拼多多价格', '价差', '相似度'
            ]
            
            # 保存路径
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"选品结果_{timestamp}.xlsx"
            filepath = os.path.join(desktop, filename)
            
            # 导出（带格式）
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='选品结果')
            
            self.last_excel_path = filepath
            messagebox.showinfo("成功", f"Excel已导出到桌面:\n{filename}")
        
        except ImportError:
            messagebox.showerror("错误", "请安装pandas和openpyxl:\npip install pandas openpyxl")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def start_listing(self):
        """一键铺货"""
        try:
            # 先导出Excel
            if not hasattr(self, 'last_excel_path'):
                self.export_to_excel()
            
            if not hasattr(self, 'last_excel_path'):
                return
            
            # 调用RPA脚本
            import subprocess
            rpa_script = os.path.join(os.path.dirname(__file__), '..', 'rpa', 'rpa_controller.py')
            
            subprocess.Popen([
                'python',
                rpa_script,
                '--excel', self.last_excel_path,
                '--column', '抖音链接'
            ])
            
            messagebox.showinfo("提示", "RPA已启动，请勿操作鼠标键盘！")
        
        except Exception as e:
            messagebox.showerror("错误", f"启动RPA失败: {str(e)}")

if __name__ == "__main__":
    app = ModernPriceApp()
    app.mainloop()

