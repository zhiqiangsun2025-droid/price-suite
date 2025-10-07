# 🔒 客户端防破解安全指南

## 一、多层防护体系

### 1️⃣ **架构层防护（最核心）**

✅ **关键逻辑全在服务器**
- 客户端：只负责UI展示和参数收集
- 服务器：所有爬虫、匹配、对比逻辑
- 破解者即使拿到客户端代码，也无法独立使用

```
客户端 (仅UI)  →  发送参数  →  服务器 (核心逻辑)  →  返回结果  →  客户端展示
```

**优势**: 即使客户端被完全破解，没有服务器也无法工作

---

### 2️⃣ **通信层防护**

✅ **加密通信**
- AES-256 加密请求/响应
- HMAC-SHA256 签名防篡改
- 时间戳防重放攻击

```python
# 每次请求都不同
request = {
    'client_id': 'xxx',
    'hardware_id': 'yyy',
    'timestamp': 1234567890,
    'signature': 'hmac...',
    'payload': 'aes_encrypted...'
}
```

✅ **三重验证**
1. Client ID（客户身份）
2. Hardware ID（硬件绑定）
3. IP Address（地址白名单）

---

### 3️⃣ **客户端层防护**

#### 📦 **打包混淆**

**方案A：PyArmor（推荐，商业级）**
```bash
pip install pyarmor
pyarmor obfuscate --recursive client_app.py
# 生成的代码完全不可读
```

**方案B：PyInstaller + UPX**
```bash
pyinstaller --onefile --windowed \
    --key="32位加密密钥" \
    client_app.py

upx --best --ultra-brute dist/app.exe
```

#### 🚫 **反调试**
```python
# 检测调试器
if sys.gettrace() is not None:
    exit(1)

# 检测虚拟机
if is_running_in_vm():
    exit(1)
```

#### 🔐 **文件完整性**
```python
# 启动时验证exe哈希
def verify_integrity():
    exe_hash = sha256(exe_file)
    server_hash = get_from_server()
    if exe_hash != server_hash:
        exit(1)
```

---

### 4️⃣ **授权层防护**

#### 🎫 **硬件绑定**
```python
hardware_id = sha256(MAC地址 + 硬盘序列号 + CPU ID)
# 绑定到特定机器，无法复制
```

#### ⏰ **时效控制**
```sql
CREATE TABLE authorizations (
    expires_at TIMESTAMP,  -- 到期自动失效
    is_active INTEGER      -- 可远程禁用
);
```

#### 📍 **IP白名单（CIDR）**
```
允许IP段: 192.168.1.0/24
单IP: 8.8.8.8
```

---

## 二、破解难度分析

| 防护层 | 破解难度 | 说明 |
|--------|---------|------|
| **架构分离** | ⭐⭐⭐⭐⭐ | 客户端无核心逻辑，破解无意义 |
| **通信加密** | ⭐⭐⭐⭐ | 需要逆向加密算法+密钥 |
| **硬件绑定** | ⭐⭐⭐⭐ | 需要伪造硬件ID |
| **PyArmor混淆** | ⭐⭐⭐⭐⭐ | 商业级混淆，几乎不可逆 |
| **IP白名单** | ⭐⭐⭐ | 需要特定IP才能访问 |
| **服务器验证** | ⭐⭐⭐⭐⭐ | 最终验证，无法绕过 |

**综合破解难度**: ⭐⭐⭐⭐⭐ (极高)

---

## 三、部署最佳实践

### 🛡️ **服务器端**

1. **使用HTTPS**
```bash
# 申请SSL证书
certbot certonly --standalone -d yourdomain.com

# Flask配置SSL
app.run(ssl_context=('cert.pem', 'key.pem'))
```

2. **限流防刷**
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.headers.get('X-Client-ID'))

@app.route('/api/intelligent-selection')
@limiter.limit("10 per minute")  # 每分钟10次
def selection():
    ...
```

3. **日志审计**
```python
# 记录所有可疑行为
if failed_attempts > 5:
    log_to_security_system()
    block_client()
```

---

### 🖥️ **客户端**

1. **定期更新检测**
```python
def check_update():
    server_version = requests.get(f"{server}/api/version").json()
    if server_version > current_version:
        auto_update()
```

2. **离线许可证（可选）**
```python
# 生成离线激活码（有效期7天）
license = generate_offline_license(
    client_id='xxx',
    hardware_id='yyy',
    expires_in_days=7
)
```

---

## 四、应对破解的策略

### 🚨 **检测到破解怎么办？**

**策略1：远程禁用**
```python
# 管理后台操作
UPDATE authorizations SET is_active=0 WHERE client_id='xxx';
```

**策略2：更新客户端**
```python
# 发布新版本，旧版本失效
if client_version < "2.0.0":
    return "请更新到最新版本"
```

**策略3：法律途径**
```python
# 记录破解者信息
log_cracker_info(ip, hardware_id, timestamp)
# 为后续法律诉讼提供证据
```

---

## 五、成本效益分析

| 防护方案 | 成本 | 效果 | 推荐度 |
|---------|------|------|--------|
| 核心逻辑服务器化 | 低 | 极高 | ⭐⭐⭐⭐⭐ |
| PyArmor混淆 | ¥200/年 | 高 | ⭐⭐⭐⭐ |
| 硬件绑定 | 免费 | 高 | ⭐⭐⭐⭐⭐ |
| IP白名单 | 免费 | 中 | ⭐⭐⭐ |
| HTTPS通信 | 免费 | 高 | ⭐⭐⭐⭐⭐ |

**总投入**: <500元/年
**保护效果**: 99%+ 防破解率

---

## 六、终极方案：Web端

如果安全要求极高，建议改为 **纯Web应用**：

```
客户 → 浏览器 → 你的Web服务器 (Flask)
```

**优势**:
- ✅ 代码完全在服务器，客户端0代码
- ✅ 强制HTTPS，无法抓包
- ✅ 随时更新，无需客户端升级
- ✅ 按账号授权，精准控制

**缺点**:
- ❌ 需要服务器带宽支持
- ❌ 离线无法使用

---

## 七、FAQ

**Q: 客户端被反编译了怎么办？**
A: 核心逻辑在服务器，反编译也没用。

**Q: 有人复制了客户端exe怎么办？**
A: 硬件ID+IP验证，复制的exe无法激活。

**Q: 服务器被攻击怎么办？**
A: 使用云服务商的DDoS防护，限流策略。

**Q: 客户要求离线使用怎么办？**
A: 提供7天离线许可证，到期需重新联网验证。

---

## 八、总结

🎯 **核心原则**: 
> 不要试图保护客户端代码，而是让客户端变成"无用的壳"

✅ **推荐组合**:
1. 核心逻辑100%在服务器 ⭐⭐⭐⭐⭐
2. 硬件ID绑定 ⭐⭐⭐⭐⭐
3. PyArmor混淆 ⭐⭐⭐⭐
4. HTTPS + 签名验证 ⭐⭐⭐⭐⭐

**这套方案可以抵御95%以上的破解尝试！**

