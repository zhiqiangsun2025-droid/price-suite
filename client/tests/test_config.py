"""
测试配置解析逻辑
"""
import pytest
import os
import json
from unittest.mock import patch, mock_open


class TestServerURLResolution:
    """测试SERVER_URL解析逻辑"""
    
    def test_env_var_priority(self, monkeypatch, tmp_path):
        """测试环境变量优先级最高"""
        # 设置环境变量
        monkeypatch.setenv("PRICE_SUITE_SERVER_URL", "http://env.example.com:8000")
        
        # 同时创建config_client.json
        config_file = tmp_path / "config_client.json"
        config_file.write_text(json.dumps({"server_url": "http://file.example.com:9000"}))
        
        # 重新导入模块以触发解析
        import importlib
        import sys
        
        # 模拟脚本目录
        with patch('os.path.dirname') as mock_dirname, \
             patch('os.path.abspath') as mock_abspath:
            mock_abspath.return_value = str(tmp_path / "fake_script.py")
            mock_dirname.return_value = str(tmp_path)
            
            # 模拟_resolve_server_url函数
            from modern_client_ultimate import _resolve_server_url
            result = _resolve_server_url()
            
            assert result == "http://env.example.com:8000"
    
    def test_config_file_fallback(self, monkeypatch, tmp_path):
        """测试config_client.json回落"""
        # 确保环境变量不存在
        monkeypatch.delenv("PRICE_SUITE_SERVER_URL", raising=False)
        
        # 创建config_client.json
        config_file = tmp_path / "config_client.json"
        config_file.write_text(json.dumps({"server_url": "http://file.example.com:7000"}))
        
        with patch('os.path.dirname', return_value=str(tmp_path)), \
             patch('os.path.abspath', return_value=str(tmp_path / "script.py")):
            from modern_client_ultimate import _resolve_server_url
            result = _resolve_server_url()
            
            assert result == "http://file.example.com:7000"
    
    def test_default_localhost(self, monkeypatch, tmp_path):
        """测试默认值127.0.0.1:5000"""
        # 环境变量不存在
        monkeypatch.delenv("PRICE_SUITE_SERVER_URL", raising=False)
        
        # config_client.json不存在
        with patch('os.path.dirname', return_value=str(tmp_path)), \
             patch('os.path.abspath', return_value=str(tmp_path / "script.py")), \
             patch('os.path.exists', return_value=False):
            from modern_client_ultimate import _resolve_server_url
            result = _resolve_server_url()
            
            assert result == "http://127.0.0.1:5000"
    
    def test_invalid_json_fallback(self, monkeypatch, tmp_path):
        """测试JSON解析失败时回落默认值"""
        monkeypatch.delenv("PRICE_SUITE_SERVER_URL", raising=False)
        
        # 创建无效JSON文件
        config_file = tmp_path / "config_client.json"
        config_file.write_text("{ invalid json }")
        
        with patch('os.path.dirname', return_value=str(tmp_path)), \
             patch('os.path.abspath', return_value=str(tmp_path / "script.py")):
            from modern_client_ultimate import _resolve_server_url
            result = _resolve_server_url()
            
            assert result == "http://127.0.0.1:5000"
    
    def test_empty_server_url_in_config(self, monkeypatch, tmp_path):
        """测试配置文件中server_url为空字符串"""
        monkeypatch.delenv("PRICE_SUITE_SERVER_URL", raising=False)
        
        config_file = tmp_path / "config_client.json"
        config_file.write_text(json.dumps({"server_url": ""}))
        
        with patch('os.path.dirname', return_value=str(tmp_path)), \
             patch('os.path.abspath', return_value=str(tmp_path / "script.py")):
            from modern_client_ultimate import _resolve_server_url
            result = _resolve_server_url()
            
            assert result == "http://127.0.0.1:5000"
    
    def test_whitespace_trimming(self, monkeypatch):
        """测试环境变量值自动去除空白"""
        monkeypatch.setenv("PRICE_SUITE_SERVER_URL", "  http://trim.example.com:5000  ")
        
        from modern_client_ultimate import _resolve_server_url
        result = _resolve_server_url()
        
        assert result == "http://trim.example.com:5000"


class TestConfigPaths:
    """测试配置路径生成"""
    
    def test_windows_config_path(self, monkeypatch):
        """测试Windows配置路径"""
        monkeypatch.setattr('platform.system', lambda: 'Windows')
        monkeypatch.setenv('LOCALAPPDATA', r'C:\Users\Test\AppData\Local')
        
        from modern_client_ultimate import get_config_path
        path = get_config_path()
        
        assert '智能选品系统' in path
        assert 'config.json' in path
    
    def test_linux_config_path(self, monkeypatch):
        """测试Linux配置路径"""
        monkeypatch.setattr('platform.system', lambda: 'Linux')
        monkeypatch.setenv('HOME', '/home/testuser')
        
        from modern_client_ultimate import get_config_path
        path = get_config_path()
        
        assert '.config' in path
        assert '智能选品系统' in path
        assert 'config.json' in path

