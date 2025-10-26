#!/usr/bin/env python3
"""
管理员工具 - 命令行版
用于管理客户端授权
"""

import requests
import json
from datetime import datetime
import sys

SERVER_URL = "http://localhost:5000"  # 修改为你的服务器地址
ADMIN_KEY = "your-secret-key-change-this"  # 修改为你的管理员密钥

def register_client():
    """注册新客户端"""
    print("\n" + "=" * 60)
    print("注册新客户端")
    print("=" * 60)
    
    client_name = input("客户名称: ").strip()
    ip_address = input("客户IP地址 (留空表示不限制): ").strip() or None
    hardware_id = input("硬件ID (由客户提供): ").strip()
    expires_days = input("授权天数 (默认365天): ").strip()
    
    try:
        expires_days = int(expires_days) if expires_days else 365
    except:
        expires_days = 365
    
    data = {
        'admin_key': ADMIN_KEY,
        'client_name': client_name,
        'ip_address': ip_address,
        'hardware_id': hardware_id,
        'expires_days': expires_days
    }
    
    try:
        response = requests.post(f"{SERVER_URL}/api/register", json=data)
        result = response.json()
        
        if result.get('success'):
            print("\n✅ 注册成功！")
            print(f"客户端ID: {result['client_id']}")
            print(f"到期时间: {result['expires_at']}")
            print("\n请将以下信息发送给客户：")
            print(f"  服务器地址: {SERVER_URL}")
            print(f"  客户端ID: {result['client_id']}")
        else:
            print(f"\n❌ 注册失败: {result.get('error')}")
    
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")

def list_clients():
    """列出所有客户端"""
    print("\n" + "=" * 60)
    print("客户端列表")
    print("=" * 60)
    
    try:
        response = requests.get(f"{SERVER_URL}/api/admin/clients?admin_key={ADMIN_KEY}")
        result = response.json()
        
        if result.get('success'):
            clients = result.get('data', [])
            
            if not clients:
                print("\n暂无客户端")
                return
            
            print(f"\n共 {len(clients)} 个客户端：\n")
            
            for client in clients:
                status = "✅ 启用" if client['is_active'] else "❌ 禁用"
                print(f"【{status}】")
                print(f"  客户名称: {client['client_name']}")
                print(f"  客户端ID: {client['client_id']}")
                print(f"  IP地址: {client['ip_address'] or '不限制'}")
                print(f"  硬件ID: {client['hardware_id'][:20]}...")
                print(f"  创建时间: {client['created_at']}")
                print(f"  到期时间: {client['expires_at']}")
                print(f"  请求次数: {client['request_count']}")
                print(f"  最后请求: {client['last_request_at'] or '从未'}")
                print("-" * 60)
        else:
            print(f"\n❌ 获取失败: {result.get('error')}")
    
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")

def toggle_client():
    """启用/禁用客户端"""
    print("\n" + "=" * 60)
    print("启用/禁用客户端")
    print("=" * 60)
    
    client_id = input("客户端ID: ").strip()
    action = input("操作 (1=启用, 0=禁用): ").strip()
    
    is_active = 1 if action == '1' else 0
    
    data = {
        'admin_key': ADMIN_KEY,
        'client_id': client_id,
        'is_active': is_active
    }
    
    try:
        response = requests.post(f"{SERVER_URL}/api/admin/toggle-client", json=data)
        result = response.json()
        
        if result.get('success'):
            print(f"\n✅ {result.get('message')}")
        else:
            print(f"\n❌ 操作失败: {result.get('error')}")
    
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")

def main():
    """主菜单"""
    while True:
        print("\n" + "=" * 60)
        print("商品价格对比系统 - 管理员工具")
        print("=" * 60)
        print("\n请选择操作：")
        print("  1. 注册新客户端")
        print("  2. 查看客户端列表")
        print("  3. 启用/禁用客户端")
        print("  0. 退出")
        print()
        
        choice = input("请输入选项: ").strip()
        
        if choice == '1':
            register_client()
        elif choice == '2':
            list_clients()
        elif choice == '3':
            toggle_client()
        elif choice == '0':
            print("\n再见！")
            sys.exit(0)
        else:
            print("\n❌ 无效选项")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n再见！")
        sys.exit(0)

