# 🤖 Windows 桌面应用程序自动化（RPA）完整解决方案

## 🎯 核心功能

这个RPA系统可以**自动控制任何 Windows 桌面软件**，包括：

✅ **自动打开铺货软件**  
✅ **自动输入商品链接**（批量）  
✅ **自动点击铺货按钮**  
✅ **自动等待完成**  
✅ **自动导出结果**  
✅ **全程截图记录**  

## 🛠️ 技术栈

### 核心库

1. **PyAutoGUI** - 模拟鼠标键盘操作
2. **pywinauto** - Windows GUI自动化
3. **OpenCV** - 图像识别和模板匹配
4. **Pillow** - 图像处理

### 三种控制策略

| 策略 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **UI自动化** (pywinauto) | 精确、可靠 | 需要控件支持 | 标准Windows应用 |
| **图像识别** (OpenCV) | 通用、不依赖控件 | 分辨率敏感 | 任何软件 |
| **坐标点击** (PyAutoGUI) | 简单快速 | 位置固定 | 快速原型 |

## 📦 安装步骤

### 1. 安装 Python 依赖

```bash
# 基础库
pip install pyautogui pillow opencv-python numpy

# Windows GUI自动化
pip install pywinauto

# 剪贴板支持（输入中文）
pip install pyperclip

# 可选：OCR文字识别
pip install pytesseract
```

### 2. 安装系统依赖

#### Windows 10/11

```batch
REM 所有依赖都已包含在Python包中
REM 无需额外安装
```

#### OCR支持（可选）

如果需要文字识别功能：
1. 下载 Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
2. 安装到 `C:\Program Files\Tesseract-OCR\`
3. 添加到系统PATH

## 🚀 快速开始

### 第一步：准备模板图片

模板图片是用于图像识别的关键。

#### 方法1：使用内置工具创建

```python
from rpa_controller import TemplateCreator

# 运行模板创建工具
TemplateCreator.create_template_interactive()

# 操作步骤：
# 1. 打开铺货软件
# 2. 截取屏幕
# 3. 用鼠标框选需要识别的按钮/输入框
# 4. 保存模板
```

#### 方法2：手动截图

1. 打开铺货软件
2. 使用 Windows 截图工具（Win + Shift + S）
3. 截取需要识别的元素（如"铺货"按钮）
4. 保存到 `templates/` 目录

**需要的模板：**
- `input_box.png` - 商品链接输入框
- `listing_button.png` - 铺货按钮
- `completion_message.png` - 完成提示
- `export_button.png` - 导出按钮

### 第二步：配置软件路径

编辑 `rpa_controller.py`，修改配置：

```python
class RPAConfig:
    # 铺货软件路径（修改为实际路径）
    LISTING_SOFTWARE_PATH = r"C:\Program Files\铺货软件\listing.exe"
    
    # 窗口标题（修改为实际标题）
    LISTING_SOFTWARE_NAME = "铺货助手"
```

### 第三步：运行测试

```python
from rpa_controller import ListingSoftwareAutomator

# 创建自动化控制器
automator = ListingSoftwareAutomator()

# 测试链接
links = [
    "https://mobile.yangkeduo.com/goods.html?goods_id=123456"
]

# 执行自动化
result = automator.run_full_process(links)
print(result)
```

## 📖 详细使用指南

### 基础操作示例

#### 1. 鼠标和键盘控制

```python
from rpa_controller import RPATools

rpa = RPATools()

# 移动鼠标
pyautogui.moveTo(500, 500, duration=1)

# 点击
pyautogui.click()

# 双击
pyautogui.doubleClick()

# 右键点击
pyautogui.rightClick()

# 输入英文
rpa.type_text("Hello World")

# 输入中文（通过粘贴）
rpa.type_chinese("你好世界")

# 按键
rpa.press_key('enter')

# 组合键
rpa.hotkey('ctrl', 'c')  # 复制
rpa.hotkey('ctrl', 'v')  # 粘贴
```

#### 2. 图像识别和点击

```python
# 查找图片并返回坐标
position = rpa.find_image_on_screen('templates/button.png')
if position:
    print(f"找到按钮在: {position}")

# 直接点击图片
rpa.click_image('templates/button.png')

# 等待图片出现再点击
rpa.wait_for_image('templates/dialog.png', timeout=10)
```

#### 3. 屏幕截图

```python
# 截取全屏
rpa.take_screenshot('screenshot.png')

# 截取特定区域
region = (100, 100, 500, 500)  # (x, y, width, height)
screenshot = pyautogui.screenshot(region=region)
screenshot.save('region.png')
```

#### 4. Windows应用控制

```python
from rpa_controller import WindowsAppController

# 创建控制器
app = WindowsAppController(
    app_path=r"C:\Program Files\MyApp\app.exe",
    window_title="我的应用"
)

# 启动应用
app.start_app()

# 或连接到已运行的应用
app.connect_app()

# 激活窗口
app.activate_window()

# 点击按钮（通过文本）
app.click_button("确定")

# 在输入框中输入文本
app.input_text_to_edit("商品链接", control_index=0)
```

### 完整流程示例

```python
from rpa_controller import ListingSoftwareAutomator

# 1. 创建自动化控制器
automator = ListingSoftwareAutomator()

# 2. 准备商品链接
product_links = [
    "https://mobile.yangkeduo.com/goods1",
    "https://mobile.yangkeduo.com/goods2",
    "https://mobile.yangkeduo.com/goods3"
]

# 3. 执行完整流程
result = automator.run_full_process(product_links)

# 4. 处理结果
if result['success']:
    print(f"✅ 成功铺货 {result['product_count']} 个商品")
    print(f"📊 结果文件: {result['result_path']}")
else:
    print(f"❌ 失败: {result['error']}")
```

## 🔧 高级功能

### 1. 自定义流程

```python
class CustomAutomator(ListingSoftwareAutomator):
    """自定义铺货流程"""
    
    def custom_step(self):
        """添加自定义步骤"""
        # 点击特定按钮
        self.rpa.click_image('templates/custom_button.png')
        
        # 等待加载
        time.sleep(2)
        
        # 输入特殊数据
        self.rpa.type_chinese("自定义文本")
    
    def run_full_process(self, product_links):
        """重写完整流程"""
        self.start()
        self.input_product_links(product_links)
        self.custom_step()  # 添加自定义步骤
        self.click_listing_button()
        self.wait_for_completion()
        return self.export_results()
```

### 2. 错误处理和重试

```python
def safe_click(template, max_retries=3):
    """安全点击，带重试"""
    for i in range(max_retries):
        try:
            if rpa.click_image(template):
                return True
            print(f"重试 {i+1}/{max_retries}...")
            time.sleep(2)
        except Exception as e:
            print(f"错误: {e}")
    
    return False
```

### 3. 条件判断

```python
# 等待两个图片之一出现
def wait_for_either(template1, template2, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        if rpa.find_image_on_screen(template1):
            return 'template1'
        if rpa.find_image_on_screen(template2):
            return 'template2'
        time.sleep(0.5)
    return None

# 使用示例
result = wait_for_either('success.png', 'error.png')
if result == 'success.png':
    print("成功！")
else:
    print("失败！")
```

### 4. OCR 文字识别

```python
import pytesseract
from PIL import Image

# 截图
screenshot = pyautogui.screenshot(region=(100, 100, 500, 200))

# OCR识别
text = pytesseract.image_to_string(screenshot, lang='chi_sim')
print(f"识别到的文字: {text}")

# 判断是否包含特定文字
if "完成" in text:
    print("铺货已完成！")
```

## ⚠️ 常见问题

### Q1: 图像识别不准确

**原因：**
- 分辨率不同
- 界面主题改变
- 模板图片质量差

**解决方案：**
```python
# 降低置信度阈值
rpa.click_image('button.png', confidence=0.7)  # 默认0.8

# 使用多个模板
templates = ['button1.png', 'button2.png', 'button3.png']
for template in templates:
    if rpa.click_image(template):
        break
```

### Q2: 找不到窗口控件

**原因：**
- 软件不支持 UI Automation
- 需要管理员权限

**解决方案：**
```python
# 改用图像识别策略
rpa.click_image('templates/button.png')

# 或使用坐标
pyautogui.click(500, 300)
```

### Q3: 中文输入失败

**原因：**
- 输入法问题

**解决方案：**
```python
# 使用粘贴方式
import pyperclip
pyperclip.copy("中文文本")
pyautogui.hotkey('ctrl', 'v')

# 或使用专用函数
rpa.type_chinese("中文文本")
```

### Q4: 程序崩溃或失控

**解决方案：**
```python
# 紧急停止：将鼠标移到屏幕左上角
# pyautogui.FAILSAFE = True 已启用

# 添加异常处理
try:
    automator.run_full_process(links)
except KeyboardInterrupt:
    print("用户中断")
except Exception as e:
    print(f"错误: {e}")
    rpa.take_screenshot('error.png')
```

## 📊 与价格对比系统集成

### 完整业务流程

```python
import requests
from rpa_controller import ListingSoftwareAutomator

# 1. 从价格对比系统获取低价商品
response = requests.post(
    'http://your-server:5000/api/compare-prices',
    headers={
        'X-Client-ID': 'your-client-id',
        'X-Hardware-ID': 'your-hardware-id'
    },
    json={
        'products': taobao_products,
        'discount_threshold': 0.3
    }
)

# 2. 提取拼多多链接
result = response.json()
if result['success']:
    pdd_links = [
        item['pinduoduo_product']['url'] 
        for item in result['data']
    ]
    
    # 3. 自动铺货
    automator = ListingSoftwareAutomator()
    listing_result = automator.run_full_process(pdd_links)
    
    # 4. 完成！
    print(f"✅ 成功铺货 {len(pdd_links)} 个商品")
```

### 客户端集成示例

```python
# 在 client_app.py 中添加

def auto_listing(self):
    """自动铺货按钮回调"""
    if not self.compare_results:
        messagebox.showwarning("警告", "请先进行价格对比")
        return
    
    # 提取链接
    links = [
        item['pinduoduo_product']['url']
        for item in self.compare_results
    ]
    
    # 执行RPA
    from rpa_controller import ListingSoftwareAutomator
    
    self.status_bar.config(text="正在自动铺货...")
    
    automator = ListingSoftwareAutomator()
    result = automator.run_full_process(links)
    
    if result['success']:
        messagebox.showinfo("成功", 
            f"成功铺货 {result['product_count']} 个商品\n"
            f"结果: {result['result_path']}")
    else:
        messagebox.showerror("失败", f"错误: {result['error']}")
```

## 🎯 实际应用案例

### 案例1：批量铺货到淘宝

```python
# 1. 获取低价商品
low_price_products = get_low_price_products()

# 2. 逐个铺货
for product in low_price_products:
    # 打开淘宝助手
    rpa.click_image('templates/taobao_icon.png')
    time.sleep(2)
    
    # 点击"新增商品"
    rpa.click_image('templates/add_product.png')
    
    # 输入链接
    rpa.type_text(product['link'])
    rpa.press_key('enter')
    
    # 等待导入完成
    rpa.wait_for_image('templates/import_success.png')
    
    # 调整价格（原价的1.2倍）
    new_price = product['price'] * 1.2
    rpa.click_image('templates/price_input.png')
    rpa.type_text(str(new_price))
    
    # 发布
    rpa.click_image('templates/publish_button.png')
    rpa.wait_for_image('templates/publish_success.png')
    
    print(f"✅ 已铺货: {product['title']}")
```

### 案例2：批量修改价格

```python
# 打开Excel表格
os.startfile('products.xlsx')
time.sleep(3)

# 读取每一行
for row in range(2, 100):  # 从第2行开始
    # 选中单元格
    pyautogui.click(100, 50 + row * 20)
    
    # 复制商品ID
    pyautogui.hotkey('ctrl', 'c')
    product_id = pyperclip.paste()
    
    # 打开商品管理软件
    # ... 查找商品
    # ... 修改价格
    # ... 保存
```

### 案例3：自动回复客服消息

```python
while True:
    # 检测新消息
    if rpa.find_image_on_screen('templates/new_message.png'):
        # 点击消息
        rpa.click_image('templates/new_message.png')
        
        # 输入回复
        rpa.type_chinese("您好，请问有什么可以帮您？")
        rpa.press_key('enter')
        
        # 返回列表
        rpa.press_key('esc')
    
    time.sleep(5)
```

## 🔐 安全建议

1. **不要在生产环境硬编码敏感信息**
2. **使用配置文件存储路径和凭据**
3. **添加日志记录所有操作**
4. **定期备份模板图片**
5. **在虚拟机中测试新脚本**

## 📞 技术支持

遇到问题？

1. 查看截图目录 `screenshots/` 了解执行过程
2. 检查模板图片 `templates/` 是否正确
3. 尝试降低图像识别置信度
4. 联系技术支持

---

**现在你完全可以自动化任何Windows桌面软件了！** 🎉

