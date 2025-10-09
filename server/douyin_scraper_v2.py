#!/usr/bin/env python3
"""
抖店商品榜单爬虫 V2
支持前后端验证码交互
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json
import base64
from io import BytesIO
from PIL import Image

class DouyinScraperV2:
    def __init__(self, headless=True):
        """初始化爬虫"""
        self.headless = headless
        self.driver = None
        self.wait = None
        self.login_status = "init"  # init/need_code/logged_in/failed
        self.last_screenshot = None  # 最新截图（Base64）
    
    def init_driver(self):
        """初始化浏览器"""
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.core.os_manager import ChromeType
        
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
        
        # 反爬虫设置
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # 设置Chromium路径
        chrome_options.binary_location = '/usr/bin/chromium-browser'
        
        # 使用 webdriver-manager 自动下载并管理 ChromeDriver
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 20)
    
    def start_login(self, email, password):
        """
        开始登录流程
        @return: (status, message)
                 status: 'need_code' - 需要验证码
                        'success' - 登录成功（不需要验证码）
                        'error' - 出错
        """
        try:
            # 打开登录页面
            self.driver.get('https://fxg.jinritemai.com/login/common')
            time.sleep(3)
            
            # 切换到邮箱登录
            try:
                email_tab = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//span[text()='邮箱登录']"))
                )
                email_tab.click()
                time.sleep(1)
            except:
                # 可能已经在邮箱登录页面
                pass
            
            # 输入邮箱
            email_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='手机号码' or @placeholder='邮箱']"))
            )
            email_input.clear()
            email_input.send_keys(email)
            time.sleep(0.5)
            
            # 输入密码
            pwd_input = self.driver.find_element(By.XPATH, "//input[@type='password']")
            pwd_input.clear()
            pwd_input.send_keys(password)
            time.sleep(0.5)
            
            # 勾选协议
            try:
                checkbox = self.driver.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                if not checkbox.is_selected():
                    # 点击checkbox的父元素（有些页面点checkbox本身无效）
                    self.driver.execute_script("arguments[0].click();", checkbox)
                time.sleep(0.5)
            except:
                pass
            
            # 点击登录按钮
            login_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '登录')]")
            login_btn.click()
            time.sleep(3)
            
            # 检测是否需要验证码
            try:
                # 检查是否有验证码输入框
                code_input = self.driver.find_element(By.XPATH, "//input[@placeholder='验证码' or contains(@placeholder, '验证码')]")
                self.login_status = "need_code"
                return "need_code", "需要输入邮箱验证码"
            except:
                pass
            
            # 检查是否登录成功（URL变化或出现特定元素）
            current_url = self.driver.current_url
            if 'homepage' in current_url or 'mshop' in current_url:
                self.login_status = "logged_in"
                return "success", "登录成功"
            
            # 等待一下看是否跳转
            time.sleep(5)
            current_url = self.driver.current_url
            if 'homepage' in current_url or 'mshop' in current_url:
                self.login_status = "logged_in"
                return "success", "登录成功"
            
            # 再次检查验证码
            try:
                code_input = self.driver.find_element(By.XPATH, "//input[@placeholder='验证码' or contains(@placeholder, '验证码')]")
                self.login_status = "need_code"
                return "need_code", "需要输入邮箱验证码"
            except:
                pass
            
            return "error", "登录状态未知"
        
        except Exception as e:
            self.login_status = "failed"
            return "error", f"登录失败：{str(e)}"
    
    def submit_verification_code(self, code):
        """
        提交验证码
        @param code: 用户输入的验证码
        @return: (success, message)
        """
        try:
            # 找到验证码输入框
            code_input = self.driver.find_element(By.XPATH, "//input[@placeholder='验证码' or contains(@placeholder, '验证码')]")
            code_input.clear()
            code_input.send_keys(code)
            time.sleep(0.5)
            
            # 点击确认/登录按钮
            confirm_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '确认') or contains(text(), '登录')]")
            confirm_btn.click()
            time.sleep(3)
            
            # 检查是否登录成功
            for i in range(10):
                current_url = self.driver.current_url
                if 'homepage' in current_url or 'mshop' in current_url:
                    self.login_status = "logged_in"
                    return True, "登录成功"
                time.sleep(1)
            
            # 检查是否有错误提示
            try:
                error_msg = self.driver.find_element(By.CSS_SELECTOR, ".error-message, .error-tip").text
                return False, f"验证码错误：{error_msg}"
            except:
                return False, "登录超时或验证码错误"
        
        except Exception as e:
            return False, f"提交验证码失败：{str(e)}"
    
    def goto_product_rank(self):
        """
        进入商品榜单页面（逐步点击，更有动感）
        路径：电商罗盘 → 商品 → 商品榜单
        """
        try:
            # 方法1：逐步点击导航（推荐，更真实）
            try:
                # 等待页面加载
                time.sleep(2)
                
                # 点击"电商罗盘"
                compass_btn = self.driver.find_element(By.XPATH, "//span[text()='电商罗盘' or contains(text(), '罗盘')]")
                compass_btn.click()
                time.sleep(1.5)
                
                # 点击"商品"
                product_btn = self.driver.find_element(By.XPATH, "//span[text()='商品' or contains(text(), '商品')]")
                product_btn.click()
                time.sleep(1.5)
                
                # 点击"商品榜单"
                rank_btn = self.driver.find_element(By.XPATH, "//span[text()='商品榜单' or contains(text(), '榜单')]")
                rank_btn.click()
                time.sleep(3)
                
                return True, "成功进入商品榜单（逐步点击）"
            
            except:
                # 方法2：直接URL（备用）
                self.driver.get('https://compass.jinritemai.com/shop/chance/product-rank')
                time.sleep(3)
                return True, "成功进入商品榜单（直接URL）"
        
        except Exception as e:
            return False, f"进入榜单失败：{str(e)}"
    
    def get_all_rank_options(self):
        """
        获取所有可选的榜单选项（用于前端显示）
        @return: dict with keys: rank_types, time_ranges, categories, price_ranges
        """
        options = {
            'rank_types': [],
            'time_ranges': [],
            'categories': [],
            'brand_types': [],
            'price_ranges': []
        }
        
        try:
            # 获取榜单类型
            rank_tabs = self.driver.find_elements(By.CSS_SELECTOR, ".rank-tab, .tab-item")
            options['rank_types'] = [tab.text for tab in rank_tabs if tab.text]
            
            # 获取时间范围
            time_btns = self.driver.find_elements(By.XPATH, "//button[contains(text(), '近') or contains(text(), '天')]")
            options['time_ranges'] = [btn.text for btn in time_btns if btn.text]
            
            # 获取行业类目（点击类目下拉框）
            try:
                category_dropdown = self.driver.find_element(By.XPATH, "//div[contains(text(), '行业类目')]")
                category_dropdown.click()
                time.sleep(1)
                category_items = self.driver.find_elements(By.CSS_SELECTOR, ".category-item, .dropdown-item")
                options['categories'] = [item.text for item in category_items if item.text]
                # 关闭下拉框
                category_dropdown.click()
            except:
                pass
            
            # 获取品牌类型
            brand_btns = self.driver.find_elements(By.XPATH, "//button[contains(text(), '知名品牌') or contains(text(), '新锐品牌') or contains(text(), '自营')]")
            options['brand_types'] = [btn.text for btn in brand_btns if btn.text]
            
            # 获取价格范围
            price_btns = self.driver.find_elements(By.XPATH, "//button[contains(text(), '价格')]")
            options['price_ranges'] = [btn.text for btn in price_btns if btn.text]
            
        except Exception as e:
            print(f"获取选项失败：{str(e)}")
        
        return options
    
    def select_options(self, rank_type=None, time_range=None, category=None, brand_type=None):
        """
        选择榜单选项
        """
        try:
            # 选择榜单类型
            if rank_type:
                rank_tab = self.driver.find_element(By.XPATH, f"//span[text()='{rank_type}']")
                rank_tab.click()
                time.sleep(2)
            
            # 选择时间范围
            if time_range:
                time_btn = self.driver.find_element(By.XPATH, f"//button[text()='{time_range}' or contains(text(), '{time_range}')]")
                time_btn.click()
                time.sleep(2)
            
            # 选择品类类型
            if brand_type:
                brand_btn = self.driver.find_element(By.XPATH, f"//button[text()='{brand_type}']")
                brand_btn.click()
                time.sleep(2)
            
            return True
        except Exception as e:
            print(f"选择选项失败：{str(e)}")
            return False
    
    def get_products(self, limit=50, first_time_only=False):
        """
        获取商品列表
        @param limit: 获取数量
        @param first_time_only: 是否只筛选首次上榜商品
        @return: 商品列表
        """
        products = []
        
        try:
            # 等待商品加载
            time.sleep(3)
            
            # 滚动加载更多商品
            for i in range(5):  # 滚动5次
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            # 提取商品数据（需要根据实际页面结构调整选择器）
            product_items = self.driver.find_elements(By.CSS_SELECTOR, "tr, .product-item, .rank-item")
            
            for idx, item in enumerate(product_items[:limit * 2], 1):  # 多取一些备用
                try:
                    product = {
                        'rank': idx,  # 排名
                        'product_id': '',  # 商品ID
                        'title': '',  # 标题
                        'price': '',  # 价格
                        'sales': '',  # 销量
                        'gmv': '',  # GMV
                        'url': '',  # 链接
                        'image': '',  # 图片
                        'shop_name': '',  # 店铺名称
                        'is_first_time': False,  # 是否首次上榜
                        'growth_rate': '',  # 增长率
                    }
                    
                    # 获取标题
                    try:
                        product['title'] = item.find_element(By.CSS_SELECTOR, "a, .title, .product-name, .goods-name").text
                    except:
                        pass
                    
                    # 获取链接
                    try:
                        product['url'] = item.find_element(By.CSS_SELECTOR, "a").get_attribute('href')
                        # 从URL提取商品ID
                        if 'product' in product['url'] or 'goods' in product['url']:
                            import re
                            match = re.search(r'(\d{10,})', product['url'])
                            if match:
                                product['product_id'] = match.group(1)
                    except:
                        pass
                    
                    # 获取价格
                    try:
                        product['price'] = item.find_element(By.CSS_SELECTOR, ".price, .product-price, .goods-price").text
                    except:
                        pass
                    
                    # 获取销量
                    try:
                        product['sales'] = item.find_element(By.CSS_SELECTOR, ".sales, .sale-count").text
                    except:
                        pass
                    
                    # 获取GMV
                    try:
                        product['gmv'] = item.find_element(By.CSS_SELECTOR, ".gmv, .revenue").text
                    except:
                        pass
                    
                    # 获取图片
                    try:
                        product['image'] = item.find_element(By.CSS_SELECTOR, "img").get_attribute('src')
                    except:
                        pass
                    
                    # 获取店铺名称
                    try:
                        product['shop_name'] = item.find_element(By.CSS_SELECTOR, ".shop, .store, .shop-name").text
                    except:
                        pass
                    
                    # 检查是否首次上榜（通常有"首次上榜"标识）
                    try:
                        first_badge = item.find_elements(By.XPATH, ".//*[contains(text(), '首次') or contains(text(), '新上榜') or contains(@class, 'first') or contains(@class, 'new')]")
                        if first_badge:
                            product['is_first_time'] = True
                    except:
                        pass
                    
                    # 获取增长率
                    try:
                        product['growth_rate'] = item.find_element(By.CSS_SELECTOR, ".growth, .rate, .increase").text
                    except:
                        pass
                    
                    # 如果只要首次上榜，则过滤
                    if first_time_only and not product['is_first_time']:
                        continue
                    
                    # 只添加有标题的
                    if product['title']:
                        products.append(product)
                        
                        # 达到数量限制
                        if len(products) >= limit:
                            break
                
                except:
                    continue
        
        except Exception as e:
            print(f"获取商品失败：{str(e)}")
        
        return products
    
    def take_screenshot(self, max_width=800):
        """
        截取当前页面，返回Base64编码的图片
        @param max_width: 最大宽度（前端显示用）
        @return: Base64字符串
        """
        try:
            # 截取整个页面
            screenshot_png = self.driver.get_screenshot_as_png()
            
            # 用PIL调整尺寸（减小传输数据量）
            img = Image.open(BytesIO(screenshot_png))
            
            # 按比例缩放到max_width
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # 转为Base64
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # 保存最新截图
            self.last_screenshot = img_base64
            
            return img_base64
        
        except Exception as e:
            print(f"截图失败：{str(e)}")
            return None
    
    def get_current_status(self):
        """
        获取当前状态信息（用于前端显示）
        @return: {status, message, screenshot}
        """
        screenshot = self.take_screenshot()
        
        return {
            'status': self.login_status,
            'current_url': self.driver.current_url if self.driver else '',
            'screenshot': screenshot
        }
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()

