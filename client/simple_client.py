#!/usr/bin/env python3
"""
简化版客户端 - 用于测试打包
"""

import customtkinter as ctk
import sys

class SimpleApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("智能选品系统 - 测试版")
        self.geometry("800x600")
        
        # 标题
        label = ctk.CTkLabel(
            self,
            text="✅ 打包成功！\n\n智能选品系统",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        label.pack(expand=True)
        
        # 版本信息
        version = ctk.CTkLabel(
            self,
            text="版本：v2.0 测试版\n如果您看到这个界面，说明打包成功！",
            font=ctk.CTkFont(size=14)
        )
        version.pack(pady=20)
        
        # 退出按钮
        btn = ctk.CTkButton(
            self,
            text="关闭",
            command=self.quit,
            width=200,
            height=50,
            font=ctk.CTkFont(size=16)
        )
        btn.pack(pady=20)

if __name__ == "__main__":
    app = SimpleApp()
    app.mainloop()

