#!/usr/bin/env python3
"""
抖店商品榜单爬虫 V2 - 优化版
支持前后端验证码交互
增强稳定性：多重定位策略、重试机制、性能优化
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options
import time
import json
import base64
from io import BytesIO
from PIL import Image
import logging
import os

logger = logging.getLogger(__name__)

# 自定义异常类
class LoginRequiredException(Exception):
    """需要登录"""
    pass

class ElementNotFoundException(Exception):
    """元素未找到"""
    pass

class NetworkException(Exception):
    """网络错误"""
    pass

class DouyinScraperV2:
    def __init__(self, headless=True):
        """初始化爬虫"""
        self.headless = headless
        self.driver = None
        self.wait = None
        self.login_status = "init"  # init/need_code/logged_in/failed
        self.last_screenshot = None  # 最新截图（Base64）
        self.last_activity = time.time()  # 最后活动时间（用于超时清理）
        self.screenshot_dir = "tmp/screenshots"  # 截图保存目录
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    def init_driver(self):
        """初始化浏览器 - 优化版"""
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.core.os_manager import ChromeType
        
        chrome_options = Options()
        
        # 性能优化参数
        prefs = {
            "profile.managed_default_content_settings.images": 2,  # 禁用图片加载
            "profile.default_content_setting_values.notifications": 2,  # 禁用通知
            "profile.default_content_settings.popups": 0,  # 禁用弹窗
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # 无头模式配置（WSL环境必须）
        if self.headless:
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-setuid-sandbox')
            chrome_options.add_argument('--single-process')  # 重要：防止WSL中的多进程问题
            chrome_options.add_argument('--remote-debugging-port=9222')
        
        # 反爬虫设置
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 设置Chromium路径
        chrome_options.binary_location = '/usr/bin/chromium-browser'
        
        try:
            # 使用 webdriver-manager 自动下载并管理 ChromeDriver
            service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.set_page_load_timeout(30)  # 页面加载超时30秒
            self.wait = WebDriverWait(self.driver, 20)
            logger.info("✅ 浏览器初始化成功")
        except Exception as e:
            logger.error(f"❌ 浏览器初始化失败: {e}")
            raise NetworkException(f"浏览器初始化失败: {e}")
    
    def safe_find_element(self, strategies, timeout=10, max_retries=3):
        """
        安全的元素查找，支持多策略和重试
        
        Args:
            strategies: [(By.XXX, "selector"), ...] 定位策略列表
            timeout: 单次尝试超时时间
            max_retries: 最大重试次数
        
        Returns:
            WebElement 或 None
        """
        self.last_activity = time.time()
        
        for attempt in range(max_retries):
            for by, value in strategies:
                try:
                    element = WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((by, value))
                    )
                    logger.debug(f"✅ 成功定位元素: {by}={value}")
                    return element
                except TimeoutException:
                    logger.debug(f"⏱ 定位超时: {by}={value}")
                    continue
                except Exception as e:
                    logger.debug(f"⚠️ 定位异常: {by}={value}, {e}")
                    continue
            
            # 所有策略都失败，等待后重试
            if attempt < max_retries - 1:
                logger.warning(f"🔄 所有策略失败，{2}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                time.sleep(2)
        
        logger.error(f"❌ 所有定位策略均失败（已重试{max_retries}次）")
        return None
    
    def safe_click(self, element, fallback_js=True):
        """
        安全的点击操作
        
        Args:
            element: 要点击的元素
            fallback_js: 失败时是否使用JS点击
        """
        try:
            element.click()
            return True
        except Exception as e:
            logger.warning(f"⚠️ 常规点击失败: {e}")
            if fallback_js:
                try:
                    self.driver.execute_script("arguments[0].click();", element)
                    logger.info("✅ JS点击成功")
                    return True
                except Exception as e2:
                    logger.error(f"❌ JS点击也失败: {e2}")
            return False
    
    def save_screenshot_on_error(self, step_name):
        """失败时保存截图"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"error_{step_name}_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            self.driver.save_screenshot(filepath)
            logger.info(f"📸 错误截图已保存: {filepath}")
            return filepath
        except Exception as e:
            logger.warning(f"⚠️ 保存截图失败: {e}")
            return None
    
    def start_login(self, email, password):
        """
        开始登录流程 - 优化版（多重定位策略）
        """
        try:
            # 1. 打开登录页面
            logger.info("正在打开登录页面...")
            try:
                self.driver.get('https://fxg.jinritemai.com/login/common')
                time.sleep(2)
            except Exception as e:
                self.save_screenshot_on_error("page_load")
                raise NetworkException(f"页面加载失败: {e}")
            
            # 2. 切换到邮箱登录 - 多重策略
            logger.info("正在切换到'邮箱登录'...")
            email_tab_strategies = [
                (By.XPATH, "//*[contains(text(),'邮箱登录') or contains(text(),'邮箱')][not(contains(text(),'手机'))]"),
                (By.XPATH, "//a[contains(text(),'邮箱登录')]"),
                (By.CSS_SELECTOR, ".semi-tabs-tab:nth-child(2)"),
                (By.XPATH, "//div[contains(@class, 'tab')]//span[contains(text(), '邮箱')]"),
            ]
            email_tab = self.safe_find_element(email_tab_strategies, timeout=5, max_retries=2)
            if email_tab:
                self.safe_click(email_tab)
                logger.info("✅ 已切换到邮箱登录")
                time.sleep(1.2)
            else:
                logger.warning("⚠️ 未找到邮箱登录标签，假设已在邮箱登录模式")
            
            # 3. 输入邮箱 - 多重策略
            logger.info("正在输入邮箱...")
            email_input_strategies = [
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input[type='text']"),
                (By.XPATH, "//input[contains(@placeholder, '邮箱')]"),
                (By.XPATH, "//input[contains(@placeholder, '手机')]"),
                (By.CSS_SELECTOR, "input.semi-input"),
                (By.TAG_NAME, "input"),  # 兜底：第一个input
            ]
            email_input = self.safe_find_element(email_input_strategies, timeout=10, max_retries=2)
            if not email_input:
                self.save_screenshot_on_error("email_input_not_found")
                raise ElementNotFoundException("未找到邮箱输入框")
            
            email_input.clear()
            time.sleep(0.3)
            email_input.send_keys(email)
            logger.info("✅ 邮箱输入完成")
            time.sleep(0.8)
            
            # 4. 输入密码 - 多重策略
            logger.info("正在输入密码...")
            pwd_input_strategies = [
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.XPATH, "//input[contains(@placeholder, '密码')]"),
            ]
            pwd_input = self.safe_find_element(pwd_input_strategies, timeout=10, max_retries=2)
            if not pwd_input:
                # 兜底：获取所有input，选第二个
                try:
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    pwd_input = inputs[1] if len(inputs) > 1 else None
                except:
                    pwd_input = None
            
            if not pwd_input:
                self.save_screenshot_on_error("password_input_not_found")
                raise ElementNotFoundException("未找到密码输入框")
            
            pwd_input.clear()
            time.sleep(0.3)
            pwd_input.send_keys(password)
            logger.info("✅ 密码输入完成")
            time.sleep(0.8)
            
            # 5. 勾选协议 - 多重策略
            logger.info("正在勾选用户协议...")
            agreement_strategies = [
                (By.XPATH, "//*[@data-icon='check-square-filled']"),
                (By.XPATH, "//input[@type='checkbox']"),
                (By.CSS_SELECTOR, ".checkbox, .agreement-checkbox"),
            ]
            agreement_box = self.safe_find_element(agreement_strategies, timeout=5, max_retries=1)
            if agreement_box:
                self.safe_click(agreement_box)
                logger.info("✅ 已勾选协议")
            else:
                logger.warning("⚠️ 未找到协议勾选框（可能已勾选）")
            
            # 6. 点击登录按钮 - 多重策略
            logger.info("正在点击登录按钮...")
            login_btn_strategies = [
                (By.XPATH, "//button[contains(text(), '登录')]"),
                (By.XPATH, "//button[contains(text(), '立即登录')]"),
                (By.CSS_SELECTOR, "button.login-button"),
                (By.CSS_SELECTOR, "button[type='submit']"),
            ]
            login_btn = self.safe_find_element(login_btn_strategies, timeout=10, max_retries=2)
            if not login_btn:
                self.save_screenshot_on_error("login_button_not_found")
                raise ElementNotFoundException("未找到登录按钮")
            
            self.safe_click(login_btn)
            logger.info("✅ 已点击登录按钮")
            time.sleep(3)
            
            # 7. 判断登录结果
            time.sleep(3)
            current_url = self.driver.current_url
            logger.info(f"当前URL: {current_url}")
            
            # 检查验证码
            if 'captcha' in current_url or self.driver.find_elements(By.ID, "captcha-wait-img"):
                self.login_status = "need_code"
                logger.info("📧 需要验证码")
                return "need_code", "需要输入验证码"
            
            # 检查是否登录成功
            if 'homepage' in current_url or 'mshop' in current_url:
                self.login_status = "logged_in"
                logger.info("🎉 登录成功！")
                return "success", "登录成功"
            
            # 检查错误提示
            error_strategies = [
                (By.CSS_SELECTOR, ".error-message"),
                (By.CSS_SELECTOR, ".Toastify__toast-body"),
                (By.XPATH, "//*[contains(@class, 'error')]"),
            ]
            for by, value in error_strategies:
                try:
                    error_elements = self.driver.find_elements(by, value)
                    if error_elements:
                        error_text = error_elements[0].text
                        logger.error(f"❌ 登录失败: {error_text}")
                        self.login_status = "failed"
                        self.save_screenshot_on_error("login_error")
                        return "error", error_text
                except:
                    continue
            
            # 未知状态
            logger.error("❌ 登录状态未知")
            self.save_screenshot_on_error("login_unknown")
            self.login_status = "failed"
            return "error", "登录失败，状态未知"
        
        except ElementNotFoundException as e:
            logger.error(f"❌ 元素定位失败: {e}")
            self.login_status = "failed"
            return "error", f"页面元素定位失败，可能页面已更新: {e}"
        except NetworkException as e:
            logger.error(f"❌ 网络错误: {e}")
            self.login_status = "failed"
            return "error", f"网络连接失败: {e}"
        except Exception as e:
            logger.error(f"❌ 登录异常: {e}", exc_info=True)
            self.save_screenshot_on_error("login_exception")
            self.login_status = "failed"
            return "error", f"登录失败: {e}"
    
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

