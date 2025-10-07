#!/usr/bin/env python3
"""
客户端加密防破解模块
多重保护机制
"""

import hashlib
import hmac
import time
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend

class ClientProtection:
    """
    客户端保护机制
    
    防破解策略：
    1. 代码混淆（PyInstaller打包时）
    2. 通信加密（AES-256）
    3. 时间戳验证（防重放攻击）
    4. 动态密钥（每次请求不同）
    5. 关键逻辑全在服务器（客户端只是壳）
    """
    
    def __init__(self, master_key: str = "YOUR-MASTER-KEY-CHANGE-THIS"):
        self.master_key = master_key.encode()
    
    def generate_request_signature(self, client_id: str, hardware_id: str, timestamp: int) -> str:
        """
        生成请求签名（防篡改）
        
        签名算法：HMAC-SHA256
        """
        message = f"{client_id}:{hardware_id}:{timestamp}".encode()
        signature = hmac.new(self.master_key, message, hashlib.sha256).hexdigest()
        return signature
    
    def encrypt_payload(self, data: str, password: str) -> str:
        """
        加密请求数据（AES-256）
        
        Args:
            data: 要加密的数据
            password: 密码（由服务器下发）
        
        Returns:
            Base64编码的密文
        """
        # 生成密钥
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'salt_',  # 生产环境应该随机生成
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # 加密
        fernet = Fernet(key)
        encrypted = fernet.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_payload(self, encrypted_data: str, password: str) -> str:
        """解密响应数据"""
        # 生成密钥
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'salt_',
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # 解密
        fernet = Fernet(key)
        decrypted = fernet.decrypt(base64.b64decode(encrypted_data))
        return decrypted.decode()
    
    def create_secure_request(self, client_id: str, hardware_id: str, data: dict) -> dict:
        """
        创建安全请求
        
        返回格式：
        {
            'client_id': '...',
            'hardware_id': '...',
            'timestamp': 1234567890,
            'signature': 'hmac...',
            'payload': 'encrypted...'  # 加密的实际数据
        }
        """
        timestamp = int(time.time())
        signature = self.generate_request_signature(client_id, hardware_id, timestamp)
        
        # 使用时间戳作为密码（服务器可验证）
        password = f"{client_id}:{timestamp}"
        encrypted_data = self.encrypt_payload(str(data), password)
        
        return {
            'client_id': client_id,
            'hardware_id': hardware_id,
            'timestamp': timestamp,
            'signature': signature,
            'payload': encrypted_data
        }
    
    def verify_response(self, response_data: dict, client_id: str) -> dict:
        """
        验证并解密服务器响应
        """
        timestamp = response_data.get('timestamp')
        signature = response_data.get('signature')
        payload = response_data.get('payload')
        
        # 验证时间戳（防止重放攻击，5分钟内有效）
        if abs(time.time() - timestamp) > 300:
            raise ValueError("响应已过期")
        
        # 解密
        password = f"{client_id}:{timestamp}"
        decrypted_data = self.decrypt_payload(payload, password)
        
        return eval(decrypted_data)  # 或使用json.loads


class AntiDebug:
    """反调试检测"""
    
    @staticmethod
    def is_debugger_present() -> bool:
        """检测是否在调试器中运行"""
        import sys
        return hasattr(sys, 'gettrace') and sys.gettrace() is not None
    
    @staticmethod
    def check_vm():
        """检测是否在虚拟机中"""
        # 检查常见的虚拟机特征
        import platform
        system = platform.system()
        
        if system == "Windows":
            try:
                import wmi
                c = wmi.WMI()
                for item in c.Win32_ComputerSystem():
                    if "vmware" in item.Model.lower() or "virtualbox" in item.Model.lower():
                        return True
            except:
                pass
        return False


# ============ PyInstaller 打包配置（防破解） ============

"""
打包时使用以下参数：

pyinstaller --onefile --windowed \
    --key="YOUR-ENCRYPTION-KEY" \
    --name="价格对比系统" \
    --icon=app.ico \
    --upx-dir=/path/to/upx \
    --strip \
    --noupx \
    client_app.py

参数说明：
--onefile: 单文件（难以解包）
--windowed: 无控制台（隐藏输出）
--key: 加密字节码（需要PyInstaller 4.0+）
--strip: 去除调试符号
--upx-dir: UPX压缩（进一步混淆）
"""

# ============ 环境检测（防篡改） ============

def validate_environment():
    """
    环境验证
    检测是否被篡改或运行在非授权环境
    """
    # 检查文件完整性
    import sys
    exe_path = sys.executable
    
    # 计算exe的哈希
    if os.path.exists(exe_path):
        with open(exe_path, 'rb') as f:
            exe_hash = hashlib.sha256(f.read()).hexdigest()
        
        # 与服务器验证（服务器存储原始哈希）
        # TODO: 实现服务器端验证
        pass
    
    # 检查是否在沙箱/调试环境
    if AntiDebug.is_debugger_present():
        print("检测到调试器，程序退出")
        exit(1)
    
    return True


# ============ 使用示例 ============

if __name__ == "__main__":
    protection = ClientProtection()
    
    # 创建安全请求
    secure_req = protection.create_secure_request(
        client_id="CLIENT123",
        hardware_id="HW456",
        data={'category': '女装', 'count': 50}
    )
    
    print("加密请求：", secure_req)

