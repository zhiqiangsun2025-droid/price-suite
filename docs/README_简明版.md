# 📝 智能选品铺货系统 - 简明说明

## 一、前后端分工（一句话版）

| 端 | 干什么 | 不干什么 |
|---|--------|---------|
| **服务器** | 爬虫+AI匹配+计算+返回JSON | ❌ 不生成Excel、不控制RPA |
| **客户端** | 收集参数+显示结果+生成Excel+调用RPA | ❌ 不爬虫、不计算 |
| **RPA** | 读Excel+自动操作铺货软件 | ❌ 不联网、不与服务器通信 |

---

## 二、数据流（5步）

```
1️⃣ 客户端：收集参数 → 发送给服务器
   ↓
2️⃣ 服务器：爬虫(无头浏览器) + AI匹配 + 计算 → 返回JSON
   ↓
3️⃣ 客户端：显示结果 → 导出Excel到桌面
   ↓
4️⃣ 客户端：调用RPA，传入Excel路径
   ↓
5️⃣ RPA：读Excel → 自动操作铺货软件
```

---

## 三、服务器返回的JSON（示例）

```json
{
  "success": true,
  "data": [
    {
      "title": "夏季新款连衣裙女2024流行宽松显瘦气质长裙",
      "douyin_url": "https://haohuo.jinritemai.com/item/123",
      "douyin_price": 128.00,
      "douyin_sales": 5000,
      "growth_rate": "43%",         ← ✅ 服务器计算好的
      "pdd_urls": ["https://mobile.yangkeduo.com/goods/456"],
      "pdd_price": 59.00,
      "discount_rate": "53.9%",     ← ✅ 服务器计算好的
      "similarity": "87%",          ← ✅ 服务器计算好的
      "image_url": "https://..."
    },
    ... (更多商品)
  ]
}
```

**重点**：
- ✅ 所有百分比都是服务器计算好的
- ✅ 客户端只负责显示，不计算

---

## 四、Excel生成（客户端）

```python
# 客户端代码
import pandas as pd

# 把服务器返回的JSON转成DataFrame
df = pd.DataFrame(result['data'])

# 选择列
df = df[[
  'title', 'douyin_url', 'douyin_price', 'douyin_sales', 'growth_rate',
  'pdd_urls', 'pdd_price', 'discount_rate', 'similarity'
]]

# 重命名（中文）
df.columns = [
  '商品标题', '抖音链接', '抖音价格', '抖音销量', '销量增长',
  '拼多多链接', '拼多多价格', '价差', '相似度'
]

# 保存到桌面
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
filepath = f"{desktop}/选品结果_{timestamp}.xlsx"
df.to_excel(filepath, index=False)
```

**重点**：
- ✅ Excel在客户端本地生成
- ✅ 数据来自服务器的JSON
- ❌ 服务器不参与Excel生成

---

## 五、RPA执行（客户端本地）

```python
# RPA代码
import pandas as pd
import pyautogui

# 1. 读Excel
df = pd.read_excel("C:\\Users\\客户\\Desktop\\选品结果.xlsx")
links = df['抖音链接'].tolist()

# 2. 打开铺货软件
os.startfile("铺货软件.exe")

# 3. 逐个输入链接
for link in links:
    pyautogui.click(input_box位置)
    pyperclip.copy(link)
    pyautogui.hotkey('ctrl', 'v')
    pyautogui.click(铺货按钮位置)
    time.sleep(3)
```

**重点**：
- ✅ RPA读取客户端生成的Excel
- ✅ 完全本地运行
- ❌ 不联网、不与服务器通信

---

## 六、中转的数据（清单）

### 📤 客户端 → 服务器

```json
{
  "category": "女装/连衣裙",
  "timerange": "近7天",
  "count": 50,
  "discount_threshold": 0.30,
  "growth_threshold": 0.20,
  "allow_official": true
}
```

### 📥 服务器 → 客户端

```json
{
  "success": true,
  "data": [
    {
      "title": "...",
      "douyin_url": "...",
      "douyin_price": 128.00,
      "growth_rate": "43%",      ← 服务器算好的
      "pdd_price": 59.00,
      "discount_rate": "53.9%",  ← 服务器算好的
      "similarity": "87%"        ← 服务器算好的
    }
  ]
}
```

### 💾 客户端 → Excel → RPA

```
Excel文件: C:\Users\客户\Desktop\选品结果.xlsx

列名: 商品标题 | 抖音链接 | 抖音价格 | 拼多多价格 | 价差 | 销量增长 | 相似度

RPA读取: df['抖音链接'] → 逐个输入铺货软件
```

---

## 七、核心技术

| 端 | 技术栈 |
|---|--------|
| **服务器** | Python + Flask + Selenium(无头浏览器) + AI匹配(TF-IDF+图片哈希) |
| **客户端** | Python + CustomTkinter + pandas(导出Excel) |
| **RPA** | Python + PyAutoGUI + pywinauto + pandas(读Excel) |

---

## 八、虚拟机方案（推荐）

```
物理主机 (你正常工作)
   ├── Word / Excel / 浏览器
   └── 微信 / QQ
   
VMware虚拟机 (后台运行，不影响主机)
   ├── 选品系统.exe
   ├── 铺货软件
   └── RPA自动工作
```

**配置**: 2核4G虚拟机足够

---

## 九、文件位置

```
服务器端（你的Linux服务器）:
  apps/price-suite/server/
  ├── app.py              # Flask主程序
  ├── ai_matcher.py       # AI匹配引擎
  └── templates/          # 管理后台

客户端（给客户的）:
  智能选品系统.exe        # 打包好的程序
  
RPA（客户端包含）:
  rpa/
  ├── rpa_controller.py   # RPA脚本
  └── templates/          # 按钮图片模板
```

---

## 十、常见问题

**Q: Excel是在哪里生成的？**
A: 客户端本地（客户桌面），不经过服务器。

**Q: 服务器返回什么？**
A: 纯JSON数据，包含计算好的价差、销量增长、相似度。

**Q: RPA如何获取链接？**
A: 读取客户端生成的Excel文件，提取"抖音链接"列。

**Q: 服务器用无头浏览器吗？**
A: 是的，`--headless`模式，后台运行看不见窗口。

**Q: RPA需要联网吗？**
A: 不需要，完全本地运行。

**Q: 客户端被破解怎么办？**
A: 没关系，客户端没有核心逻辑，破解了也无法独立使用。

---

有任何问题看这3个文档：
1. `数据流向详解.md` - 超级详细版
2. `前后端分工清单.md` - 代码级详解
3. `README_简明版.md` - 本文档（快速查询）



