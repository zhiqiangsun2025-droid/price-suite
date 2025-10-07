#!/usr/bin/env python3
"""
商品价格对比系统 - Windows 客户端
功能：
1. 硬件绑定
2. 服务器通信
3. 图形界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import json
import uuid
import hashlib
import platform
import subprocess
from datetime import datetime
import csv
import os

# ==================== 配置 ====================

SERVER_URL = "http://你的服务器IP:5000"  # 修改为你的服务器地址
CLIENT_ID_FILE = "client_config.json"

# ==================== 硬件信息获取 ====================

def get_hardware_id():
    """获取硬件ID（MAC地址 + 硬盘序列号）"""
    try:
        # 获取MAC地址
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                       for elements in range(0, 2*6, 2)][::-1])
        
        # 获取硬盘序列号（Windows）
        if platform.system() == 'Windows':
            try:
                output = subprocess.check_output(
                    "wmic diskdrive get serialnumber", 
                    shell=True
                ).decode()
                disk_serial = output.split('\n')[1].strip()
            except:
                disk_serial = "UNKNOWN"
        else:
            disk_serial = "UNKNOWN"
        
        # 组合生成唯一硬件ID
        hardware_string = f"{mac}_{disk_serial}_{platform.node()}"
        hardware_id = hashlib.sha256(hardware_string.encode()).hexdigest()[:32]
        
        return hardware_id
    except Exception as e:
        print(f"获取硬件ID失败: {e}")
        return "HARDWARE_ERROR"

def load_client_config():
    """加载客户端配置"""
    if os.path.exists(CLIENT_ID_FILE):
        with open(CLIENT_ID_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_client_config(config):
    """保存客户端配置"""
    with open(CLIENT_ID_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# ==================== API 通信类 ====================

class APIClient:
    def __init__(self, server_url, client_id, hardware_id):
        self.server_url = server_url
        self.client_id = client_id
        self.hardware_id = hardware_id
    
    def _get_headers(self):
        """获取请求头"""
        return {
            'Content-Type': 'application/json',
            'X-Client-ID': self.client_id,
            'X-Hardware-ID': self.hardware_id
        }
    
    def health_check(self):
        """健康检查"""
        try:
            response = requests.get(f"{self.server_url}/api/health", timeout=5)
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def scrape_taobao(self, keyword, max_count=50):
        """淘宝商品爬取"""
        try:
            response = requests.post(
                f"{self.server_url}/api/scrape-taobao",
                headers=self._get_headers(),
                json={'keyword': keyword, 'max_count': max_count},
                timeout=60
            )
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def compare_prices(self, products, discount_threshold=0.3):
        """价格对比"""
        try:
            response = requests.post(
                f"{self.server_url}/api/compare-prices",
                headers=self._get_headers(),
                json={'products': products, 'discount_threshold': discount_threshold},
                timeout=120
            )
            return response.json()
        except Exception as e:
            return {'success': False, 'error': str(e)}

# ==================== GUI 主界面 ====================

class PriceComparisonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("商品价格对比系统 - 客户端 v1.0")
        self.root.geometry("1000x700")
        
        # 获取硬件ID
        self.hardware_id = get_hardware_id()
        
        # 加载配置
        config = load_client_config()
        if config and config.get('client_id'):
            self.client_id = config['client_id']
            self.server_url = config.get('server_url', SERVER_URL)
        else:
            self.show_activation_dialog()
            return
        
        # 初始化API客户端
        self.api = APIClient(self.server_url, self.client_id, self.hardware_id)
        
        # 检查连接
        self.check_connection()
        
        # 创建界面
        self.create_widgets()
    
    def show_activation_dialog(self):
        """显示激活对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("软件激活")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="请输入激活信息", font=('Arial', 14, 'bold')).pack(pady=20)
        
        # 服务器地址
        tk.Label(dialog, text="服务器地址:").pack()
        server_entry = tk.Entry(dialog, width=50)
        server_entry.insert(0, SERVER_URL)
        server_entry.pack(pady=5)
        
        # 客户端ID
        tk.Label(dialog, text="客户端ID (由管理员提供):").pack()
        client_id_entry = tk.Entry(dialog, width=50)
        client_id_entry.pack(pady=5)
        
        # 硬件ID（只读）
        tk.Label(dialog, text="硬件ID (自动生成):").pack()
        hardware_entry = tk.Entry(dialog, width=50)
        hardware_entry.insert(0, self.hardware_id)
        hardware_entry.config(state='readonly')
        hardware_entry.pack(pady=5)
        
        def activate():
            server_url = server_entry.get().strip()
            client_id = client_id_entry.get().strip()
            
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
            self.api = APIClient(server_url, client_id, self.hardware_id)
            
            dialog.destroy()
            self.check_connection()
            self.create_widgets()
        
        tk.Button(dialog, text="激活", command=activate, 
                 bg='#4CAF50', fg='white', padx=30, pady=10).pack(pady=20)
    
    def check_connection(self):
        """检查服务器连接"""
        result = self.api.health_check()
        if not result.get('success'):
            messagebox.showerror("连接失败", 
                               f"无法连接到服务器\n错误: {result.get('error')}\n\n请检查网络或联系管理员")
    
    def create_widgets(self):
        """创建主界面"""
        # 顶部信息栏
        info_frame = tk.Frame(self.root, bg='#2196F3', height=60)
        info_frame.pack(fill=tk.X)
        
        tk.Label(info_frame, text="🛍️ 商品价格对比系统", 
                font=('Arial', 16, 'bold'), bg='#2196F3', fg='white').pack(side=tk.LEFT, padx=20, pady=10)
        
        tk.Label(info_frame, text=f"客户端ID: {self.client_id[:16]}...", 
                bg='#2196F3', fg='white').pack(side=tk.RIGHT, padx=20)
        
        # 创建笔记本（标签页）
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标签页1：淘宝爬取
        tab1 = tk.Frame(notebook)
        notebook.add(tab1, text="📦 淘宝商品爬取")
        self.create_taobao_tab(tab1)
        
        # 标签页2：价格对比
        tab2 = tk.Frame(notebook)
        notebook.add(tab2, text="💰 价格对比")
        self.create_compare_tab(tab2)
        
        # 标签页3：自动选品 / 一键执行
        tab3 = tk.Frame(notebook)
        notebook.add(tab3, text="⚙️ 自动选品")
        self.create_automation_tab(tab3)

        # 标签页4：导出管理
        tab4 = tk.Frame(notebook)
        notebook.add(tab4, text="📊 导出管理")
        self.create_export_tab(tab4)
        
        # 状态栏
        self.status_bar = tk.Label(self.root, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_taobao_tab(self, parent):
        """创建淘宝爬取标签页"""
        # 搜索框
        search_frame = tk.Frame(parent)
        search_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(search_frame, text="商品关键词:", font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W)
        self.keyword_entry = tk.Entry(search_frame, width=40, font=('Arial', 10))
        self.keyword_entry.grid(row=0, column=1, padx=10)
        
        tk.Label(search_frame, text="数量:", font=('Arial', 10)).grid(row=0, column=2)
        self.count_entry = tk.Entry(search_frame, width=10, font=('Arial', 10))
        self.count_entry.insert(0, "50")
        self.count_entry.grid(row=0, column=3, padx=10)
        
        tk.Button(search_frame, text="🔍 开始爬取", command=self.start_scrape_taobao,
                 bg='#4CAF50', fg='white', padx=20, pady=10).grid(row=0, column=4, padx=10)
        
        # 进度条
        self.progress = ttk.Progressbar(parent, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=20, pady=10)
        
        # 结果显示
        result_frame = tk.Frame(parent)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 创建表格
        columns = ('排名', '商品名称', '价格', '销量', '店铺')
        self.taobao_tree = ttk.Treeview(result_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.taobao_tree.heading(col, text=col)
            self.taobao_tree.column(col, width=150)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.taobao_tree.yview)
        self.taobao_tree.configure(yscroll=scrollbar.set)
        
        self.taobao_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.taobao_products = []  # 存储爬取结果
    
    def create_compare_tab(self, parent):
        """创建价格对比标签页"""
        # 配置框
        config_frame = tk.Frame(parent)
        config_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(config_frame, text="价格折扣阈值:", font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W)
        self.discount_entry = tk.Entry(config_frame, width=10, font=('Arial', 10))
        self.discount_entry.insert(0, "30")
        self.discount_entry.grid(row=0, column=1, padx=10)
        tk.Label(config_frame, text="%", font=('Arial', 10)).grid(row=0, column=2)
        
        tk.Button(config_frame, text="🔄 开始对比", command=self.start_compare,
                 bg='#FF9800', fg='white', padx=20, pady=10).grid(row=0, column=3, padx=20)
        
        # 结果显示
        result_frame = tk.Frame(parent)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        columns = ('商品名称', '淘宝价格', '拼多多价格', '折扣率', '差价')
        self.compare_tree = ttk.Treeview(result_frame, columns=columns, show='headings', height=18)
        
        for col in columns:
            self.compare_tree.heading(col, text=col)
            self.compare_tree.column(col, width=180)
        
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.compare_tree.yview)
        self.compare_tree.configure(yscroll=scrollbar.set)
        
        self.compare_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.compare_results = []
    
    def create_export_tab(self, parent):
        """创建导出管理标签页"""
        tk.Label(parent, text="📊 导出选项", font=('Arial', 14, 'bold')).pack(pady=20)
        
        button_frame = tk.Frame(parent)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="💾 导出为 CSV", command=self.export_csv,
                 bg='#2196F3', fg='white', padx=30, pady=15, font=('Arial', 11)).pack(pady=10)
        
        tk.Button(button_frame, text="📤 导出到铺货软件", command=self.export_to_listing_tool,
                 bg='#9C27B0', fg='white', padx=30, pady=15, font=('Arial', 11)).pack(pady=10)
        
        tk.Label(parent, text="导出格式：支持 CSV、Excel 等格式\n"
                             "可直接导入一键铺货软件", 
                font=('Arial', 10), fg='gray').pack(pady=20)
    
    def start_scrape_taobao(self):
        """开始淘宝爬取"""
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            messagebox.showwarning("警告", "请输入商品关键词")
            return
        
        try:
            count = int(self.count_entry.get())
        except:
            messagebox.showerror("错误", "数量必须是数字")
            return
        
        self.status_bar.config(text="正在爬取淘宝商品...")
        self.progress.start()
        
        # 在实际应用中，这里应该使用线程避免界面冻结
        result = self.api.scrape_taobao(keyword, count)
        
        self.progress.stop()
        
        if result.get('success'):
            products = result.get('data', [])
            self.taobao_products = products
            
            # 清空表格
            for item in self.taobao_tree.get_children():
                self.taobao_tree.delete(item)
            
            # 填充数据
            for idx, product in enumerate(products, 1):
                self.taobao_tree.insert('', tk.END, values=(
                    idx,
                    product.get('title', '')[:50],
                    f"¥{product.get('price', 0)}",
                    product.get('sales', ''),
                    product.get('shop_name', '')
                ))
            
            self.status_bar.config(text=f"成功爬取 {len(products)} 个商品")
            messagebox.showinfo("成功", f"成功爬取 {len(products)} 个商品")
        else:
            error = result.get('error', '未知错误')
            self.status_bar.config(text=f"爬取失败: {error}")
            messagebox.showerror("错误", f"爬取失败: {error}")

    def create_automation_tab(self, parent):
        """自动选品与一键执行（按新需求）"""
        frame = tk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 规则下拉
        tk.Label(frame, text="选品规则:").grid(row=0, column=0, sticky=tk.W)
        self.rule_var = tk.StringVar()
        self.rule_combo = ttk.Combobox(frame, textvariable=self.rule_var, state='readonly')
        self.rule_combo.grid(row=0, column=1, sticky=tk.W, padx=10)

        tk.Button(frame, text="同步服务器规则", command=self.sync_rules, bg='#607D8B', fg='white').grid(row=0, column=2, padx=10)

        # 一键执行
        tk.Button(frame, text="🚀 一键选品→对比→铺货", command=self.one_click_run,
                  bg='#4CAF50', fg='white', padx=20, pady=10).grid(row=1, column=0, columnspan=3, pady=20)

        # 执行结果
        self.auto_text = tk.Text(frame, height=16)
        self.auto_text.grid(row=2, column=0, columnspan=3, sticky='nsew')
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(2, weight=1)

    def log_auto(self, text):
        try:
            self.auto_text.insert(tk.END, text + "\n")
            self.auto_text.see(tk.END)
        except:
            pass

    def sync_rules(self):
        """从服务器同步规则列表"""
        try:
            headers = {
                'X-Client-ID': self.client_id,
                'X-Hardware-ID': self.hardware_id
            }
            resp = requests.get(f"{self.server_url}/api/rules/active", headers=headers, timeout=15).json()
            if resp.get('success'):
                rules = resp.get('data', [])
                self.rules_cache = rules
                names = [f"#{r['id']} {r['name']} (≥{int(r['price_diff_threshold']*100)}%)" for r in rules]
                self.rule_combo['values'] = names
                if names:
                    self.rule_combo.current(0)
                messagebox.showinfo("成功", f"已同步 {len(rules)} 条规则")
            else:
                messagebox.showerror("错误", resp.get('error', '同步失败'))
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def one_click_run(self):
        """一键执行：按选中规则 → 触发对比 → 生成链接 → 调用RPA（占位）"""
        self.log_auto("开始执行...")
        # 示例：这里假设 compare_results 中已有拼多多链接
        if not self.compare_results:
            self.log_auto("暂无对比结果，先进行‘价格对比’或手动导入链接")
            return
        links = [c['pinduoduo_product'].get('url','') for c in self.compare_results if c['pinduoduo_product'].get('url')]
        if not links:
            self.log_auto("对比结果没有链接字段，无法继续")
            return

        # 写入临时CSV
        tmp_csv = os.path.join(os.path.expanduser('~'), 'Desktop', 'pdd_links.csv')
        try:
            with open(tmp_csv, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=['url'])
                writer.writeheader()
                for u in links:
                    writer.writerow({'url': u})
            self.log_auto(f"已导出 {len(links)} 条链接 → {tmp_csv}")
        except Exception as e:
            self.log_auto(f"导出CSV失败: {e}")
            return

        # 调用 RPA CLI（Windows 上）
        try:
            # 假设 rpa_controller.py 被放到 C:\rpa\rpa_controller.py
            rpa_path = r"C:\\rpa\\rpa_controller.py"
            if os.path.exists(rpa_path):
                cmd = f'python "{rpa_path}" --csv "{tmp_csv}"'
                self.log_auto(f"执行: {cmd}")
                subprocess.Popen(cmd, shell=True)
                self.log_auto("RPA 已启动，请查看铺货软件窗口...")
            else:
                self.log_auto("未找到 rpa_controller.py，请确认已在 Windows 配置 RPA 环境")
        except Exception as e:
            self.log_auto(f"启动RPA失败: {e}")
    
    def start_compare(self):
        """开始价格对比"""
        if not self.taobao_products:
            messagebox.showwarning("警告", "请先爬取淘宝商品")
            return
        
        try:
            discount = float(self.discount_entry.get()) / 100
        except:
            messagebox.showerror("错误", "折扣必须是数字")
            return
        
        self.status_bar.config(text="正在对比价格...")
        self.progress.start()
        
        result = self.api.compare_prices(self.taobao_products, discount)
        
        self.progress.stop()
        
        if result.get('success'):
            comparisons = result.get('data', [])
            self.compare_results = comparisons
            
            # 清空表格
            for item in self.compare_tree.get_children():
                self.compare_tree.delete(item)
            
            # 填充数据
            for comp in comparisons:
                self.compare_tree.insert('', tk.END, values=(
                    comp['taobao_product']['title'][:40],
                    f"¥{comp['taobao_price']}",
                    f"¥{comp['pinduoduo_price']}",
                    comp['discount_rate'],
                    f"¥{comp['price_diff']:.2f}"
                ))
            
            self.status_bar.config(text=f"找到 {len(comparisons)} 个低价商品")
            messagebox.showinfo("成功", f"找到 {len(comparisons)} 个低价商品")
        else:
            error = result.get('error', '未知错误')
            self.status_bar.config(text=f"对比失败: {error}")
            messagebox.showerror("错误", f"对比失败: {error}")
    
    def export_csv(self):
        """导出为 CSV"""
        if not self.compare_results:
            messagebox.showwarning("警告", "没有可导出的数据")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            initialfile=f"价格对比_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    fieldnames = ['淘宝商品', '淘宝价格', '拼多多商品', '拼多多价格', 
                                '折扣率', '差价', '淘宝链接', '拼多多链接']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for comp in self.compare_results:
                        writer.writerow({
                            '淘宝商品': comp['taobao_product']['title'],
                            '淘宝价格': comp['taobao_price'],
                            '拼多多商品': comp['pinduoduo_product']['title'],
                            '拼多多价格': comp['pinduoduo_price'],
                            '折扣率': comp['discount_rate'],
                            '差价': comp['price_diff'],
                            '淘宝链接': comp['taobao_product'].get('url', ''),
                            '拼多多链接': comp['pinduoduo_product'].get('url', '')
                        })
                
                messagebox.showinfo("成功", f"已导出到:\n{filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")
    
    def export_to_listing_tool(self):
        """导出到铺货软件"""
        # 这里实现导出到特定铺货软件的格式
        messagebox.showinfo("提示", "此功能需要根据具体的铺货软件格式定制")

# ==================== 主程序入口 ====================

def main():
    root = tk.Tk()
    app = PriceComparisonApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

