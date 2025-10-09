#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音登录功能测试脚本（无GUI版本）
用于在WSL中测试登录逻辑
"""

import requests
import uuid
import platform

# 配置
SERVER_URL = "http://127.0.0.1:5000"

# 生成硬件ID
def get_hardware_id():
    return str(uuid.UUID(int=uuid.getnode()))

# 生成客户端ID
def generate_client_id():
    import hashlib
    hardware_id = get_hardware_id()
    node = platform.node()
    unique_str = f"{hardware_id}_{node}"
    return hashlib.md5(unique_str.encode()).hexdigest()

def test_douyin_login():
    """测试抖音登录流程"""
    
    # 1. 生成客户端凭证
    client_id = generate_client_id()
    hardware_id = get_hardware_id()
    
    print("=" * 60)
    print("抖音登录测试脚本")
    print("=" * 60)
    print(f"客户端ID: {client_id}")
    print(f"硬件ID: {hardware_id}")
    print(f"服务器地址: {SERVER_URL}")
    print("=" * 60)
    
    # 2. 准备请求头
    headers = {
        'X-Client-ID': client_id,
        'X-Hardware-ID': hardware_id,
        'Content-Type': 'application/json'
    }
    
    # 3. 测试登录
    email = "doudianpuhuo3@163.com"
    password = "Ping99re.com"
    
    print(f"\n[步骤1] 准备发送登录请求...")
    print(f"  - 邮箱: {email}")
    print(f"  - 密码: {'*' * len(password)}")
    
    try:
        print(f"\n[步骤2] 发送POST请求到: {SERVER_URL}/api/douyin-login-start")
        response = requests.post(
            f"{SERVER_URL}/api/douyin-login-start",
            headers=headers,
            json={'email': email, 'password': password},
            timeout=120  # 增加超时时间，因为需要启动浏览器
        )
        
        print(f"\n[步骤3] 收到响应")
        print(f"  - HTTP状态码: {response.status_code}")
        print(f"  - 响应头: {dict(response.headers)}")
        
        if response.ok:
            result = response.json()
            print(f"\n[步骤4] 解析响应内容")
            print(f"  - 成功: {result.get('success')}")
            print(f"  - 状态: {result.get('status')}")
            print(f"  - 消息: {result.get('message')}")
            print(f"  - 完整响应: {result}")
            
            if result.get('status') == 'need_code':
                print("\n✅ 登录流程正常！服务器要求输入验证码。")
                print("   （在实际客户端中，这里会弹出验证码输入框）")
            elif result.get('status') == 'success':
                print("\n✅ 登录成功！无需验证码。")
            else:
                print(f"\n⚠️  未知状态: {result.get('status')}")
        else:
            print(f"\n❌ HTTP请求失败！")
            print(f"  - 状态码: {response.status_code}")
            print(f"  - 响应内容: {response.text}")
            
    except requests.exceptions.Timeout:
        print("\n❌ 请求超时（120秒）")
        print("   可能原因：")
        print("   1. 后端浏览器初始化太慢")
        print("   2. 网络连接问题")
        
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ 无法连接到服务器: {e}")
        print(f"   请确认后端服务正在运行：{SERVER_URL}")
        
    except Exception as e:
        print(f"\n❌ 发生异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_douyin_login()

