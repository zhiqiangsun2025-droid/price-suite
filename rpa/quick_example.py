#!/usr/bin/env python3
"""
快速开始示例 - 5分钟上手 RPA
"""

import pyautogui
import time

print("""
╔═══════════════════════════════════════════════════════════╗
║   🤖 Windows 桌面自动化 - 快速示例                      ║
╚═══════════════════════════════════════════════════════════╝

这个脚本将演示如何：
1. 自动打开记事本
2. 自动输入文字
3. 自动保存文件

5秒后开始...（将鼠标移到左上角可紧急停止）
""")

time.sleep(5)

# ==================== 示例1：打开记事本 ====================

print("\n[1/5] 打开记事本...")

# 方法1：使用 Win + R 运行
pyautogui.hotkey('win', 'r')  # 打开"运行"对话框
time.sleep(0.5)

pyautogui.typewrite('notepad', interval=0.1)  # 输入 notepad
pyautogui.press('enter')  # 回车
time.sleep(1)

print("✅ 记事本已打开")

# ==================== 示例2：输入文字 ====================

print("\n[2/5] 输入文字...")

# 英文（直接输入）
pyautogui.typewrite('Hello, this is RPA automation!', interval=0.05)
pyautogui.press('enter')
pyautogui.press('enter')

# 中文（使用粘贴）
import pyperclip

chinese_text = """
这是一个自动化测试！

功能展示：
1. 自动打开应用程序
2. 自动输入文字（中英文）
3. 自动保存文件
4. 自动关闭程序

生成时间：""" + time.strftime('%Y-%m-%d %H:%M:%S')

pyperclip.copy(chinese_text)
pyautogui.hotkey('ctrl', 'v')

print("✅ 文字已输入")

# ==================== 示例3：截图 ====================

print("\n[3/5] 截图保存...")

screenshot = pyautogui.screenshot()
screenshot.save('notepad_screenshot.png')

print("✅ 截图已保存: notepad_screenshot.png")

# ==================== 示例4：保存文件 ====================

print("\n[4/5] 保存文件...")

# Ctrl + S 保存
pyautogui.hotkey('ctrl', 's')
time.sleep(0.5)

# 输入文件名
filename = 'rpa_test_' + time.strftime('%Y%m%d_%H%M%S') + '.txt'
pyautogui.typewrite(filename, interval=0.05)
time.sleep(0.3)

# 回车保存
pyautogui.press('enter')
time.sleep(0.5)

print(f"✅ 文件已保存: {filename}")

# ==================== 示例5：关闭记事本 ====================

print("\n[5/5] 关闭记事本...")

# Alt + F4 关闭
pyautogui.hotkey('alt', 'F4')
time.sleep(0.3)

print("✅ 记事本已关闭")

# ==================== 完成 ====================

print("""
╔═══════════════════════════════════════════════════════════╗
║   ✅ 自动化演示完成！                                    ║
╚═══════════════════════════════════════════════════════════╝

你已经学会了基础的RPA操作：
✅ 打开程序
✅ 输入文字（英文和中文）
✅ 截图
✅ 保存文件
✅ 关闭程序

下一步：
1. 查看 rpa_controller.py 了解完整功能
2. 查看 README_RPA.md 了解详细文档
3. 开始自动化你的铺货软件！

""")

# ==================== 进阶示例：图像识别 ====================

print("=" * 60)
print("🎓 进阶功能演示")
print("=" * 60)

demo_choice = input("\n是否演示图像识别功能？(y/n): ")

if demo_choice.lower() == 'y':
    print("\n准备中...")
    print("即将演示如何查找屏幕上的图标...")
    
    time.sleep(2)
    
    # 截取桌面
    print("\n1. 截取当前桌面...")
    desktop = pyautogui.screenshot()
    desktop.save('desktop.png')
    
    # 获取屏幕尺寸
    screen_width, screen_height = pyautogui.size()
    print(f"   屏幕分辨率: {screen_width} x {screen_height}")
    
    # 鼠标当前位置
    x, y = pyautogui.position()
    print(f"   鼠标位置: ({x}, {y})")
    
    # 获取鼠标位置的颜色
    pixel_color = pyautogui.pixel(x, y)
    print(f"   鼠标处颜色: RGB{pixel_color}")
    
    print("\n💡 提示：")
    print("   - 移动鼠标可以获取任意位置坐标")
    print("   - 使用 pyautogui.click(x, y) 点击指定位置")
    print("   - 使用图像模板可以智能识别按钮位置")

print("\n" + "=" * 60)
print("👨‍💻 实战练习建议")
print("=" * 60)
print("""
1. 练习1：自动打开浏览器并访问网站
   pyautogui.hotkey('win', 'r')
   pyautogui.typewrite('chrome https://www.baidu.com')
   pyautogui.press('enter')

2. 练习2：自动复制粘贴
   pyautogui.hotkey('ctrl', 'c')  # 复制
   pyautogui.hotkey('ctrl', 'v')  # 粘贴

3. 练习3：创建你的第一个铺货自动化
   - 手动打开铺货软件
   - 记录每个步骤的坐标
   - 编写自动化脚本

开始吧！🚀
""")

