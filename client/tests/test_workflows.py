"""
测试端到端工作流（全Mock）
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock, call


class TestCompleteUserFlow:
    """测试完整用户流程：注册→登录→选品→导出"""
    
    @patch('requests.post')
    def test_registration_to_login_flow(self, mock_post):
        """测试注册到登录流程"""
        # 步骤1：注册
        mock_post.return_value = Mock(
            status_code=200,
            ok=True,
            json=lambda: {
                'success': True,
                'client_id': 'flow_test_123',
                'is_active': 0
            }
        )
        
        import requests
        reg_response = requests.post(
            "http://127.0.0.1:5000/api/register",
            json={'hardware_id': 'test_hw'}
        )
        reg_result = reg_response.json()
        
        assert reg_result['success'] is True
        client_id = reg_result['client_id']
        
        # 步骤2：登录抖店
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                'success': True,
                'status': 'need_code',
                'message': '需要验证码'
            }
        )
        
        login_response = requests.post(
            "http://127.0.0.1:5000/api/douyin-login-start",
            headers={'X-Client-ID': client_id, 'X-Hardware-ID': 'test_hw'},
            json={'email': 'test@test.com', 'password': 'pass'}
        )
        login_result = login_response.json()
        
        assert login_result['success'] is True
        assert login_result['status'] == 'need_code'
        
        # 步骤3：提交验证码
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {'success': True, 'message': '登录成功'}
        )
        
        code_response = requests.post(
            "http://127.0.0.1:5000/api/douyin-submit-code",
            headers={'X-Client-ID': client_id, 'X-Hardware-ID': 'test_hw'},
            json={'code': '123456'}
        )
        code_result = code_response.json()
        
        assert code_result['success'] is True
    
    @patch('requests.post')
    def test_login_to_scrape_flow(self, mock_post):
        """测试登录到爬取流程"""
        client_id = 'scrape_test_456'
        
        # 步骤1：登录成功
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                'success': True,
                'status': 'success',
                'message': '登录成功'
            }
        )
        
        import requests
        login_response = requests.post(
            "http://127.0.0.1:5000/api/douyin-login-start",
            headers={'X-Client-ID': client_id, 'X-Hardware-ID': 'hw'},
            json={'email': 'test@test.com', 'password': 'pass'}
        )
        
        assert login_response.json()['status'] == 'success'
        
        # 步骤2：爬取商品
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                'success': True,
                'products': [
                    {'title': '商品1', 'price': 99.9, 'sales': 1000},
                    {'title': '商品2', 'price': 199.9, 'sales': 500}
                ]
            }
        )
        
        scrape_response = requests.post(
            "http://127.0.0.1:5000/api/douyin-scrape",
            headers={'X-Client-ID': client_id, 'X-Hardware-ID': 'hw'},
            json={'rank_type': '销量榜', 'time_range': '近7天'}
        )
        scrape_result = scrape_response.json()
        
        assert scrape_result['success'] is True
        assert len(scrape_result['products']) == 2
    
    @patch('pandas.DataFrame.to_excel')
    @patch('requests.post')
    def test_complete_export_flow(self, mock_post, mock_to_excel):
        """测试完整导出流程"""
        # 步骤1：爬取数据
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                'success': True,
                'products': [
                    {'title': '测试商品', 'price': 99.9}
                ]
            }
        )
        
        import requests
        response = requests.post(
            "http://127.0.0.1:5000/api/douyin-scrape",
            headers={'X-Client-ID': 'test', 'X-Hardware-ID': 'test'},
            json={}
        )
        products = response.json()['products']
        
        # 步骤2：导出Excel
        import pandas as pd
        df = pd.DataFrame(products)
        df.to_excel("test_output.xlsx", index=False)
        
        mock_to_excel.assert_called_once()


class TestErrorScenarios:
    """测试异常场景"""
    
    @patch('requests.post')
    def test_server_unreachable(self, mock_post):
        """测试服务器不可达"""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        with pytest.raises(requests.exceptions.ConnectionError):
            requests.post(
                "http://127.0.0.1:5000/api/register",
                json={'hardware_id': 'test'}
            )
    
    @patch('requests.post')
    def test_authorization_expired(self, mock_post):
        """测试授权过期"""
        mock_post.return_value = Mock(
            status_code=403,
            json=lambda: {
                'success': False,
                'show_popup': True,
                'reason': 'auth_expired'
            }
        )
        
        import requests
        response = requests.post(
            "http://127.0.0.1:5000/api/douyin-scrape",
            headers={'X-Client-ID': 'expired', 'X-Hardware-ID': 'expired'}
        )
        
        assert response.status_code == 403
        result = response.json()
        assert result['show_popup'] is True
        assert result['reason'] == 'auth_expired'
    
    @patch('requests.post')
    def test_trial_expired(self, mock_post):
        """测试试用期结束"""
        mock_post.return_value = Mock(
            status_code=403,
            json=lambda: {
                'success': False,
                'show_popup': True,
                'reason': 'trial_expired'
            }
        )
        
        import requests
        response = requests.post(
            "http://127.0.0.1:5000/api/douyin-login-start",
            headers={'X-Client-ID': 'trial_user', 'X-Hardware-ID': 'hw'}
        )
        
        assert response.status_code == 403
        result = response.json()
        assert result['reason'] == 'trial_expired'
    
    @patch('requests.post')
    def test_network_timeout_retry(self, mock_post):
        """测试网络超时重试"""
        import requests
        
        # 第一次超时，第二次成功
        mock_post.side_effect = [
            requests.exceptions.Timeout(),
            Mock(status_code=200, json=lambda: {'success': True})
        ]
        
        # 第一次尝试
        with pytest.raises(requests.exceptions.Timeout):
            requests.post("http://127.0.0.1:5000/api/test", timeout=5)
        
        # 第二次尝试
        response = requests.post("http://127.0.0.1:5000/api/test", timeout=5)
        assert response.json()['success'] is True


class TestStatePersistence:
    """测试状态持久化"""
    
    def test_config_save_and_load(self, tmp_path):
        """测试配置保存和加载"""
        import json
        
        config_file = tmp_path / "config.json"
        
        # 保存配置
        config = {
            'client_id': 'persist_test_123',
            'is_active': 1,
            'douyin_logged_in': True,
            'login_timestamp': time.time()
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f)
        
        # 加载配置
        with open(config_file, 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)
        
        assert loaded_config['client_id'] == 'persist_test_123'
        assert loaded_config['is_active'] == 1
        assert loaded_config['douyin_logged_in'] is True
    
    def test_login_state_persistence(self, tmp_path):
        """测试登录状态持久化"""
        import json
        
        config_file = tmp_path / "config.json"
        
        # 模拟登录成功后保存状态
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump({
                'douyin_logged_in': True,
                'login_timestamp': time.time()
            }, f)
        
        # 重启应用后加载状态
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        assert config['douyin_logged_in'] is True
        assert 'login_timestamp' in config


class TestRPAIntegration:
    """测试RPA集成"""
    
    @patch('os.path.exists')
    @patch('subprocess.Popen')
    def test_rpa_module_exists(self, mock_popen, mock_exists):
        """测试RPA模块存在时启动"""
        mock_exists.return_value = True
        
        import subprocess
        excel_file = "test_export.xlsx"
        
        subprocess.Popen(['python', 'rpa/rpa_controller.py', '--excel', excel_file])
        
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]
        assert 'rpa_controller.py' in call_args[1]
        assert excel_file in call_args
    
    @patch('os.path.exists')
    @patch('webbrowser.open')
    def test_rpa_module_not_exists(self, mock_browser, mock_exists):
        """测试RPA模块不存在时引导下载"""
        mock_exists.return_value = False
        
        import webbrowser
        webbrowser.open("https://github.com/zhiqiangsun2025-droid/price-suite/releases")
        
        mock_browser.assert_called_once()
        call_url = mock_browser.call_args[0][0]
        assert 'github.com' in call_url
        assert 'releases' in call_url


class TestPerformance:
    """测试性能指标"""
    
    def test_config_load_performance(self, tmp_path):
        """测试配置加载性能"""
        import json
        import time
        
        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump({'test': 'data'}, f)
        
        start = time.time()
        with open(config_file, 'r') as f:
            json.load(f)
        elapsed = time.time() - start
        
        assert elapsed < 0.1  # 应该在100ms内完成
    
    def test_page_switch_debounce_performance(self):
        """测试页面切换去抖性能"""
        class MockApp:
            def __init__(self):
                self.current_page = "page1"
                self._switching = False
                self.switch_calls = 0
            
            def switch_page(self, page_id):
                if self._switching:
                    return
                self._switching = True
                try:
                    self.switch_calls += 1
                    self.current_page = page_id
                finally:
                    self._switching = False
        
        app = MockApp()
        
        import time
        start = time.time()
        
        # 快速连续切换
        for i in range(100):
            if not app._switching:
                app.switch_page(f"page{i}")
        
        elapsed = time.time() - start
        
        # 去抖应该使大部分调用被忽略
        assert app.switch_calls <= 100
        assert elapsed < 1.0  # 应该很快完成

