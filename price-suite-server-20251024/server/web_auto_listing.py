#!/usr/bin/env python3
"""
网页自动上货模块
使用Selenium操作网页版上货系统
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import logging

logger = logging.getLogger(__name__)

class WebAutoListing:
    """网页自动上货类"""
    
    def __init__(self, headless=False):
        """初始化
        
        Args:
            headless: 是否无头模式（不显示浏览器窗口）
        """
        self.driver = None
        self.headless = headless
        self.is_logged_in = False
    
    def start_browser(self):
        """启动浏览器"""
        try:
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            
            # 常用选项
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            # 反检测
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
            })
            
            logger.info("浏览器启动成功")
            return True
        except Exception as e:
            logger.error(f"启动浏览器失败: {e}")
            return False
    
    def login(self, url, username, password):
        """登录上货系统
        
        Args:
            url: 登录页面URL
            username: 用户名
            password: 密码
        
        Returns:
            bool: 是否登录成功
        """
        try:
            self.driver.get(url)
            time.sleep(2)
            
            # 查找并填写用户名（多种可能的选择器）
            username_selectors = [
                (By.ID, 'username'),
                (By.NAME, 'username'),
                (By.XPATH, '//input[@type="text"]'),
                (By.CSS_SELECTOR, 'input[placeholder*="用户名"]'),
                (By.CSS_SELECTOR, 'input[placeholder*="账号"]')
            ]
            
            for by, selector in username_selectors:
                try:
                    elem = self.driver.find_element(by, selector)
                    elem.clear()
                    elem.send_keys(username)
                    logger.info(f"用户名已填写，选择器: {selector}")
                    break
                except:
                    continue
            
            # 查找并填写密码
            password_selectors = [
                (By.ID, 'password'),
                (By.NAME, 'password'),
                (By.XPATH, '//input[@type="password"]'),
            ]
            
            for by, selector in password_selectors:
                try:
                    elem = self.driver.find_element(by, selector)
                    elem.clear()
                    elem.send_keys(password)
                    logger.info(f"密码已填写，选择器: {selector}")
                    break
                except:
                    continue
            
            # 点击登录按钮
            login_selectors = [
                (By.XPATH, '//button[contains(text(), "登录")]'),
                (By.XPATH, '//input[@type="submit"]'),
                (By.CSS_SELECTOR, 'button.login-btn'),
                (By.ID, 'login-button')
            ]
            
            for by, selector in login_selectors:
                try:
                    elem = self.driver.find_element(by, selector)
                    elem.click()
                    logger.info(f"点击登录按钮，选择器: {selector}")
                    break
                except:
                    continue
            
            # 等待登录完成
            time.sleep(3)
            
            # 检查是否登录成功（通过URL变化或特定元素）
            if '登录' not in self.driver.title:
                self.is_logged_in = True
                logger.info("登录成功")
                return True
            else:
                logger.warning("登录可能失败")
                return False
                
        except Exception as e:
            logger.error(f"登录失败: {e}")
            return False
    
    def upload_product(self, product_data):
        """上传单个商品
        
        Args:
            product_data: 商品数据字典 {'名称': '', '价格': '', '链接': '', ...}
        
        Returns:
            bool: 是否上传成功
        """
        try:
            # 找到【添加商品】按钮
            add_btn_selectors = [
                (By.XPATH, '//button[contains(text(), "添加商品")]'),
                (By.XPATH, '//a[contains(text(), "添加商品")]'),
                (By.CSS_SELECTOR, 'button.add-product'),
            ]
            
            for by, selector in add_btn_selectors:
                try:
                    elem = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    elem.click()
                    logger.info("点击添加商品按钮")
                    break
                except:
                    continue
            
            time.sleep(1)
            
            # 填写商品信息
            # 商品名称
            try:
                title_elem = self.driver.find_element(By.NAME, 'title')
                title_elem.clear()
                title_elem.send_keys(product_data.get('商品名称', ''))
            except:
                pass
            
            # 商品价格
            try:
                price_elem = self.driver.find_element(By.NAME, 'price')
                price_elem.clear()
                price_elem.send_keys(str(product_data.get('价格', '')))
            except:
                pass
            
            # 商品链接（如果有）
            try:
                url_elem = self.driver.find_element(By.NAME, 'source_url')
                url_elem.clear()
                url_elem.send_keys(product_data.get('商品链接', ''))
            except:
                pass
            
            # 点击提交/发布
            submit_selectors = [
                (By.XPATH, '//button[contains(text(), "提交")]'),
                (By.XPATH, '//button[contains(text(), "发布")]'),
                (By.XPATH, '//button[contains(text(), "保存")]'),
                (By.CSS_SELECTOR, 'button[type="submit"]'),
            ]
            
            for by, selector in submit_selectors:
                try:
                    elem = self.driver.find_element(by, selector)
                    elem.click()
                    logger.info("点击提交按钮")
                    break
                except:
                    continue
            
            time.sleep(2)
            return True
            
        except Exception as e:
            logger.error(f"上传商品失败: {e}")
            return False
    
    def batch_upload(self, excel_file, column_mapping=None):
        """批量上货
        
        Args:
            excel_file: Excel文件路径
            column_mapping: 列名映射 {'Excel列名': '网页字段名'}
        
        Returns:
            dict: {'success': int, 'failed': int, 'total': int}
        """
        try:
            # 读取Excel
            df = pd.read_excel(excel_file)
            total = len(df)
            success_count = 0
            failed_count = 0
            
            logger.info(f"开始批量上货，共 {total} 个商品")
            
            # 循环上货
            for index, row in df.iterrows():
                product_data = row.to_dict()
                
                logger.info(f"上货进度: {index+1}/{total} - {product_data.get('商品名称', '')}")
                
                if self.upload_product(product_data):
                    success_count += 1
                else:
                    failed_count += 1
                
                # 短暂延迟，避免过快
                time.sleep(1)
            
            result = {
                'success': success_count,
                'failed': failed_count,
                'total': total
            }
            
            logger.info(f"批量上货完成: 成功{success_count}, 失败{failed_count}, 总计{total}")
            return result
            
        except Exception as e:
            logger.error(f"批量上货失败: {e}")
            return {'success': 0, 'failed': 0, 'total': 0, 'error': str(e)}
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            logger.info("浏览器已关闭")


# ==================== 使用示例 ====================

if __name__ == '__main__':
    # 创建自动上货实例
    auto_listing = WebAutoListing(headless=False)  # headless=True时不显示浏览器
    
    # 启动浏览器
    if auto_listing.start_browser():
        # 登录上货系统
        if auto_listing.login(
            url='http://上货系统网址/login',
            username='你的账号',
            password='你的密码'
        ):
            # 批量上货
            result = auto_listing.batch_upload('选品结果.xlsx')
            print(f"上货完成：成功{result['success']}个，失败{result['failed']}个")
        
        # 关闭浏览器
        auto_listing.close()

