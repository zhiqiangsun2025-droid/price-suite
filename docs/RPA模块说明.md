# RPA模块详细说明

## 🤖 什么是RPA？

**RPA** = Robotic Process Automation（机器人流程自动化）

简单说：**模拟人操作电脑的程序**

---

## 🎯 在本项目中的作用

### 完整工作流程

```
1. 客户端(GUI) → 选择商品参数
   ↓
2. 服务器 → 爬取抖音商品数据
   ↓
3. 客户端 → 导出Excel到桌面
   ↓
4. RPA模块 → 读取Excel，自动操作铺货软件
   ↓
5. 完成 → 商品自动上架到你的店铺
```

### RPA做什么？

**场景**：你有100个商品要上架到抖店/淘宝店

**人工操作**：
```
打开铺货软件 → 复制商品链接 → 粘贴 → 点击【获取】 
→ 填写价格 → 点击【上架】 → 重复100次 ❌ 累死了
```

**RPA自动化**：
```
启动RPA → 读取Excel → 自动循环100次：
  1. 鼠标移动到输入框
  2. 自动输入商品链接
  3. 点击【获取】按钮
  4. 等待加载
  5. 填写利润价格
  6. 点击【上架】
✅ 5分钟完成，无需人工
```

---

## 💻 RPA技术实现原理

### 核心技术栈

本项目使用的RPA技术：

```python
# rpa/rpa_controller.py

1. PyAutoGUI - 控制鼠标键盘
   - pyautogui.click(x, y)      # 点击坐标
   - pyautogui.typewrite('text') # 输入文字
   - pyautogui.hotkey('ctrl', 'v') # 快捷键

2. pywinauto - 识别窗口和控件
   - app = Application().connect(title='铺货软件')
   - app['窗口'].Button.click()

3. OpenCV - 图像识别定位
   - 截图 → 查找按钮图片 → 获取坐标 → 点击
   - 适用于无法识别控件的情况

4. pandas - 读取Excel
   - df = pd.read_excel('商品列表.xlsx')
   - for row in df.iterrows(): 自动填充
```

### 实现原理图

```
Excel文件
  ↓ pandas读取
商品列表数据
  ↓ for循环每个商品
  ├→ pywinauto定位【输入框】
  ├→ pyautogui输入【商品链接】
  ├→ pywinauto点击【获取按钮】
  ├→ time.sleep等待加载
  ├→ OpenCV识别【上架按钮】位置
  └→ pyautogui点击【上架】
重复下一个商品
```

---

## 📁 为什么RPA要单独目录？

### 原因1：独立的子系统

```
price-suite/
├── client/          # 前端：用户交互、选品
├── server/          # 后端：爬虫、API
└── rpa/             # 自动化：铺货操作
    ↑ 可选模块，不是所有用户都需要
```

**为什么不合并到client？**
- ✅ RPA是可选功能（有些用户只要选品，不需要自动铺货）
- ✅ 依赖不同（PyAutoGUI、pywinauto、OpenCV）
- ✅ 运行环境不同（必须在Windows，且不能远程桌面）
- ✅ 独立销售（可以单独作为增值服务）

### 原因2：技术栈差异

| 模块 | 技术 | 环境要求 |
|------|------|---------|
| client | CustomTkinter(GUI) | Windows/Mac/Linux |
| server | Flask(Web) + Selenium | Linux服务器 |
| rpa | PyAutoGUI(桌面自动化) | **仅Windows本地** |

### 原因3：部署方式

```
client: 打包成EXE分发给用户
server: 部署到云服务器
rpa: 用户本地运行，或打包成独立工具
```

---

## 🔧 BAT文件说明

从截图看到的BAT文件：

| 文件 | 作用 | 状态 | 处理 |
|------|------|------|------|
| `build-exe.bat` | 手动打包客户端EXE | ⚠️ 已有GitHub Actions | **移到scripts/windows/** |
| `install-deps.bat` | Windows安装依赖 | ✅ 有用 | **移到scripts/windows/** |
| `run-all.bat` | 启动所有服务 | ✅ 有用 | **移到scripts/windows/** |
| `run-server.bat` | 启动服务器 | ✅ 有用 | **移到scripts/windows/** |
| `stop-all.bat` | 停止所有服务 | ✅ 有用 | **移到scripts/windows/** |
| `setup-portable-python.bat` | 配置便携Python | ⚠️ 看情况 | **移到scripts/windows/** |

**处理原则**：
- 全部移到 `scripts/windows/`
- 在 `scripts/README.md` 说明用途
- 根目录只保留 `README.md`

---

## 📚 关于多版本MD文件

你说得对！这些文件**绝对不应该放根目录**：

```
❌ 错误做法（当前）：
├── 构建成功报告-20251021006.md
├── 最终构建成功-20251021007.md
├── 优化完成报告-v1012001.md
└── ... 更多版本文档

✅ 正确做法（应该）：
docs/
├── README.md（文档索引）
├── guides/（当前指南）
│   ├── 部署指南.md
│   ├── 使用指南.md
│   └── 开发指南.md
└── archive/
    └── versions/（版本历史报告）
        ├── 20251021/
        │   ├── 006-构建报告.md
        │   └── 007-最终报告.md
        └── 20251023/
            └── 001-项目优化总结.md
```

---

## 🎯 RPA详细解释

### RPA目录结构

```
rpa/
├── rpa_controller.py    # 主控制器
├── quick_example.py     # 快速示例
├── install_rpa.bat      # 安装RPA依赖
└── README_RPA.md        # RPA说明文档
```

### RPA实现原理（与众不同的地方）

**普通程序 vs RPA**：

```
普通程序（API调用）：
程序 → HTTP请求 → 服务器API → 返回数据
✅ 快速、稳定
❌ 需要对方提供API

RPA（模拟人操作）：
程序 → 控制鼠标 → 点击软件界面 → 模拟人操作
✅ 不需要API，任何软件都能自动化
❌ 依赖界面，界面变化会失效
```

### 本项目RPA的特别之处

**自动铺货流程**：

```python
# rpa_controller.py 核心逻辑

import pyautogui
import pywinauto
import pandas as pd

# 1. 读取选品Excel
df = pd.read_excel('抖音选品结果.xlsx')

# 2. 打开铺货软件（如：甩手工具箱）
app = pywinauto.Application().connect(title='甩手工具箱')

# 3. 循环每个商品
for index, row in df.iterrows():
    商品链接 = row['商品链接']
    
    # 4. 定位输入框并输入
    输入框 = app['主窗口'].Edit
    输入框.set_text(商品链接)
    
    # 5. 点击【获取】按钮
    获取按钮 = app['主窗口'].Button('获取商品')
    获取按钮.click()
    
    # 6. 等待数据加载
    time.sleep(3)
    
    # 7. 设置价格（成本价+利润）
    原价 = float(row['价格'])
    售价 = 原价 * 1.3  # 加30%利润
    价格输入框.set_text(str(售价))
    
    # 8. 点击【上架】
    上架按钮.click()
    
    # 9. 等待上架完成
    time.sleep(2)

print(f'✅ 完成{len(df)}个商品自动铺货')
```

### 关键技术点

1. **窗口识别**：
   ```python
   # 找到铺货软件窗口
   hwnd = pywinauto.findwindows.find_window(title_re='.*铺货.*')
   ```

2. **控件操作**：
   ```python
   # 方式A：通过控件类型
   app.window().Edit.type_keys('商品链接')
   
   # 方式B：通过图像识别
   location = pyautogui.locateOnScreen('get_button.png')
   pyautogui.click(location)
   ```

3. **容错处理**：
   ```python
   # 失败重试
   for attempt in range(3):
       try:
           点击按钮()
           break
       except:
           time.sleep(1)
   ```

---

## 🚀 立即执行全面整理

<function_calls>
<invoke name="run_terminal_cmd">
<parameter name="command">cd /home/user/projects/shopxo-master/apps/price-suite && mv 构建成功报告-20251021006.md 最终构建成功-20251021007.md 优化完成报告-v1012001.md docs/archive/versions/ && mv 前端自动化测试实施完成报告.md docs/archive/ && echo "✅ 多版本md已整理"
