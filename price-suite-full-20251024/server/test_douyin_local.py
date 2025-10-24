#!/usr/bin/env python3
"""
抖店爬虫本地测试脚本
可以直观看到浏览器操作过程
"""

from douyin_scraper_v2 import DouyinScraperV2
import time

def main():
    print("=" * 60)
    print("抖店爬虫测试 - 本地测试模式")
    print("=" * 60)
    
    # 非headless模式（可以看到浏览器）
    scraper = DouyinScraperV2(headless=False)
    
    try:
        # 初始化浏览器
        print("\n✅ 初始化浏览器...")
        scraper.init_driver()
        print("✅ 浏览器启动成功！")
        
        # 开始登录
        print("\n🔄 开始登录抖店...")
        print("   邮箱：doudianpuhuo3@163.com")
        print("   密码：Ping99re.com")
        
        status, message = scraper.start_login(
            'doudianpuhuo3@163.com',
            'Ping99re.com'
        )
        
        print(f"\n登录状态：{status}")
        print(f"提示信息：{message}")
        
        # 测试截图功能
        print("\n📸 测试截图功能...")
        screenshot_base64 = scraper.take_screenshot(max_width=800)
        if screenshot_base64:
            print(f"✅ 截图成功！Base64长度：{len(screenshot_base64)} 字符")
            
            # 保存截图到本地（可选）
            import base64
            from PIL import Image
            from io import BytesIO
            
            img_data = base64.b64decode(screenshot_base64)
            img = Image.open(BytesIO(img_data))
            img.save('test_screenshot.png')
            print("✅ 截图已保存：test_screenshot.png")
        else:
            print("❌ 截图失败")
        
        # 如果需要验证码
        if status == 'need_code':
            print("\n📧 需要验证码！")
            print("请去邮箱 doudianpuhuo3@163.com 查看验证码")
            
            code = input("\n请输入验证码：")
            
            if code:
                print("\n🔄 提交验证码...")
                success, msg = scraper.submit_verification_code(code)
                print(f"结果：{msg}")
                
                if success:
                    print("\n✅ 登录成功！")
                    
                    # 再次截图
                    print("\n📸 登录成功后截图...")
                    screenshot_base64 = scraper.take_screenshot()
                    if screenshot_base64:
                        print(f"✅ 截图成功！Base64长度：{len(screenshot_base64)} 字符")
                        
                        img_data = base64.b64decode(screenshot_base64)
                        img = Image.open(BytesIO(img_data))
                        img.save('test_screenshot_logged_in.png')
                        print("✅ 截图已保存：test_screenshot_logged_in.png")
        
        elif status == 'success':
            print("\n✅ 登录成功（无需验证码）！")
        
        # 如果登录成功，测试跳转
        if scraper.login_status == 'logged_in':
            print("\n🔄 测试跳转到商品榜单页面...")
            success, msg = scraper.goto_product_rank()
            print(f"结果：{msg}")
            
            if success:
                # 等待页面加载
                time.sleep(3)
                
                # 截图
                print("\n📸 榜单页面截图...")
                screenshot_base64 = scraper.take_screenshot()
                if screenshot_base64:
                    print(f"✅ 截图成功！Base64长度：{len(screenshot_base64)} 字符")
                    
                    img_data = base64.b64decode(screenshot_base64)
                    img = Image.open(BytesIO(img_data))
                    img.save('test_screenshot_rank_page.png')
                    print("✅ 截图已保存：test_screenshot_rank_page.png")
                
                # 测试获取选项
                print("\n🔄 测试获取榜单选项...")
                options = scraper.get_all_rank_options()
                
                print("\n可用选项：")
                print(f"  榜单类型：{options.get('rank_types', [])}")
                print(f"  时间范围：{options.get('time_ranges', [])}")
                print(f"  行业类目：{options.get('categories', [])}")
                print(f"  品牌类型：{options.get('brand_types', [])}")
                
                if not options['rank_types']:
                    print("\n⚠️  警告：未能获取榜单选项，可能需要调整元素定位！")
        
        print("\n" + "=" * 60)
        print("✅ 测试完成！")
        print("=" * 60)
        print("\n测试结果：")
        print(f"  登录状态：{scraper.login_status}")
        print(f"  当前URL：{scraper.driver.current_url if scraper.driver else 'N/A'}")
        print(f"  截图功能：{'✅ 正常' if screenshot_base64 else '❌ 失败'}")
        
        # 暂停，让用户查看
        input("\n按回车键关闭浏览器...")
    
    except Exception as e:
        print(f"\n❌ 错误：{str(e)}")
        import traceback
        traceback.print_exc()
        
        input("\n按回车键关闭浏览器...")
    
    finally:
        print("\n🔄 关闭浏览器...")
        scraper.close()
        print("✅ 测试结束")

if __name__ == '__main__':
    main()

