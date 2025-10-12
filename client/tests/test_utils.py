"""
测试工具函数
"""
import pytest
import os
import json
import uuid
import hashlib
import platform
from unittest.mock import patch, mock_open


class TestHardwareID:
    """测试硬件ID生成"""
    
    def test_hardware_id_format(self):
        """测试硬件ID返回UUID格式"""
        from modern_client_ultimate import get_hardware_id
        hardware_id = get_hardware_id()
        
        # 应该是UUID字符串格式
        assert isinstance(hardware_id, str)
        assert len(hardware_id) > 0
        
        # 验证可以转换回UUID
        try:
            uuid.UUID(hardware_id)
        except ValueError:
            pytest.fail("hardware_id不是有效的UUID格式")
    
    def test_hardware_id_consistency(self):
        """测试同一机器多次调用返回相同ID"""
        from modern_client_ultimate import get_hardware_id
        
        id1 = get_hardware_id()
        id2 = get_hardware_id()
        
        assert id1 == id2


class TestClientIDGeneration:
    """测试客户端ID生成"""
    
    @patch('uuid.getnode', return_value=123456789)
    @patch('platform.node', return_value='test-machine')
    def test_client_id_generation(self, mock_node, mock_getnode):
        """测试客户端ID生成逻辑"""
        # 手动计算期望值
        hardware_id = str(uuid.UUID(int=123456789))
        unique_str = f"{hardware_id}_test-machine"
        expected_id = hashlib.md5(unique_str.encode()).hexdigest()
        
        # 导入并测试
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        # 模拟生成逻辑
        def generate_client_id():
            node_id = uuid.UUID(int=uuid.getnode())
            hardware_id = str(node_id)
            node_name = platform.node()
            unique_str = f"{hardware_id}_{node_name}"
            return hashlib.md5(unique_str.encode()).hexdigest()
        
        result = generate_client_id()
        assert result == expected_id
        assert len(result) == 32  # MD5哈希长度
    
    def test_client_id_uniqueness(self):
        """测试不同机器生成不同ID"""
        with patch('uuid.getnode', return_value=111111), \
             patch('platform.node', return_value='machine-1'):
            
            def gen_id():
                hardware_id = str(uuid.UUID(int=uuid.getnode()))
                unique_str = f"{hardware_id}_{platform.node()}"
                return hashlib.md5(unique_str.encode()).hexdigest()
            
            id1 = gen_id()
        
        with patch('uuid.getnode', return_value=222222), \
             patch('platform.node', return_value='machine-2'):
            id2 = gen_id()
        
        assert id1 != id2


class TestConfigFileOperations:
    """测试配置文件读写"""
    
    def test_load_config_existing(self, temp_config_file):
        """测试加载已存在的配置文件"""
        from modern_client_ultimate import load_config
        
        with patch('modern_client_ultimate.CONFIG_FILE', temp_config_file):
            config = load_config()
            
            assert isinstance(config, dict)
            assert 'client_id' in config
            assert config['client_id'] == 'test_client_123'
    
    def test_load_config_nonexistent(self, tmp_path):
        """测试加载不存在的配置文件返回空字典"""
        from modern_client_ultimate import load_config
        
        fake_path = str(tmp_path / "nonexistent.json")
        with patch('modern_client_ultimate.CONFIG_FILE', fake_path):
            config = load_config()
            
            assert isinstance(config, dict)
            assert len(config) == 0
    
    def test_save_config(self, tmp_path):
        """测试保存配置文件"""
        from modern_client_ultimate import save_config
        
        config_path = str(tmp_path / "test_config.json")
        test_config = {
            'client_id': 'new_client_789',
            'is_active': 1,
            'test_key': 'test_value'
        }
        
        with patch('modern_client_ultimate.CONFIG_FILE', config_path):
            save_config(test_config)
        
        # 验证文件已创建并包含正确数据
        assert os.path.exists(config_path)
        with open(config_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        
        assert loaded == test_config
    
    def test_save_load_roundtrip(self, tmp_path):
        """测试保存后加载的往返一致性"""
        from modern_client_ultimate import save_config, load_config
        
        config_path = str(tmp_path / "roundtrip.json")
        original_config = {
            'client_id': 'roundtrip_123',
            'hardware_id': 'hw_456',
            'nested': {'key': 'value'}
        }
        
        with patch('modern_client_ultimate.CONFIG_FILE', config_path):
            save_config(original_config)
            loaded_config = load_config()
        
        assert loaded_config == original_config


class TestConfigPath:
    """测试配置路径生成"""
    
    @patch('platform.system', return_value='Windows')
    def test_windows_path(self, mock_system):
        """测试Windows路径生成"""
        with patch.dict(os.environ, {'LOCALAPPDATA': r'C:\Users\Test\AppData\Local'}):
            from modern_client_ultimate import get_config_path
            path = get_config_path()
            
            assert 'AppData' in path or 'LOCALAPPDATA' in path.upper()
            assert '智能选品系统' in path
            assert path.endswith('config.json')
    
    @patch('platform.system', return_value='Linux')
    def test_linux_path(self, mock_system):
        """测试Linux路径生成"""
        from modern_client_ultimate import get_config_path
        path = get_config_path()
        
        assert '.config' in path
        assert '智能选品系统' in path
        assert path.endswith('config.json')
    
    @patch('platform.system', return_value='Darwin')
    def test_macos_path(self, mock_system):
        """测试macOS路径生成（应该与Linux相同）"""
        from modern_client_ultimate import get_config_path
        path = get_config_path()
        
        assert '.config' in path
        assert '智能选品系统' in path


class TestThemeConstants:
    """测试主题常量定义"""
    
    def test_theme_colors_defined(self):
        """测试所有主题颜色已定义"""
        from modern_client_ultimate import Theme
        
        required_colors = [
            'BG_PRIMARY', 'BG_SECONDARY', 'CARD_BG',
            'PRIMARY', 'SECONDARY', 'RED', 'ORANGE', 
            'YELLOW', 'CYAN', 'GREEN',
            'TEXT_PRIMARY', 'TEXT_SECONDARY', 'TEXT_HINT',
            'BORDER'
        ]
        
        for color in required_colors:
            assert hasattr(Theme, color), f"Theme缺少颜色定义: {color}"
            value = getattr(Theme, color)
            assert isinstance(value, str), f"{color}应该是字符串"
            assert value.startswith('#'), f"{color}应该以#开头"
    
    def test_color_hex_format(self):
        """测试颜色值为有效十六进制格式"""
        from modern_client_ultimate import Theme
        import re
        
        hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
        
        for attr in dir(Theme):
            if not attr.startswith('_'):
                value = getattr(Theme, attr)
                if isinstance(value, str) and value.startswith('#'):
                    assert hex_pattern.match(value), f"{attr}颜色值格式无效: {value}"

