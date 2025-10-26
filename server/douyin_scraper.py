#!/usr/bin/env python3
"""
抖店商品榜单爬虫
功能：
1. 自动登录抖店
2. 抓取商品榜单数据
3. 支持多种榜单类型
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json

# 榜单类型映射
RANK_TYPES = {
    "search": "搜索榜",
    "live": "直播榜",
    "product_card": "商品卡榜",
    "talent": "达人带货榜",
    "video": "短视频榜",
    "realtime": "实时爆品挖掘榜"
}

# 时间范围映射
TIME_RANGES = {
    "1day": "近1天",
    "7days": "近7天",
    "30days": "近30天"
}

class DouyinScraper:
    def __init__(self, headless=True):
        """初始化爬虫"""
        self.headless = headless
        self.driver = None
        self.wait = None
    
    def init_driver(self):
        """初始化浏览器"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
        
        # 反爬虫设置
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User-Agent
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 20)
    
    def login(self, email, password):
        """
        登录抖店
        @param email: 邮箱
        @param password: 密码
        @return: (success, message)
        """
        try:
            # 打开登录页面
            self.driver.get('https://fxg.jinritemai.com/login/common')
            time.sleep(3)
            
            # 切换到邮箱登录
            email_tab = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '邮箱登录')]"))
            )
            email_tab.click()
            time.sleep(1)
            
            # 输入邮箱
            email_input = self.driver.find_element(By.XPATH, "//input[@placeholder='手机号码']")
            email_input.clear()
            email_input.send_keys(email)
            time.sleep(0.5)
            
            # 勾选协议
            checkbox = self.driver.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
            if not checkbox.is_selected():
                checkbox.click()
            time.sleep(0.5)
            
            # 点击发送验证码
            send_code_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '发送验证码')]")
            send_code_btn.click()
            
            # 等待用户手动输入验证码并登录
            # TODO: 这里需要手动处理验证码，或者集成打码平台
            print("请在浏览器中输入验证码并完成登录...")
            
            # 等待登录成功（检测URL变化）
            for i in range(60):  # 最多等待60秒
                current_url = self.driver.current_url
                if 'homepage' in current_url or 'mshop' in current_url:
                    print("登录成功！")
                    return True, "登录成功"
                time.sleep(1)
            
            return False, "登录超时"
        
        except Exception as e:
            return False, f"登录失败：{str(e)}"
    
    def goto_product_rank(self):
        """
        进入商品榜单页面
        @return: (success, message)
        """
        try:
            # 访问电商罗盘
            self.driver.get('https://fxg.jinritemai.com/ffa/mshop/homepage/index')
            time.sleep(2)
            
            # 点击"商品"菜单
            product_menu = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '商品')]"))
            )
            product_menu.click()
            time.sleep(1)
            
            # 点击"商品榜单"
            rank_menu = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '商品榜单')]"))
            )
            rank_menu.click()
            time.sleep(2)
            
            return True, "成功进入商品榜单"
        
        except Exception as e:
            return False, f"进入榜单失败：{str(e)}"
    
    def get_rank_products(self, rank_type="search", time_range="1day", category=None, limit=50):
        """
        获取榜单商品
        @param rank_type: 榜单类型（search/live/product_card等）
        @param time_range: 时间范围（1day/7days/30days）
        @param category: 品类（可选）
        @param limit: 获取数量
        @return: 商品列表
        """
        products = []
        
        try:
            # 切换榜单类型
            rank_tab = self.driver.find_element(By.XPATH, f"//span[contains(text(), '{RANK_TYPES[rank_type]}')]")
            rank_tab.click()
            time.sleep(2)
            
            # 切换时间范围
            if time_range:
                time_btn = self.driver.find_element(By.XPATH, f"//span[contains(text(), '{TIME_RANGES[time_range]}')]")
                time_btn.click()
                time.sleep(2)
            
            # TODO: 选择品类（如果有）
            
            # 解析商品数据
            # 这里需要根据实际页面结构来定位商品列表
            product_items = self.driver.find_elements(By.CSS_SELECTOR, ".product-item")  # 示例选择器
            
            for item in product_items[:limit]:
                try:
                    product = {
                        'title': item.find_element(By.CSS_SELECTOR, '.title').text,
                        'price': item.find_element(By.CSS_SELECTOR, '.price').text,
                        'sales': item.find_element(By.CSS_SELECTOR, '.sales').text,
                        'image': item.find_element(By.CSS_SELECTOR, 'img').get_attribute('src'),
                        'url': item.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                    }
                    products.append(product)
                except:
                    continue
            
            return products
        
        except Exception as e:
            print(f"获取榜单失败：{str(e)}")
            return []
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()

# 测试函数
if __name__ == "__main__":
    scraper = DouyinScraper(headless=False)  # 先不用无头模式，方便调试
    
    try:
        scraper.init_driver()
        
        # 登录
        success, msg = scraper.login('doudianpuhuo3@163.com', 'Ping99re.com')
        print(msg)
        
        if success:
            # 进入商品榜单
            success, msg = scraper.goto_product_rank()
            print(msg)
            
            if success:
                # 获取搜索榜商品
                products = scraper.get_rank_products(rank_type="search", time_range="1day", limit=10)
                print(f"获取到 {len(products)} 个商品")
                for p in products:
                    print(p)
    
    finally:
        input("按Enter关闭浏览器...")
        scraper.close()

