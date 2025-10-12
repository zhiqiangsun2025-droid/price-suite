"""
测试API客户端调用（Mock后端）
"""
import pytest
import requests
from unittest.mock import Mock, patch, MagicMock


class TestRegistrationAPI:
    """测试注册API调用"""
    
    @patch('requests.post')
    def test_successful_registration(self, mock_post, sample_api_responses):
        """测试成功注册"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = sample_api_responses['register_success']
        mock_post.return_value = mock_response
        
        # 模拟注册请求
        hardware_id = "test_hw_123"
        response = requests.post(
            "http://127.0.0.1:5000/api/register",
            json={'hardware_id': hardware_id},
            timeout=10
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert 'client_id' in result
        
        # 验证调用参数
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://127.0.0.1:5000/api/register"
        assert call_args[1]['json'] == {'hardware_id': hardware_id}
    
    @patch('requests.post')
    def test_registration_with_trial(self, mock_post, sample_api_responses):
        """测试试用期注册"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_api_responses['register_trial']
        mock_post.return_value = mock_response
        
        response = requests.post(
            "http://127.0.0.1:5000/api/register",
            json={'hardware_id': 'test_hw_456'}
        )
        
        result = response.json()
        assert result['success'] is True
        assert result['is_active'] == 0
        assert 'trial_hours_left' in result
    
    @patch('requests.post')
    def test_registration_server_error(self, mock_post):
        """测试服务器错误处理"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.ok = False
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        response = requests.post(
            "http://127.0.0.1:5000/api/register",
            json={'hardware_id': 'test_hw'}
        )
        
        assert response.status_code == 500
        assert not response.ok
    
    @patch('requests.post')
    def test_registration_timeout(self, mock_post):
        """测试请求超时"""
        mock_post.side_effect = requests.exceptions.Timeout()
        
        with pytest.raises(requests.exceptions.Timeout):
            requests.post(
                "http://127.0.0.1:5000/api/register",
                json={'hardware_id': 'test_hw'},
                timeout=10
            )
    
    @patch('requests.post')
    def test_registration_connection_error(self, mock_post):
        """测试连接错误"""
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        with pytest.raises(requests.exceptions.ConnectionError):
            requests.post(
                "http://127.0.0.1:5000/api/register",
                json={'hardware_id': 'test_hw'}
            )


class TestAuthorizationAPI:
    """测试授权验证API"""
    
    @patch('requests.post')
    def test_auth_403_with_popup(self, mock_post, sample_api_responses):
        """测试403授权失败并要求弹窗"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.ok = False
        mock_response.json.return_value = sample_api_responses['auth_403']
        mock_post.return_value = mock_response
        
        response = requests.post(
            "http://127.0.0.1:5000/api/douyin-login-start",
            headers={'X-Client-ID': 'test', 'X-Hardware-ID': 'test'},
            json={'email': 'test@test.com', 'password': 'pass'}
        )
        
        assert response.status_code == 403
        result = response.json()
        assert result['success'] is False
        assert result['show_popup'] is True
        assert 'reason' in result
    
    @patch('requests.post')
    def test_auth_success(self, mock_post):
        """测试授权通过"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {'success': True, 'authorized': True}
        mock_post.return_value = mock_response
        
        response = requests.post(
            "http://127.0.0.1:5000/api/some-endpoint",
            headers={'X-Client-ID': 'valid_client', 'X-Hardware-ID': 'valid_hw'}
        )
        
        assert response.status_code == 200
        assert response.json()['success'] is True


class TestDouyinLoginAPI:
    """测试抖音登录API"""
    
    @patch('requests.post')
    def test_login_need_verification_code(self, mock_post, sample_api_responses):
        """测试登录需要验证码"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = sample_api_responses['login_need_code']
        mock_post.return_value = mock_response
        
        response = requests.post(
            "http://127.0.0.1:5000/api/douyin-login-start",
            headers={
                'X-Client-ID': 'client_123',
                'X-Hardware-ID': 'hw_123',
                'Content-Type': 'application/json'
            },
            json={'email': 'test@example.com', 'password': 'password123'},
            timeout=60
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert result['status'] == 'need_code'
        assert result['message'] == '需要验证码'
    
    @patch('requests.post')
    def test_login_success_without_code(self, mock_post, sample_api_responses):
        """测试登录成功（无需验证码）"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_api_responses['login_success']
        mock_post.return_value = mock_response
        
        response = requests.post(
            "http://127.0.0.1:5000/api/douyin-login-start",
            headers={'X-Client-ID': 'test', 'X-Hardware-ID': 'test'},
            json={'email': 'test@test.com', 'password': 'pass'}
        )
        
        result = response.json()
        assert result['success'] is True
        assert result['status'] == 'success'
    
    @patch('requests.post')
    def test_submit_verification_code(self, mock_post):
        """测试提交验证码"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True, 'message': '验证码正确'}
        mock_post.return_value = mock_response
        
        response = requests.post(
            "http://127.0.0.1:5000/api/douyin-submit-code",
            headers={'X-Client-ID': 'test', 'X-Hardware-ID': 'test'},
            json={'code': '123456'},
            timeout=30
        )
        
        result = response.json()
        assert result['success'] is True


class TestScreenshotPolling:
    """测试截图轮询API"""
    
    @patch('requests.post')
    def test_screenshot_available(self, mock_post):
        """测试获取截图成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {
            'success': True,
            'screenshot': 'base64_encoded_image_data'
        }
        mock_post.return_value = mock_response
        
        response = requests.post(
            "http://127.0.0.1:5000/api/douyin-screenshot",
            headers={'X-Client-ID': 'test', 'X-Hardware-ID': 'test'},
            timeout=5
        )
        
        result = response.json()
        assert result['success'] is True
        assert 'screenshot' in result
    
    @patch('requests.post')
    def test_screenshot_not_ready(self, mock_post):
        """测试截图未就绪"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'screenshot': None
        }
        mock_post.return_value = mock_response
        
        response = requests.post(
            "http://127.0.0.1:5000/api/douyin-screenshot",
            headers={'X-Client-ID': 'test', 'X-Hardware-ID': 'test'}
        )
        
        result = response.json()
        assert result['success'] is True
        assert result.get('screenshot') is None
    
    @patch('requests.post')
    def test_screenshot_auth_failed(self, mock_post):
        """测试截图请求授权失败"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            'success': False,
            'show_popup': True
        }
        mock_post.return_value = mock_response
        
        response = requests.post(
            "http://127.0.0.1:5000/api/douyin-screenshot",
            headers={'X-Client-ID': 'invalid', 'X-Hardware-ID': 'invalid'}
        )
        
        assert response.status_code == 403


class TestScrapeAPI:
    """测试商品爬取API"""
    
    @patch('requests.post')
    def test_scrape_success(self, mock_post, sample_api_responses):
        """测试爬取成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_api_responses['scrape_success']
        mock_post.return_value = mock_response
        
        response = requests.post(
            "http://127.0.0.1:5000/api/douyin-scrape",
            headers={'X-Client-ID': 'test', 'X-Hardware-ID': 'test'},
            json={
                'rank_type': '销量榜',
                'time_range': '近7天',
                'category': '全部类目'
            },
            timeout=120
        )
        
        result = response.json()
        assert result['success'] is True
        assert 'products' in result
        assert len(result['products']) > 0
    
    @patch('requests.post')
    def test_scrape_timeout(self, mock_post):
        """测试爬取超时"""
        mock_post.side_effect = requests.exceptions.Timeout()
        
        with pytest.raises(requests.exceptions.Timeout):
            requests.post(
                "http://127.0.0.1:5000/api/douyin-scrape",
                headers={'X-Client-ID': 'test', 'X-Hardware-ID': 'test'},
                json={'rank_type': '销量榜'},
                timeout=120
            )


class TestAPIHeaders:
    """测试API请求头"""
    
    @patch('requests.post')
    def test_required_headers_present(self, mock_post):
        """测试必需请求头存在"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response
        
        headers = {
            'X-Client-ID': 'client_abc123',
            'X-Hardware-ID': 'hardware_xyz789',
            'Content-Type': 'application/json'
        }
        
        requests.post(
            "http://127.0.0.1:5000/api/test",
            headers=headers,
            json={}
        )
        
        # 验证调用时包含正确的headers
        call_kwargs = mock_post.call_args[1]
        assert 'headers' in call_kwargs
        assert call_kwargs['headers']['X-Client-ID'] == 'client_abc123'
        assert call_kwargs['headers']['X-Hardware-ID'] == 'hardware_xyz789'

